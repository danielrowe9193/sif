"""
Split netCDF data into datasets to plot vertical profile and stability indices
"""

from pathlib import Path
import xarray as xr

cycles = ["00","06","12","18"]

BASE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "IFS"
path = "2026-08-13/18z/ifs/20260813180000-12h-oper-fc.nc"

# for i in cycles:
#     input_folder = BASE_PATH / date_input / f"{i}z" / "ifs" 
#     output_folder = BASE_PATH / date_input / "netCDF" / f"{i}z" 
#     output_folder.mkdir(parents=True, exist_ok=True)

# load data
ds = BASE_PATH / path
 

# vertical profile

