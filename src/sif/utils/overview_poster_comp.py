from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from sklearn.metrics import mean_squared_error, r2_score

from src.sif.utils.file_management import NETCDF_DIR


def load_ds(filename: str):
    """Load the netcdf file into a xr.Dataset from its filename."""
    path = NETCDF_DIR / Path(filename)
    ds = xr.open_dataset(path)
    return ds


def mod_fxxh(model: xr.Dataset, forecast_hour: str, times: np.ndarray) -> xr.Dataset:
    """Load the given model data for the given forecast hour for the given times."""
    ds = (
        model
        .where(model.forecast_hour == forecast_hour, drop=True)
        .sortby("valid_time")
        .sel(valid_time=times, method='nearest')
    )

    return ds


def calculate_stats(
    observation: np.ndarray,
    model: np.ndarray,
) -> dict:
    """Calculate statistics between observations and model values."""

    observation = np.asarray(observation)
    model = np.asarray(model)

    # Remove pairs where either observation or model is NaN.
    valid = np.isfinite(observation) & np.isfinite(model)

    observation = observation[valid]
    model = model[valid]

    stats = {
        "R2": r2_score(observation, model),
        "RMSE": np.sqrt(mean_squared_error(observation, model)),
        "Bias": np.mean(model - observation),
    }

    return stats


# Load the Fehmarn radiosonde dataset and select the launch times.
fehmarn = load_ds('sif.std_plvl_radiosondes.profiles.level2.nc').sel(station='Fehmarn')
launch_times = fehmarn.launch_time.values
sounding_nums = fehmarn.sounding_num.values

# Date/time labels for the x-axis.
tick_labels = [
    mdates.num2date(mdates.date2num(time)).strftime(format="%m-%d %H:%M")
    for time in launch_times[sounding_nums]
]

# Y-axis limits for each stability index.
y_limits = {
    "k_index": (-15, 40),
    "ri": (19, 35),
    "ji": (None, None),
    "li": (0, 16),
}


# Load the IFS.
ifs = load_ds('ifs.radiosondes.profiles.level1.nc').sel(station='Fehmarn')

ifs_f12h = (mod_fxxh(ifs, "12h", launch_times)
            .assign_coords(sounding_num=('valid_time', fehmarn.sounding_num.values))
            )
ifs_f24h = (mod_fxxh(ifs, "24h", launch_times)
            .assign_coords(sounding_num=('valid_time', fehmarn.sounding_num.values))
            )
ifs_f48h = (mod_fxxh(ifs, "48h", launch_times)
            .assign_coords(sounding_num=('valid_time', fehmarn.sounding_num.values))
            )


# Load the GFS.
gfs = load_ds('gfs.radiosondes.profiles.level1.nc').sel(station='Fehmarn')

gfs_f12h = (mod_fxxh(gfs, "12h", launch_times)
            .assign_coords(sounding_num=('valid_time', fehmarn.sounding_num.values))
            )
gfs_f24h = (mod_fxxh(gfs, "24h", launch_times)
            .assign_coords(sounding_num=('valid_time', fehmarn.sounding_num.values))
            )
gfs_f48h = (mod_fxxh(gfs, "48h", launch_times)
            .assign_coords(sounding_num=('valid_time', fehmarn.sounding_num.values))
            )


# Stability indices to plot.
indices = [
    "k_index",
    "ri",
    "ji",
    "li",
]

# Forecast datasets.
forecast_datasets = {
    "12 Hour Forecast": (ifs_f12h, gfs_f12h),
    "24 Hour Forecast": (ifs_f24h, gfs_f24h),
    "48 Hour Forecast": (ifs_f48h, gfs_f48h),
}


# Plotting
fig, axes = plt.subplots(4, 3, figsize=(28, 24), sharex=True)

# Plot each stability index.
for row, index in enumerate(indices):

    for col, (forecast_hour, (ifs_ds, gfs_ds)) in enumerate(forecast_datasets.items()):

        ax = axes[row, col]

        # Fehmarn observation.
        ax.plot(
            sounding_nums,
            fehmarn[index].values,
            color="black",
            linewidth=2,
            marker="o",
            label="Fehmarn",
        )

        # IFS.
        ax.plot(
            sounding_nums,
            ifs_ds[index].values,
            color="gold",
            marker="o",
            label="IFS",
        )

        # GFS.
        ax.plot(
            sounding_nums,
            gfs_ds[index].values,
            color="red",
            marker="o",
            label="GFS",
        )

        # Column title.
        if row == 0:
            ax.set_title(forecast_hour, fontsize=14, fontweight="bold")

        # Y-axis label.
        if col == 0:
            ax.set_ylabel(fehmarn[index].attrs.get("long_name", index), fontsize=12)

        ax.set_ylim(y_limits[index])

        # X-axis label.
        if row == len(indices) - 1:
            ax.set_xlabel("Launch time", fontsize=12,)

        ax.set_xticks(sounding_nums)
        ax.set_xticklabels(tick_labels, rotation=45, ha="right")
        ax.set_xlim(sounding_nums.min(), sounding_nums.max())


        # Compute statistics.
        ifs_stats = calculate_stats(
            fehmarn[index].values,
            ifs_ds[index].values,
        )

        gfs_stats = calculate_stats(
            fehmarn[index].values,
            gfs_ds[index].values,
        )

        stats_text = (
            "IFS\n"
            f"$R^2$ = {ifs_stats['R2']:.2f}\n"
            f"RMSE = {ifs_stats['RMSE']:.2f}\n"
            f"Bias = {ifs_stats['Bias']:.2f}\n\n"
            "GFS\n"
            f"$R^2$ = {gfs_stats['R2']:.2f}\n"
            f"RMSE = {gfs_stats['RMSE']:.2f}\n"
            f"Bias = {gfs_stats['Bias']:.2f}"
        )

        if row == 0:
            ax.text(
                0.80,
                0.52,
                stats_text,
                transform=ax.transAxes,
                verticalalignment="top",
                fontsize=14,
                bbox=dict(
                    boxstyle="round",
                    facecolor="white",
                    alpha=0.8,
                ),
            )

        elif row == 1:
            ax.text(
                0.02,
                0.98,
                stats_text,
                transform=ax.transAxes,
                verticalalignment="top",
                fontsize=14,
                bbox=dict(
                    boxstyle="round",
                    facecolor="white",
                    alpha=0.8,
                ),
            )

        elif row == 3:
            ax.text(
                0.80,
                0.98,
                stats_text,
                transform=ax.transAxes,
                verticalalignment="top",
                fontsize=14,
                bbox=dict(
                    boxstyle="round",
                    facecolor="white",
                    alpha=0.8,
                ),
            )

        # Grid.
        ax.grid(True, alpha=0.3)

# Add one legend to the figure.
handles, labels = axes[0, 0].get_legend_handles_labels()

fig.legend(
    handles,
    labels,
    loc="upper center",
    ncol=3,
    fontsize=12,
)

fig.tight_layout(rect=[0, 0, 1, 0.96])

plt.show()