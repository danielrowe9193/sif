from pathlib import Path
from datetime import datetime
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
output_path = BASE_PATH / "netcdf"
output_path.mkdir(parents=True, exist_ok=True)

cell_file = BASE_PATH / "lat_lon.txt"


for cycle in cycles:
    input_path = BASE_PATH / f"id2_lex2026_{date_no_dash}{cycle}.nc"
    ds = xr.open_dataset(input_path)

    # rename levels and cells
    clean_ds = ds.rename({
        # "height": "level",
        "ncells": "cell",
    })

    # read lat long info with cooresponding cells
    cells = pd.read_csv(
        cell_file,
        sep=r"\s+"
    )
    cells["cell_index"] = cells["cell"]

    clean_ds = xr.Dataset(
        data_vars={ #select variables
            "t": ds["T"], #temperature
            "p": ds["P"], #pressure # in Pa -> change to hPa?
            "q": ds["QV"], # specific humidity
            "rh": ds["RELHUM_2M"], # relative humidity
            "td": ds["TD_2M"], #dew point temperature (2m)
            "U": ds["U"],
            "V": ds["V"],
            "CAPE_ML": ds["CAPE_ML"],
            "CIN_ML": ds["CIN_ML"],
        },
        coords={
            # "valid_time": ds["time"],
            # "level": ds["height"],
            "cells": ds["ncells"],
            "latitude": ("cell", cells["lat"].values,),
            "longitude": ("cell", cells["lon"].values,),
        },
    )

    output = output_path / f"ALL-{date_input}-{cycle}z.nc"
    clean_ds.to_netcdf(output)
