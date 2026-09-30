from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from src.sif.utils.overview_poster_comp import load_ds
from src.sif.utils.file_management import NETCDF_DIR


# Load the statistics dataset.
ds = load_ds("fehmarn.per_level_stats.nc")

# Forecast hours.
forecast_hours = ["12h", "24h", "48h"]

# Statistics to plot.
ta_statistics = [
    ("ta_r2", "R²"),
    ("ta_rmse", "RMSE / K"),
    ("ta_bias", "Bias / K"),
]


# Create figure.
fig, axes = plt.subplots(
    nrows=len(ta_statistics),
    ncols=len(forecast_hours),
    figsize=(20, 28),
    sharey=True,
)

# Pressure levels.
pressure_levels = ds.p.values

# Equal-spaced positions for each pressure level.
pressure_positions = np.arange(len(pressure_levels))

# Plot.
for row, (variable, statistic_name) in enumerate(ta_statistics):

    for col, forecast_hour in enumerate(forecast_hours):

        ax = axes[row, col]

        # GFS.
        gfs = ds[variable].sel(model="GFS", forecast_hour=forecast_hour,)

        ax.plot(
            gfs,
            pressure_positions,
            marker="o",
            label="GFS",
        )

        # IFS.
        ifs = ds[variable].sel(model="IFS", forecast_hour=forecast_hour, )

        ax.plot(
            ifs,
            pressure_positions,
            marker="o",
            label="GFS",
        )

        # Formatting
        ax.set_ylim(len(pressure_levels) - 1, 0)

        ax.set_yticks(pressure_positions)
        ax.set_yticklabels([f"{int(p)}" for p in pressure_levels])

        ax.grid(
            which="major",
            linestyle="--",
            alpha=0.5,
        )

        # Column titles.
        if row == 0:
            ax.set_title(f"{forecast_hour} Forecast", fontsize=24, fontweight="bold")

        # X-axis label.
        ax.set_xlabel(statistic_name)

        # Y-axis label only on first column.
        if col == 0:
            ax.set_ylabel("Pressure (hPa)", fontsize=24)

        # Set x-limits.
        if row == 0:
            ax.set_xlim(0, 1)

        elif row == 1:
            ax.set_xlim(0, 2.5)

        elif row == 2:
            ax.set_xlim(-1, 1)

# Row labels
for row, (_, statistic_name) in enumerate(ta_statistics):

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

axes[0, -1].legend(loc="best")

fig.suptitle("Fehmarn Radiosonde Model Verification - Temperature", fontsize=30)

fig.tight_layout(rect=[0, 0, 1, 0.97])

plt.show()
