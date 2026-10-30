import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

import metpy.calc as mpcalc
from metpy.units import units


def calculate_ji(radiosonde_dataset: xr.Dataset | xr.DataTree):
    """
    Calculate the Jefferson Index (JI) using
        0.6 * theta_w_850 -  T_500 - 0.5(T_700 - T_d_700) - 8

    :param radiosonde_dataset: A dataset containing radiosonde profiles.
    :return: A dataset updated with the JI for each radiosonde.
    """

    eight: int = 8

    theta_w_850 = radiosonde_dataset["theta_w"].sel(p=850, method="nearest") - 273.15

    ta_500 = radiosonde_dataset["ta"].sel(p=500, method="nearest") - 273.15

    ta_700 = radiosonde_dataset["ta"].sel(p=700, method="nearest") - 273.15

    td_700 = radiosonde_dataset["td"].sel(p=700, method="nearest") - 273.15

    ji = (1.6 * theta_w_850) - ta_500 - (0.5 * (ta_700 - td_700)) - eight  # ;)

    radiosonde_dataset["ji"] = xr.DataArray(
        ji,
        dims=radiosonde_dataset["ta"].dims[0:2],
        attrs={
            "long_name": "Jefferson Index",
            "units": "Delta Degree Celsius",
        },
    )

    return radiosonde_dataset


ds_ptu0 = xr.open_dataset("../data/netcdf/sif.ptu_radiosondes.profiles.level0.nc")
ds_ptu1 = xr.open_dataset("../data/netcdf/sif.ptu_radiosondes.profiles.level1.nc")
ds_ptu2 = xr.open_dataset("../data/netcdf/sif.ptu_radiosondes.profiles.level2.nc")
ds_ptu2 = calculate_ji(ds_ptu2)
# ds_ptu2.to_netcdf("/Users/danielrowe/Python/sif.ptu_radiosondes.profiles.level2.nc")

# launch_times1 = ds_ptu1.launch_time.values
launch_times2 = ds_ptu2.launch_time.values

# ds_std_plvl0 = xr.open_dataset("../data/netcdf/sif.std_plvl_radiosondes.profiles.level0.nc")
# ds_std_plvl1 = xr.open_dataset("../data/netcdf/sif.std_plvl_radiosondes.profiles.level1.nc")
# ds_std_plvl2 = xr.open_dataset("../data/netcdf/sif.std_plvl_radiosondes.profiles.level2.nc")
# ds_std_plvl2 = calculate_ji(ds_std_plvl2)
# ds_std_plvl2.to_netcdf("/Users/danielrowe/Python/sif.std_plvl_radiosondes.profiles.level2.nc")
#
# print(
#     f"Level 0 PTU:\n{ds_ptu0}\n\n"
#     f"Level 1 PTU:\n{ds_ptu1}\n\n"
#     f"Level 2 PTU:\n{ds_ptu2}\n\n"
#     f"Level 2 PTU DATA VARS:\n{ds_ptu2['ji'].values}\n\n"
#     f"Level 0 STDLVL:\n{ds_std_plvl0}\n\n"
#     f"Level 1 STDLVL:\n{ds_std_plvl1}\n\n"
#     f"Level 2 STDLVL:\n{ds_std_plvl2}\n\n"
#     f"Level 2 STDLVL DATA VARS:\n{ds_std_plvl2['ji'].values}\n\n"
# )


# ds_ifs0 = xr.open_dataset("../data/ifs/ifs.radiosondes.profiles.level0.nc")
# ds_ifs1 = xr.open_dataset("../data/ifs/ifs.radiosondes.profiles.level1.nc")
# ds_ifs1 = calculate_ji(ds_ifs1)
# ds_ifs1.to_netcdf("/Users/danielrowe/Python/ifs.radiosondes.profiles.level1.nc")
#
# print(
#     f"IFS DATASET LEVEL ZERO:\n{ds_ifs0}\n\n"
#     f"IFS DATASET LEVEL ONE:\n{ds_ifs1['ji'].values}\n\n"
# )
#
#
# igra = xr.open_dataset("../data/netcdf/sif.igra_radiosondes.profiles.level0.nc")
#
# print(
#     f"IGRA:\n{igra}\n\n"
#     f"IGRA DATA VARS:\n{igra.data_vars}\n\n"
#     f"IGRA STATION NAME:\n{igra.attrs}\n\n",
#     flush=True
# )

gfs0 = xr.open_dataset("../data/gfs/gfs.radiosondes.profiles.level0.nc")
gfs1 = xr.open_dataset("../data/gfs/gfs.radiosondes.profiles.level1.nc")
gfs1 = calculate_ji(gfs1)
gfs1.to_netcdf("/Users/danielrowe/Python/gfs.radiosondes.profiles.level1.nc")

# print(
#     f"GFS LEVEL ZERO:\n{gfs0}\n\n"
#     f"GFS LEVEL ONE:\n{gfs1['ji'].values}\n\n"
# )

# forecast_hour = ['anl', '12h', '24h', '48h']
# icon = xr.open_dataset("../data/icon/2026-08-11/ALL-2026-08-11-00z.nc")
# icon = icon.isel(time=[0, 12, 24, 48])
# icon = icon.assign_coords(forecast_hour=('time', forecast_hour))
# print(icon)

icon0 = xr.open_dataset("../data/icon/icon.radiosondes.profiles.level0.nc")
icon0_f12h = icon0.sel(forecast_hour="12h", height=20, station="Fehmarn")
icon0_f48h = icon0.sel(forecast_hour="48h", height=20, station="Fehmarn")

print(
    f"ICON LEVEL ZERO:\n{icon0}\n\nICON LEVEL ZERO DATA VARS:\n{icon0.data_vars}\n\n",
    flush=True,
)

# We have profiles as functions of an arbitrary height/level dimension.
icon1 = icon0.copy()

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
theta = mpcalc.potential_temperature(pressure=p.T, temperature=ta.T).to(units.kelvin)
theta_w = mpcalc.wet_bulb_potential_temperature(
    pressure=p.T, temperature=ta.T, dewpoint=td
).to(units.kelvin)
h = mpcalc.pressure_to_height_std(pressure=p.T).to(units.m)

# Calculate parcel profiles
# parcel_p, parcel_t, parcel_td = mpcalc.mixed_parcel(
#     pressure=p.T, temperature=ta.T, dewpoint=td, depth=500 * units.m, height=h
# )


# Calculate Indices
k = mpcalc.k_index(pressure=p.T, temperature=ta.T, dewpoint=td).magnitude
tt = mpcalc.total_totals_index(pressure=p.T, temperature=ta.T, dewpoint=td).magnitude

# Add computed variables to icon1 dataset
icon1["td"] = xr.DataArray(
    td.magnitude.T,
    dims=icon1["ta"].dims,
    attrs={
        "long_name": "Dewpoint Temperature",
        "units": "Kelvin",
    },
)

icon1["theta"] = xr.DataArray(
    theta.magnitude.T,
    dims=icon1["ta"].dims,
    attrs={
        "long_name": "Potential Temperature",
        "units": "Kelvin",
    },
)

icon1["theta_w"] = xr.DataArray(
    theta.magnitude.T,
    dims=icon1["ta"].dims,
    attrs={
        "long_name": "Potential Temperature",
        "units": "Kelvin",
    },
)

icon1["h"] = xr.DataArray(
    h.magnitude.T,
    dims=icon1["ta"].dims,
    attrs={
        "long_name": "Height",
        "units": "metre",
    },
)

# Add indices
icon1["k_index"] = xr.DataArray(
    k.T,
    dims=icon1["ta"].dims[0:2],
    attrs={
        "long_name": "K-Index",
        "units": "Celsius",
    },
)

icon1["tt_index"] = xr.DataArray(
    tt.T,
    dims=icon1["ta"].dims[0:2],
    attrs={
        "long_name": "Totals Totals Index",
        "units": "Delta Degree Celsius",
    },
)


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
        for index, valid_time in enumerate(station["valid_time"].values):
            profile = station.isel(valid_time=index).sortby("p", ascending=False)

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


icon1 = calculate_li(icon1)
icon1 = calculate_si(icon1)
icon1 = calculate_ri(icon1)
icon1 = calculate_ji(icon1)

valid_times_f12 = (
    icon1.sel(station="Fehmarn", forecast_hour="24h").sortby("valid_time").valid_time
)

launch_time_indices = np.where(np.isin(valid_times_f12, launch_times2))[0]

print(
    f"ICON TEST:\n{icon1.sel(station='Fehmarn', forecast_hour='24h').isel(valid_time=launch_time_indices).sortby('valid_time')}\n\n"
    f"F12H:\n{valid_times_f12.values} {valid_times_f12.forecast_hour.values} {launch_times2}"
)


all2026081100z = xr.open_dataset("../data/icon/2026-08-11/ALL-2026-08-11-00z.nc")
all2026081106z = xr.open_dataset("../data/icon/2026-08-11/ALL-2026-08-11-06z.nc")
all2026081112z = xr.open_dataset("../data/icon/2026-08-11/ALL-2026-08-11-12z.nc")
all2026081118z = xr.open_dataset("../data/icon/2026-08-11/ALL-2026-08-11-18z.nc")

print(
    f"{all2026081100z.isel(time=[0, 12, 24, 48]).time.values}\n"
    f"{all2026081106z.isel(time=[0, 12, 24, 48]).time.values}\n"
    f"{all2026081112z.isel(time=[0, 12, 24, 48]).time.values}\n"
    f"{all2026081118z.isel(time=[0, 12, 24, 48]).time.values}\n"
)

idx900 = np.abs(icon1.p - 900).argmin(dim="height")
idx850 = np.abs(icon1.p - 850).argmin(dim="height")
idx500 = np.abs(icon1.p - 500).argmin(dim="height")
idx700 = np.abs(icon1.p - 700).argmin(dim="height")
icon1_900 = icon1.isel(height=idx900).sortby("valid_time")
icon1_850 = icon1.isel(height=idx850).sortby("valid_time")
icon1_700 = icon1.isel(height=idx700).sortby("valid_time")
icon1_500 = icon1.isel(height=idx500).sortby("valid_time")
theta_w850 = icon1_850.theta_w.values
p900 = icon1_900["p"].data * units.hPa
p850 = icon1_850["p"].data * units.hPa
ta900 = icon1_900["ta"].data * units.kelvin
td900 = icon1_900["td"].data * units.kelvin
ta850 = icon1_850["ta"].data * units.kelvin
td850 = icon1_850["td"].data * units.kelvin
ta700 = icon1_700["ta"].data * units.kelvin
td700 = icon1_700["td"].data * units.kelvin
ta500 = icon1_500["ta"].data * units.kelvin
theta_w900 = mpcalc.wet_bulb_potential_temperature(
    pressure=p900, temperature=ta900, dewpoint=td900
)
theta_w850_calc = mpcalc.wet_bulb_potential_temperature(
    pressure=p850, temperature=ta850, dewpoint=td850
)

ji = (
    (1.6 * theta_w850_calc.to(units.degC))
    - ta500.to(units.degC)
    - (0.5 * (ta700.to(units.degC) - td700.to(units.degC)))
    - (8 * units.degC)
)
ri = theta_w900 - ta500

print(ri)

fig, axes = plt.subplots(nrows=3)
ax1, ax2, ax3 = axes.flatten()

# Introduce pressure grid for icon dataset.
ax1.plot(
    theta_w850,
    label="theta_w ICON",
)
ax1.plot(
    theta_w850_calc.magnitude,
    label="theta_w ICON new calc",
)
ax1.plot(
    gfs1.sel(station="Fehmarn", forecast_hour="24h", p=850)
    .sortby("valid_time")
    .theta_w.values,
    label="theta_w GFS",
)

ax2.plot(
    icon1.sel(station="Fehmarn", forecast_hour="24h").sortby("valid_time").ji.values,
    label="ji ICON def",
)
ax2.plot(ji, label="ji ICON calc")

ax3.plot(
    icon1.sel(station="Fehmarn", forecast_hour="24h").sortby("valid_time").ri.values,
    label="ri ICON def",
    color="red",
)
ax3.plot(ri, label="ri ICON calc", color="green")

fig.legend()

plt.show()

icon1["ri"] = xr.DataArray(
    ri.magnitude,
    dims=("station", "valid_time"),
    attrs={"long_name": "Rackliff Index", "units": "Delta Degrees Celsius"},
)

icon1["ji"] = xr.DataArray(
    ji.magnitude,
    dims=("station", "valid_time"),
    attrs={"long_name": "Jefferson Index", "units": "Delta Degrees Celsius"},
)

icon1.to_netcdf("/Users/danielrowe/Python/icon.radiosondes.profiles.level1.nc")

print(icon1)
