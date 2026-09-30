from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import root_mean_squared_error, r2_score, mean_absolute_error
import xarray as xr

from src.sif.utils.overview_poster_comp import load_ds, mod_fxxh
from src.sif.utils.file_management import NETCDF_DIR


# Load the Fehmarn radiosonde dataset and select the launch times.
ref_dataset = 'sif.std_plvl_radiosondes.profiles.level2.nc'
ds = load_ds(ref_dataset)

station_name = ds.station.values.item()     # Fehmarn

fehmarn = ds.sel(station=station_name, p=slice(None, 70))
launch_times = fehmarn.launch_time.values
sounding_nums = fehmarn.sounding_num.values


# Load ERA5.
era5 = load_ds('era5.radiosondes.profiles.level1.nc')


# Load the IFS.
ifs_dataset = 'ifs.radiosondes.profiles.level1.nc'
ifs = load_ds(ifs_dataset).sel(station=station_name)

ifs_f12h = mod_fxxh(ifs, "12h", launch_times)
ifs_f24h = mod_fxxh(ifs, "24h", launch_times)
ifs_f48h = mod_fxxh(ifs, "48h", launch_times)


# Load the GFS.
gfs_dataset = 'gfs.radiosondes.profiles.level1.nc'
gfs = load_ds(gfs_dataset).sel(station=station_name)

gfs_f12h = mod_fxxh(gfs, "12h", launch_times)
gfs_f24h = mod_fxxh(gfs, "24h", launch_times)
gfs_f48h = mod_fxxh(gfs, "48h", launch_times)


# Common pressure levels.
common_p = fehmarn.p.values

for ds in [era5, ifs_f12h, ifs_f24h, ifs_f48h, gfs_f12h, gfs_f24h, gfs_f48h]:
    common_p = np.intersect1d(common_p, ds.p.values)


# Model and forecast datasets.
models = ["ERA5", "GFS", "IFS"]
lead_times = ["00h", "12h", "24h", "48h"]

forecast_datasets = {
    "ERA5": {
        "00h": era5,
    },
    "GFS": {
        "12h": gfs_f12h,
        "24h": gfs_f24h,
        "48h": gfs_f48h,
    },
    "IFS": {
        "12h": ifs_f12h,
        "24h": ifs_f24h,
        "48h": ifs_f48h,
    },
}


# Initialize empty arrays.
shape = (
    len(models),
    len(lead_times),
    len(common_p),
)

ta_r2 = np.full(shape, np.nan)
ta_rmse = np.full(shape, np.nan)
ta_bias = np.full(shape, np.nan)
ta_mae = np.full(shape, np.nan)

td_r2 = np.full(shape, np.nan)
td_rmse = np.full(shape, np.nan)
td_bias = np.full(shape, np.nan)
td_mae = np.full(shape, np.nan)

n_ta = np.zeros(shape, dtype=int)
n_td = np.zeros(shape, dtype=int)


# Calculate statistics.
for i, model_name in enumerate(models):

    for j, forecast_hour in enumerate(lead_times):

        # ERA5 only has a 00h entry.
        # GFS and IFS have 12h, 24h, and 48h entries.
        if forecast_hour not in forecast_datasets[model_name]:
            continue

        model_ds = forecast_datasets[model_name][forecast_hour]

        for k, p in enumerate(common_p):

            # Temperature
            obs_ta = fehmarn.ta.sel(p=p).values
            mod_ta = model_ds.ta.sel(p=p).values

            valid_ta = np.isfinite(obs_ta) & np.isfinite(mod_ta)

            obs_ta = obs_ta[valid_ta]
            mod_ta = mod_ta[valid_ta]

            n_ta[i, j, k] = len(obs_ta)

            if len(obs_ta) >= 2:
                ta_r2[i, j, k] = r2_score(obs_ta, mod_ta)
                ta_rmse[i, j, k] = root_mean_squared_error(obs_ta, mod_ta)
                ta_bias[i, j, k] = np.mean(mod_ta - obs_ta)
                ta_mae[i, j, k] = mean_absolute_error(obs_ta, mod_ta)

            # Dewpoint
            obs_td = fehmarn.td.sel(p=p).values
            mod_td = model_ds.td.sel(p=p).values

            valid_td = np.isfinite(obs_td) & np.isfinite(mod_td)

            obs_td = obs_td[valid_td]
            mod_td = mod_td[valid_td]

            n_td[i, j, k] = len(obs_td)

            if len(obs_td) >= 2:
                td_r2[i, j, k] = r2_score(obs_td, mod_td)
                td_rmse[i, j, k] = root_mean_squared_error(obs_td, mod_td)
                td_bias[i, j, k] = np.mean(mod_td - obs_td)
                td_mae[i, j, k] = mean_absolute_error(obs_td, mod_td)


# Create statistics Dataset
stats_ds = xr.Dataset(
    {
        "ta_r2": (
            ("model", "lead_time", "p"),
            ta_r2,
            {
                "long_name": "Temperature coefficient of determination",
                "description": (
                    "Coefficient of determination between observed "
                    "and model temperature"
                ),
                "units": "1",
            },
        ),
        "ta_rmse": (
            ("model", "lead_time", "p"),
            ta_rmse,
            {
                "long_name": "Temperature root mean square error",
                "description": (
                    "Root mean square error between observed "
                    "and model temperature"
                ),
                "units": "K",
            },
        ),
        "ta_bias": (
            ("model", "lead_time", "p"),
            ta_bias,
            {
                "long_name": "Temperature bias",
                "description": (
                    "Mean model temperature minus observed temperature"
                ),
                "units": "K",
            },
        ),
        "ta_mae": (
            ("model", "lead_time", "p"),
            ta_mae,
            {
                "long_name": "Temperature mean absolute error",
                "description": (
                    "Mean absolute error between observed "
                    "and model temperature"
                ),
                "units": "K",
            },
        ),
        "td_r2": (
            ("model", "lead_time", "p"),
            td_r2,
            {
                "long_name": "Dewpoint coefficient of determination",
                "description": (
                    "Coefficient of determination between observed "
                    "and model dewpoint"
                ),
                "units": "1",
            },
        ),
        "td_rmse": (
            ("model", "lead_time", "p"),
            td_rmse,
            {
                "long_name": "Dewpoint root mean square error",
                "description": (
                    "Root mean square error between observed "
                    "and model dewpoint"
                ),
                "units": "K",
            },
        ),
        "td_bias": (
            ("model", "lead_time", "p"),
            td_bias,
            {
                "long_name": "Dewpoint bias",
                "description": (
                    "Mean model dewpoint minus observed dewpoint"
                ),
                "units": "K",
            },
        ),
        "td_mae": (
            ("model", "lead_time", "p"),
            td_mae,
            {
                "long_name": "Dewpoint mean absolute error",
                "description": (
                    "Mean absolute error between observed "
                    "and model dewpoint"
                ),
                "units": "K",
            },
        ),
        "n_ta": (
            ("model", "lead_time", "p"),
            n_ta,
            {
                "long_name": "Number of valid temperature pairs",
                "description": (
                    "Number of paired valid observation and "
                    "model temperature values"
                ),
                "units": "1",
            },
        ),
        "n_td": (
            ("model", "lead_time", "p"),
            n_td,
            {
                "long_name": "Number of valid dewpoint pairs",
                "description": (
                    "Number of paired valid observation and "
                    "model dewpoint values"
                ),
                "units": "1",
            },
        ),
    },
    coords={
        "model": (
            "model",
            models,
            {
                "long_name": "Numerical weather prediction model",
            },
        ),
        "lead_time": (
            "lead_time",
            lead_times,
            {
                "long_name": "Forecast lead time",
            },
        ),
        "p": (
            "p",
            common_p,
            {
                "long_name": "Pressure",
                "standard_name": "air_pressure",
                "units": "hPa",
            },
        ),
    },
    attrs={
        "title": f"{station_name} Radiosonde Model Verification Statistics",
        "description": (
            "Statistical comparison of ERA5, IFS, and GFS model temperature "
            f"and dewpoint against {station_name} radiosonde observations. ERA5 is "
            "ncluded at 00h, while IFS and GFS are included at 12h, 24h, "
            "and 48h forecast lead times."
        ),
        "station": f'{station_name}',
        "reference_dataset": (
            f"{ref_dataset}"
        ),
        "model_datasets": (
            "era5.radiosondes.profiles.level1.nc; "
            f"{ifs_dataset}; "
            f"{gfs_dataset}"
        ),
        "models": "ERA5; GFS; IFS",
        "lead_times": "00h; 12h; 24h; 48h",
        "statistics": "R²; RMSE; bias; MAE; sample size",
        "temperature_variable": "ta",
        "dewpoint_variable": "td",
        "date_start": pd.to_datetime(launch_times.min()).strftime("%B %d, %Y %H:%M"),
        "date_end": pd.to_datetime(launch_times.min()).strftime("%B %d, %Y %H:%M"),
        "created": datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M"),
    },
)

filename = station_name.lower() + ".per_level_stats.nc"

stats_ds.to_netcdf(NETCDF_DIR / filename)
print(f"Saved {filename} to {NETCDF_DIR.resolve()}.")