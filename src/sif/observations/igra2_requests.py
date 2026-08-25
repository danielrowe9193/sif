from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from src.sif.utils.utils import FileManagement


def igra2_stations_df():
    """Returns a dataframe of the stations in the IGRA2 database from the link
    https://www.ncei.noaa.gov/pub/data/igra/igra2-station-list.txt."""

    station_list_url = 'https://www.ncei.noaa.gov/pub/data/igra/igra2-station-list.txt'

    headers = ["station_id", "latitude", "longitude", "elevation", "state", "station_name", "first_year", "last_year",
               "number_of_soundings"]

    colspecs = [
            (0, 11),    # ID Character
            (12, 20),   # LATITUDE  Real
            (21, 30),   # LONGITUDE  Real
            (31, 37),   # ELEVATION Real
            (38, 40),   # STATE Character
            (41, 71),   # NAME  Character
            (72, 76),   # FSTYEAR Integer
            (77, 81),   # LST Integer
            (82, 88),   # NOBS Integer
        ]

    df = pd.read_fwf(
        station_list_url,
        colspecs=colspecs,
        names=headers,
    )

    return df


def region_box(lat_min: float, lat_max: float, lon_min: float, lon_max: float) -> dict:
    """Return a dictionary defining a geographic bounding box."""

    return {
        "lat_min": lat_min,
        "lat_max": lat_max,
        "lon_min": lon_min,
        "lon_max": lon_max,
    }


def region_mask(df: pd.DataFrame, region: dict, last_year=None) -> bool:
    """Return a boolean a mask for selecting stations within a region."""
    mask = (
        (df['latitude'] >= region['lat_min']) &
        (df['latitude'] <= region['lat_max']) &
        (df['longitude'] >= region['lon_min']) &
        (df['longitude'] <= region['lon_max'])
    )

    if last_year >= 2026:
        mask = mask & (df['last_year'] == last_year)

    return mask

# northern_germany_stations = list(df[mask]['station_id'])

def get_station_ids(
    df: pd.DataFrame,
    value: Optional[str] = None,
    col: Optional[str] = None,
    region_mask: Optional[pd.Series] = None
)\
        -> list[str]:
    """Return a list of IGRA2 station IDs based on a value or region mask.

    Parameters
        df: pd.DataFrame
            DataFrame containing IGRA2 stations data.

        value: str, optional
            Search value. The value is searched for across all columns.
            Matching is case-insensitive and allows partial matches.

        region_mask : pandas.Series, optional
            Boolean mask selecting stations within a region.

    Notes:
        If both `value` and `region_mask` are provided, both conditions must be satisfied.

    Returns:
        A list of IGRA2 station IDs.
    """

    if value is not None:

        if col is not None:
            mask = df[col].astype(str).str.contains(
                value,
                case=False,
                na=False,
            )
        else:
            mask = df.astype(str).apply(
                lambda column: column.str.contains(
                    value,
                    case=False,
                    na=False,
                )
            ).any(axis=1)

    elif region_mask is not None:
        mask = region_mask

    else:
        return list(df["station_id"])

    return list(df[mask]["station_id"])


def download_soundings(station_ids: list[str], derived: bool = True) -> None:
    """This function downloads the sounding data for a given list of station ids."""

    base_url = "https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/access/"

    FileManagement.IGRA_DIR.mkdir(exist_ok=True, parents=True)

    for station_id in station_ids:

        data_types = ['data']

        if derived:
            data_types.append('drvd')

        for data_type in data_types:

            directory = "data-por" if data_type == "data" else "derived-por"

            zip_file = Path(f"{station_id}-{data_type}.txt.zip")
            data_url = f"{base_url}{directory}/{zip_file.name}"

            print(f"Downloading: {zip_file} ...")

            response = requests.get(data_url)

            if response.status_code == 200:

                output_file = FileManagement.IGRA_DIR / zip_file

                with open(output_file, "wb") as zf:
                    zf.write(response.content)

                print("Successfully downloaded!\n")

            else:
                print(f"Could not download {zip_file}; response code: {response.status_code}.")


def main():
    df = igra2_stations_df()
    NORTHERN_GERMANY = region_box(53, 55, 7, 15)
    mask = region_mask(df, NORTHERN_GERMANY, last_year=2026)
    northern_germany_stations = get_station_ids(df, region_mask=mask)
    download_soundings(northern_germany_stations)


if __name__ == "__main__":
    main()








# # Northern Germany box.
# lat_min, lat_max, lon_min, lon_max = 53, 55, 7, 15
#
# mask = (df['latitude'] >= lat_min) & (df['latitude'] <= lat_max) & (df['longitude'] >= lon_min) & (df['longitude'] <= lon_max) & (df['last_year'] == 2026)

# all_sounding_data_url = "https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/access/data-por/"
#
# northern_germany_stations = list(df[mask]['station_id'])
#
# for station_id in northern_germany_stations:
#     zip_file = Path(f"{station_id}-data.txt.zip")
#     data_url = all_sounding_data_url + zip_file.name
#
#     FileManagement.IGRA_DIR.mkdir(exist_ok=True, parents=True)
#
#     print(f"Downloading: {zip_file} ...")
#
#     response = requests.get(data_url)
#
#     if response.status_code == 200:
#
#         output_dir = FileManagement.IGRA_DIR / zip_file
#
#         with open(f'{output_dir}', 'wb') as zf:
#             zf.write(response.content)
#             print("Successfully downloaded!\n")
#
#     else:
#         print(f"Could not download {zip_file}; response code: {response.status_code}.")

# response = requests.get(station_list_url)
#
# for line in response.text.splitlines():
#     print(line)

# for station in df[mask]['station_id']:
#     print(f"{station}-data.txt.zip")