import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import xarray as xr

from datetime import datetime
from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter, NullLocator
from metpy.plots import SkewT
from metpy.units import units

sif2 = xr.open_dataset("../data/netcdf/sif.ptu_radiosondes.profiles.level2.nc")
igra = xr.open_dataset("../data/netcdf/sif.igra_radiosondes.profiles.level0.nc")

print(igra.data_vars)

schleswig12 = igra.sel(station="Schleswig", time="2026-08-15T00")
norderney12 = igra.sel(station="Norderney", time="2026-08-15T12")
greifswald12 = igra.sel(station="Greifswald", time="2026-08-15T12")
fehmarn12 = sif2.sel(station="Fehmarn", sounding_num=9, method="nearest")

schleswig_lat_lon = (
    igra.sel(station="Schleswig", time="2026-08-15T00").latitude.values,
    igra.sel(station="Schleswig", time="2026-08-15T00").longitude.values,
)
norderney_lat_lon = (
    igra.sel(station="Norderney", time="2026-08-15T00").latitude.values,
    igra.sel(station="Norderney", time="2026-08-15T00").longitude.values,
)
greifswald_lat_lon = (
    igra.sel(station="Greifswald", time="2026-08-15T12").latitude.values,
    igra.sel(station="Greifswald", time="2026-08-15T12").longitude.values,
)
fehmarn_lat_lon = (
    sif2.sel(station="Fehmarn").isel(sounding_num=0, p=0).lat.values,
    sif2.sel(station="Fehmarn").isel(sounding_num=0, p=0).lon.values,
)

print(schleswig_lat_lon, greifswald_lat_lon, norderney_lat_lon, fehmarn_lat_lon)


def plot_skewt(radiosonde_profile: xr.Dataset):
    """Plot Skew-T of radiosondes profile."""

    u = (radiosonde_profile["u"].data * (units.meter / units.second)).to(units.knots)
    v = (radiosonde_profile["v"].data * (units.meter / units.second)).to(units.knots)

    p = radiosonde_profile["p"].data * units.hPa
    ta = (radiosonde_profile["ta"].data * units.kelvin).to("degC")
    td = (radiosonde_profile["td"].data * units.kelvin).to("degC")

    fig = plt.figure(figsize=(8, 10), dpi=500, constrained_layout=True)
    skew = SkewT(fig, rotation=45)

    skew.plot(p, ta, color="black", linewidth=2.5, label="Temperature")
    skew.plot(p, td, color="blue", linewidth=2.5, label="Dewpoint")

    skew.plot_barbs(p[::100], u[::100], v[::100], length=8.5)

    skew.ax.set_xlim(-30, 40)
    skew.ax.tick_params(axis="both", labelsize=14)

    skew.ax.axvline(0, color="k", linewidth=1, alpha=0.5)
    skew.plot_dry_adiabats(alpha=0.3)
    skew.plot_moist_adiabats(alpha=0.3)

    skew.ax.legend(fontsize=14)

    return fig, skew


def plot_northern_germany_soundings():
    """
    Plots winds for stations across northern germany.
    :return:
    """

    levels = np.arange(0, 100, 10)

    # Create figure and map projection
    fig = plt.figure(figsize=(12, 16), dpi=500, tight_layout=True)
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Northern Germany extent
    # [lon_min, lon_max, lat_min, lat_max]
    ax.set_extent([5.0, 16.0, 53.0, 56.5], crs=ccrs.PlateCarree())

    # Add map features
    ax.add_feature(cfeature.LAND, facecolor="white")
    # ax.add_feature(cfeature.COASTLINE, linewidth=0.8, color="white")
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.OCEAN, facecolor="lightblue")

    # Gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, linestyle="--", alpha=0.7)
    gl.top_labels = False
    gl.right_labels = False

    # Plot
    ax.set_title("Observed 500 hPa Winds, 2026-08-15T12Z")

    ax.scatter(
        x=norderney_lat_lon[1],
        y=norderney_lat_lon[0],
        s=100,
        label="Norderney",
        color="black",
    )
    ax.scatter(
        x=schleswig_lat_lon[1],
        y=schleswig_lat_lon[0],
        s=100,
        label="Schleswig",
        color="orange",
    )
    ax.scatter(
        x=fehmarn_lat_lon[1], y=fehmarn_lat_lon[0], s=100, label="Fehmarn", color="red"
    )
    ax.scatter(
        x=greifswald_lat_lon[1],
        y=greifswald_lat_lon[0],
        s=100,
        label="Greifswald",
        color="purple",
    )

    plvl = 50_000

    schl_idx = np.abs(schleswig12.pressure - plvl).argmin(dim="level")
    schleswig12_plvl = schleswig12.interpolate_na(dim="level").isel(level=schl_idx)

    nord_idx = np.abs(norderney12.pressure - plvl).argmin(dim="level")
    norderney12_plvl = norderney12.interpolate_na(dim="level").isel(level=nord_idx)

    greif_idx = np.abs(greifswald12.pressure - plvl).argmin(dim="level")
    greifswald12_plvl = greifswald12.interpolate_na(dim="level").isel(level=greif_idx)

    ax.barbs(
        schleswig_lat_lon[1],
        schleswig_lat_lon[0],
        schleswig12_plvl["u_wind"] * 1.944,
        schleswig12_plvl["v_wind"] * 1.944,
        length=8.5,
    )

    ax.barbs(
        greifswald_lat_lon[1],
        greifswald_lat_lon[0],
        greifswald12_plvl["u_wind"] * 1.944,
        greifswald12_plvl["v_wind"] * 1.944,
        length=8.5,
    )

    ax.barbs(
        norderney_lat_lon[1],
        norderney_lat_lon[0],
        norderney12_plvl["u_wind"] * 1.944,
        norderney12_plvl["v_wind"] * 1.944,
        length=8.5,
    )

    ax.barbs(
        fehmarn_lat_lon[1],
        fehmarn_lat_lon[0],
        fehmarn12.sel(p=(plvl / 100), method="nearest")["u"] * 1.944,
        fehmarn12.sel(p=(plvl / 100), method="nearest")["v"] * 1.944,
        length=8.5,
    )

    ax.legend(fontsize=14)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    plt.savefig(
        "../plots/poster_northern_germany.png",
        bbox_inches="tight",
    )

    plt.close()


def sif_cold_front():
    """Showing evolution of variables in time at Fehmarn during passage of cold front."""

    pressure_ticks = [1000, 850, 700, 500, 300, 200]

    sif_cf = sif2.assign_coords(lt=("sounding_num", sif2.launch_time.values))
    sif_cf = sif_cf.sel(
        station="Fehmarn", lt=["2026-08-15T06", "2026-08-15T12", "2026-08-15T18"]
    )
    sif_cf = sif_cf.drop_dims("launch_time")

    print(sif_cf)

    fig, ax = plt.subplots(figsize=(12, 8), dpi=300, tight_layout=True)

    ax.set_title("Cold Front Passage at Fehmarn, 2026-08-15", fontsize=20)

    # cf = ax.contourf(
    #     sif_cf.lt,
    #     sif_cf.p,
    #     (sif_cf.ta.T - 273.15),
    #     levels=100,
    #     cmap="RdBu_r",
    #     extend="both",
    # )
    ta_cl = ax.contour(
        sif_cf.lt,
        sif_cf.p,
        (sif_cf.ta.T - 273.15),
        levels=[-50, -30, -15, 0, 10, 15, 20],
        colors="black",
        linewidths=2,
        negative_linestyles="--",
    )
    # theta_cl = ax.contour(
    #     sif_cf.lt,
    #     sif_cf.p,
    #     sif_cf.theta.T,
    #     levels=[292, 300, 305, 310, 320, 360],
    #     colors="black",
    #     linewidths=2,
    # )
    rh_cf = ax.contourf(
        sif_cf.sel(p=sif_cf.p.values[::50]).lt,
        sif_cf.sel(p=sif_cf.p.values[::50]).p,
        sif_cf.sel(p=sif_cf.p.values[::50]).rh.T,
        cmap="BrBG",
        levels=np.linspace(5, 95, 91),
        extend="both",
    )

    target_time = mdates.date2num(np.datetime64("2026-08-15T08:00"))

    # label_positions = []
    # for path in ta_cl.get_paths():
    #     vertices = path.vertices
    #     try:
    #         label_positions.append(tuple(vertices[0]))
    #         label_positions.append(tuple(vertices[-1]))
    #     except:
    #         pass

    # ax.clabel(ta_cl, fmt=' %d C', fontsize=12)

    manual_positions = []
    for path in ta_cl.get_paths():
        verts = path.vertices
        x = verts[:, 0]

        if x.min() <= target_time <= x.max():
            idx = np.argmin(np.abs(x - target_time))
            manual_positions.append(tuple(verts[idx]))

    ax.clabel(ta_cl, manual=manual_positions, inline=True, fmt=lambda x: f" {x:.0f} C")

    ax.barbs(
        sif_cf.sel(p=[1000, 850, 700, 500, 300, 200]).lt,
        sif_cf.sel(p=[1000, 850, 700, 500, 300, 200]).p,
        sif_cf.sel(p=[1000, 850, 700, 500, 300, 200]).u.T * 1.944,
        sif_cf.sel(p=[1000, 850, 700, 500, 300, 200]).v.T * 1.944,
        length=6,
    )

    ax.set_xlabel("Time")
    ax.set_xlim(np.datetime64("2026-08-15T04:30"), np.datetime64("2026-08-15T19"))
    ax.set_xticks(
        [
            np.datetime64("2026-08-15T06"),
            np.datetime64("2026-08-15T12"),
            np.datetime64("2026-08-15T18"),
        ]
    )
    ax.set_xticklabels(["06Z", "12Z", "18Z"])

    ax.set_ylabel("Pressure [hPa]", fontsize=14)
    ax.set_yscale("log")
    ax.set_ylim(180, 1040)
    ax.set_yticks([1000, 850, 700, 500, 300, 200, 100])
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_yticklabels(["1000", "850", "700", "500", "300", "200", "100"], fontsize=14)
    ax.invert_yaxis()

    cb = fig.colorbar(rh_cf, ax=ax, extend="both", orientation="horizontal", shrink=0.5, pad=0.07)
    cb.ax.tick_params(labelsize=12)
    cb.set_label("Relative Humidity [%]", fontsize=14)
    cb.set_ticks([0, 25, 50, 75, 100])

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.grid(linestyle=":", linewidth=0.5)

    plt.savefig("../plots/sif_cold_front.png")

    plt.close()

    return None


# sif2 = sif2.sel(station="Fehmarn", sounding_num=10, method="nearest")
# launch_time = sif2.time.values[0]
# fig, skew = plot_skewt(sif2)
# plt.title("Skew-T, Fehmarn, 2026-08-15T18Z", fontsize=20)
# plt.xlabel("Temperature [C]", fontsize=16)
# plt.ylabel("Pressure [hPa]", fontsize=16)
#
# plt.savefig("../plots/poster_skewt.png")
# plt.close()

plot_northern_germany_soundings()
sif_cold_front()
