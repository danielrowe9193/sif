import xarray as xr
from plotting import plot_cross_section

from pathlib import Path
# Cold front dates: 2026-08-15

# date = "2026-08-09"

BASE_PATH = Path.cwd().resolve().parent / "data" 
   
# load observational data
sif = xr.open_dataset(BASE_PATH / "sif" / "sif.ptu_radiosondes.profiles.level2.nc")
igra = xr.open_dataset(BASE_PATH / "igra" / "sif.igra_radiosondes.profiles.level0.nc")
# load model data
gfs = xr.open_dataset(BASE_PATH / "GFS" / "gfs.radiosondes.profiles.level1.nc")
ifs = xr.open_dataset(BASE_PATH / "IFS" / "ifs.radiosondes.profiles.level1.nc")


cycles = ["00","06","12","18"]
for i in cycles:
    time = f"2026-08-15T{i}:00:00.000000000"
    gfs_plot = plot_cross_section(gfs, time, station_order=["Norderney","Schleswig", "Fehmarn", "Greifswald"], title="GFS")
    gfs_plot.savefig(f"figures/gfs/gfs_2026-08-15T{i}.png", dpi=300, bbox_inches="tight")
    ifs_plot = plot_cross_section(ifs, time, station_order=["Norderney","Schleswig", "Fehmarn", "Greifswald"], title="IFS")
    ifs_plot.savefig(f"figures/ifs/ifs_2026-08-15T{i}.png", dpi=300, bbox_inches="tight")

