"""
Framework for preparing model radiosondes at the 4 stations of interest for SIF.
"""

import numpy as np
import xarray as xr

from src.sif.utils.utils import FileManagement
from pathlib import Path

xr.set_options(use_new_combine_kwarg_defaults=True)

ifs_data_dir = FileManagement.IFS_DIR

gfs_data_path = Path("../data/test_data/test_gfs/ALL-2026-08-09-00z.nc")

gfs_test_ds = xr.open_dataset(gfs_data_path)
print(gfs_test_ds.data_vars)

ifs_ds = xr.open_dataset("../data/ifs/ifs.radiosondes.profiles.level1.nc")
print(ifs_ds)

sif_ds = xr.open_dataset("../data/netcdf/sif.radiosondes.profiles.nc")
print(sif_ds)

# sif = xr.open_dataset(FileManagement.NETCDF_DIR / 'sif.radiosondes.profiles.nc')
# launch_times = sif.isel(p=0).time.values
# print(launch_times)
# ifs_lvl1 = xr.open_dataset(FileManagement.IFS_DIR / 'ifs.radiosondes.profiles.level1.nc')
# ifs_lvl1_12h = ifs_lvl1.sel(
#     station='Fehmarn', forecast_hour='12h'
# )
# ifs_lvl1_12h = ifs_lvl1_12h.sel(
#     valid_time=np.sort(launch_times), method='nearest'
# )
# print(ifs_lvl1_12h)

# fig = plt.figure(figsize=(14, 9), constrained_layout=True)
# skew = SkewT(
#     fig,
#     rotation=45,
# )
#
# plt.title(f"ifs init: {time} valid: {valid_time}")
# plt.xlabel(r"Temperature \ $^\circ C$")
# plt.ylabel(r"Pressure \ $hPa$")
#
# skew.plot(p, t, color="darkorange", linewidth=2.5, label="T")
# skew.plot(p, td, color="navy", linewidth=2.5, label="Td")
#
# skew.plot_barbs(p, u, v)
#
# skew.ax.set_xlim(-30, 40)
# skew.ax.tick_params(axis="both", labelsize=14)
#
# skew.ax.axvline(0, color="k", linewidth=1, alpha=0.5)
# skew.plot_dry_adiabats(alpha=0.3)
# skew.plot_moist_adiabats(alpha=0.3)
#
# skew.ax.legend(fontsize=14)
#
# plt.savefig(
#     f"../plots/ifs/ifs.init{time}.valid{valid_time}.png"
# )
