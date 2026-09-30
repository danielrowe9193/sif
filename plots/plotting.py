# single plot
import numpy as np
import matplotlib.pyplot as plt

from metpy.units import units
from metpy.calc import dewpoint_from_specific_humidity
from matplotlib.ticker import NullFormatter, FixedLocator, FixedFormatter
from matplotlib.lines import Line2D

def parse_time(time):
    """
    Convert YYYY-MM-DD-HHz directly to numpy.datetime64.
    """

    time_clean = str(time).lower().replace("z", "")

    date_part, hour_part = time_clean.rsplit("-", 1)

    return np.datetime64(
        f"{date_part}T{hour_part}:00"
    )

def format_time(time):
    """
    Format datetime as YYYY-MM-DD-HHz.
    """

    time_string = str(time)
    if "." in time_string:
        time_string = time_string.split(".")[0]
    date_part, hour_part = time_string.split("T")

    hour = hour_part[:2]

    return f"{date_part}-{hour}z"


def normalize_forecast_hour(forecast_hour):
    if isinstance(forecast_hour, str):

        forecast_hour = (
            forecast_hour
            .strip()
            .lower()
        )

        if not forecast_hour.endswith("h"):
            forecast_hour += "h"

    else:
        forecast_hour = f"{forecast_hour}h"

    return forecast_hour


def select_time(ds,
    time,
    forecast_hour
):
    """
    Select the valid time closest to the requested time,
    restricted to the selected forecast hour.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing:
            valid_time
            forecast_hour
            init_time

    time : str
        Requested valid time.
        Format:
            YYYY-MM-DD-HHz

    forecast_hour : str or int
        Forecast hour.
    Returns
    -------
    time_index : int
        Index corresponding to the selected valid time.

    selected_time : numpy.datetime64
        Selected valid time.

    init_time : numpy.datetime64
        Corresponding initialization time.
    """

    target_time = parse_time(time)
    selected_forecast_hour = normalize_forecast_hour(
        forecast_hour
    )
    valid_times = np.asarray(
        ds["valid_time"].values
    )

    forecast_hours = np.asarray(
        ds["forecast_hour"].values
    ).astype(str)

    # Normalize dataset forecast-hour values
    forecast_hours = np.array([
        fh if fh.lower().endswith("h")
        else f"{fh}h"
        for fh in forecast_hours
    ])

    if "init_time" not in ds.coords:
        raise ValueError(
            "Dataset does not contain an 'init_time' coordinate."
        )

    init_times = np.asarray(
        ds["init_time"].values
    )

    forecast_mask = (
        forecast_hours == selected_forecast_hour
    )

    if not np.any(forecast_mask):

        available_hours = np.unique(
            forecast_hours
        )

        raise ValueError(
            f"Forecast hour "
            f"'{selected_forecast_hour}' "
            f"not found in Dataset.\n"
            f"Available forecast hours: "
            f"{available_hours}"
        )

    available_times = valid_times[
        forecast_mask
    ]

    local_index = np.argmin(
        np.abs(
            available_times - target_time
        )
    )

    selected_time = available_times[
        local_index
    ]

    original_indices = np.where(
        forecast_mask
    )[0]

    time_index = original_indices[
        local_index
    ]

    init_time = init_times[
        time_index
    ]

    print("TIME SELECTION")
    print("-" * 70)
    print(
        f"Requested time:     "
        f"{format_time(target_time)}"
    )
    print(
        f"Forecast hour:      "
        f"{selected_forecast_hour}"
    )
    print(
        f"Selected valid time:"
        f" {format_time(selected_time)}"
    )
    print(
        f"Initialization time:"
        f" {format_time(init_time)}"
    )
    print(
        f"Dataset time index:  "
        f"{time_index}"
    )

    return (
        time_index,
        selected_time,
        init_time
    )


def select_stations(
    ds,
    station_order=None
):
    """
    Select station names and their indices.
    """

    dataset_stations = np.asarray(
        ds["station"].values
    ).astype(str)

    # default station order
    if station_order is None:
        stations = dataset_stations.copy()
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
                f"Stations not present in Dataset: "
                f"{missing}"
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

# changes for icon made here
def get_cross_section_data(ds, time_index, station_indices):
    """Extract and calculate meteorological cross-section variables."""
    pressure = ds["p"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    pressure = np.asarray(
        pressure,
        dtype=float
    )

    ta = ds["ta"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    ta = np.asarray(
        ta,
        dtype=float
    )

    q = ds["q"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    q = np.asarray(
        q,
        dtype=float
    )

    u = ds["u"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    u = np.asarray(
        u,
        dtype=float
    )

    v = ds["v"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    v = np.asarray(
        v,
        dtype=float
    )

    print("CROSS-SECTION DATA SHAPES")
    print("-" * 70)
    print("Pressure:       ", pressure.shape)
    print("Temperature:    ", ta.shape)
    print("Specific humidity: ", q.shape)
    print("U wind:         ", u.shape)
    print("V wind:         ", v.shape)

    if not (
        pressure.shape ==
        ta.shape ==
        q.shape ==
        u.shape ==
        v.shape
    ):
        raise ValueError(
            "Pressure, temperature, humidity, and wind "
            "must all have the same shape. "
            f"Got: p={pressure.shape}, "
            f"ta={ta.shape}, "
            f"q={q.shape}, "
            f"u={u.shape}, "
            f"v={v.shape}"
        )

    temperature = ta - 273.15

    dewpoint = dewpoint_from_specific_humidity(
        pressure * units.hPa,
        ta * units.kelvin,
        q * units("kg/kg")
    )

    dewpoint = dewpoint.to("degC").magnitude

    return {
        "pressure": pressure,
        "temperature": temperature,
        "dewpoint": dewpoint,
        "u": u,
        "v": v,
    }


def interpolate_cross_section(values, x_station, x):
    """
    Interpolate station data onto a regular x grid.
    """

    interpolated = np.empty(
        (
            len(x),
            values.shape[1]
        )
    )

    for j in range(
        values.shape[1]
    ):

        interpolated[:, j] = np.interp(
            x,
            x_station,
            values[:, j]
        )

    return interpolated

# change for icon
def prepare_interpolated_data(data, nstation):
    """Create x coordinates and interpolate cross-section fields."""

    x_station = np.arange(
        nstation,
        dtype=float
    )

    x_min = -0.5
    x_max = nstation - 0.5

    x = np.linspace(x_min, x_max, 400)

    temperature_x = interpolate_cross_section(data["temperature"], x_station, x)

    dewpoint_x = interpolate_cross_section(data["dewpoint"], x_station, x)

    pressure = np.asarray(data["pressure"])

    if pressure.ndim == 1:

        # Same pressure levels at every station
        P_station = np.tile(
            pressure,
            (nstation, 1)
        )

    elif pressure.ndim == 2:

        # Pressure varies by station
        P_station = pressure

    else:

        raise ValueError(
            "Pressure must have either 1 or 2 dimensions. "
            f"Got shape {pressure.shape}"
        )

    pressure_x = interpolate_cross_section(
        P_station,
        x_station,
        x
    )

    X = np.tile(
        x[:, None],
        (1, pressure_x.shape[1])
    )

    P = pressure_x

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
    }


def get_contour_levels(values, interval=5):
    """
    Calculate contour levels for a field.
    """

    vmin = np.floor(
        np.nanmin(values) / interval
    ) * interval

    vmax = np.ceil(
        np.nanmax(values) / interval
    ) * interval

    return np.arange(
        vmin,
        vmax + interval,
        interval
    )


def plot_temperature(ax, data):
    """
    Plot temperature-filled contours
    and temperature lines.
    """
    temperature_levels = get_contour_levels(
        data["temperature_x"]
    )

    cf = ax.contourf(
        data["X"],
        data["P"],
        data["temperature_x"],
        levels=temperature_levels,
        cmap="RdBu_r",
        extend="both",
        alpha=0.75 # change this for saturation
    )

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


def plot_dewpoint(ax, data):
    """
    Plot dewpoint contours.
    """

    dewpoint_levels = get_contour_levels(data["dewpoint_x"])

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

# change here for icon
def plot_wind_barbs(ax, data,):
    """Plot wind barbs at selected pressure levels.
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

    nstation = len(x_station)

    if pressure.ndim == 1:

        barb_x = []
        barb_y = []
        barb_u = []
        barb_v = []

        for level in requested_pressure:

            # Find nearest pressure level
            pressure_index = np.argmin(np.abs(pressure - level))

            actual_pressure = pressure[pressure_index]

            for station_index in range(nstation):

                barb_x.append(x_station[station_index])
                barb_y.append(actual_pressure)

                barb_u.append(u[station_index, pressure_index])
                barb_v.append(v[station_index, pressure_index])

    elif pressure.ndim == 2:

        barb_x = []
        barb_y = []
        barb_u = []
        barb_v = []

        for station_index in range(nstation):

            station_pressure = pressure[station_index, : ]

            for level in requested_pressure:
                pressure_index = np.argmin(np.abs(station_pressure - level))
                actual_pressure = (station_pressure[pressure_index])

                barb_x.append(x_station[station_index])
                barb_y.append(actual_pressure)

                barb_u.append(u[station_index, pressure_index])
                barb_v.append(v[station_index, pressure_index])

    else:
        raise ValueError(
            "Pressure must have 1 or 2 dimensions. "
            f"Got shape {pressure.shape}"
        )

    ax.barbs(
        np.asarray(barb_x),
        np.asarray(barb_y),
        np.asarray(barb_u),
        np.asarray(barb_v),
        length=7,
        linewidth=1.2,
        color="black"
    )


def format_axes(ax, stations, x_station, x_min, x_max):
    """
    Configure pressure and station axes.
    """

    pressure_ticks = [
        1000,
        925,
        850,
        700,
        500,
        300,
        200,
    ]

    ax.set_yscale("log")
    ax.set_ylim(1000, 200)

    ax.yaxis.set_major_locator(FixedLocator(pressure_ticks))
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

    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(x_min, x_max)
    ax.set_xticks(x_station)

    ax.set_xticklabels(
        stations,
        rotation=45,
        ha="right"
    )

    for xpos in x_station:

        ax.axvline(
            xpos,
            color="gray",
            linewidth=0.6,
            linestyle=":",
            alpha=0.4
        )

    ax.set_xlabel("Station")
    ax.set_ylabel("Pressure (hPa)")
    ax.grid(
        True,
        which="major",
        linestyle="--",
        alpha=0.25
    )


def add_legend(ax):
    """
    Add temperature/dewpoint legend.
    """

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

# main plotting function
def plot_cross_section(ds, time, forecast_hour, station_order=None, title=None):
    """
    Plot atmospheric cross section.
    """

    ( time_index, selected_time, init_time) = select_time(ds, time, forecast_hour)
    (stations, station_indices) = select_stations(ds, station_order)

    data = get_cross_section_data(ds, time_index, station_indices)
    data = prepare_interpolated_data(data, len(stations))

    fig, ax = plt.subplots(figsize=(15, 9))

    cf = plot_temperature(ax, data)

    plot_dewpoint(ax, data)
    plot_wind_barbs(ax, data)

    format_axes(
        ax,
        stations,
        data["x_station"],
        data["x_min"],
        data["x_max"]
    )

    init_time_string = format_time(init_time)
    selected_time_string = format_time(selected_time)
    forecast_hour_string = (normalize_forecast_hour(forecast_hour))

    if title is None:
        title = "Atmospheric Cross Section"

    else:
        title = (
            f"{title} "
            f"Atmospheric Cross Section"
        )

    ax.set_title(
        f"{title}\n"
        f"Init: {init_time_string} | "
        f"Forecast: {forecast_hour_string} | "
        f"Valid: {selected_time_string}"
    )

    cbar = fig.colorbar(
        cf,
        ax=ax,
        pad=0.02
    )

    cbar.set_label("Temperature (°C)")
    add_legend(ax)

    plt.tight_layout()

    return fig

# function to verify dataset
def verify_forecast_selection(
    ds,
    time,
    forecast_hour
):
    """
    Verify the exact initialization time, forecast hour,
    valid time, and dataset index selected for plotting.
    """

    target_time = parse_time(time)

    selected_forecast_hour = normalize_forecast_hour(
        forecast_hour
    )

    valid_times = np.asarray(
        ds["valid_time"].values
    )

    forecast_hours = np.asarray(
        ds["forecast_hour"].values
    ).astype(str)

    init_times = np.asarray(
        ds["init_time"].values
    )

    # Normalize forecast-hour strings
    forecast_hours = np.array([
        fh if fh.lower().endswith("h")
        else f"{fh}h"
        for fh in forecast_hours
    ])

    # Find records for requested forecast hour
    mask = (
        forecast_hours ==
        selected_forecast_hour
    )

    indices = np.where(mask)[0]

    if len(indices) == 0:
        raise ValueError(
            f"No records found for "
            f"{selected_forecast_hour}"
        )

    # Find closest valid time
    local_index = np.argmin(
        np.abs(
            valid_times[indices] -
            target_time
        )
    )

    selected_index = indices[
        local_index
    ]

    # Get corresponding values
    selected_valid_time = (
        valid_times[selected_index]
    )

    selected_init_time = (
        init_times[selected_index]
    )

    selected_fh = (
        forecast_hours[selected_index]
    )

    print("=" * 80)
    print("FORECAST SELECTION VERIFICATION")
    print("=" * 80)

    print(
        f"Requested valid time : "
        f"{format_time(target_time)}"
    )

    print(
        f"Requested forecast   : "
        f"{selected_forecast_hour}"
    )

    print("-" * 80)

    print(
        f"Dataset index        : "
        f"{selected_index}"
    )

    print(
        f"Initialization time  : "
        f"{format_time(selected_init_time)}"
    )

    print(
        f"Forecast hour        : "
        f"{selected_fh}"
    )

    print(
        f"Valid time           : "
        f"{format_time(selected_valid_time)}"
    )

    print("-" * 80)

    # Calculate expected valid time
    forecast_number = int(
        selected_fh.replace("h", "")
    )

    expected_valid_time = (
        selected_init_time +
        np.timedelta64(
            forecast_number,
            "h"
        )
    )

    print(
        f"Expected valid time  : "
        f"{format_time(expected_valid_time)}"
    )

    print("=" * 80)

    if selected_valid_time == expected_valid_time:

        print(
            "✓ PASS: init_time + forecast_hour "
            "matches valid_time"
        )

    else:

        print(
            "✗ WARNING: init_time + forecast_hour "
            "does NOT match valid_time"
        )

        print(
            f"  Difference: "
            f"{selected_valid_time - expected_valid_time}"
        )

    print("=" * 80)

    return selected_index