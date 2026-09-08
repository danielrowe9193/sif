from pathlib import Path
from datetime import datetime
import numpy as np
import xarray as xr
import pandas as pd

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
    lat = data["latitude"].values
    lon = data["longitude"].values

    for name, station_lat, station_lon in stations:
        station_lat = np.deg2rad(station_lat)
        station_lon = np.deg2rad(station_lon)

        dlat = lat - station_lat
        dlon = (lon - station_lon + np.pi) % (2 * np.pi) - np.pi
        # calculate spherical distance
        a = (
            np.sin(dlat / 2) ** 2
            + np.cos(station_lat)
            * np.cos(lat)
            * np.sin(dlon / 2) ** 2
        )

        distance = 2 * np.arcsin(np.sqrt(a))
        cell_idx = np.nanargmin(distance)
        point = data.isel(cell=cell_idx)

        # add station as another dimension
        point = point.expand_dims(station=[name])
        selected.append(point)

    return xr.concat(selected, dim="station", data_vars="minimal", coords="minimal", compat="override")

# stations
stations = [
    ("Fehmarn", 54.527846, 11.060437), 
    ("Schleswig", 54.528, 9.55), 
    ("Greifswald", 54.097, 13.405), 
    ("Norderney", 53.712, 7.152), 
    ]

date_input = get_date()
date_no_dash = date_input.replace("-","") # remove dash from date

cycles = ["00","06","12","18"]

BASE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "ICON"
output_path = BASE_PATH / date_input 
output_path.mkdir(parents=True, exist_ok=True)

cell_file = BASE_PATH / "lat_lon.txt"


for cycle in cycles:
    input_path = BASE_PATH / f"id2_lex2026_{date_no_dash}{cycle}.nc"
    ds = xr.open_dataset(input_path)

    # read lat long info with cooresponding cells
    cells = pd.read_csv(
        cell_file,
        sep=r"\s+"
    )

    # rename levels and cells
    clean_ds = ds.rename({
        # "height": "level",
        "ncells": "cell",
    })
# clean_ds = xr.Dataset(
#     data_vars={
#         "t": ds["T"].rename({"ncells": "cell"}),
#         "p": ds["P"].rename({"ncells": "cell"}),
#     },


    clean_ds = xr.Dataset(
        data_vars={ #select variables
            "t": ds["T"].rename({"ncells": "cell"}), #temperature
            "p": ds["P"].rename({"ncells": "cell"}), #pressure # in Pa 
            "q": ds["QV"].rename({"ncells": "cell"}), # specific humidity
            "rh": ds["RELHUM_2M"].rename({"ncells": "cell"}), # relative humidity
            "td": ds["TD_2M"].rename({"ncells": "cell"}), #dew point temperature (2m)
            "U": ds["U"].rename({"ncells": "cell"}),
            "V": ds["V"].rename({"ncells": "cell"}),
            "CAPE_ML": ds["CAPE_ML"].rename({"ncells": "cell"}),
            "CIN_ML": ds["CIN_ML"].rename({"ncells": "cell"}),
        },
        coords={
            "valid_time": ds["time"],
            # "level": ds["height"],
            "cell": np.arange(len(cells)),
            "latitude": ("cell", cells["lat"].values,),
            "longitude": ("cell", cells["lon"].values,),
        },
    )

    # change to hPa
    clean_ds["p"] = clean_ds["p"] / 100
    clean_ds["p"].attrs["units"] = "hPa"

    clean_ds = select_station(clean_ds, stations)

    output = output_path / f"ALL-{date_input}-{cycle}z.nc"
    clean_ds.to_netcdf(output)
