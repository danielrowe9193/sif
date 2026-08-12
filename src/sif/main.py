import xarray as xr

from plot import FehmarnRadiosondePlotter
from radiosondes import Radiosonde

stem = "RS_TestData_Westermarkelsdorf_20220825_131825"

# Construct radiosonde from .mwx data.
radiosonde = Radiosonde(
    filepath=f"../../data/{stem}.mwx"
)
radiosonde.extract_mwx()
radiosonde.build_radiosonde()
radiosonde.summarize()

# Can load radiosonde data as xarray dataset, if desired.
ds = xr.open_dataset(f'../../data/{stem}.nc')

# Plot a skew-t diagram of the radiosonde.
plotter = FehmarnRadiosondePlotter(
    filepath=f'../../data/{stem}.nc'
)
plotter.plot_skewt()
