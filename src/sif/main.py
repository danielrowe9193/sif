import xarray as xr

from radiosondes import Radiosonde

radiosonde = Radiosonde(
    filepath="../../data/Westermarkelsdorf_RS92_20260811_114920.mwx"
)
radiosonde.extract_mwx()
radiosonde.build_radiosonde()

ds = xr.open_dataset('../../data/Westermarkelsdorf_RS92_20260811_114920.nc')
print(ds.data_vars)
