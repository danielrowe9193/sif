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


def select_variables(data):
    wanted_variables = [
        "t",
        "r",
        "q",
        "gh",
        "u",
        "v",
    ]

    if "latitude" not in data.coords or "longitude" not in data.coords:
        return None

    available_variables = [
        variable
        for variable in wanted_variables
        if variable in data.data_vars
    ]

    if not available_variables:
        return None

    data = data[available_variables]

    if "isobaricInhPa" in data.coords:
        data = data.rename(
            {"isobaricInhPa": "p"}
        )

    if "gh" in data.data_vars:
        data = data.rename(
            {"gh": "height"}
        )

    return data


def get_parameter_keys(data):
    wanted_variables = [
        "t",
        "r",
        "q",
        "gh",
        "u",
        "v",
    ]

    return [
        variable
        for variable in wanted_variables
        if variable in data.data_vars
    ]


date_input = get_date()
cycles = ["00"]#,"06","12","18"]
extensions = [".f012", ".f024", ".f048"] #.anl

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

        data = xr.open_dataset(
            filename,
            engine="cfgrib",
            backend_kwargs={
                "filter_by_keys": {
                    "typeOfLevel": "isobaricInhPa"
                },
                "indexpath": ""
            }
        )

        file_datasets[extension] = {}

        parameter_keys = get_parameter_keys(data)

        for parameter in parameter_keys:
            file_datasets[extension].setdefault(
                parameter,
                []
            )
            file_datasets[extension][parameter].append(
                data[[parameter]]
            )

    group_keys = set()

    for extension in file_datasets:
        group_keys.update(
            file_datasets[extension].keys()
        )

    print(f"Number of parameter groups: {len(group_keys)}")

    for extension in file_datasets:
        print(
            f"  {extension}: "
            f"{len(file_datasets[extension])}"
        )

    combined_groups = []

    for group_key in group_keys:

        selected_groups = []

        print(f"  Parameter group: {group_key}")

        for extension in extensions:

            if extension not in file_datasets:
                continue

            if group_key not in file_datasets[extension]:
                continue

            datasets = file_datasets[extension][group_key]

            for data in datasets:

                print(f"  {extension}: {list(data.data_vars)}")

                try:

                    data = select_variables(data)

                    if data is None:
                        print(
                            f"  No wanted variables "
                            f"in {extension}"
                        )
                        continue

                    selected = select_station(data,stations)

                    selected_groups.append(selected)

                except Exception as e:
                    print(
                        f"  ERROR selecting stations "
                        f"from {extension}: {e}"
                    )

        if not selected_groups:
            continue

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
                f"{group_key}: {e}"
            )
            continue

        if "valid_time" in combined.coords:
            combined = combined.sortby("valid_time")
            times = combined["valid_time"].values
            _, unique_indices = np.unique(times, return_index=True)
            unique_indices = np.sort(unique_indices)
            combined = combined.isel(valid_time=unique_indices)

        combined_groups.append(combined)

    final_dataset = xr.merge(combined_groups, compat="override", join="outer")
    
    output_file = output_folder / f"ALL-{date_input}-{cycle}z.nc"

    if output_file.exists():
        output_file.unlink()
        
    final_dataset.to_netcdf(output_file, engine="netcdf4")
    final_dataset.close()

    print(f"Finished: {output_file}")


# sort by levels
# def get_date():
#     while True: 
#         date_string = input(
#             "Enter date to download (YYYY-MM-DD): "
#         ).strip()

#         try:

#             date = datetime.strptime(
#                 date_string,
#                 "%Y-%m-%d",
#             )
#             break

#         except ValueError:
#             print(
#                 "Invalid date format. "
#                 "Please use YYYY-MM-DD, for example 2026-08-11."
#             )
#     return date_string

# # select stations
# def select_station(data, stations):
#     selected = []
#     for name, lat, lon in stations:
#         point = data.sel(
#             latitude=lat,
#             longitude=lon,
#             method="nearest"
#         )
#         # add station as another dimension
#         point = point.expand_dims(station=[name])
#         selected.append(point)

#     return xr.concat(selected, dim="station", data_vars="minimal", coords="minimal", compat="override")


# def select_variables(data):
#     wanted_variables = [
#         "t",
#         "r",
#         "q",
#         "gh",
#         "u",
#         "v",
#     ]

#     if "latitude" not in data.coords or "longitude" not in data.coords:
#         return None

#     available_variables = [
#         variable
#         for variable in wanted_variables
#         if variable in data.data_vars
#     ]

#     if not available_variables:
#         return None

#     data = data[available_variables]

#     if "isobaricInhPa" in data.coords:
#         data = data.rename(
#             {"isobaricInhPa": "p"}
#         )

#     if "gh" in data.data_vars:
#         data = data.rename(
#             {"gh": "height"}
#         )

#     return data


# def get_level_key(data):
#     if "isobaricInhPa" in data.coords:
#         values = np.atleast_1d(
#             data["isobaricInhPa"].values
#         ).tolist()

#         return (
#             "isobaricInhPa",
#             tuple(values)
#         )

#     if "heightAboveGround" in data.coords:
#         values = np.atleast_1d(
#             data["heightAboveGround"].values
#         ).tolist()

#         return (
#             "heightAboveGround",
#             tuple(values)
#         )

#     if "surface" in data.coords:
#         values = np.atleast_1d(
#             data["surface"].values
#         ).tolist()

#         return (
#             "surface",
#             tuple(values)
#         )

#     if "meanSea" in data.coords:
#         values = np.atleast_1d(
#             data["meanSea"].values
#         ).tolist()

#         return (
#             "meanSea",
#             tuple(values)
#         )

#     for variable in data.data_vars:
#         var = data[variable]

#         type_of_level = var.attrs.get(
#             "GRIB_typeOfLevel"
#         )

#         level = var.attrs.get(
#             "GRIB_level"
#         )

#         if type_of_level is not None:
#             return (
#                 type_of_level,
#                 level
#             )

#     return None


# date_input = get_date()
# cycles = ["00"]#,"06","12","18"]
# extensions = [".f012", ".f024", ".f048"] #.anl

# BASE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "GFS"

# # stations
# stations = [
#     ("Fehmarn", 54.527846, 11.060437), # Fehmarn
#     ("Schleswig", 54.528, 9.55), # Schleswig
#     ("Greifswald", 54.097, 13.405), # Greifswald
#     ("Norderney", 53.712, 7.152), # Norderney
#     ]
    
# for cycle in cycles:
#     input_folder = BASE_PATH / date_input 
#     output_folder = BASE_PATH / date_input / "netCDF" 
#     output_folder.mkdir(parents=True, exist_ok=True)

#     files_set = {}

#     for extension in extensions:
#         filename = (input_folder / f"gfs.t{cycle}z.pgrb2.0p25{extension}")

#         if filename.exists():
#             files_set[extension] = filename

#     file_datasets = {}

#     for extension, filename in files_set.items():
#         print(f"Converting: {filename.name}")

#         datasets = cfgrib.open_datasets(
#             str(filename),
#             indexpath=""
#         )

#         file_datasets[extension] = {}

#         for data in datasets:
#             level_key = get_level_key(data)

#             if level_key is not None:
#                 file_datasets[extension][level_key] = data

#     group_keys = set()

#     for extension in file_datasets:
#         group_keys.update(
#             file_datasets[extension].keys()
#         )

#     print(f"Number of level groups: {len(group_keys)}")

#     for extension in file_datasets:
#         print(
#             f"  {extension}: "
#             f"{len(file_datasets[extension])}"
#         )

#     combined_groups = []

#     for group_key in group_keys:

#         selected_groups = []

#         print(f"  Level group: {group_key}")

#         for extension in extensions:

#             if extension not in file_datasets:
#                 continue

#             if group_key not in file_datasets[extension]:
#                 continue

#             data = file_datasets[extension][group_key]

#             print(f"  {extension}: {list(data.data_vars)}")

#             try:

#                 data = select_variables(data)

#                 if data is None:
#                     print(
#                         f"  No wanted variables "
#                         f"in {extension}"
#                     )
#                     continue

#                 selected = select_station(data,stations)

#                 selected_groups.append(selected)

#             except Exception as e:
#                 print(
#                     f"  ERROR selecting stations "
#                     f"from {extension}: {e}"
#                 )

#         if not selected_groups:
#             continue

#         try:
#             combined = xr.concat(
#                 selected_groups,
#                 dim="valid_time",
#                 data_vars="minimal",
#                 coords="minimal",
#                 compat="override"
#             )
#         except Exception as e:
#             print(
#                 f"  ERROR concatenating group "
#                 f"{group_key}: {e}"
#             )
#             continue

#         if "valid_time" in combined.coords:
#             combined = combined.sortby("valid_time")
#             times = combined["valid_time"].values
#             _, unique_indices = np.unique(times, return_index=True)
#             unique_indices = np.sort(unique_indices)
#             combined = combined.isel(valid_time=unique_indices)

#         combined_groups.append(combined)

#     final_dataset = xr.merge(combined_groups, compat="override", join="outer")
    
#     output_file = output_folder / f"ALL-{date_input}-{cycle}z.nc"

#     if output_file.exists():
#         output_file.unlink()
        
#     final_dataset.to_netcdf(output_file, engine="netcdf4")
#     final_dataset.close()

#     print(f"Finished: {output_file}")
                    

    # Concatenate all datasets into one
    # combined = xr.concat(all_datasets, dim="valid_time")

    # output_file = output_folder / f"ALL-{date_input}-{cycle}z.nc"

    # combined.to_netcdf(output_file)

    # combined.close()
