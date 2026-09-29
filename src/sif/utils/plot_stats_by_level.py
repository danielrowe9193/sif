from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from src.sif.utils.overview_poster_comp import load_ds
from src.sif.utils.file_management import NETCDF_DIR


# Load the statistics dataset.
ds = load_ds("fehmarn.per_level_stats.nc")

# Forecast hours.
lead_times = ["12h", "24h", "48h"]


# Statistics to plot.
statistics = [
    ("ta_r2", "R²"),
    ("ta_rmse", "RMSE (K)"),
    ("ta_bias", "Bias (K)"),
]


# Create figure.
fig, axes = plt.subplots(
    nrows=len(statistics),
    ncols=len(lead_times),
    figsize=(24, 28),
    sharey=True,
)

# Pressure levels.
pressure_levels = ds.p.values

# Equal-spaced positions for each pressure level.
pressure_positions = np.arange(len(pressure_levels))


# Plotting.

for row, (variable, statistic_name) in enumerate(statistics):

    for col, lead_time in enumerate(lead_times):

        ax = axes[row, col]

        # ERA5.
        if col == 0:

            era5 = ds[variable].sel(model="ERA5", lead_time="00h")

            ax.plot(
                era5,
                pressure_positions,
                marker="s",
                linestyle="--",
                label="ERA5 (00h)",
            )

        # GFS.
        gfs = ds[variable].sel(model="GFS", lead_time=lead_time)

        ax.plot(
            gfs,
            pressure_positions,
            marker="o",
            label="GFS",
        )

        # IFS
        ifs = ds[variable].sel(model="IFS", lead_time=lead_time)

        ax.plot(
            ifs,
            pressure_positions,
            marker="o",
            label="IFS",
        )

        ax.set_ylim(len(pressure_levels) - 1, 0)

        ax.set_yticks(pressure_positions)
        ax.set_yticklabels([f"{int(p)}" for p in pressure_levels])
        ax.tick_params(axis="y", which="major", labelsize=18)
        ax.tick_params(axis="x", which="major", labelsize=18)

        ax.grid(
            which="major",
            linestyle="--",
            alpha=0.3,
        )

        # Column titles.
        if row == 0:

            if col == 0:
                ax.set_title("ERA5 00h / GFS & IFS 12h", fontsize=26, fontweight='medium')

            else:
                ax.set_title(f"{lead_time} Forecast",fontsize=26, fontweight='medium')

        # X-axis label.
        ax.set_xlabel(statistic_name, fontsize=24)

        # Y-axis label only on first column.
        if col == 0:
            ax.set_ylabel("Pressure / hPa", fontsize=24)

        # Set x-limits.

        # R².
        if row == 0:
            ax.set_xlim(0.5, 1)

        # RMSE.
        if row == 1:
            ax.set_xlim(0, 1.8)

        # Mean Bias.
        if row == 2:
            ax.set_xlim(-1, 1)


# Row labels

for row, (_, statistic_name) in enumerate(statistics):

    axes[row, 0].text(
        -0.28,
        0.5,
        statistic_name,
        transform=axes[row, 0].transAxes,
        rotation=90,
        va="center",
        ha="center",
        fontsize=24,
    )


# Add one legend to the figure.
handles, labels = axes[0, 0].get_legend_handles_labels()

fig.legend(
    handles,
    labels,
    loc="lower center",
    ncol=4,
    fontsize=26,
)

fig.suptitle("Fehmarn Radiosonde Model Verification - Temperature", fontsize=32, fontweight='bold')

fig.tight_layout(rect=[0, 0.04, 1, 0.97])

plt.show()