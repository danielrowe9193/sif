import zipfile

import numpy as np
import pandas as pd
import xarray as xr

from src.sif.config import DATA_DIR


def _parse_header(line: list) -> dict:
    """Parse one IGRA header line using the Header Record Format from
    https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/doc/igra2-data-format.txt."""

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


def _parse_level(line: list) -> dict:
    """Parse one IGRA profile line using the Data Record Format from
    https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/doc/igra2-data-format.txt."""

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


def _parse_derived_header(line: list) -> dict:
    """Parse one IGRA derived index using the Header Record Format from
    https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/doc/igra2-derived-format.txt."""

    return {
        "station": line[1:12].strip(),

        "year": int(line[13:17]),
        "month": int(line[18:20]),
        "day": int(line[21:23]),
        "hour": int(line[24:26]),

        "numlev": int(line[31:36]),

        "pw": int(line[37:43]),
        "inversion_pressure": int(line[43:49]),
        "inversion_height": int(line[49:55]),

        "mixed_layer_pressure": int(line[55:61]),
        "mixed_layer_height": int(line[61:67]),

        "freezing_pressure": int(line[67:73]),
        "freezing_height": int(line[73:79]),

        "lcl_pressure": int(line[79:85]),
        "lcl_height": int(line[85:91]),

        "lfc_pressure": int(line[91:97]),
        "lfc_height": int(line[97:103]),

        "lnb_pressure": int(line[103:109]),
        "lnb_height": int(line[109:115]),

        "lifted_index": int(line[115:121]),
        "showalter_index": int(line[121:127]),
        "k_index": int(line[127:133]),
        "total_totals_index": int(line[133:139]),

        "cape": int(line[139:145]),
        "cin": int(line[145:151]),
    }


def _parse_derived_level(line: str) -> dict:
    """Parse one IGRA derived profile line using the Data Record Format from
    https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/doc/igra2-derived-format.txt."""

    return {
        "pressure": int(line[0:7]),

        "reported_geopotential_height": int(line[8:15]),
        "calculated_geopotential_height": int(line[16:23]),

        "temperature": int(line[24:31]),
        "temperature_gradient": int(line[32:39]),

        "potential_temperature": int(line[40:47]),
        "potential_temperature_gradient": int(line[48:55]),

        "virtual_temperature": int(line[56:63]),
        "virtual_potential_temperature": int(line[64:71]),

        "vapor_pressure": int(line[72:79]),
        "saturation_vapor_pressure": int(line[80:87]),

        "reported_relative_humidity": int(line[88:95]),
        "calculated_relative_humidity": int(line[96:103]),
        "relative_humidity_gradient": int(line[104:111]),

        "u_wind": int(line[112:119]),
        "u_wind_gradient": int(line[120:127]),

        "v_wind": int(line[128:135]),
        "v_wind_gradient": int(line[136:143]),

        "refractive_index": int(line[144:151]),
    }


# Parse the entire file.
def parse_soundings(lines: list[str]) -> dict[pd.Timestamp, pd.DataFrame]:
    """
    Parse an IGRA station file into a dictionary of soundings.

    Parameters
        lines : list[str]
            List of lines from an IGRA station file.

    Returns
        dict[pandas.Timestamp, pandas.DataFrame]
            Dictionary whose keys are launch datetimes and whose values are
            DataFrames containing the sounding profile. The header metadata
            are stored in each DataFrame's ``attrs`` dictionary.
    """

    soundings = {}

    line_number = 0

    # Loop through each profile associated with each heading.
    while line_number < len(lines):

        # Skip if line is not a header.
        if not lines[line_number].startswith("#"):
            line_number += 1
            continue

        header = _parse_header(lines[line_number])

        profile = []

        for sounding_level in range(header["numlev"]):

            profile.append(_parse_level(lines[line_number + sounding_level + 1]))

        df = pd.DataFrame(profile)

        # Replace IGRA missing values with NaN.
        df.replace([-9999, -8888], np.nan, inplace=True)

        # Convert units
        df["temperature"] = df["temperature"] / 10.0 + 273.15       # tenths C -> K
        df["dpdp"] /= 10.0                                          # tenths C -> C
        df["dewpoint"] = df["temperature"] - df["dpdp"]
        df["wind_speed"] /= 10.0                                    # tenths m/s -> m/s

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

        line_number += header["numlev"] + 1

    return soundings


def parse_derived_soundings(lines: list[str]) -> dict[pd.Timestamp, pd.DataFrame]:
    """
    Parse an IGRA station file into a dictionary of soundings.

    Parameters
        lines : list[str]
            List of lines from an IGRA station file.

    Returns
        dict[pandas.Timestamp, pandas.DataFrame]
            Dictionary whose keys are launch datetimes and whose values are
            DataFrames containing the sounding profile. The header metadata
            are stored in each DataFrame's ``attrs`` dictionary.
    """

    soundings = {}

    line_number = 0

    # Loop through each profile associated with each heading.
    while line_number < len(lines):

        # Skip if line is not a header.
        if not lines[line_number].startswith("#"):
            line_number += 1
            continue

        header = _parse_derived_header(lines[line_number])

        profile = []

        for sounding_level in range(header["numlev"]):

            profile.append(_parse_derived_level(lines[line_number + sounding_level + 1]))

        df = pd.DataFrame(profile)

        # Replace IGRA missing values with NaN.
        df.replace(-99999, np.nan, inplace=True)

        # Convert units.
        df["temperature"] /= 10.0
        df["temperature_gradient"] /= 10.0              # K/km

        df["potential_temperature"] /= 10.0
        df["potential_temperature_gradient"] /= 10.0    # K/km

        df["virtual_temperature"] /= 10.0
        df["virtual_potential_temperature"] /= 10.0     # K/km

        df["vapor_pressure"] /= 10.0
        df["saturation_vapor_pressure"] /= 10.0

        df["reported_relative_humidity"] /= 10.0
        df["calculated_relative_humidity"] /= 10.0
        df["relative_humidity_gradient"] /= 10          # %/km

        df["u_wind"] /= 10.0
        df["u_wind_gradient"] /= 10                     # m/s/km

        df["v_wind"] /= 10.0
        df["v_wind_gradient"] /= 10                     # m/s/km

        dt = pd.Timestamp(
            year=header["year"],
            month=header["month"],
            day=header["day"],
            hour=header["hour"],
        )

        df.attrs = header

        soundings[dt] = df

        line_number += header["numlev"] + 1

    return soundings


def soundings_to_xarray(soundings: dict[pd.Timestamp, pd.DataFrame]) -> xr.Dataset:
    """
    Convert a dictionary of IGRA soundings into an xarray Dataset.

    Parameters
        soundings : dict[pd.Timestamp, pd.DataFrame]. This is generated using parse_soundings.

    Returns
        xr.Dataset for each sounding sorted by timestamp.
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

    # Initialize metadata arrays for profiles with NaN values. (e.g. pressure, temp)
    arrays = {
        var: np.full((ntime, max_levels), np.nan)
        for var in profile_vars
    }

    # Initialize metadata with one value per sounding. (e.g. lat, lon, launch time)
    release_time = np.full(ntime, np.nan)
    numlev = np.full(ntime, np.nan)
    lat = np.full(ntime, np.nan)
    lon = np.full(ntime, np.nan)

    p_src = []
    np_src = []

    # Loop through soundings to fill arrays.
    for i, time in enumerate(times):

        df = soundings[time]

        n = len(df)

        # Fill the arrays.
        for var in profile_vars:

            if var in df.columns:
                arrays[var][i, :n] = df[var].values

        # Metadata from header.
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


def derived_soundings_to_xarray(soundings: dict[pd.Timestamp, pd.DataFrame]) -> xr.Dataset:
    """
    Convert a dictionary of IGRA derived quantities into an xarray Dataset.

    Parameters
        soundings : dict[pd.Timestamp, pd.DataFrame]. This is generated using parse_soundings.

    Returns
        xr.Dataset for each derived sounding sorted by timestamp.
    """

    # Sort chronologically
    times = sorted(soundings.keys())

    ntime = len(times)
    max_levels = max(len(soundings[t]) for t in times)

    profile_vars = [
        "pressure",
        "reported_geopotential_height",
        "calculated_geopotential_height",
        "temperature",
        "temperature_gradient",
        "potential_temperature",
        "potential_temperature_gradient",
        "virtual_temperature",
        "virtual_potential_temperature",
        "vapor_pressure",
        "saturation_vapor_pressure",
        "reported_relative_humidity",
        "calculated_relative_humidity",
        "relative_humidity_gradient",
        "u_wind",
        "u_wind_gradient",
        "v_wind",
        "v_wind_gradient",
        "refractive_index",
    ]

    # Initialize metadata arrays for profiles with NaN values. (e.g. pressure, temp)
    arrays = {
        var: np.full((ntime, max_levels), np.nan)
        for var in profile_vars
    }

    # Initialize metadata with one value per sounding. (e.g. lat, lon, launch time)
    pw = np.full(ntime, np.nan)

    inversion_pressure = np.full(ntime, np.nan)
    inversion_height = np.full(ntime, np.nan)

    mixed_layer_pressure = np.full(ntime, np.nan)
    mixed_layer_height = np.full(ntime, np.nan)

    freezing_pressure = np.full(ntime, np.nan)
    freezing_height = np.full(ntime, np.nan)

    lcl_pressure = np.full(ntime, np.nan)
    lcl_height = np.full(ntime, np.nan)

    lfc_pressure = np.full(ntime, np.nan)
    lfc_height = np.full(ntime, np.nan)

    lnb_pressure = np.full(ntime, np.nan)
    lnb_height = np.full(ntime, np.nan)

    lifted_index = np.full(ntime, np.nan)
    showalter_index = np.full(ntime, np.nan)
    k_index = np.full(ntime, np.nan)
    total_totals_index = np.full(ntime, np.nan)

    cape = np.full(ntime, np.nan)
    cin = np.full(ntime, np.nan)

    # Loop through soundings to fill arrays.
    for i, time in enumerate(times):

        df = soundings[time]

        n = len(df)

        # Fill the arrays.
        for var in profile_vars:

            if var in df.columns:
                arrays[var][i, :n] = df[var].values

        # Metadata from header.
        attrs = df.attrs

        pw[i] = attrs["pw"]

        inversion_pressure[i] = attrs["inversion_pressure"]
        inversion_height[i] = attrs["inversion_height"]

        mixed_layer_pressure[i] = attrs["mixed_layer_pressure"]
        mixed_layer_height[i] = attrs["mixed_layer_height"]

        freezing_pressure[i] = attrs["freezing_pressure"]
        freezing_height[i] = attrs["freezing_height"]

        lcl_pressure[i] = attrs["lcl_pressure"]
        lcl_height[i] = attrs["lcl_height"]

        lfc_pressure[i] = attrs["lfc_pressure"]
        lfc_height[i] = attrs["lfc_height"]

        lnb_pressure[i] = attrs["lnb_pressure"]
        lnb_height[i] = attrs["lnb_height"]

        cape[i] = attrs["cape"]
        cin[i] = attrs["cin"]

        lifted_index[i] = attrs["lifted_index"]
        showalter_index[i] = attrs["showalter_index"]

        k_index[i] = attrs["k_index"]
        total_totals_index[i] = attrs["total_totals_index"]

    ds = xr.Dataset(

        data_vars={

            **{
                var: (("time", "level"), arrays[var])
                for var in profile_vars
            },

            "pw": ("time", pw),

            "inversion_pressure": ("time", inversion_pressure),
            "inversion_height": ("time", inversion_height),

            "mixed_layer_pressure": ("time", mixed_layer_pressure),
            "mixed_layer_height": ("time", mixed_layer_height),

            "freezing_pressure": ("time", freezing_pressure),
            "freezing_height": ("time", freezing_height),

            "lcl_pressure": ("time", lcl_pressure),
            "lcl_height": ("time", lcl_height),

            "lfc_pressure": ("time", lfc_pressure),
            "lfc_height": ("time", lfc_height),

            "lnb_pressure": ("time", lnb_pressure),
            "lnb_height": ("time", lnb_height),

            "cape": ("time", cape),
            "cin": ("time", cin),

            "lifted_index": ("time", lifted_index),
            "showalter_index": ("time", showalter_index),

            "k_index": ("time", k_index),
            "total_totals_index": (
                "time",
                total_totals_index
            ),
        },

        coords={
            "time": pd.to_datetime(times),
            "level": np.arange(max_levels),
        },

        attrs={
            "source": "NOAA NCEI Integrated Global Radiosonde Archive (IGRA Version 2)",
            "institution": "NOAA National Centers for Environmental Information",
            "station": soundings[times[0]].attrs["station"],
            "title": "IGRA Derived Radiosonde Profiles",
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


def merge_sounding_datasets(
        obs_ds: xr.Dataset,
        derived_ds: xr.Dataset
) -> xr.Dataset:
    """Merges the observed profiles dataset and the derived profiles dataset into a single dataset."""
    return xr.merge([obs_ds, derived_ds], compat="override")


def decode_igra_zipfile(zip_path: Path) -> list[str]:
    """Return the decoded line in the first text file in the IGRA2 zipfile."""
    with zipfile.ZipFile(zip_path, mode='r') as zf:

        text_files = [file for file in zf.namelist() if file.endswith(".txt")]

        if not text_files:
            raise(f"No .txt files found in {zip_path.resolve().name}.")

        with zf.open(text_files[0]) as f:
            lines = f.read().decode("ascii").splitlines()

        return lines


data_file = "BBM00078954-data.txt.zip"
drvd_file = "BBM00078954-drvd.txt.zip"

zip_data_file = DATA_DIR / data_file
zip_drvd_file = DATA_DIR / drvd_file

data_lines = decode_igra_zipfile(zip_data_file)
drvd_lines = decode_igra_zipfile(zip_drvd_file)

filename = "BBM00078954-data.txt.zip"
zip_file = DATA_DIR / filename


with zipfile.ZipFile(zip_file, mode='r') as zf:

    text_files = [file for file in zf.namelist() if file.endswith(".txt")]

    if not text_files:
        raise RuntimeError(f"No .txt files found in {DATA_DIR.resolve().name}.")

    with zf.open(text_files[0]) as f:
        lines = f.read().decode("ascii").splitlines()

soundings = parse_soundings(lines)

ds = soundings_to_xarray(soundings)
print(ds, '\n')

output_file = filename.split('-')[0] + '.nc'
ds.to_netcdf(DATA_DIR / output_file)

print(f"Wrote {output_file} to the directory {DATA_DIR.resolve()}.")