# Plotting summary of radiosondes launched during SIF
# Plotting summary of model radiosondes from ICON

import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs


sif = xr.open_dataset("../data/netcdf/sif.radiosondes.profiles.nc")
