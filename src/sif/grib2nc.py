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

# select station function here
def select_station(data, stations):
    selected = []
    for name, lat, lon in stations:
        point = data.sel(
            latitude=lat,
            longitude=lon,
            method="nearest"
        )
        # add station as another dimension
        point = point.expand_dims(station=[name])
        selected.append(point)

    return xr.concat(selected, dim="station")
         
date_input = get_date()
cycles = ["00","06","12","18"]
extensions = ".grib2"

BASE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "IFS"

for cycle in cycles:
    input_folder = BASE_PATH / date_input / f"{cycle}z" / "ifs" 
    output_folder = BASE_PATH / date_input / "netCDF"  
    output_folder.mkdir(parents=True, exist_ok=True)

    # concat by station to each cycle
    datasets = []

    for filename in input_folder.iterdir():
        if filename.is_file() and filename.suffix.lower() in extensions:
            print(f"Converting: {filename.name}")

            try:
                stations = [
                    ("Fehmarn", 54.527846, 11.060437), # Fehmarn
                    ("Schleswig", 54.528, 9.55), # Schleswig
                    ("Greifswald", 54.097, 13.405), # Greifswald
                    ("Norderney", 53.712, 7.152), # Norderney
                    ]
                data = xr.open_dataset(filename, engine="cfgrib")
                data = select_station(data, stations)
                # output_file = output_folder / f"{filename.stem}.nc"

                # data.to_netcdf(output_file)
                # data.close()

                # print(f"  → {output_file.name}")
                datasets.append(data)

            except Exception as e:
                print(f"  ERROR: {e}")

    # Concatenate all datasets into one
    combined = xr.concat(datasets, dim="valid_time")
    
    output_file = output_folder / f"ALL-{date_input}-{cycle}z.nc"

    combined.to_netcdf(output_file)

    combined.close()
