import xarray as xr
import matplotlib.pyplot as plt

from metpy.plots import SkewT
from metpy.units import units
from metpy.calc import dewpoint_from_specific_humidity

from pathlib import Path

date = "2026-08-09"
cycle = "00z"
FULL_PATH = Path.cwd().resolve().parent / "data" / "IFS" / date /"netCDF" / cycle / f"ALL-{date}-{cycle}.nc"

# forecast data
ds = xr.open_dataset(FULL_PATH)

def plot_skewt(skew, data, title):
    """
    Plots forecast atmospheric sounding on a SkewT
    """

    p = data["pressure"].values * units.hPa
    t = data["t"].values * units.kelvin
    q = data["q"].values * units("kg/kg")
    td = dewpoint_from_specific_humidity(p, t, q)

    u = data["u"].values * units("m/s")
    v = data["v"].values * units("m/s")

    # plot temperature and dewpoint
    skew.plot(p, t, color="red", linewidth=2)
    skew.plot(p, td, color="green", linewidth=2)

    # wind 
    skew.plot_barbs(p, u, v)

    # thermodynamic reference lines
    skew.plot_dry_adiabats(alpha=0.25)
    skew.plot_moist_adiabats(alpha=0.25)
    skew.plot_mixing_lines(alpha=0.25)

    skew.ax.set_title(title)



fig = plt.figure(figsize=(18, 7))

for i, location in enumerate(locations, start=1):

    data = ds.sel(
        time=valid_time, #check here
        location=location
        )

    # skew-T in subplot 
    skew = SkewT(
        fig=fig,
        subplot=(1, 4, i),
        rotation=30,
    )

    plot_skewt(
        skew,
        data,
        title=str(location),
    )

plt.tight_layout()
plt.show()