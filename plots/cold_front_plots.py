import xarray as xr
from plotting_all_models import plot_cross_section

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
icon = xr.open_dataset(BASE_PATH / "ICON" / "icon.radiosondes.profiles.level1.nc")

cycles = ["00","06","12","18"]
forecast = ["12h", "24h", "48h"]
for i in forecast:
    for j in cycles:
        time = f"2026-08-15-{j}z"
        plots = plot_cross_section(ifs, gfs, icon, time, i, station_order=["Norderney","Schleswig", "Fehmarn", "Greifswald"], title="Atmospheric Cross Sections", subplot_titles=[
        "IFS", "GFS", "ICON"])
        plots.savefig(f"figures/models_2026-08-15-{j}_{i}.png", dpi=300, bbox_inches="tight")
        