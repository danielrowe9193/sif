import numpy as np
import matplotlib.pyplot as plt

from metpy.units import units
from metpy.calc import dewpoint_from_specific_humidity
from matplotlib.ticker import NullFormatter, FixedLocator, FixedFormatter
from matplotlib.lines import Line2D

def select_time(ds, time):
    """Return the index and actual valid time closest to the requested time."""
    target_time = np.datetime64(time)
    valid_times = np.asarray(ds["valid_time"].values)

    time_index = np.argmin(np.abs(valid_times - target_time))
    selected_time = valid_times[time_index]

    print()
    print("TIME")
    print("-" * 70)
    print("Requested:", target_time)
    print("Selected: ", selected_time)

    return time_index, selected_time


def select_stations(ds, station_order=None):
    """Selected station names and their indices."""
    dataset_stations = np.asarray(
        ds["station"].values
    ).astype(str)

    if station_order is None:
        stations = dataset_stations.copy()
    else:
        stations = np.asarray(station_order).astype(str)

        missing = [
            station
            for station in stations
            if station not in dataset_stations
        ]

        if missing:
            raise ValueError(
                f"Stations not present in Dataset: {missing}"
            )

        if len(stations) != len(dataset_stations):
            raise ValueError(
                "station_order must contain all stations."
            )

    station_indices = np.array([
        np.where(dataset_stations == station)[0][0]
        for station in stations
    ])

    return stations, station_indices


# def get_cross_section_data(ds, time_index, station_indices):
#     """Find and calculate meteorological cross-section variables."""
#     pressure = np.asarray(
#         ds["p"].values,
#         dtype=float
#     )

#     ta = ds["ta"].values[
#         time_index,
#         station_indices,
#         :
#     ]

#     q = ds["q"].values[
#         time_index,
#         station_indices,
#         :
#     ]

#     u = ds["u"].values[
#         time_index,
#         station_indices,
#         :
#     ]

#     v = ds["v"].values[
#         time_index,
#         station_indices,
#         :
#     ]

#     temperature = ta - 273.15 # change to celcius

#     dewpoint = dewpoint_from_specific_humidity(
#         pressure[None, :] * units.hPa,
#         ta * units.kelvin,
#         q * units("kg/kg")
#     )

#     dewpoint = dewpoint.to("degC").magnitude

#     return {
#         "pressure": pressure,
#         "temperature": temperature,
#         "dewpoint": dewpoint,
#         "u": u,
#         "v": v,
#     }

def get_cross_section_data(ds, time_index, station_indices):
    """Extract and calculate meteorological cross-section variables."""

    pressure = np.asarray(
        ds["p"].values,
        dtype=float
    )

    ta = ds["ta"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    q = ds["q"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    u = ds["u"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    v = ds["v"].isel(
        valid_time=time_index,
        station=station_indices
    ).values

    temperature = ta - 273.15

    dewpoint = dewpoint_from_specific_humidity(
        pressure[None, :] * units.hPa,
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



def interpolate_cross_section(values,x_station,x,):
    """Interpolate station data onto a regular x grid."""
    interpolated = np.empty(
        (len(x), values.shape[1])
    )

    for j in range(values.shape[1]):
        interpolated[:, j] = np.interp(
            x,
            x_station,
            values[:, j]
        )

    return interpolated


def prepare_interpolated_data(data, nstation):
    """Create x coordinates and interpolate cross-section fields."""
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

    temperature_x = interpolate_cross_section(
        data["temperature"],
        x_station,
        x
    )

    dewpoint_x = interpolate_cross_section(
        data["dewpoint"],
        x_station,
        x
    )

    X, P = np.meshgrid(
        x,
        data["pressure"],
        indexing="ij"
    )

    return {
        **data,
        "x": x,
        "x_station": x_station,
        "x_min": x_min,
        "x_max": x_max,
        "X": X,
        "P": P,
        "temperature_x": temperature_x,
        "dewpoint_x": dewpoint_x,
    }


def get_contour_levels(values, interval=5):
    """Calculate contour levels for field."""
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


def plot_temperature(ax,data,):
    """Plot temperature-filled contours and temperature lines."""
    temperature_levels = get_contour_levels(
        data["temperature_x"]
    )

    cf = ax.contourf(
        data["X"],
        data["P"],
        data["temperature_x"],
        levels=temperature_levels,
        cmap="RdBu_r",
        extend="both"
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
    """Plot dewpoint contours."""
    dewpoint_levels = get_contour_levels(
        data["dewpoint_x"]
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


def plot_wind_barbs(
    ax,
    data,
):
    """Plot wind barbs at selected pressure levels."""
    requested_pressure = np.array([
        1000,
        925,
        850,
        700,
        500,
        300,
        200,
    ])

    pressure = data["pressure"]

    valid_pressure = requested_pressure[
        np.isin(requested_pressure, pressure)
    ]

    barb_indices = np.array([
        np.where(pressure == level)[0][0]
        for level in valid_pressure
    ])

    x_station = data["x_station"]
    nstation = len(x_station)

    barb_x = np.repeat(
        x_station[:, None],
        len(barb_indices),
        axis=1
    )

    barb_y = np.tile(
        pressure[barb_indices],
        (nstation, 1)
    )

    barb_u = data["u"][:, barb_indices]
    barb_v = data["v"][:, barb_indices]

    ax.barbs(
        barb_x,
        barb_y,
        barb_u,
        barb_v,
        length=6,
        linewidth=1.0,
        color="black"
    )


def format_axes(
    ax,
    stations,
    x_station,
    x_min,
    x_max,
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

    ax.set_yscale("log")
    ax.set_ylim(1000, 200)

    ax.yaxis.set_major_locator(
        FixedLocator(pressure_ticks)
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


def plot_cross_section(ds, time, station_order=None, title=None):
    """
    Plot atmospheric cross section

    Parameters:
    ds : xarray.Dataset
    time : Requested valid time

    station_order : list, optional
    If None, the order stored in ds["station"] is used.
    """

    # choose data
    time_index, selected_time = select_time(ds, time)
    # choose station
    stations, station_indices = select_stations(ds, station_order)
    # get data
    data = get_cross_section_data(ds, time_index, station_indices)
    data = prepare_interpolated_data(data, len(stations))
    # plot
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

    ax.set_title(
        f"{title} Atmospheric Cross Section\n"
        f"Valid: {selected_time}"
    )

    cbar = fig.colorbar(
        cf,
        ax=ax,
        pad=0.02
    )

    cbar.set_label("Temperature (°C)")
    add_legend(ax)

    plt.tight_layout()
    plt.show()
