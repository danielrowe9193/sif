from pathlib import Path
import zipfile

import numpy as np
import pandas as pd
import xarray as xr

from src.sif.utils.utils import FileManagement


# Areas for users to edit.
igra_data_folder = FileManagement.IGRA_DIR.glob("*.txt.zip")

# For soundings in a particular date range.
start_date: str = "2006-08"
end_date: str = "2026-09"

# For soundings in only this year or these months.
year: int = None
month: int = 8


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
    """Parse one IGRA profile line using the Header Record Format from
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
        "inversion_temperature_difference": int(line[55:61]),

        "mixed_layer_pressure": int(line[61:67]),
        "mixed_layer_height": int(line[67:73]),

        "freezing_pressure": int(line[73:79]),
        "freezing_height": int(line[79:85]),

        "lcl_pressure": int(line[85:91]),
        "lcl_height": int(line[91:97]),

        "lfc_pressure": int(line[97:103]),
        "lfc_height": int(line[103:109]),

        "lnb_pressure": int(line[109:115]),
        "lnb_height": int(line[115:121]),

        "lifted_index": int(line[121:127]),
        "showalter_index": int(line[127:133]),
        "k_index": int(line[133:139]),
        "total_totals_index": int(line[139:145]),

        "cape": int(line[145:151]),
        "cin": int(line[151:157]),
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
def parse_soundings(
        lines: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
        year: int | None = None,
        month: int | None = None
)\
        -> dict[pd.Timestamp, pd.DataFrame]:
    """
    Parse an IGRA2 station file into a dictionary of soundings.

    Parameters
        lines : list[str]
            List of lines from an IGRA station file.

        start_date : str, optional
            Earliest sounding to include in date range.

        end_date : str, optional
            Latest sounding to include in date range.

        year : int, optional
            Only include soundings from this year.

        month : int, optional
            Only include soundings from this month in the date range.

    Returns
        dict[pandas.Timestamp, pandas.DataFrame]
            Dictionary whose keys are launch datetimes and whose values are
            DataFrames containing the sounding profile. The header metadata
            are stored in each DataFrame's ``attrs`` dictionary.
    """
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    soundings = {}

    line_number = 0

    # Loop through each profile associated with each heading.
    while line_number < len(lines):
        # Skip if line is not a header.
        if not lines[line_number].startswith("#"):
            line_number += 1
            continue

        header = _parse_header(lines[line_number])

        # Datetime for this sounding.
        dt = pd.Timestamp(
            year=header["year"],
            month=header["month"],
            day=header["day"],
            hour=header["hour"],
        )

        # Number of levels in this sounding.
        numlev = header["numlev"]

        # Date-range filtering.
        if start_date is not None and dt < start_date:
            line_number += numlev + 1
            continue

        if end_date is not None and dt > end_date:
            break

        # Year filtering.
        if year is not None and dt.year < year:
            line_number += numlev + 1
            continue

        # Month filtering.
        if month is not None and dt.month != month:
            line_number += numlev + 1
            continue

        profile = []

        for sounding_level in range(numlev):
            profile.append(_parse_level(lines[line_number + sounding_level + 1]))

        df = pd.DataFrame(profile)

        # Replace IGRA missing values with NaN.
        df.replace([-9999, -8888], np.nan, inplace=True)

        # Convert units
        df["temperature"] = df["temperature"] / 10.0 + 273.15  # tenths C -> K
        df["dpdp"] /= 10.0  # tenths C -> C
        df["dewpoint"] = df["temperature"] - df["dpdp"]
        df["wind_speed"] /= 10.0  # tenths m/s -> m/s

        # header["release_time"] = pd.to_datetime(
        #     dt.strftime("%Y-%m-%d") + str(header["release_time"]).zfill(4),
        #     format="%Y-%m-%d%H%M",
        # )

        # Store metadata in DataFrame attributes
        df.attrs = header

        # Save sounding
        soundings[dt] = df

        line_number += header["numlev"] + 1

    return soundings


def parse_derived_soundings(
        lines: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
        year: int | None = None,
        month: int | None = None
) \
        -> dict[pd.Timestamp, pd.DataFrame]:
    """
    Parse an IGRA2 derived parameters station file into a dictionary of derived parameters.

    Parameters
        lines : list[str]
            List of lines from an IGRA2 derived station file.

        start_date : str, optional
            Earliest sounding to include in date range.

        end_date : str, optional
            Latest sounding to include in date range.

        year : int, optional
            Only include soundings from this year.

        month : int, optional
            Only include soundings from this month in the date range.

    Returns
        dict[pandas.Timestamp, pandas.DataFrame]
            Dictionary whose keys are launch datetimes and whose values are
            DataFrames containing the sounding profile. The header metadata
            are stored in each DataFrame's ``attrs`` dictionary.
    """
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    soundings = {}

    line_number = 0

    # Loop through each profile associated with each heading.
    while line_number < len(lines):

        # Skip if line is not a header.
        if not lines[line_number].startswith("#"):
            line_number += 1
            continue

        header = _parse_derived_header(lines[line_number])

        # Datetime for this sounding.
        dt = pd.Timestamp(
            year=header["year"],
            month=header["month"],
            day=header["day"],
            hour=header["hour"],
        )

        # Number of levels in this sounding.
        numlev = header["numlev"]

        # Date-range filtering.
        if start_date is not None and dt < start_date:
            line_number += numlev + 1
            continue

        if end_date is not None and dt > end_date:
            break

        # Year filtering.
        if year is not None and dt.year < year:
            line_number += numlev + 1
            continue

        # Month filtering.
        if month is not None and dt.month != month:
            line_number += numlev + 1
            continue

        profile = []

        for sounding_level in range(numlev):

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

        # df["pw"] /= 100                                 # mm

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
    arrays = {var: np.full((ntime, max_levels), np.nan) for var in profile_vars}

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
            "pressure": (
                ("time", "level"),
                arrays["pressure"],
                {
                    "long_name": "air pressure",
                    "standard_name": "air_pressure",
                    "units": "Pa",
                    "description": "Air pressure at the sounding level.",
                },
            ),

            "height": (
                ("time", "level"),
                arrays["height"],
                {
                    "long_name": "geopotential height",
                    "standard_name": "geopotential_height",
                    "units": "m",
                    "description": "Geopotential height of the sounding level.",
                },
            ),

            "temperature": (
                ("time", "level"),
                arrays["temperature"],
                {
                    "long_name": "air temperature",
                    "standard_name": "air_temperature",
                    "units": "K",
                    "description": "Air temperature at the sounding level.",
                },
            ),

            "dewpoint": (
                ("time", "level"),
                arrays["dewpoint"],
                {
                    "long_name": "dew-point temperature",
                    "standard_name": "dew_point_temperature",
                    "units": "K",
                    "description": "Dew-point temperature at the sounding level.",
                },
            ),

            "dew_point_depression": (
                ("time", "level"),
                arrays["dew_point_depression"],
                {
                    "long_name": "dew-point depression",
                    "units": "K",
                    "description": "Difference between air temperature and dew-point temperature."                    ,
                },
            ),

            "wind_dir": (
                ("time", "level"),
                arrays["wind_dir"],
                {
                    "long_name": "wind direction",
                    "standard_name": "wind_from_direction",
                    "units": "degrees",
                    "description": (
                        "Direction from which the wind is blowing, "
                        "measured clockwise from true north."
                    ),
                },
            ),

            "wind_speed": (
                ("time", "level"),
                arrays["wind_speed"],
                {
                    "long_name": "wind speed",
                    "standard_name": "wind_speed",
                    "units": "m/s",
                    "description": "Horizontal wind speed at the sounding level.",
                },
            ),

            "relative_humidity": (
                ("time", "level"),
                arrays["relative_humidity"],
                {
                    "long_name": "relative humidity",
                    "standard_name": "relative_humidity",
                    "units": "%",
                    "description": "Relative humidity at the sounding level.",
                },
            ),

            "lvltyp1": (
                ("time", "level"),
                arrays["lvltyp1"],
                {
                    "long_name": "primary level type",
                    "description": (
                        "IGRA level-type code identifying the primary "
                        "characteristic of the sounding level."
                    ),
                },
            ),

            "lvltyp2": (
                ("time", "level"),
                arrays["lvltyp2"],
                {
                    "long_name": "secondary level type",
                    "description": (
                        "IGRA level-type code identifying the secondary "
                        "characteristic of the sounding level."
                    ),
                },
            ),

            "etime": (
                ("time", "level"),
                arrays["etime"],
                {
                    "long_name": "elapsed time since launch",
                    "units": "s",
                    "description": (
                        "Elapsed time from radiosonde launch to the "
                        "observation at the sounding level."
                    ),
                },
            ),

            # Per-sounding variables

            "release_time": (
                "time",
                release_time,
                {
                    "long_name": "release time",
                    "units": "minutes",
                    "description": (
                        "Time of radiosonde release relative to "
                        "the nominal sounding time."
                    ),
                },
            ),

            "numlev": (
                "time",
                numlev,
                {
                    "long_name": "number of levels",
                    "units": "1",
                    "description": "Number of reported levels in the sounding."
                },
            ),

            "latitude": (
                "time",
                lat,
                {
                    "long_name": "station latitude",
                    "standard_name": "latitude",
                    "units": "degrees_north",
                },
            ),

            "longitude": (
                "time",
                lon,
                {
                    "long_name": "station longitude",
                    "standard_name": "longitude",
                    "units": "degrees_east",
                },
            ),

            "pressure_source": (
                "time",
                np.asarray(p_src, dtype="U16"),
                {
                    "long_name": "pressure source",
                    "description": "IGRA source code for pressure observations.",
                },
            ),

            "nonpressure_source": (
                "time",
                np.asarray(np_src, dtype="U16"),
                {
                    "long_name": "non-pressure source",
                    "description": "IGRA source code for non-pressure observations."
                },
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
            "title": "IGRA Radiosonde Profiles",
            "history": (
                f"Converted from IGRA text format on "
                f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M UTC')}"
            ),
            "references": (
                "https://www.ncei.noaa.gov/products/weather-balloon/integrated-global-radiosonde-archive"
                "integrated-global-radiosonde-archive"
            ),
            "featureType": "timeSeriesProfile",
        },
    )

    return ds


def derived_soundings_to_xarray(soundings: dict[pd.Timestamp, pd.DataFrame]) -> xr.Dataset:
    """
    Convert a dictionary of IGRA derived sounding quantities into an xarray Dataset.

    Parameters
    ----------
    soundings : dict[pd.Timestamp, pd.DataFrame]
        Dictionary generated using ``parse_derived_soundings``.

    Returns
    ----------
    xr.Dataset
        IGRA derived sounding parameters sorted chronologically.
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

            # Profile variables

            "pressure": (
                ("time", "level"),
                arrays["pressure"],
                {
                    "long_name": "air pressure",
                    "standard_name": "air_pressure",
                    "units": "hPa",
                    "description": "Reported pressure at the sounding level.",
                },
            ),

            "reported_geopotential_height": (
                ("time", "level"),
                arrays["reported_geopotential_height"],
                {
                    "long_name": "reported geopotential height",
                    "standard_name": "geopotential_height",
                    "units": "m",
                    "description": "Reported geopotential height at the sounding level.",
                },
            ),

            "calculated_geopotential_height": (
                ("time", "level"),
                arrays["calculated_geopotential_height"],
                {
                    "long_name": "calculated geopotential height",
                    "standard_name": "geopotential_height",
                    "units": "m",
                    "description": (
                        "Geopotential height calculated using hydrostatic "
                        "balance where reported geopotential height is "
                        "unavailable."
                    ),
                },
            ),

            "temperature": (
                ("time", "level"),
                arrays["temperature"],
                {
                    "long_name": "air temperature",
                    "standard_name": "air_temperature",
                    "units": "K",
                    "description": (
                        "Reported air temperature at the sounding level."
                    ),
                },
            ),

            "temperature_gradient": (
                ("time", "level"),
                arrays["temperature_gradient"],
                {
                    "long_name": "vertical temperature gradient",
                    "units": "K km-1",
                    "description": (
                        "Temperature gradient between the current level "
                        "and the next higher level with a temperature "
                        "observation. Positive values indicate increasing "
                        "temperature with height."
                    ),
                },
            ),

            "potential_temperature": (
                ("time", "level"),
                arrays["potential_temperature"],
                {
                    "long_name": "potential temperature",
                    "standard_name": "air_potential_temperature",
                    "units": "K",
                    "description": "Potential temperature at the sounding level.",
                },
            ),

            "potential_temperature_gradient": (
                ("time", "level"),
                arrays["potential_temperature_gradient"],
                {
                    "long_name": "vertical potential temperature gradient",
                    "units": "K km-1",
                    "description": (
                        "Potential temperature gradient between the current "
                        "level and the next higher level with a potential "
                        "temperature observation. Positive values indicate "
                        "increasing potential temperature with height."
                    ),
                },
            ),

            "virtual_temperature": (
                ("time", "level"),
                arrays["virtual_temperature"],
                {
                    "long_name": "virtual temperature",
                    "standard_name": "virtual_temperature",
                    "units": "K",
                    "description": "Virtual temperature at the sounding level.",
                },
            ),

            "virtual_potential_temperature": (
                ("time", "level"),
                arrays["virtual_potential_temperature"],
                {
                    "long_name": "virtual potential temperature",
                    "standard_name": "virtual_potential_temperature",
                    "units": "K",
                    "description": "Virtual potential temperature at the sounding level.",
                },
            ),

            "vapor_pressure": (
                ("time", "level"),
                arrays["vapor_pressure"],
                {
                    "long_name": "water vapor pressure",
                    "standard_name": "water_vapor_partial_pressure_in_air",
                    "units": "hPa",
                    "description": (
                        "Vapor pressure calculated from temperature, "
                        "pressure, and dew-point depression."
                    ),
                },
            ),

            "saturation_vapor_pressure": (
                ("time", "level"),
                arrays["saturation_vapor_pressure"],
                {
                    "long_name": "saturation vapor pressure",
                    "standard_name": "water_vapor_saturation_pressure",
                    "units": "hPa",
                    "description": "Saturation vapor pressure calculated from pressure and temperature.",
                },
            ),

            "reported_relative_humidity": (
                ("time", "level"),
                arrays["reported_relative_humidity"],
                {
                    "long_name": "reported relative humidity",
                    "standard_name": "relative_humidity",
                    "units": "%",
                    "description": "Relative humidity reported in the original sounding.",
                },
            ),

            "calculated_relative_humidity": (
                ("time", "level"),
                arrays["calculated_relative_humidity"],
                {
                    "long_name": "calculated relative humidity",
                    "standard_name": "relative_humidity",
                    "units": "%",
                    "description": (
                        "Relative humidity calculated from vapor pressure, "
                        "saturation vapor pressure, and pressure."
                    ),
                },
            ),

            "relative_humidity_gradient": (
                ("time", "level"),
                arrays["relative_humidity_gradient"],
                {
                    "long_name": "vertical relative humidity gradient",
                    "units": "% km-1",
                    "description": (
                        "Relative humidity gradient between the current "
                        "level and the next higher usable level. Positive "
                        "values indicate increasing relative humidity "
                        "with height."
                    ),
                },
            ),

            "u_wind": (
                ("time", "level"),
                arrays["u_wind"],
                {
                    "long_name": "zonal wind component",
                    "standard_name": "eastward_wind",
                    "units": "m s-1",
                    "description": (
                        "Zonal wind component calculated from reported "
                        "wind speed and direction. Positive values are "
                        "eastward."
                    ),
                },
            ),

            "u_wind_gradient": (
                ("time", "level"),
                arrays["u_wind_gradient"],
                {
                    "long_name": "vertical zonal wind gradient",
                    "units": "m s-1 km-1",
                    "description": (
                        "Vertical gradient of the zonal wind component "
                        "between the current level and the next higher "
                        "level with a wind observation. Positive values "
                        "indicate that zonal wind becomes more positive "
                        "with height."
                    ),
                },
            ),

            "v_wind": (
                ("time", "level"),
                arrays["v_wind"],
                {
                    "long_name": "meridional wind component",
                    "standard_name": "northward_wind",
                    "units": "m s-1",
                    "description": (
                        "Meridional wind component calculated from reported "
                        "wind speed and direction. Positive values are "
                        "northward."
                    ),
                },
            ),

            "v_wind_gradient": (
                ("time", "level"),
                arrays["v_wind_gradient"],
                {
                    "long_name": "vertical meridional wind gradient",
                    "units": "m s-1 km-1",
                    "description": (
                        "Vertical gradient of the meridional wind component "
                        "between the current level and the next higher "
                        "level with a wind observation. Positive values "
                        "indicate that meridional wind becomes more positive "
                        "with height."
                    ),
                },
            ),

            "refractive_index": (
                ("time", "level"),
                arrays["refractive_index"],
                {
                    "long_name": "radio refractive index",
                    "units": "1",
                    "description": (
                        "Atmospheric refractive index at the sounding level."
                    ),
                },
            ),

            # Sounding-level parameters

            "pw": (
                "time",
                pw,
                {
                    "long_name": "precipitable water",
                    "standard_name": "atmosphere_water_vapor_content",
                    "units": "mm",
                    "description": "Precipitable water between the surface and 500 hPa.",
                },
            ),

            "inversion_pressure": (
                "time",
                inversion_pressure,
                {
                    "long_name": "inversion pressure",
                    "units": "Pa",
                    "description": (
                        "Pressure at the level of the warmest temperature "
                        "in the sounding when the warmest temperature "
                        "occurs above the surface."
                    ),
                },
            ),

            "inversion_height": (
                "time",
                inversion_height,
                {
                    "long_name": "inversion height",
                    "units": "m",
                    "description": "Height above the surface of the warmest temperature in the sounding.",
                },
            ),

            "mixed_layer_pressure": (
                "time",
                mixed_layer_pressure,
                {
                    "long_name": "mixed-layer top pressure",
                    "units": "Pa",
                    "description": "Pressure at the top of the mixed layer determined using the parcel method.",
                },
            ),

            "mixed_layer_height": (
                "time",
                mixed_layer_height,
                {
                    "long_name": "mixed-layer top height",
                    "units": "m",
                    "description": (
                        "Height above the surface of the top of the "
                        "mixed layer determined using the parcel method."
                    ),
                },
            ),

            "freezing_pressure": (
                "time",
                freezing_pressure,
                {
                    "long_name": "freezing-level pressure",
                    "units": "Pa",
                    "description": (
                        "Pressure where temperature first reaches the "
                        "freezing point when moving upward from the surface."
                    ),
                },
            ),

            "freezing_height": (
                "time",
                freezing_height,
                {
                    "long_name": "freezing-level height",
                    "units": "m",
                    "description": (
                        "Height above the surface where temperature first "
                        "reaches the freezing point."
                    ),
                },
            ),

            "lcl_pressure": (
                "time",
                lcl_pressure,
                {
                    "long_name": "lifting condensation level pressure",
                    "standard_name": "air_pressure_at_lifting_condensation_level",
                    "units": "Pa",
                    "description": "Pressure at the lifting condensation level.",
                },
            ),

            "lcl_height": (
                "time",
                lcl_height,
                {
                    "long_name": "lifting condensation level height",
                    "units": "m",
                    "description": "Height above the surface of the lifting condensation level.",
                },
            ),

            "lfc_pressure": (
                "time",
                lfc_pressure,
                {
                    "long_name": "level of free convection pressure",
                    "units": "Pa",
                    "description": "Pressure at the level of free convection.",
                },
            ),

            "lfc_height": (
                "time",
                lfc_height,
                {
                    "long_name": "level of free convection height",
                    "units": "m",
                    "description": "Height above the surface of the level of free convection.",
                },
            ),

            "lnb_pressure": (
                "time",
                lnb_pressure,
                {
                    "long_name": "level of neutral buoyancy pressure",
                    "units": "Pa",
                    "description": (
                        "Pressure at the level of neutral buoyancy, "
                        "also known as the equilibrium level."
                    ),
                },
            ),

            "lnb_height": (
                "time",
                lnb_height,
                {
                    "long_name": "level of neutral buoyancy height",
                    "units": "m",
                    "description": (
                        "Height above the surface of the level of "
                        "neutral buoyancy."
                    ),
                },
            ),

            # Stability indices

            "lifted_index": (
                "time",
                lifted_index,
                {
                    "long_name": "lifted index",
                    "units": "degC",
                    "description": "Lifted index calculated from the sounding.",
                },
            ),

            "showalter_index": (
                "time",
                showalter_index,
                {
                    "long_name": "Showalter index",
                    "units": "degC",
                    "description": (
                        "Showalter stability index calculated from "
                        "the sounding."
                    ),
                },
            ),

            "k_index": (
                "time",
                k_index,
                {
                    "long_name": "K index",
                    "units": "degC",
                    "description": (
                        "K index calculated from the sounding."
                    ),
                },
            ),

            "total_totals_index": (
                "time",
                total_totals_index,
                {
                    "long_name": "total totals index",
                    "units": "degC",
                    "description": (
                        "Total totals stability index calculated from "
                        "the sounding."
                    ),
                },
            ),

            "cape": (
                "time",
                cape,
                {
                    "long_name": "convective available potential energy",
                    "standard_name": "atmosphere_specific_convective_available_potential_energy",
                    "units": "J kg-1",
                    "description": (
                        "Convective available potential energy calculated "
                        "from the sounding."
                    ),
                },
            ),

            "cin": (
                "time",
                cin,
                {
                    "long_name": "convective inhibition",
                    "standard_name": "atmosphere_specific_convective_inhibition",
                    "units": "J kg-1",
                    "description": (
                        "Convective inhibition calculated from the sounding."
                    ),
                },
            ),
        },

        coords={
            "time": (
                "time",
                pd.to_datetime(times),
                {
                    "long_name": "sounding time",
                    "standard_name": "time",
                    "description": "Date and time of the radiosonde sounding.",
                },
            ),
            "level": (
                "level",
                np.arange(max_levels),
                {
                    "long_name": "sounding level",
                    "description": "Index of the vertical sounding levels.",
                },
            ),
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
)\
        -> xr.Dataset:
    """Merges the observed profiles dataset and the derived indices dataset into a single dataset."""
    return xr.merge([obs_ds, derived_ds], compat="override", join='outer')


def decode_igra_zipfile(zip_path: Path) -> list[str]:
    """Return the decoded lines in the first text file in the IGRA2 zipfile."""
    with zipfile.ZipFile(zip_path, mode='r') as zf:

        text_files = [file for file in zf.namelist() if file.endswith(".txt")]

        if not text_files:
            raise(f"No .txt files found in {zip_path.resolve().name}.")

        with zf.open(text_files[0]) as f:
            lines = f.read().decode("ascii").splitlines()

        return lines


def data_zipfiles(file_list: list[str]) -> list[str]:
    """Extract the IGRA2 data files from a mixed list."""
    data_files = [file for file in file_list if file.endswith("-data.txt.zip")]

    return data_files


def drvd_zipfiles(file_list: list[str]) -> list[str]:
    """Extract the IGRA2 derived files from a mixed list."""
    drvd_files = [file for file in file_list if file.endswith("-drvd.txt.zip")]

    return drvd_files


def main():
    zip_files = [zip_file.name for zip_file in igra_data_folder]

    # Extract the IGRA2 files.
    data_files = data_zipfiles(zip_files)
    drvd_files = drvd_zipfiles(zip_files)

    for data_file in data_files:

        # Get the station id.
        station_id = data_file.split('-')[0]

        # Locate the data file.
        zip_data_file = FileManagement.IGRA_DIR / data_file

        print(f"Processing {station_id}...")

        # Decode the data file.
        print(f'Decoding {data_file}...')
        data_lines = decode_igra_zipfile(zip_data_file)

        # Parse the data lines into a dictionary of Timestamps and DataFrames.
        print('Parsing sounding...')
        soundings = parse_soundings(
            data_lines,
            start_date=start_date,
            end_date=end_date,
            year=year,
            month=month
        )

        print('Writing the sounding dictionary into xarray...')
        ds_data = soundings_to_xarray(soundings)
        print("Successfully wrote to xarray.\n")

        # Find the corresponding derived file.
        drvd_file = f"{station_id}-drvd.txt.zip"
        zip_drvd_file = FileManagement.IGRA_DIR / drvd_file

        # If the derived file exists, decode, parse, and merge it.
        if zip_drvd_file.exists():

            print(f"Found derived file for {station_id}.")

            print(f'Decoding {drvd_file}...')
            drvd_lines = decode_igra_zipfile(zip_drvd_file)

            print('Parsing derived file...')
            derived_soundings = parse_derived_soundings(
                drvd_lines,
                start_date=start_date,
                end_date=end_date,
                year=year,
                month=month
            )

            print('Writing the derived dictionary into xarray...')
            ds_drvd = derived_soundings_to_xarray(derived_soundings)
            print("Successfully wrote to xarray.\n")

            # Merge the data and derived datasets.
            print("Merging sounding data and derived datasets...")
            ds_data = merge_sounding_datasets(ds_data, ds_drvd)
            print("Datasets successfully merged.\n")

        else:
            print(f"No derived file found for {station_id}.")
            print("Creating dataset from sounding data only.\n")

        # Create the NetCDF directory.
        FileManagement.NETCDF_DIR.mkdir(
            exist_ok=True,
            parents=True,
        )

        # Write the output file.
        output_file = FileManagement.NETCDF_DIR / f"Aug-2006-2026-{station_id}.nc"

        print("Generating NetCDF file...\n")
        ds_data.to_netcdf(output_file)

        print(
            f"Successfully wrote {output_file.name} "
            f"to {FileManagement.NETCDF_DIR.resolve()}.\n"
        )


if __name__ == "__main__":
    main()

# # File names for the data file and the derived sounding files.
# data_file = "BBM00078954-data.txt.zip"
# drvd_file = "BBM00078954-drvd.txt.zip"
#
# # Locate the data and the derived sounding files.
# zip_data_file = FileManagement.IGRA_DIR
# zip_drvd_file = DATA_DIR / drvd_file
#
# # Decode the data and the derived sounding files into a list of lines.
# data_lines = decode_igra_zipfile(zip_data_file)
# drvd_lines = decode_igra_zipfile(zip_drvd_file)
#
# # Parse the list of data lines into a dictionary of Timestamps and DataFrames.
# soundings = parse_soundings(data_lines)
# ds_data = soundings_to_xarray(soundings)
#
# # Parse the list of derived lines into a dictionary of Timestamp and DataFrames.
# derived_soundings = parse_derived_soundings(drvd_lines)
# ds_drvd = derived_soundings_to_xarray(derived_soundings)
#
# # Merge the data and derived datasets.
# ds = merge_sounding_datasets(ds_data, ds_drvd)
#
# # Write the output file to the data directory.
# output_file = data_file.split('-')[0] + '4.nc'
# ds.to_netcdf(DATA_DIR / output_file)
#
# print(f"Wrote {output_file} to the directory {DATA_DIR.resolve()}.")

# ROOT = Path(__file__).resolve().parents[2]
# DATA_DIR = Path("data")
# ZIP_DIR = ROOT / DATA_DIR
#
# filename = "BBM00078954-data.txt.zip"
# zip_file = ZIP_DIR / filename
#
#
# with zipfile.ZipFile(zip_file, mode="r") as zf:
#     text_files = [file for file in zf.namelist() if file.endswith(".txt")]
#
#     if not text_files:
#         raise RuntimeError(f"No .txt files found in {ZIP_DIR.resolve().name}.")
#
#     with zf.open(text_files[0]) as f:
#         lines = f.read().decode("ascii").splitlines()
#
# soundings = parse_soundings(lines)
#
# ds = soundings_to_xarray(soundings)
# print(ds, "\n")
#
# output_file = filename.split("-")[0] + ".nc"
# ds.to_netcdf(ZIP_DIR / output_file)
#
# print(f"Wrote {output_file} to the directory {ZIP_DIR.resolve()}.")
