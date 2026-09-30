# Prepare level 1 ICON dataset.

import metpy.calc as mpcalc
import numpy as np
import src.sif.utils.file_management as fm
import xarray as xr

from metpy.units import units


# Constants
icon0 = xr.open_dataset(fm.ICON_DIR / "icon.radiosondes.profiles.level0.nc")
icon1 = icon0.copy()


def calculate_li(radiosonde_dataset: xr.Dataset | xr.DataArray):
    """
    Calculate Lifted Index using loops.
    :param radiosonde_dataset: A dataset with radiosonde data.
    :return: A dataset with totals index.
    """

    radiosonde_dataset = radiosonde_dataset.copy()

    li_stations = []

    for index, station in enumerate(radiosonde_dataset.station.values):
        station = radiosonde_dataset.sel(station=station)
        li_list = []
        for index, valid_time in enumerate(station["valid_time"].values):
            profile = station.isel(valid_time=index).sortby("p", ascending=False)

            p = profile["p"].values * units.hPa
            ta = profile["ta"].values * units.kelvin
            td = profile["td"].values * units.kelvin
            h = profile["h"].values * units.m

            # Calculate 500m mixed parcel
            parcel_p, parcel_t, parcel_td = mpcalc.mixed_parcel(
                p, ta, td, depth=500 * units.m, height=h
            )

            # Replace sounding temp/pressure in lowest 500m with mixed values
            above = h > 500 * units.m
            press = np.concatenate([[parcel_p], p[above]])
            temp = np.concatenate([[parcel_t], ta[above]])

            # Calculate parcel profile from our new mixed parcel
            mixed_prof = mpcalc.parcel_profile(press, parcel_t, parcel_td)

            # Calculate lifted index using our mixed profile
            li = mpcalc.lifted_index(press, temp, mixed_prof)

            li_list.append(li)
        li_stations.append(li_list)

    stations_arr = np.array(li_stations)

    radiosonde_dataset["li"] = xr.DataArray(
        stations_arr[:, :, 0],
        dims=radiosonde_dataset["k_index"].dims,
        attrs={
            "long_name": "Lifted Index",
            "units": "Delta Degree Celsius",
        },
    )

    return radiosonde_dataset


def calculate_si(radiosonde_dataset: xr.Dataset | xr.DataArray):
    """
    Calculate Showalter Index using loops.
    :param radiosonde_dataset: A dataset with radiosonde data.
    :return: A dataset with Showalter index.
    """

    si_stations = []

    for index, station in enumerate(radiosonde_dataset.station.values):
        station = radiosonde_dataset.sel(station=station)
        si_list = []
        for idx, valid_time in enumerate(station["valid_time"].values):
            profile = station.isel(valid_time=idx).sortby("p", ascending=False)

            p = profile["p"].values * units.hPa
            ta = profile["ta"].values * units.kelvin
            td = profile["td"].values * units.kelvin

            si = mpcalc.showalter_index(p, ta, td)

            si_list.append(si)
        si_stations.append(si_list)

    stations_arr = np.array(si_stations)

    radiosonde_dataset["si"] = xr.DataArray(
        stations_arr[:, :, 0],
        dims=radiosonde_dataset["k_index"].dims,
        attrs={
            "long_name": "Showalter Index",
            "units": "Delta Degree Celsius",
        },
    )

    return radiosonde_dataset


def calculate_ri(radiosonde_dataset: xr.Dataset | xr.DataArray):
    """
    Calculate Rackliff Index using loops.
    :param radiosonde_dataset: A dataset with radiosonde data.
    :return: A dataset with Rackliff index.
    """

    ri_stations = []
    for index, station in enumerate(radiosonde_dataset.station.values):
        station = radiosonde_dataset.sel(station=station)
        ri_list = []
        for index, valid_time in enumerate(station["valid_time"].values):
            profile = station.isel(valid_time=index).sortby("p", ascending=False)

            target_pressure_900 = 900
            target_pressure_500 = 500

            nearest_level_900 = np.abs(profile["p"] - target_pressure_900).argmin()

            nearest_level_500 = np.abs(profile["p"] - target_pressure_500).argmin()

            theta_w_900 = profile["theta_w"].isel(height=nearest_level_900)

            ta_500 = profile["ta"].isel(height=nearest_level_500)

            ri = theta_w_900 - ta_500

            ri_list.append(ri)

        ri_stations.append(ri_list)

    stations_arr = np.array(ri_stations)

    radiosonde_dataset["ri"] = xr.DataArray(
        stations_arr,
        dims=radiosonde_dataset["k_index"].dims,
        attrs={
            "long_name": "Rackliff Index",
            "units": "Delta Degree Celsius",
        },
    )

    return radiosonde_dataset


def calculate_ji(radiosonde_dataset: xr.Dataset | xr.DataArray):
    """
    Calculate Jefferson Index using loops.
    :param radiosonde_dataset: A dataset with radiosonde data.
    :return: A dataset with Jefferson index.
    """

    ji_stations = []
    for index, station in enumerate(radiosonde_dataset.station.values):
        station = radiosonde_dataset.sel(station=station)
        ji_list = []
        for index, valid_time in enumerate(station["valid_time"].values):
            profile = station.isel(valid_time=index).sortby("p", ascending=False)

            target_pressure_850 = 850
            target_pressure_700 = 700
            target_pressure_500 = 500

            nearest_level_850 = np.abs(profile["p"] - target_pressure_850).argmin()

            nearest_level_700 = np.abs(profile["p"] - target_pressure_700).argmin()

            nearest_level_500 = np.abs(profile["p"] - target_pressure_500).argmin()

            theta_w_850 = profile["theta_w"].isel(height=nearest_level_850) - 273.15

            ta_500 = profile["ta"].isel(height=nearest_level_500) - 273.15

            ta_700 = profile["ta"].isel(height=nearest_level_700) - 273.15

            td_700 = profile["td"].isel(height=nearest_level_700) - 273.15

            ji = (1.6 * theta_w_850) - ta_500 - (0.5 * (ta_700 - td_700)) - 8  # ;)

            ji_list.append(ji)

        ji_stations.append(ji_list)

    stations_arr = np.array(ji_stations)

    radiosonde_dataset["ji"] = xr.DataArray(
        stations_arr,
        dims=radiosonde_dataset["k_index"].dims,
        attrs={
            "long_name": "Jefferson Index",
            "units": "Delta Degree Celsius",
        },
    )

    return radiosonde_dataset


# Attach units to our pressure and temperature profiles.
# Dewpoint temperature does not exist as a variable in ICON datasets. Therefore, we calculate it from q, ta and p.
# Transpositions are applied to align datasets to achieve metpy compliance.
p = icon1["p"].values * units.hPa
ta = icon1["ta"].values * units.kelvin
q = icon1["q"].values * units("kg/kg")
# Calculate profile quantities
td = mpcalc.dewpoint_from_specific_humidity(pressure=p.T, specific_humidity=q.T).to(
    units.kelvin
)
rh = mpcalc.relative_humidity_from_specific_humidity(pressure=p.T, temperature=ta.T, specific_humidity=q.T)
theta = mpcalc.potential_temperature(pressure=p.T, temperature=ta.T).to(units.kelvin)
theta_w = mpcalc.wet_bulb_potential_temperature(
    pressure=p.T, temperature=ta.T, dewpoint=td
).to(units.kelvin)
h = mpcalc.pressure_to_height_std(pressure=p.T).to(units.m)

# Calculate Indices
k = mpcalc.k_index(pressure=p.T, temperature=ta.T, dewpoint=td).magnitude
tt = mpcalc.total_totals_index(pressure=p.T, temperature=ta.T, dewpoint=td).magnitude

# Add computed variables to icon1 dataset
icon1['rh'] = xr.DataArray(
    rh.magnitude.T * 100,
    dims=icon1['ta'].dims,
    attrs={
        "long_name": "Relative Humidity",
        "units": "Percent",
    },
)

icon1['td'] = xr.DataArray(
    td.magnitude.T,
    dims=icon1['ta'].dims,
    attrs={
        "long_name": "Dewpoint Temperature",
        "units": "Kelvin",
    },
)

icon1['theta'] = xr.DataArray(
    theta.magnitude.T,
    dims=icon1['ta'].dims,
    attrs={
        "long_name": "Potential Temperature",
        "units": "Kelvin",
    },
)

icon1['theta_w'] = xr.DataArray(
    theta.magnitude.T,
    dims=icon1['ta'].dims,
    attrs={
        "long_name": "Potential Temperature",
        "units": "Kelvin",
    },
)

icon1['h'] = xr.DataArray(
    h.magnitude.T,
    dims=icon1['ta'].dims,
    attrs={
        "long_name": "Height",
        "units": "metre",
    },
)

# Add indices
icon1['k_index'] = xr.DataArray(
    k.T,
    dims=icon1['ta'].dims[0:2],
    attrs={
        "long_name": "K-Index",
        "units": "Celsius",
    },
)

icon1['tt_index'] = xr.DataArray(
    tt.T,
    dims=icon1['ta'].dims[0:2],
    attrs={
        "long_name": "Totals Totals Index",
        "units": "Delta Degree Celsius",
    }
)

icon1 = calculate_li(icon1)
icon1 = calculate_si(icon1)
icon1 = calculate_ri(icon1)
icon1 = calculate_ji(icon1)

icon1.to_netcdf(fm.ICON_DIR / "icon.radiosondes.profiles.level1.nc")

