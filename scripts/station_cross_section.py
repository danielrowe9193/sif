import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import matplotlib.dates as mdates
import metpy.calc as mpcalc
import matplotlib.pyplot as plt
import xarray as xr

from datetime import datetime
from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter, NullLocator
from metpy.plots import SkewT
from metpy.units import units

sif = xr.open_dataset("../data/netcdf/sif.ptu_radiosondes.profiles.level2.nc")
igra = xr.open_dataset("../data/netcdf/sif.igra_radiosondes.profiles.level0.nc")
igra = igra.interpolate_na(dim="level")
print(igra.u_wind)

norderney12 = igra.sel(station="Norderney", time="2026-08-15T12")
schleswig12 = igra.sel(station="Schleswig", time="2026-08-15T12")
fehmarn12 = sif.sel(sounding_num=9)
greifswald12 = igra.sel(station="Greifswald", time="2026-08-15T12")

norderney12_2 = igra.sel(station="Norderney", time="2026-08-13T12")
schleswig12_2 = igra.sel(station="Schleswig", time="2026-08-13T12")
fehmarn12_2 = sif.sel(sounding_num=4)
greifswald12_2 = igra.sel(station="Greifswald", time="2026-08-13T12")


def monotonicity_checks(array: np.ndarray, name_of_var: str):
    """Checks if an array is monotonically increasing or decreasing."""
    is_increasing = np.all(np.diff(array) >= 0)
    is_strictly_increasing = np.all(np.diff(array) > 0)
    is_decreasing = np.all(np.diff(array) <= 0)
    is_strictly_decreasing = np.all(np.diff(array) < 0)

    print(
        f"{name_of_var} is_increasing: {is_increasing}\n"
        f"{name_of_var} is_strictly_increasing: {is_strictly_increasing}\n"
        f"{name_of_var} is_decreasing: {is_decreasing}\n"
        f"{name_of_var} is_strictly_decreasing: {is_strictly_decreasing}\n"
    )


def make_profile(igra_station_data: xr.Dataset, station_id: str) -> xr.Dataset:
    """
    Ingests igra dataset for a station, extracts key variables, and creates a new dataset indexed by pressure and interpolated onto a pressure grid.
    :param igra_station_data:
    :return:
    """

    pressure = igra_station_data.pressure.values
    pressure = pressure[~np.isnan(pressure)]

    temperature = igra_station_data.temperature.values[0 : len(pressure)]
    uwind = igra_station_data.u_wind.values[0 : len(pressure)]
    vwind = igra_station_data.v_wind.values[0 : len(pressure)]
    relative_humidity = igra_station_data.relative_humidity.values[0 : len(pressure)]
    dewpoint = igra_station_data.dewpoint.values[0 : len(pressure)]

    monotonicity_checks(pressure, "pressure")
    monotonicity_checks(temperature, "temperature")
    monotonicity_checks(uwind, "uwind")
    monotonicity_checks(vwind, "vwind")
    monotonicity_checks(relative_humidity, "relative_humidity")
    monotonicity_checks(dewpoint, "dewpoint")

    profile = xr.Dataset(
        data_vars={
            "u": (
                ("station", "pressure"),
                uwind[np.newaxis, :],
                {
                    "long_name": "Zonal wind component",
                    "units": "m s-1",
                },
            ),
            "v": (
                ("station", "pressure"),
                vwind[np.newaxis, :],
                {
                    "long_name": "Meridional wind component",
                    "units": "m s-1",
                },
            ),
            "rh": (
                ("station", "pressure"),
                relative_humidity[np.newaxis, :],
                {
                    "long_name": "Relative humidity",
                    "units": "%",
                },
            ),
            "ta": (
                ("station", "pressure"),
                temperature[np.newaxis, :],
                {
                    "long_name": "Air temperature",
                    "units": "K",
                },
            ),
            "td": (
                ("station", "pressure"),
                dewpoint[np.newaxis, :],
                {
                    "long_name": "Dewpoint temperature",
                    "units": "K",
                },
            ),
        },
        coords={
            "station": [station_id],
            "pressure": (
                "pressure",
                pressure / 100,
                {
                    "long_name": "Air pressure",
                    "units": "hPa",
                    "positive": "down",
                },
            ),
        },
        attrs={
            "creation_time": datetime.today().isoformat(),
        },
    )

    return profile


def make_cross_section_ready_profile(
    profile: xr.Dataset, station_id: str
) -> xr.Dataset:

    pressure_grid = np.arange(1000, 90, -10)

    profile = make_profile(profile, station_id)

    rh = mpcalc.relative_humidity_from_dewpoint(
        temperature=profile["ta"].values * units.kelvin,
        dewpoint=profile["td"].values * units.kelvin,
    )

    profile["rh"] = xr.DataArray(
        rh.magnitude * 100,
        dims=("station", "pressure"),
        attrs={
            "long_name": "Relative humidity",
            "units": "percent",
        },
    )

    profile = profile.interp(pressure=pressure_grid).sortby("pressure", ascending=False)

    return profile


nord12 = make_cross_section_ready_profile(norderney12, "Norderney")
schl12 = make_cross_section_ready_profile(schleswig12, "Schleswig")
fehm12 = fehmarn12.sel(p=nord12.pressure, method="nearest")
grei12 = make_cross_section_ready_profile(greifswald12, "Greifswald")

cross_section = xr.concat([nord12, schl12, fehm12, grei12], dim="station")

fig, ax = plt.subplots(figsize=(12, 8), dpi=500, tight_layout=True)

ax.set_title("Cold Front Cross Section, 2026-08-15T12Z", fontsize=20)

cf = ax.contourf(
    [1, 2, 3, 4],
    cross_section.pressure,
    cross_section.rh.T,
    cmap="BrBG",
    levels=np.linspace(5, 95, 91),
    extend="both",
)
cl = ax.contour(
    [1, 2, 3, 4],
    cross_section.pressure,
    cross_section.ta.T - 273.15,
    colors="black",
    levels=[-50, -35, -20, -10, 0, 10, 15, 20],
)

ax.barbs(
    [1, 2, 3, 4],
    cross_section.sel(p=[1000, 850, 700, 500, 300, 200, 100]).p,
    cross_section.sel(p=[1000, 850, 700, 500, 300, 200, 100]).u.T * 1.944,
    cross_section.sel(p=[1000, 850, 700, 500, 300, 200, 100]).v.T * 1.944,
    length=6,
)

target_location = 3.4

manual_positions = []
for path in cl.get_paths():
    verts = path.vertices
    x = verts[:, 0]

    if x.min() <= target_location <= x.max():
        idx = np.argmin(np.abs(x - target_location))
        manual_positions.append(tuple(verts[idx]))

ax.clabel(cl, manual=manual_positions, inline=True, fmt=lambda x: f" {x:.0f} C")

cb = fig.colorbar(cf, ax=ax, extend="both", orientation="horizontal", shrink=0.5, pad=0.06)
cb.ax.tick_params(labelsize=12)
cb.set_label("Relative Humidity [%]", fontsize=14)
cb.set_ticks([5, 25, 50, 75, 95])

ax.set_xlim(0.5, 4.5)
ax.set_xticks([1, 2, 3, 4])
ax.set_xticklabels(cross_section.station.values, fontsize=14)

ax.set_ylabel("Pressure [hPa]", fontsize=14)
ax.set_yscale("log")
ax.set_ylim(180, 1040)
ax.yaxis.set_minor_locator(NullLocator())
ax.set_yticks([1000, 850, 700, 500, 300, 200, 100])
ax.set_yticklabels(["1000", "850", "700", "500", "300", "200", "100"], fontsize=14)
ax.invert_yaxis()

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)

ax.grid(linestyle=":", linewidth=0.5)

plt.savefig("../plots/station_cross_section.png", bbox_inches="tight")
plt.close()

nord12_2 = make_cross_section_ready_profile(norderney12_2, "Norderney")
schl12_2= make_cross_section_ready_profile(schleswig12_2, "Schleswig")
fehm12_2 = fehmarn12.sel(p=nord12_2.pressure, method="nearest")
grei12_2 = make_cross_section_ready_profile(greifswald12_2, "Greifswald")

cross_section2 = xr.concat([nord12_2, schl12_2, fehm12_2, grei12_2], dim="station")

fig2, ax2 = plt.subplots(figsize=(12, 8), dpi=500, tight_layout=True)

ax2.set_title("Northern Germany Cross Section, 2026-08-13T12Z", fontsize=20)

cf = ax2.contourf(
    [1, 2, 3, 4],
    cross_section2.pressure,
    cross_section2.rh.T,
    cmap="BrBG",
    levels=np.linspace(5, 95, 91),
    extend="both",
)
cl = ax2.contour(
    [1, 2, 3, 4],
    cross_section2.pressure,
    cross_section2.ta.T - 273.15,
    colors="black",
    levels=[-50, -35, -20, -10, 0, 10, 15, 20],
)

ax2.barbs(
    [1, 2, 3, 4],
    cross_section2.sel(p=[1000, 850, 700, 500, 300, 200, 100]).p,
    cross_section2.sel(p=[1000, 850, 700, 500, 300, 200, 100]).u.T * 1.944,
    cross_section2.sel(p=[1000, 850, 700, 500, 300, 200, 100]).v.T * 1.944,
    length=8,
)

target_location = 1.5

manual_positions = []
for path in cl.get_paths():
    verts = path.vertices

    if verts.size == 0:
        continue

    x = verts[:, 0]

    if x.min() <= target_location <= x.max():
        idx = np.argmin(np.abs(x - target_location))
        manual_positions.append(tuple(verts[idx]))

ax2.clabel(cl, manual=manual_positions, inline=True, fmt=lambda x: f" {x:.0f} C")

cb2 = fig2.colorbar(cf, ax=ax2, extend="both", orientation="horizontal", shrink=0.5, pad=0.06)
cb2.ax.tick_params(labelsize=12)
cb2.set_label("Relative Humidity [%]", fontsize=14)
cb2.set_ticks([5, 25, 50, 75, 95])

ax2.set_xlim(0.5, 4.5)
ax2.set_xticks([1, 2, 3, 4])
ax2.set_xticklabels(cross_section2.station.values, fontsize=14)

ax2.set_ylabel("Pressure [hPa]", fontsize=14)
ax2.set_yscale("log")
ax2.set_ylim(180, 1080)
ax2.yaxis.set_minor_locator(NullLocator())
ax2.set_yticks([1000, 850, 700, 500, 300, 200, 100])
ax2.set_yticklabels(["1000", "850", "700", "500", "300", "200", "100"], fontsize=14)
ax2.invert_yaxis()

ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.spines["bottom"].set_visible(False)
ax2.spines["left"].set_visible(False)

ax2.grid(linestyle=":", linewidth=0.5)

plt.savefig("../plots/overview_station_cross_section.png", bbox_inches="tight")
plt.close()
