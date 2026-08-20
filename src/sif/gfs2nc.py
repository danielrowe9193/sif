"""
Convert the GFS files (.anl and other) to .nc files.
"""
import numpy as np
from pathlib import Path
from datetime import datetime
import xarray as xr
import cfgrib


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

# select stations
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

    return xr.concat(selected, dim="station", data_vars="minimal", coords="minimal", compat="override")


date_input = get_date()
cycles = ["00"]#,"06","12","18"]
extensions = [".anl", ".f012", ".f024", ".f048"]

BASE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "GFS"

# stations
stations = [
    ("Fehmarn", 54.527846, 11.060437), # Fehmarn
    ("Schleswig", 54.528, 9.55), # Schleswig
    ("Greifswald", 54.097, 13.405), # Greifswald
    ("Norderney", 53.712, 7.152), # Norderney
    ]
    
for cycle in cycles:
    input_folder = BASE_PATH / date_input 
    output_folder = BASE_PATH / date_input / "netCDF" 
    output_folder.mkdir(parents=True, exist_ok=True)

    files_set = {}

    for extension in extensions:
        filename = (input_folder / f"gfs.t{cycle}z.pgrb2.0p25{extension}")

        if filename.exists():
            files_set[extension] = filename

    file_datasets = {}

    for extension, filename in files_set.items():
        print(f"Converting: {filename.name}")

        datasets = cfgrib.open_datasets(
            str(filename),
            indexpath=""
        )

        file_datasets[extension] = datasets

    group_counts = {extension: len(datasets) for extension, datasets in file_datasets.items()}

    print(f"GRIB group counts: {group_counts}")
    for extension, count in group_counts.items():
        print(f"  {extension}: {count}")

    number_of_groups = min(group_counts.values())

    combined_groups = []
    for group_index in range(number_of_groups):

        selected_groups = []
        for extension in extensions:

            if extension not in file_datasets:
                continue

            datasets = file_datasets[extension]
            data = datasets[group_index]

            print(f"  {extension}: {list(data.data_vars)}")
            try:
                selected = select_station(data, stations)
                selected_groups.append(selected)
                
            except Exception as e:
                print(
                    f"  ERROR selecting stations "
                    f"from {extension}: {e}"
                )
        # if not selected_groups:
        #     continue
        try:
            combined = xr.concat(
                selected_groups,
                dim="valid_time",
                data_vars="minimal",
                coords="minimal",
                compat="override"
            )
        except Exception as e:
            print(
                f"  ERROR concatenating group "
                f"{group_index}: {e}"
            )
            continue

        if "valid_time" in combined.coords:
            combined = combined.sortby("valid_time")
            times = combined["valid_time"].values
            _, unique_indices = np.unique(times, return_index=True)
            unique_indices = np.sort(unique_indices)
            combined = combined.isel(valid_time=unique_indices)

        combined_groups.append(combined)
    # join groups
    final_dataset = xr.merge(combined_groups, compat="override", join="outer")
    
    output_file = output_folder / f"ALL-{date_input}-{cycle}z.nc"

    if output_file.exists():
        output_file.unlink()
        
    final_dataset.to_netcdf(output_file, engine="netcdf4")
    final_dataset.close()

    print(f"Finished: {output_file}")
                    

    # Concatenate all datasets into one
    # combined = xr.concat(all_datasets, dim="valid_time")

    # output_file = output_folder / f"ALL-{date_input}-{cycle}z.nc"

    # combined.to_netcdf(output_file)

    # combined.close()
