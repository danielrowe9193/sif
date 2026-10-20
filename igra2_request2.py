from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from siphon.simplewebservice.igra2 import IGRAUpperAir
import xarray as xr

from src.sif.observations.igra2_requests import igra2_stations_df


def build_request(
    station_id: str,
    start_date: datetime | str,
    end_date: Optional[datetime | str] = None,
    derived: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame]:

    start_date = pd.to_datetime(start_date)

    if end_date is None:
        dates = start_date

    else:
        end_date = pd.to_datetime(end_date)
        dates = [start_date, end_date]

    df, header = IGRAUpperAir.request_data(
        dates,
        station_id,
        derived=derived
    )

    if df.empty:

        if end_date is None:
            raise ValueError(
                f"No sounding found for station {station_id} "
                f"at {start_date:%Y-%m-%d %H:%M}."
            )

        else:
            raise ValueError(
                f"No soundings found for station {station_id} "
                f"between {start_date:%Y-%m-%d %H:%M} and "
                f"{end_date:%Y-%m-%d %H:%M}."
            )

    # Create a common datetime column in the header.
    header["date"] = pd.to_datetime(
        header[["year", "month", "day", "hour"]]
    )

    return df, header


def data_dataset(
    df_data: pd.DataFrame,
    header_data: pd.DataFrame
) \
        -> xr.Dataset:
    """
    Convert non-derived IGRA sounding data into an xarray Dataset.

    Parameters
    ----------
    df_data : pd.DataFrame
        IGRA sounding data returned by Siphon with derived=False.

    header_data : pd.DataFrame
        IGRA sounding header data.

    Returns
    -------
    xr.Dataset
        xarray Dataset containing the reported IGRA sounding profiles.
    """

    # Time and level dimensions.
    times = sorted(df_data["date"].unique())
    ntime = len(times)

    max_levels = df_data.groupby("date").size().max()
    levels = np.arange(max_levels)

    # Variables with vertical levels.
    profile_vars = [
        "pressure",
        "height",
        "temperature",
        "dewpoint",
        "relative_humidity",
        "direction",
        "speed",
        "u_wind",
        "v_wind",
        "lvltyp1",
        "lvltyp2",
        "etime",
    ]

    # Initialize arrays for profile variables with NaN values.
    arrays = {
        var: np.full((ntime, max_levels), np.nan)
        for var in profile_vars
    }

    # Per-sounding variables without vertical levels.
    release_time = np.full(ntime, np.nan)
    numlev = np.full(ntime, np.nan)
    lat = np.full(ntime, np.nan)
    lon = np.full(ntime, np.nan)

    p_src = []
    np_src = []

    # Loop through soundings
    for i, time in enumerate(times):

        sounding = df_data[df_data["date"] == time]

        n = len(sounding)

        # Fill profile arrays.
        for var in profile_vars:

            if var in sounding.columns:
                arrays[var][i, :n] = sounding[var].values

        # Get header information for this sounding.
        header = header_data[header_data["date"] == time]

        if len(header) > 0:

            header = header.iloc[0]

            release_time[i] = header["release_time"]
            numlev[i] = header["number_levels"]

            lat[i] = header["latitude"]
            lon[i] = header["longitude"]

            p_src.append(header["pressure_source_code"])
            np_src.append(header["non_pressure_source_code"])

        else:

            release_time[i] = np.nan
            numlev[i] = np.nan

            lat[i] = np.nan
            lon[i] = np.nan

            p_src.append("")
            np_src.append("")

    # ------------------------------------------------------------
    # Get station attributes
    # ------------------------------------------------------------

    station_id = header_data.iloc[0]["site_id"]

    station_df = igra2_stations_df()

    attrs_dict = (
        station_df.loc[
            station_df["station_id"] == station_id
        ]
        .reset_index(drop=True)
        .iloc[0]
        .to_dict()
    )

    # ------------------------------------------------------------
    # Construct Dataset
    # ------------------------------------------------------------

    ds = xr.Dataset(
        data_vars={

            # ----------------------------------------------------
            # Profile variables
            # ----------------------------------------------------

            "pressure": (
                ("time", "level"),
                arrays["pressure"],
                {
                    "long_name": "air pressure",
                    "standard_name": "air_pressure",
                    "units": "hPa",
                    "description": (
                        "Air pressure at the sounding level."
                    ),
                },
            ),

            "height": (
                ("time", "level"),
                arrays["height"],
                {
                    "long_name": "geopotential height",
                    "standard_name": "geopotential_height",
                    "units": "m",
                    "description": (
                        "Geopotential height of the sounding level."
                    ),
                },
            ),

            "temperature": (
                ("time", "level"),
                arrays["temperature"],
                {
                    "long_name": "air temperature",
                    "standard_name": "air_temperature",
                    "units": "degC",
                    "description": (
                        "Air temperature at the sounding level."
                    ),
                },
            ),

            "dewpoint": (
                ("time", "level"),
                arrays["dewpoint"],
                {
                    "long_name": "dew-point temperature",
                    "standard_name": "dew_point_temperature",
                    "units": "degC",
                    "description": (
                        "Dew-point temperature at the sounding level."
                    ),
                },
            ),

            "wind_dir": (
                ("time", "level"),
                arrays["direction"],
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
                arrays["speed"],
                {
                    "long_name": "wind speed",
                    "standard_name": "wind_speed",
                    "units": "m/s",
                    "description": (
                        "Horizontal wind speed at the sounding level."
                    ),
                },
            ),

            "u_wind": (
                ("time", "level"),
                arrays["u_wind"],
                {
                    "long_name": "zonal wind component",
                    "standard_name": "eastward_wind",
                    "units": "m/s",
                    "description": (
                        "Eastward component of horizontal wind."
                    ),
                },
            ),

            "v_wind": (
                ("time", "level"),
                arrays["v_wind"],
                {
                    "long_name": "meridional wind component",
                    "standard_name": "northward_wind",
                    "units": "m/s",
                    "description": (
                        "Northward component of horizontal wind."
                    ),
                },
            ),

            "relative_humidity": (
                ("time", "level"),
                arrays["relative_humidity"],
                {
                    "long_name": "relative humidity",
                    "standard_name": "relative_humidity",
                    "units": "%",
                    "description": (
                        "Relative humidity at the sounding level."
                    ),
                },
            ),

            "lvltyp1": (
                ("time", "level"),
                arrays["lvltyp1"],
                {
                    "long_name": "primary level type",
                    "description": (
                        "IGRA primary level-type code."
                    ),
                },
            ),

            "lvltyp2": (
                ("time", "level"),
                arrays["lvltyp2"],
                {
                    "long_name": "secondary level type",
                    "description": (
                        "IGRA secondary level-type code."
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
                        "Elapsed time from radiosonde launch to "
                        "the observation at the sounding level."
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
                    "description": (
                        "Number of reported levels in the sounding."
                    ),
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
                    "description": (
                        "IGRA source code for pressure observations."
                    ),
                },
            ),

            "nonpressure_source": (
                "time",
                np.asarray(np_src, dtype="U16"),
                {
                    "long_name": "non-pressure source",
                    "description": (
                        "IGRA source code for non-pressure observations."
                    ),
                },
            ),
        },

        coords={
            "time": pd.to_datetime(times),
            "level": levels,
        },

        attrs={
            "source": (
                "NOAA NCEI Integrated Global Radiosonde Archive "
                "(IGRA Version 2)"
            ),
            "institution": (
                "NOAA National Centers for Environmental Information"
            ),
            "title": "IGRA Radiosonde Profiles",
            "history": (
                f"Converted from IGRA data using Siphon on "
                f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M UTC')}"
            ),
            "references": (
                "https://www.ncei.noaa.gov/products/weather-balloon/"
                "integrated-global-radiosonde-archive"
            ),
            "featureType": "timeSeriesProfile",
        },
    )

    # Add station metadata
    ds.attrs.update(attrs_dict)

    ds.attrs["station_name"] = (
        ds.attrs["station_name"].title()
    )

    ds.attrs["elevation_units"] = "m"

    return ds


def drvd_dataset(
    df_drvd: pd.DataFrame,
    header_drvd: pd.DataFrame
) \
        -> xr.Dataset:
    """
    Convert IGRA derived sounding data into an xarray Dataset.

    Parameters
    ----------
    df_drvd : pd.DataFrame
        IGRA derived sounding data returned by Siphon.

    header_drvd : pd.DataFrame
        IGRA derived sounding header data.

    Returns
    ----------
    xr.Dataset
        IGRA derived sounding parameters sorted chronologically.
    """

    # Sort chronologically
    times = sorted(df_drvd["date"].unique())
    ntime = len(times)

    max_levels = df_drvd.groupby("date").size().max()
    levels = np.arange(max_levels)

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

        sounding = df_drvd[df_drvd["date"] == time]

        n = len(sounding)

        # Fill the arrays.
        for var in profile_vars:

            if var in sounding.columns:
                arrays[var][i, :n] = sounding[var].values

        # Get header information for this sounding.
        header = header_drvd[header_drvd["date"] == time]

        if len(header) > 0:
            header = header.iloc[0]

            # Thermodynamic sounding parameters.
            pw[i] = header["precipitable_water"]

            inversion_pressure[i] = header["inv_pressure"]
            inversion_height[i] = header["inv_height"]

            mixed_layer_pressure[i] = header["mixed_layer_pressure"]
            mixed_layer_height[i] = header["mixed_layer_height"]

            freezing_pressure[i] = header["freezing_point_pressure"]
            freezing_height[i] = header["freezing_point_height"]

            lcl_pressure[i] = header["lcl_pressure"]
            lcl_height[i] = header["lcl_height"]

            lfc_pressure[i] = header["lfc_pressure"]
            lfc_height[i] = header["lfc_height"]

            lnb_pressure[i] = header["lnb_pressure"]
            lnb_height[i] = header["lnb_height"]

            # Stability indices.
            cape[i] = header["cape"]
            cin[i] = header["convective_inhibition"]

            lifted_index[i] = header["lifted_index"]
            showalter_index[i] = header["showalter_index"]

            k_index[i] = header["k_index"]
            total_totals_index[i] = header["total_totals_index"]


    # Get station metadata from the IGRA station list.
    station_id = header_drvd.iloc[0]["site_id"]

    station_df = igra2_stations_df()

    attrs_dict = station_df.loc[station_df["station_id"] == station_id].reset_index(drop=True).iloc[0].to_dict()


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

    # Add station metadata.
    ds.attrs.update(attrs_dict)
    ds.attrs['station_name'] = ds.attrs['station_name'].title()
    ds.attrs['elevation_units'] = 'm'

    return ds


def merge_sounding_datasets(
        obs_ds: xr.Dataset,
        derived_ds: xr.Dataset
)\
        -> xr.Dataset:
    """Merges the observed profiles dataset and the derived indices dataset into a single dataset."""
    return xr.merge([obs_ds, derived_ds], compat="override", join='outer')


# Request data

df1, header1 = build_request(
    "BBM00078954",
    start_date="2020-07-18",
    end_date="2020-07-20",
    derived=False
)

df2, header2 = build_request(
    "BBM00078954",
    start_date="2020-07-18",
    end_date="2020-07-20",
    derived=True
)

# ================================================================
# Convert to xarray
# ================================================================

ds1 = data_dataset(df1, header1)
ds2 = drvd_dataset(df2, header2)

ds = merge_sounding_datasets(ds1, ds2)