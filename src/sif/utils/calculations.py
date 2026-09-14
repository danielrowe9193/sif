import metpy.calc as mpcalc
import numpy as np
import xarray as xr

from metpy.units import units


def calculate_potential_temperature(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculates the potential temperature from a concatenated radiosonde dataset.

    :param radiosonde_dataset: The radiosonde dataset. Expects to contain pressure and temperature
    stored as 'p' and 'ta'.
    :return: A dataset updated with potential temperature labelled as theta.
    """

    p = radiosonde_dataset['p']
    ta = radiosonde_dataset['ta']

    def calc_theta(pressure, temperature):
        """Compute the potential temperature."""
        pressure = pressure * units.hPa
        temperature = temperature * units.kelvin

        _theta = mpcalc.potential_temperature(
            pressure=pressure,
            temperature=temperature
        )

        return _theta.magnitude

    theta = xr.apply_ufunc(
        calc_theta,
        p,
        ta,
        input_core_dims=[["p"], ["p"]],
        output_core_dims=[["p"]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[float],
    )

    radiosonde_dataset['theta'] = xr.DataArray(
        theta,
        dims=radiosonde_dataset["ta"].dims,
        coords=radiosonde_dataset["ta"].coords,
        attrs={
            "long_name": "potential temperature",
            "units": "K",
        },
    )


def calculate_height_from_geopotential(profile: xr.Dataset | xr.DataTree):

    geopot = profile["z"]

    def z_from_geo(geopot):

        geopot = geopot * units("m^2/s^2")
        height = mpcalc.geopotential_to_height(geopot)

        return height.magnitude

    height = xr.apply_ufunc(
        z_from_geo,
        geopot,
        input_core_dims=[["p"]],
        output_core_dims=[["p"]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[float],
    )

    profile["height"] = height

    return profile


def calculate_td_from_q(profile: xr.Dataset | xr.DataTree):

    p = profile["p"]
    q = profile["q"]

    def td(p, q):
        p = p * units.hPa
        q = q * units("kg/kg")

        td = (mpcalc.dewpoint_from_specific_humidity(p, q)).to(units.kelvin)

        return td.magnitude

    t_d = xr.apply_ufunc(
        td,
        p,
        q,
        input_core_dims=[["p"], ["p"]],
        output_core_dims=[["p"]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[float],
    )

    profile["td"] = t_d

    return profile


def calculate_td_from_rh(radiosonde_dataset: xr.Dataset | xr.DataTree) -> xr.Dataset:
    """
    Calculates dewpoint temperatures for every radiosonde in the dataset.

    Requires that the vertical coordinate is labelled 'p'.
    :param radiosonde_dataset: The dataset containing air temperature and relative humidity values with the required shape.
    :return: Updated dataset containing dewpoint temperatures as a variable 'td'
    """

    radiosonde_dataset = radiosonde_dataset.copy()

    air_temp = radiosonde_dataset["ta"].data * units.kelvin
    rel_humi = radiosonde_dataset["rh"].data * units.percent

    dew_temp = mpcalc.dewpoint_from_relative_humidity(air_temp, rel_humi).to(
        units.kelvin
    )

    radiosonde_dataset["td"] = xr.DataArray(
        dew_temp.magnitude,
        dims=radiosonde_dataset["ta"].dims,
        coords=radiosonde_dataset["ta"].coords,
        attrs={
            "long_name": "Dewpoint temperature",
            "units": "K",
        },
    )

    return radiosonde_dataset


def calculate_cape(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculate CAPE and CIN from a collection of soundings.

    Parameters
    ----------
    radiosonde_dataset : xr.Dataset | xr.DataTree
        Dataset containing p, ta and td with dimensions
        (sounding_id, p).

    Returns
    -------
    xr.Dataset
        Original dataset with CAPE and CIN added as variables
        with dimension (sounding_id,).
    """

    radiosonde_dataset = radiosonde_dataset.copy()

    cape_list = []
    cin_list = []

    for sounding_num in radiosonde_dataset.sounding_num.values:
        try:
            radiosonde = radiosonde_dataset.sel(sounding_num=sounding_num)

            p = radiosonde["p"].values * units.hPa
            t = radiosonde["ta"].values * units.kelvin
            td = radiosonde["td"].values * units.kelvin

            # Calculate parcel profile
            parcel = mpcalc.parcel_profile(p, t[0], td[0]).to("degC")

            # Calculate CAPE and CIN
            cape, cin = mpcalc.cape_cin(p, t.to("degC"), td.to("degC"), parcel)

            cape_list.append(cape.magnitude)
            cin_list.append(cin.magnitude)

        except Exception as e:
            print(f"CAPE/CIN calculation failed for sounding {sounding_num}: {e}")

            cape_list.append(np.nan)
            cin_list.append(np.nan)

    # Convert results back into xarray
    cape = xr.DataArray(
        cape_list,
        dims=["sounding_num"],
        coords={"sounding_num": radiosonde_dataset.sounding_num + 1},
        attrs={
            "long_name": "Convective Available Potential Energy",
            "units": "J/Kg",
        },
    )

    cin = xr.DataArray(
        cin_list,
        dims=["sounding_num"],
        coords={"sounding_num": radiosonde_dataset.sounding_num},
        attrs={
            "long_name": "Convective Inhibition",
            "units": "J/Kg",
        },
    )

    radiosonde_dataset["cape"] = cape
    radiosonde_dataset["cin"] = cin

    return radiosonde_dataset


def calculate_k_index(radiosonde_dataset: xr.Dataset | xr.DataTree):

    radiosonde_dataset = radiosonde_dataset.copy()

    p = (
        np.broadcast_to(radiosonde_dataset["p"].data, radiosonde_dataset["ta"].shape)
        * units.hPa
    )
    t = radiosonde_dataset["ta"].data * units.kelvin
    td = radiosonde_dataset["td"].data * units.kelvin

    k = mpcalc.k_index(p.T, t.T, td.T).magnitude

    radiosonde_dataset["k_index"] = xr.DataArray(
        k,
        dims=("sounding_num",),
        coords={"sounding_num": radiosonde_dataset["sounding_num"]},
        attrs={
            "long_name": "K-Index",
            "units": "Celsius",
        },
    )

    return radiosonde_dataset


def calculate_tt_index(radiosonde_dataset: xr.Dataset | xr.DataTree):

    radiosonde_dataset = radiosonde_dataset.copy()

    p = (
        np.broadcast_to(radiosonde_dataset["p"].data, radiosonde_dataset["ta"].shape)
        * units.hPa
    )
    ta = radiosonde_dataset["ta"].data * units.kelvin
    td = radiosonde_dataset["td"].data * units.kelvin

    tt = mpcalc.total_totals_index(p.T, ta.T, td.T).magnitude

    radiosonde_dataset["tt_index"] = xr.DataArray(
        tt,
        dims=("sounding_num",),
        coords={"sounding_num": radiosonde_dataset["sounding_num"]},
        attrs={
            "long_name": "Totals Totals Index",
            "units": "Celsius",
        },
    )

    return radiosonde_dataset


def calculate_li(radiosonde_dataset: xr.Dataset | xr.DataTree):

    def calculate_single_li(p, ta, td, h):

        try:
            # Attach units
            p = p * units.hPa
            ta = ta * units.kelvin
            td = td * units.kelvin
            h = h * units.m

            # 500-m mixed parcel
            parcel_p, parcel_t, parcel_td = mpcalc.mixed_parcel(
                p, ta, td, depth=500 * units.m, height=h
            )

            # Replace lowest 500 m with mixed parcel
            above = h > 500 * units.m

            press = np.concatenate([[parcel_p], p[above]])

            temp = np.concatenate([[parcel_t], ta[above]])

            # Parcel profile
            mixed_prof = mpcalc.parcel_profile(press, parcel_t, parcel_td)

            # Lifted Index
            li = mpcalc.lifted_index(press, temp, mixed_prof)

            return li.magnitude.item()

        except Exception:
            return np.nan

    li = xr.apply_ufunc(
        calculate_single_li,
        radiosonde_dataset["p"],
        radiosonde_dataset["ta"],
        radiosonde_dataset["td"],
        radiosonde_dataset["height"],
        input_core_dims=[
            ["p"],
            ["p"],
            ["p"],
            ["p"],
        ],
        output_core_dims=[[]],
        vectorize=True,
        output_dtypes=[float],
    )

    radiosonde_dataset["li"] = xr.DataArray(
        li,
        dims=("sounding_num",),
        coords={"sounding_num": radiosonde_dataset["sounding_num"]},
        attrs={
            "long_name": "Lifted Index",
            "units": "Celsius",
        },
    )

    return radiosonde_dataset
