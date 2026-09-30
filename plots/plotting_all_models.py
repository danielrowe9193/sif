# all model plots
import numpy as np
import matplotlib.pyplot as plt

from metpy.units import units
from metpy.calc import dewpoint_from_specific_humidity
from matplotlib.ticker import NullFormatter, FixedLocator, FixedFormatter
from matplotlib.lines import Line2D


def parse_time(time):
    """
    Convert YYYY-MM-DD-HHz to numpy.datetime64.

    Example
    -------
    "2029-09-29-00z"
    """

    time_clean = str(time).lower().replace("z", "")

    date_part, hour_part = time_clean.rsplit("-", 1)

    return np.datetime64(
        f"{date_part}T{hour_part}:00"
    )


def format_time(time):
    """
    Format datetime as YYYY-MM-DD-HHz.

    Example
    -------
    2029-09-29T00:00:00
    ->
    2029-09-29-00z
    """

    time_string = str(time)

    # Remove fractional seconds
    if "." in time_string:
        time_string = time_string.split(".")[0]

    date_part, hour_part = time_string.split("T")

    hour = hour_part[:2]

    return f"{date_part}-{hour}z"


def normalize_forecast_hour(forecast_hour):
    """
    Normalize forecast-hour input.

    Examples
    --------
    12
    "12"
    "12h"

    All become:

    "12h"
    """

    forecast_hour = str(
        forecast_hour
    ).lower().strip()

    if forecast_hour.endswith("h"):
        return forecast_hour

    return f"{forecast_hour}h"


# ============================================================
# TIME / FORECAST SELECTION
# ============================================================

def select_time(
    ds,
    time,
    forecast_hour
):
    """
    Select the record matching the requested valid time
    and forecast hour.

    The selection is performed using:

        forecast_hour
        +
        valid_time

    The corresponding init_time is returned as well.
    """

    target_time = parse_time(
        time
    )

    requested_forecast_hour = (
        normalize_forecast_hour(
            forecast_hour
        )
    )

    # --------------------------------------------------------
    # Dataset coordinates
    # --------------------------------------------------------

    valid_times = np.asarray(
        ds["valid_time"].values
    )

    forecast_hours = np.asarray(
        ds["forecast_hour"].values
    ).astype(str)

    init_times = np.asarray(
        ds["init_time"].values
    )

    # --------------------------------------------------------
    # Normalize forecast-hour strings
    # --------------------------------------------------------

    forecast_hours = np.array([
        normalize_forecast_hour(fh)
        for fh in forecast_hours
    ])

    # --------------------------------------------------------
    # Find records matching forecast hour
    # --------------------------------------------------------

    forecast_mask = (
        forecast_hours ==
        requested_forecast_hour
    )

    matching_indices = np.where(
        forecast_mask
    )[0]

    if len(matching_indices) == 0:

        raise ValueError(
            f"No records found for "
            f"forecast hour "
            f"{requested_forecast_hour}."
        )

    # --------------------------------------------------------
    # Find closest valid time among those records
    # --------------------------------------------------------

    time_difference = np.abs(
        valid_times[matching_indices]
        -
        target_time
    )

    local_index = np.argmin(
        time_difference
    )

    time_index = matching_indices[
        local_index
    ]

    # --------------------------------------------------------
    # Selected values
    # --------------------------------------------------------

    selected_time = (
        valid_times[time_index]
    )

    selected_init_time = (
        init_times[time_index]
    )

    selected_forecast_hour = (
        forecast_hours[time_index]
    )

    # --------------------------------------------------------
    # Print selection
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("TIME SELECTION")
    print("=" * 80)

    print(
        f"Requested valid time : "
        f"{format_time(target_time)}"
    )

    print(
        f"Requested forecast   : "
        f"{requested_forecast_hour}"
    )

    print(
        f"Selected init time   : "
        f"{format_time(selected_init_time)}"
    )

    print(
        f"Selected valid time  : "
        f"{format_time(selected_time)}"
    )

    print(
        f"Selected forecast    : "
        f"{selected_forecast_hour}"
    )

    print(
        f"Dataset time index   : "
        f"{time_index}"
    )

    # --------------------------------------------------------
    # Verify init + forecast = valid
    # --------------------------------------------------------

    forecast_hours_number = int(
        selected_forecast_hour.replace(
            "h",
            ""
        )
    )

    expected_valid_time = (
        selected_init_time
        +
        np.timedelta64(
            forecast_hours_number,
            "h"
        )
    )

    print(
        f"Expected valid time  : "
        f"{format_time(expected_valid_time)}"
    )

    if selected_time == expected_valid_time:

        print(
            "✓ PASS: init_time + forecast_hour "
            "matches valid_time"
        )

    else:

        print(
            "WARNING: init_time + forecast_hour "
            "does not match valid_time."
        )

        print(
            f"Difference: "
            f"{selected_time - expected_valid_time}"
        )

    print("=" * 80)

    return (
        time_index,
        selected_time,
        selected_init_time
    )


# ============================================================
# STATION SELECTION
# ============================================================

def select_stations(
    ds,
    station_order=None
):
    """Select station names and their indices."""

    dataset_stations = np.asarray(
        ds["station"].values
    ).astype(str)

    if station_order is None:

        stations = (
            dataset_stations.copy()
        )

    else:

        stations = np.asarray(
            station_order
        ).astype(str)

        missing = [
            station
            for station in stations
            if station not in dataset_stations
        ]

        if missing:

            raise ValueError(
                f"Stations not present "
                f"in Dataset: {missing}"
            )

        if len(stations) != len(
            dataset_stations
        ):

            raise ValueError(
                "station_order must contain "
                "all stations."
            )

    station_indices = np.array([
        np.where(
            dataset_stations == station
        )[0][0]
        for station in stations
    ])

    return (
        stations,
        station_indices
    )


# ============================================================
# DATA EXTRACTION
# ============================================================

def get_cross_section_data(
    ds,
    time_index,
    station_indices
):
    """
    Extract and calculate meteorological cross-section variables.

    Handles two dataset structures:

    DS1 / DS2
    ----------
    p:
        (p,)

    meteorological variables:
        (station, valid_time, p)

    DS3
    ----------
    p:
        (station, valid_time, height)

    meteorological variables:
        (station, valid_time, height)
    """

    # =========================================================
    # Determine vertical dimension
    # =========================================================

    if "height" in ds["ta"].dims:

        vertical_dim = "height"

    elif "p" in ds["ta"].dims:

        vertical_dim = "p"

    else:

        raise ValueError(
            "Could not determine vertical dimension "
            "from temperature variable."
        )

    # =========================================================
    # PRESSURE
    # =========================================================

    if vertical_dim == "p":

        # -----------------------------------------------------
        # DS1 / DS2
        #
        # Pressure is a common 1-D coordinate.
        #
        # p.shape = (levels,)
        # -----------------------------------------------------

        pressure = np.asarray(
            ds["p"].values,
            dtype=float
        )

    else:

        # -----------------------------------------------------
        # DS3
        #
        # Pressure varies by station and valid time.
        #
        # p.shape =
        # (station, valid_time, height)
        #
        # Select the requested time and stations.
        # -----------------------------------------------------

        pressure = ds["p"].isel(
            valid_time=time_index,
            station=station_indices
        ).values

        pressure = np.asarray(
            pressure,
            dtype=float
        )

    # =========================================================
    # TEMPERATURE
    # =========================================================

    ta = ds["ta"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    ta = np.asarray(
        ta,
        dtype=float
    )

    # =========================================================
    # SPECIFIC HUMIDITY
    # =========================================================

    q = ds["q"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    q = np.asarray(
        q,
        dtype=float
    )

    # =========================================================
    # U WIND
    # =========================================================

    u = ds["u"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    u = np.asarray(
        u,
        dtype=float
    )

    # =========================================================
    # V WIND
    # =========================================================

    v = ds["v"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    v = np.asarray(
        v,
        dtype=float
    )

    # =========================================================
    # RELATIVE HUMIDITY
    # =========================================================

    r = ds["r"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    r = np.asarray(
        r,
        dtype=float
    )


    # =========================================================
    # POTENTIAL TEMPERATURE
    # =========================================================

    theta = ds["theta"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    theta = np.asarray(
        theta,
        dtype=float
    )


    # =========================================================
    # WET-BULB POTENTIAL TEMPERATURE
    # =========================================================

    theta_w = ds["theta_w"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    theta_w = np.asarray(
        theta_w,
        dtype=float
    )

    # =========================================================
    # Print diagnostic shapes
    # =========================================================

    print()
    print("CROSS-SECTION DATA SHAPES")
    print("-" * 70)

    print(
        "Vertical dimension:",
        vertical_dim
    )

    print(
        "Pressure:       ",
        pressure.shape
    )

    print(
        "Temperature:    ",
        ta.shape
    )

    print(
        "Specific humid: ",
        q.shape
    )

    print(
        "U wind:         ",
        u.shape
    )

    print(
        "V wind:         ",
        v.shape
    )

    print(
        "Relative humid: ",
        r.shape
    )

    print(
        "Theta:          ",
        theta.shape
    )

    print(
        "Theta_w:        ",
        theta_w.shape
    )

    # =========================================================
    # Handle pressure shape
    # =========================================================

    if vertical_dim == "p":

        # -----------------------------------------------------
        # DS1 / DS2
        #
        # pressure:
        #     (levels,)
        #
        # meteorological fields:
        #     (station, levels)
        # -----------------------------------------------------

        if pressure.ndim != 1:

            raise ValueError(
                "For pressure-level datasets, pressure "
                "must be 1-dimensional. "
                f"Got {pressure.shape}"
            )

        if ta.shape[1] != len(
            pressure
        ):

            raise ValueError(
                "Temperature vertical dimension does not "
                "match pressure dimension.\n"
                f"Temperature: {ta.shape}\n"
                f"Pressure: {pressure.shape}"
            )

        # -----------------------------------------------------
        # Pressure for dewpoint needs to be broadcast across
        # stations.
        # -----------------------------------------------------

        pressure_for_calculation = (
            pressure[None, :]
        )

    else:

        # -----------------------------------------------------
        # DS3
        #
        # pressure:
        #     (station, height)
        #
        # fields:
        #     (station, height)
        # -----------------------------------------------------

        if pressure.ndim != 2:

            raise ValueError(
                "For height-based datasets, pressure "
                "must be 2-dimensional. "
                f"Got {pressure.shape}"
            )

        if pressure.shape != ta.shape:

            raise ValueError(
                "Pressure and temperature shapes "
                "do not match.\n"
                f"Pressure: {pressure.shape}\n"
                f"Temperature: {ta.shape}"
            )

        pressure_for_calculation = (
            pressure
        )

    # =========================================================
    # Check all meteorological variables
    # =========================================================

    if ta.shape != q.shape:

        raise ValueError(
            "Temperature and humidity shapes do not match:\n"
            f"ta={ta.shape}\n"
            f"q={q.shape}"
        )

    if ta.shape != u.shape:

        raise ValueError(
            "Temperature and U-wind shapes do not match:\n"
            f"ta={ta.shape}\n"
            f"u={u.shape}"
        )

    if ta.shape != v.shape:

        raise ValueError(
            "Temperature and V-wind shapes do not match:\n"
            f"ta={ta.shape}\n"
            f"v={v.shape}"
        )

    # =========================================================
    # TEMPERATURE
    # =========================================================

    temperature = (
        ta - 273.15
    )

    # =========================================================
    # DEWPOINT
    # =========================================================

    dewpoint = (
        dewpoint_from_specific_humidity(
            pressure_for_calculation
            * units.hPa,

            ta * units.kelvin,

            q * units("kg/kg")
        )
    )

    dewpoint = dewpoint.to(
        "degC"
    ).magnitude

    # =========================================================
    # RETURN
    # =========================================================

    return {
        "pressure": pressure,
        "temperature": temperature,
        "dewpoint": dewpoint,

        "relative_humidity": r,
        "theta": theta,
        "theta_w": theta_w,

        "u": u,
        "v": v,
    }



# ============================================================
# INTERPOLATION
# ============================================================

def interpolate_cross_section(
    values,
    x_station,
    x
):
    """Interpolate station data onto a regular x grid."""

    interpolated = np.empty(
        (
            len(x),
            values.shape[1]
        )
    )

    for j in range(
        values.shape[1]
    ):

        interpolated[:, j] = (
            np.interp(
                x,
                x_station,
                values[:, j]
            )
        )

    return interpolated


def prepare_interpolated_data(
    data,
    nstation
):
    """
    Create x coordinates and interpolate cross-section fields.

    Pressure can be either:

        (height,)

    or:

        (station, height)
    """

    # --------------------------------------------------------
    # Station coordinates
    # --------------------------------------------------------

    x_station = np.arange(
        nstation,
        dtype=float
    )

    x_min = -0.5
    x_max = nstation - 0.5

    x = np.linspace(
        x_min,
        x_max,
        400
    )

    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    temperature_x = (
        interpolate_cross_section(
            data["temperature"],
            x_station,
            x
        )
    )

    # --------------------------------------------------------
    # Dewpoint
    # --------------------------------------------------------

    dewpoint_x = (
        interpolate_cross_section(
            data["dewpoint"],
            x_station,
            x
        )
    )

    relative_humidity_x = interpolate_cross_section(
        data["relative_humidity"],
        x_station,
        x
    )

    theta_x = interpolate_cross_section(
        data["theta"],
        x_station,
        x
    )

    theta_w_x = interpolate_cross_section(
        data["theta_w"],
        x_station,
        x
    )
    # --------------------------------------------------------
    # Pressure
    # --------------------------------------------------------

    pressure = np.asarray(
        data["pressure"],
        dtype=float
    )

    if pressure.ndim == 1:

        # Common pressure levels
        # at every station.

        pressure_station = np.tile(
            pressure,
            (nstation, 1)
        )

    elif pressure.ndim == 2:

        # Pressure varies by station.

        pressure_station = pressure

    else:

        raise ValueError(
            "Pressure must have either "
            "1 or 2 dimensions. "
            f"Got {pressure.shape}"
        )

    # --------------------------------------------------------
    # Interpolate pressure horizontally
    # --------------------------------------------------------

    pressure_x = (
        interpolate_cross_section(
            pressure_station,
            x_station,
            x
        )
    )

    # --------------------------------------------------------
    # Create plotting grids
    # --------------------------------------------------------

    X = np.tile(
        x[:, None],
        (
            1,
            pressure_x.shape[1]
        )
    )

    P = pressure_x

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {
        **data,

        "x": x,
        "x_station": x_station,

        "x_min": x_min,
        "x_max": x_max,

        "X": X,
        "P": P,

        "pressure_x": pressure_x,

        "temperature_x": temperature_x,
        "dewpoint_x": dewpoint_x,

        "relative_humidity_x": relative_humidity_x,
        "theta_x": theta_x,
        "theta_w_x": theta_w_x,
    }


# ============================================================
# CONTOUR LEVELS
# ============================================================

def get_contour_levels(
    values,
    interval=5
):
    """Calculate contour levels for a field."""

    vmin = (
        np.floor(
            np.nanmin(values)
            /
            interval
        )
        *
        interval
    )

    vmax = (
        np.ceil(
            np.nanmax(values)
            /
            interval
        )
        *
        interval
    )

    return np.arange(
        vmin,
        vmax + interval,
        interval
    )


# ============================================================
# TEMPERATURE
# ============================================================

def plot_temperature(
    ax,
    data,
    temperature_levels
):
    """
    Plot temperature-filled contours and
    temperature contour lines.

    The same temperature levels are used
    for every subplot.
    """

    # --------------------------------------------------------
    # Filled contours
    # --------------------------------------------------------

    cf = ax.contourf(
        data["X"],
        data["P"],
        data["temperature_x"],
        levels=temperature_levels,
        cmap="RdBu_r",
        extend="both",
        alpha=0.55
    )

    # --------------------------------------------------------
    # Temperature lines
    # --------------------------------------------------------

    temp_cs = ax.contour(
        data["X"],
        data["P"],
        data["temperature_x"],
        levels=temperature_levels,
        colors="black",
        linewidths=0.8
    )

    ax.clabel(
        temp_cs,
        inline=True,
        fontsize=8,
        fmt="%d°C"
    )

    return cf


# ============================================================
# DEWPOINT
# ============================================================

def plot_dewpoint(
    ax,
    data
):
    """Plot dewpoint contours."""

    dewpoint_levels = (
        get_contour_levels(
            data["dewpoint_x"]
        )
    )

    td_cs = ax.contour(
        data["X"],
        data["P"],
        data["dewpoint_x"],
        levels=dewpoint_levels,
        colors="limegreen",
        linewidths=1.5
    )

    ax.clabel(
        td_cs,
        inline=True,
        fontsize=8,
        fmt="%d°C"
    )


# ============================================================
# WIND BARBS
# ============================================================

def plot_wind_barbs(
    ax,
    data
):
    """
    Plot wind barbs at selected pressure levels.

    Handles both:

        pressure = (height,)

    and:

        pressure = (station, height)

    For station-dependent pressure, the closest
    pressure level is found independently for
    each station.
    """

    requested_pressure = np.array([
        1000,
        925,
        850,
        700,
        500,
        300,
        200,
    ])

    pressure = np.asarray(
        data["pressure"],
        dtype=float
    )

    u = np.asarray(
        data["u"],
        dtype=float
    )

    v = np.asarray(
        data["v"],
        dtype=float
    )

    x_station = data["x_station"]

    nstation = len(
        x_station
    )

    # --------------------------------------------------------
    # Storage
    # --------------------------------------------------------

    barb_x = []
    barb_y = []
    barb_u = []
    barb_v = []

    # ========================================================
    # Common pressure levels
    # ========================================================

    if pressure.ndim == 1:

        for level in requested_pressure:

            pressure_index = np.argmin(
                np.abs(
                    pressure - level
                )
            )

            actual_pressure = (
                pressure[
                    pressure_index
                ]
            )

            for station_index in range(
                nstation
            ):

                barb_x.append(
                    x_station[
                        station_index
                    ]
                )

                barb_y.append(
                    actual_pressure
                )

                barb_u.append(
                    u[
                        station_index,
                        pressure_index
                    ]
                )

                barb_v.append(
                    v[
                        station_index,
                        pressure_index
                    ]
                )

    # ========================================================
    # Station-dependent pressure
    # ========================================================

    elif pressure.ndim == 2:

        for station_index in range(
            nstation
        ):

            station_pressure = (
                pressure[
                    station_index,
                    :
                ]
            )

            for level in requested_pressure:

                pressure_index = np.argmin(
                    np.abs(
                        station_pressure
                        -
                        level
                    )
                )

                actual_pressure = (
                    station_pressure[
                        pressure_index
                    ]
                )

                barb_x.append(
                    x_station[
                        station_index
                    ]
                )

                barb_y.append(
                    actual_pressure
                )

                barb_u.append(
                    u[
                        station_index,
                        pressure_index
                    ]
                )

                barb_v.append(
                    v[
                        station_index,
                        pressure_index
                    ]
                )

    else:

        raise ValueError(
            "Pressure must have 1 or 2 dimensions. "
            f"Got {pressure.shape}"
        )

    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    ax.barbs(
        np.asarray(barb_x),
        np.asarray(barb_y),
        np.asarray(barb_u),
        np.asarray(barb_v),
        length=7,
        linewidth=1.2,
        color="black"
    )


# ============================================================
# AXIS FORMATTING
# ============================================================

def format_axes(
    ax,
    stations,
    x_station,
    x_min,
    x_max
):
    """Configure pressure and station axes."""

    pressure_ticks = [
        1000,
        925,
        850,
        700,
        500,
        300,
        200,
    ]

    # --------------------------------------------------------
    # Pressure axis
    # --------------------------------------------------------

    ax.set_yscale(
        "log"
    )

    ax.set_ylim(
        1000,
        200
    )

    ax.yaxis.set_major_locator(
        FixedLocator(
            pressure_ticks
        )
    )

    ax.yaxis.set_major_formatter(
        FixedFormatter([
            "1000",
            "925",
            "850",
            "700",
            "500",
            "300",
            "200",
        ])
    )

    ax.yaxis.set_minor_formatter(
        NullFormatter()
    )

    # --------------------------------------------------------
    # X axis
    # --------------------------------------------------------

    ax.set_xlim(
        x_min,
        x_max
    )

    ax.set_xticks(
        x_station
    )

    ax.set_xticklabels(
        stations,
        rotation=45,
        ha="right"
    )

    # --------------------------------------------------------
    # Station lines
    # --------------------------------------------------------

    for xpos in x_station:

        ax.axvline(
            xpos,
            color="gray",
            linewidth=0.6,
            linestyle=":",
            alpha=0.4
        )

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    ax.set_xlabel(
        "Station"
    )

    ax.set_ylabel(
        "Pressure (hPa)"
    )

    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    ax.grid(
        True,
        which="major",
        linestyle="--",
        alpha=0.25
    )


# ============================================================
# LEGEND
# ============================================================

def add_legend(
    ax
):
    """Add temperature/dewpoint legend."""

    legend_lines = [
        Line2D(
            [0],
            [0],
            color="black",
            linewidth=1.0,
            label="Temperature (°C)"
        ),

        Line2D(
            [0],
            [0],
            color="limegreen",
            linewidth=1.5,
            label="Dewpoint (°C)"
        ),
    ]

    ax.legend(
        handles=legend_lines,
        loc="upper right"
    )


# ============================================================
# MAIN PLOTTING FUNCTION
# ============================================================

def plot_cross_section(
    ds1,
    ds2,
    ds3,
    time,
    forecast_hour,
    station_order=None,
    title=None,
    subplot_titles=None,
    figsize=(15, 18)
):
    """
    Plot three atmospheric cross sections as subplots.

    Parameters
    ----------
    ds1, ds2, ds3 : xarray.Dataset
        Three datasets to plot.

    time : str
        Requested valid time.

        Example:
            "2029-09-29-00z"

    forecast_hour : str or int
        Forecast hour to select.

        Examples:
            "12h"
            "24h"
            "48h"

    station_order : list, optional
        Station order.

    title : str, optional
        Overall figure title.

    subplot_titles : list, optional
        Title corresponding to each dataset.

    figsize : tuple, optional
        Figure size.

    Returns
    -------
    fig
        Matplotlib figure.
    """

    # ========================================================
    # Datasets
    # ========================================================

    datasets = [
        ds1,
        ds2,
        ds3
    ]

    # ========================================================
    # Subplot titles
    # ========================================================

    if subplot_titles is None:

        subplot_titles = [
            "Dataset 1",
            "Dataset 2",
            "Dataset 3"
        ]

    if len(
        subplot_titles
    ) != 3:

        raise ValueError(
            "subplot_titles must contain "
            "exactly three titles."
        )

    # ========================================================
    # Create figure
    # ========================================================

    fig, axes = plt.subplots(
        3,
        1,
        figsize=figsize,
        sharey=True
    )

    # ========================================================
    # Process datasets
    # ========================================================

    all_data = []

    selected_times = []
    init_times = []

    for ds in datasets:

        # ----------------------------------------------------
        # Select time
        # ----------------------------------------------------

        (
            time_index,
            selected_time,
            init_time
        ) = select_time(
            ds,
            time,
            forecast_hour
        )

        selected_times.append(
            selected_time
        )

        init_times.append(
            init_time
        )

        # ----------------------------------------------------
        # Select stations
        # ----------------------------------------------------

        (
            stations,
            station_indices
        ) = select_stations(
            ds,
            station_order
        )

        # ----------------------------------------------------
        # Extract data
        # ----------------------------------------------------

        data = get_cross_section_data(
            ds,
            time_index,
            station_indices
        )

        # ----------------------------------------------------
        # Interpolate
        # ----------------------------------------------------

        data = prepare_interpolated_data(
            data,
            len(stations)
        )

        # Store stations
        data["stations"] = stations

        all_data.append(
            data
        )

    # ========================================================
    # Common temperature levels
    #
    # All three datasets use exactly the same temperature
    # color scale.
    # ========================================================

    all_temperature_values = np.concatenate([
        data[
            "temperature_x"
        ].ravel()
        for data in all_data
    ])

    temperature_levels = (
        get_contour_levels(
            all_temperature_values
        )
    )

    # ========================================================
    # Plot each dataset
    # ========================================================

    contourf_objects = []

    for i, (
        ax,
        data
    ) in enumerate(
        zip(
            axes,
            all_data
        )
    ):

        # ----------------------------------------------------
        # Temperature
        # ----------------------------------------------------

        cf = plot_temperature(
            ax,
            data,
            temperature_levels
        )

        contourf_objects.append(
            cf
        )

        # ----------------------------------------------------
        # Dewpoint
        # ----------------------------------------------------

        plot_dewpoint(
            ax,
            data
        )

        # ----------------------------------------------------
        # Relative humidity
        # ----------------------------------------------------

        plot_relative_humidity(
            ax,
            data
        )

        # ----------------------------------------------------
        # Potential temperature
        # ----------------------------------------------------

        plot_theta(
            ax,
            data
        )

        # ----------------------------------------------------
        # Wet-bulb potential temperature
        # ----------------------------------------------------

        plot_theta_w(
            ax,
            data
        )

        # ----------------------------------------------------
        # Wind barbs
        # ----------------------------------------------------

        plot_wind_barbs(
            ax,
            data
        )

        # ----------------------------------------------------
        # Axis formatting
        # ----------------------------------------------------

        format_axes(
            ax,
            data["stations"],
            data["x_station"],
            data["x_min"],
            data["x_max"]
        )

        # ----------------------------------------------------
        # Time strings
        # ----------------------------------------------------

        init_time_string = format_time(
            init_times[i]
        )

        selected_time_string = format_time(
            selected_times[i]
        )

        forecast_hour_string = normalize_forecast_hour(
            forecast_hour
        )

        # ----------------------------------------------------
        # Dataset-specific title
        # ----------------------------------------------------

        ax.set_title(
            f"{subplot_titles[i]}\n"
            f"Init: {init_time_string} | "
            f"Forecast: {forecast_hour_string} | "
            f"Valid: {selected_time_string}"
        )

        # ----------------------------------------------------
        # Legend
        # ----------------------------------------------------

        add_legend(
            ax
        )

    # ========================================================
    # Shared colorbar
    # ========================================================

    cbar = fig.colorbar(
        contourf_objects[0],
        ax=axes,
        orientation="vertical",
        pad=0.02,
        fraction=0.025
    )

    cbar.set_label(
        "Temperature (°C)"
    )

    # ========================================================
    # Overall title
    # ========================================================

    if title is not None:

        fig.suptitle(
            title,
            fontsize=16,
            y=0.995
        )

    # ========================================================
    # Layout
    # ========================================================

    plt.tight_layout(
        rect=(
            0,
            0,
            1,
            0.98
        )
    )

    return fig

