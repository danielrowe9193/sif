from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from metpy.plots import SkewT
import xarray as xr

from .utils import FileManagement


filename = Path("BBM00078954.nc")
data = FileManagement.DATA_DIR / filename


# Load the data.
ds = xr.open_dataset(data)

recent = ds.sel(time="2026-04-04T12:00:00.000000000")

pressure = recent["pressure"].values / 100
temperature = recent["temperature"].values - 273.15
dewpoint = recent["dewpoint"].values - 273.15

# Remove NaN.
mask = ~np.isnan(pressure) & ~np.isnan(temperature) & ~np.isnan(dewpoint)


fig = plt.figure(figsize=(10, 14), dpi=300)
skew = SkewT(fig, rotation=45)

skew.plot(
    pressure[mask], temperature[mask], color="darkorange", linewidth=2.5, label="T"
)
skew.plot(pressure[mask], dewpoint[mask], color="navy", linewidth=2.5, label="Td")

skew.ax.set_xlim(-30, 40)
skew.ax.tick_params(axis="both", labelsize=14)

skew.ax.axvline(0, color="k", linewidth=1, alpha=0.5)
skew.plot_dry_adiabats(alpha=0.3)
skew.plot_moist_adiabats(alpha=0.3)

skew.ax.legend(fontsize=14)


plt.show()
