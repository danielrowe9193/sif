import xarray as xr

from plot import FehmarnRadiosondePlotter
from radiosondes import Radiosonde

stem = "RS_TestData_Westermarkelsdorf_20220825_131825"

radiosonde = Radiosonde(
    filepath=f"../../data/{stem}.mwx"
)
radiosonde.extract_mwx()
radiosonde.build_radiosonde()

ds = xr.open_dataset(f'../../data/{stem}.nc')
print(ds)

plotter = FehmarnRadiosondePlotter(
    filepath=f'../../data/{stem}.nc'
)
plotter.plot_skewt()
