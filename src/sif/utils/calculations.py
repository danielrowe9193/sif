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
            "long_name": "Potential Temperature",
            "units": "K",
        },
    )

    return radiosonde_dataset


def calculate_wet_bulb_potential_temperature(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculates the wet bulb potential temperature for each radiosonde in a given
    dataset.

    :param radiosonde_dataset: The radiosonde dataset. Expects to contain pressure and temperature
    stored as 'p' and 'ta'.
    :return: A dataset updated with wet bulb potential temperature labelled as theta_w.
    """

    p = radiosonde_dataset['p']
    ta = radiosonde_dataset['ta']
    td = radiosonde_dataset['td']

    def calc_wet_bulb_potential_temperature(pressure, temperature, dewpoint):
        """Calculate and return wet bulb potential temperature."""
        press = pressure * units.hPa
        temp = temperature * units.kelvin
        dew = dewpoint * units.kelvin

        _theta_w = mpcalc.wet_bulb_potential_temperature(
            pressure=press,
            temperature=temp,
            dewpoint=dew
        )

        return _theta_w.magnitude

    theta_w = xr.apply_ufunc(
        calc_wet_bulb_potential_temperature,
        p,
        ta,
        td,
        input_core_dims=[
            ["p"],
            ["p"],
            ["p"]
        ],
        output_core_dims=[["p"]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[float],
    )

    radiosonde_dataset['theta_w'] = xr.DataArray(
        theta_w,
        dims=radiosonde_dataset["ta"].dims,
        coords=radiosonde_dataset["ta"].coords,
        attrs={
            "long_name": "Wet Bulb Potential Temperature",
            "units": "K",
        },
    )

    return radiosonde_dataset


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


def calculate_cape_with_loop(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculate CAPE and CIN from a collection of soundings.

    The calculations are done using a loop.

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
        dims=radiosonde_dataset["ta"].dims,
        attrs={
            "long_name": "Convective Available Potential Energy",
            "units": "J/Kg",
        },
    )

    cin = xr.DataArray(
        cin_list,
        dims=radiosonde_dataset["ta"].dims,
        attrs={
            "long_name": "Convective Inhibition",
            "units": "J/Kg",
        },
    )

    radiosonde_dataset["cape"] = cape
    radiosonde_dataset["cin"] = cin

    return radiosonde_dataset


def calculate_cape_cin(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calcualtes the CAPE and CIN using array broadcasting.
    :param radiosonde_dataset:
    :return:
    """

    radiosonde_dataset = radiosonde_dataset.copy()

    p = radiosonde_dataset["p"]
    ta = radiosonde_dataset["ta"]
    td = radiosonde_dataset["td"]

    def calc_cape_cin(pressure, temperature, dewpoint):
        """Calculate and return the CAPE and CIN."""

        pres = pressure * units.hPa
        temp = temperature * units.kelvin
        dewp = dewpoint * units.kelvin

        prof = mpcalc.parcel_profile(pres, temp[0], dewp[0])

        _cape, _cin = mpcalc.cape_cin(
            pres,
            temp,
            dewp,
            prof
        )

        return _cape.magnitude, _cin.magnitude

    cape, cin = xr.apply_ufunc(
        calc_cape_cin,
        p,
        ta,
        td,
        input_core_dims=[["p"], ["p"], ["p"]],
        output_core_dims=[[], []],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[float, float],
    )

    radiosonde_dataset["cape"] = xr.DataArray(
        cape,
        dims=radiosonde_dataset["ta"].dims[0:2],
        attrs={
            "long_name": "Convective Available Potential Energy",
            "units": "J/Kg",
        },
    )

    radiosonde_dataset["cin"] = xr.DataArray(
        cin,
        dims=radiosonde_dataset["ta"].dims[0:2],
        attrs={
            "long_name": "Convective Inhibition",
            "units": "J/Kg",
        },
    )

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
        k.T,
        dims=radiosonde_dataset["ta"].dims[0:2],
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
        tt.T,
        dims=radiosonde_dataset["ta"].dims[0:2],
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
        dims=radiosonde_dataset["ta"].dims[0:2],
        attrs={
            "long_name": "Lifted Index",
            "units": "Celsius",
        },
    )

    return radiosonde_dataset


def calculate_si(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculate the Showalter Index (SI) for each radiosonde in a dataset.
    :param radiosonde_dataset: A dataset containing radiosonde profiles.
    :return: A dataset updated with the SI for each radiosonde.
    """

    p = radiosonde_dataset['p']
    ta = radiosonde_dataset['ta']
    td = radiosonde_dataset['td']

    def calc_si(pressure, temperature, dewpoint):
        """Calculate the SI and return the magnitude."""

        press = pressure * units.hPa
        temp = temperature * units.kelvin
        dew = dewpoint * units.kelvin

        _si = mpcalc.showalter_index(
            pressure=press,
            temperature=temp,
            dewpoint=dew
        )

        return _si.magnitude.item()

    si = xr.apply_ufunc(
        calc_si,
        p,
        ta,
        td,
        input_core_dims=[
            ["p"],
            ["p"],
            ["p"],
        ],
        output_core_dims=[[]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[float],
    )

    radiosonde_dataset['si'] = xr.DataArray(
        si,
        dims=radiosonde_dataset["ta"].dims[0:2],
        attrs={
            "long_name": "Showalter Index",
            "units": "Delta Degree Celsius",
        },
    )

    return radiosonde_dataset


def calculate_ri(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculates the Rackliff Index (RI) using
        theta_w_900 - T_500

    :param radiosonde_dataset: A dataset containing radiosonde profiles.
    :return: A dataset updated with the RI for each radiosonde.
    """

    theta_w_900 = radiosonde_dataset['theta_w'].sel(
        p=900, method='nearest'
    )

    ta_500 = radiosonde_dataset['ta'].sel(
        p=500, method='nearest'
    )

    ri = theta_w_900 - ta_500

    radiosonde_dataset['ri'] = xr.DataArray(
        ri,
        dims=radiosonde_dataset["ta"].dims[0:2],
        attrs={
            "long_name": "Rackliff Index",
            "units": "Delta Degree Celsius",
        },
    )

    return radiosonde_dataset


def calculate_ji(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculate the Jefferson Index (JI) using
        0.6 * theta_w_850 -  T_500 - 0.5(T_700 - T_d_700) - 8

    :param radiosonde_dataset: A dataset containing radiosonde profiles.
    :return: A dataset updated with the JI for each radiosonde.
    """

    eight: int = 8

    theta_w_850 = radiosonde_dataset["theta_w"].sel(
        p=850, method='nearest'
    )

    ta_500 = radiosonde_dataset['ta'].sel(
        p=500, method='nearest'
    )

    ta_700 = radiosonde_dataset['ta'].sel(
        p=700, method='nearest'
    )

    td_700 = radiosonde_dataset['td'].sel(
        p=700, method='nearest'
    )

    ji = (1.6 * theta_w_850) - ta_500 - (0.5 * (ta_700 - td_700)) - eight  # ;)

    radiosonde_dataset['ji'] = xr.DataArray(
        ji,
        dims=radiosonde_dataset["ta"].dims[0:2],
        attrs={
            "long_name": "Jefferson Index",
            "units": "Delta Degree Celsius",
        },
    )

    return radiosonde_dataset


def calculate_pwbi(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculate the Potential Wet Bulb Index (PWBI).
    :param radiosonde_dataset:
    :return:
    """
    ...


def calculate_ciir(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculate the Convective Instability Index of Reap
    :param radiosonde_dataset:
    :return:
    """
    ...


def calculate_ko(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculate the Konvectionsindex (KO)
    :param radiosonde_dataset:
    :return:
    """
    ...


def calculate_bi(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculate the Boyden Index (BI)
    :param radiosonde_dataset:
    :return:
    """
    ...


def calculate_brn(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculate the Bulk Richardson Number (BRN)
    :param radiosonde_dataset:
    :return:
    """
    ...


def calculate_pw(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculate the Precipitable Water (PW) for each radiosonde in a dataset.
    :param radiosonde_dataset: A dataset containing radiosonde profiles.
    :return: A dataset updated with the PW for each radiosonde.
    """

    p = radiosonde_dataset['p']
    td = radiosonde_dataset['td']

    def calc_pw(pressure, dewpoint):
        """Calculate and return PW."""

        pres = pressure * units.hPa
        dew = dewpoint * units.kelvin

        _pw = mpcalc.precipitable_water(
            pressure=pres,
            dewpoint=dew
        )

        return _pw.magnitude.item()

    pw = xr.apply_ufunc(
        calc_pw,
        p,
        td,
        input_core_dims=[
            ["p"],
            ["p"],
        ],
        output_core_dims=[[]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[float],
    )

    radiosonde_dataset['pw'] = xr.DataArray(
        pw,
        dims=radiosonde_dataset["ta"].dims[0:2],
        attrs={
            "long_name": "Precipitable Water",
            "units": "millimeter",
        },
    )

    return radiosonde_dataset


def round_to_synoptic_hour(times: np.ndarray):
    """Rounds launch times for radiosondes to the nearest synoptic hour."""

    synoptic_hours = np.array([0, 6, 12, 18])

    hours = times.astype('datetime64[h]').astype(int) % 24
    nearest = synoptic_hours[
        np.argmin(
            np.abs(hours[:, None] - synoptic_hours),
            axis=1
        )
    ]

    rounded = times.astype("datetime64[D]") + nearest.astype("timedelta64[h]")

    return rounded
