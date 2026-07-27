from pathlib import Path
import zipfile

import numpy as np
import pandas as pd
import xarray as xr


def parse_header(line):
    """Parse one IGRA header line."""

    return {

        "station": line[1:12].strip(),

        "year": int(line[13:17]),
        "month": int(line[18:20]),
        "day": int(line[21:23]),
        "hour": int(line[24:26]),

        "release_time": int(line[27:31]),

        "numlev": int(line[32:36]),

        "p_src": line[37:45].strip(),
        "np_src": line[46:54].strip(),

        "lat": int(line[55:62]) / 10000,
        "lon": int(line[63:71]) / 10000,
    }


def parse_level(line):
    """Parse one IGRA profile line."""

    return {

        "lvltyp1": int(line[0]),
        "lvltyp2": int(line[1]),

        "etime": int(line[3:8]),

        "pressure": int(line[9:15]),

        "pflag": line[15],

        "height": int(line[16:21]),

        "zflag": line[21],

        "temperature": int(line[22:27]),

        "tflag": line[27],

        "rh": int(line[28:33]),

        "dpdp": int(line[34:39]),

        "wind_dir": int(line[40:45]),

        "wind_speed": int(line[46:51]),

    }


# Parse the entire file.
def parse_soundings(lines: list[str]) -> dict[pd.Timestamp, pd.DataFrame]:
    """
    Parse an IGRA station file into a dictionary of soundings.

    Parameters
    ----------
    lines : list[str]
        List of lines from an IGRA station file.

    Returns
    -------
    dict[pandas.Timestamp, pandas.DataFrame]
        Dictionary whose keys are launch datetimes and whose values are
        DataFrames containing the sounding profile. The header metadata
        are stored in each DataFrame's ``attrs`` dictionary.
    """

    soundings = {}

    i = 0

    while i < len(lines):

        if not lines[i].startswith("#"):
            i += 1
            continue

        header = parse_header(lines[i])

        profile = []

        for j in range(header["numlev"]):

            profile.append(parse_level(lines[i + j + 1]))

        df = pd.DataFrame(profile)

        # Replace IGRA missing values with NaN.
        df.replace([-9999, -8888], np.nan, inplace=True)

        # Convert units
        df["pressure"] /= 100.0          # Pa -> hPa
        df["temperature"] /= 10.0        # tenths C -> C
        df["dpdp"] /= 10.0               # tenths C -> C
        df["dewpoint"] = df["temperature"] - df["dpdp"]
        df["wind_speed"] /= 10.0         # tenths m/s -> m/s

        # Datetime for this sounding.
        dt = pd.Timestamp(
            year=header["year"],
            month=header["month"],
            day=header["day"],
            hour=header["hour"],
        )

        # Store metadata in DataFrame attributes
        df.attrs = header

        # Save sounding
        soundings[dt] = df

        i += header["numlev"] + 1

    return soundings


def soundings_to_xarray(soundings):
    """
    Convert a dictionary of IGRA soundings into an xarray Dataset.

    Parameters
    ----------
    soundings : dict[pd.Timestamp, pd.DataFrame]

    Returns
    -------
    xr.Dataset
    """

    # Sort chronologically
    times = sorted(soundings.keys())

    ntime = len(times)
    max_levels = max(len(soundings[t]) for t in times)

    profile_vars = [
        "pressure",
        "height",
        "temperature",
        "dewpoint",
        "dew_point_depression",
        "wind_dir",
        "wind_speed",
        "relative_humidity",
        "lvltyp1",
        "lvltyp2",
        "etime",
    ]

    # Allocate arrays
    arrays = {
        var: np.full((ntime, max_levels), np.nan)
        for var in profile_vars
    }

    # Metadata (one value per sounding)
    release_time = np.full(ntime, np.nan)
    numlev = np.full(ntime, np.nan)

    p_src = []
    np_src = []

    lat = np.full(ntime, np.nan)
    lon = np.full(ntime, np.nan)

    # Fill arrays
    for i, time in enumerate(times):

        df = soundings[time]

        n = len(df)

        for var in profile_vars:

            if var in df.columns:
                arrays[var][i, :n] = df[var].values

        attrs = df.attrs

        release_time[i] = attrs["release_time"]
        numlev[i] = attrs["numlev"]

        lat[i] = attrs["lat"]
        lon[i] = attrs["lon"]

        p_src.append(attrs["p_src"])
        np_src.append(attrs["np_src"])

    ds = xr.Dataset(

        data_vars={

            **{
                var: (("time", "level"), arrays[var])
                for var in profile_vars
            },

            "release_time": ("time", release_time),
            "numlev": ("time", numlev),

            "latitude": ("time", lat),
            "longitude": ("time", lon),

            "pressure_source": ("time", np.asarray(p_src, dtype="U16")),
            "nonpressure_source": ("time", np.asarray(np_src, dtype="U16")),
        },

        coords={

            "time": pd.to_datetime(times),

            "level": np.arange(max_levels),
        },

        attrs={
            "source": "NOAA NCEI Integrated Global Radiosonde Archive (IGRA Version 2)",
            "institution": "NOAA National Centers for Environmental Information",
            "station": soundings[times[0]].attrs["station"],
            "title": "IGRA Radiosonde Profiles",
            "history": (
                f"Converted from IGRA text format on "
                f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M UTC')}"
            ),
            "references": (
                "https://www.ncei.noaa.gov/products/weather-balloon/integrated-global-radiosonde-archive"
                "integrated-global-radiosonde-archive"
            ),
            "featureType": "timeSeriesProfile"
        }

    )

    return ds


DATA_DIR = Path("data")
filename = "BBM00078954-data.txt.zip"
zip_path = Path(__file__).parents[2] / DATA_DIR / filename


with zipfile.ZipFile(zip_path, mode='r') as z:

    text_files = [file for file in z.namelist() if file.endswith(".txt")]

    if not text_files:
        raise("No .txt files found in ZIP")

    with z.open(text_files[0]) as f:
        lines = f.read().decode("ascii").splitlines()

soundings = parse_soundings(lines)

ds = soundings_to_xarray(soundings)
print(ds)

# ds.to_netcdf(filename.split('-')[0] + '.nc')