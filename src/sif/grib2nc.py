"""
Convert .grib2 files to .nc files.
"""

from pathlib import Path
from datetime import datetime
import xarray as xr


def get_date():
    while True: 
        date_string = input(
            "Enter date to download (YYYY-MM-DD): "
        ).strip()

        try:

            date = datetime.strptime(
                date_string,
                "%Y-%m-%d",
            )
            break

        except ValueError:
            print(
                "Invalid date format. "
                "Please use YYYY-MM-DD, for example 2026-08-11."
            )
    return date_string
            
date_input = get_date()
cycles = ["00","06","12","18"]
extensions = ".grib2"

BASE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "IFS"

for i in cycles:
    input_folder = BASE_PATH / date_input / f"{i}z" / "ifs" 
    output_folder = input_folder
# output_folder.mkdir(parents=True, exist_ok=True)

    for filename in input_folder.iterdir():
        if filename.is_file() and filename.suffix.lower() in extensions:
            print(f"Converting: {filename.name}")

            try:
                data = xr.open_dataset(filename, engine="cfgrib")
                output_file = output_folder / f"{filename.stem}.nc"

                data.to_netcdf(output_file)
                data.close()

                print(f"  → {output_file.name}")

            except Exception as e:
                print(f"  ERROR: {e}")
