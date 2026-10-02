import matplotlib.dates as mdates
from matplotlib import pyplot as plt
import numpy as np

from src.sif.utils.file_management import PLOT_DIR
from src.sif.utils.overview_poster_comp import load_ds


def plot_index(index, ax):
    """Plots a given sounding index on the given axis."""

    # Colors corresponding to weather index 1–6
    weather_colors = {
        1: "lightgreen",
        2: "green",
        3: "yellow",
        4: "orange",
        5: "red",
        6: "darkred",
    }

    # Connecting line
    ax.plot(
        ds.sounding_num,
        index,
        color="black",
        linewidth=1.5,
        zorder=1,
    )

    # Colored markers
    for sounding_num, idx, weather_index in zip(
        ds.sounding_num.values,
        index.values,
        ds.weather_index.values,
    ):
        ax.scatter(
            sounding_num,
            idx,
            color=weather_colors[weather_index],
            edgecolor="black",
            s=200,
            zorder=2,
        )

    # Labels
    ax.set_xlabel("Sounding Number", fontsize=20)
    ax.set_ylabel(f"{index.attrs['long_name']}", fontsize=20)
    ax.set_title(f"{index.attrs['long_name']}", fontsize=22, fontweight='bold')

    ax.set_xticks(ds.sounding_num.values)
    ax.set_xticklabels(np.arange(1, len(ds.sounding_num) + 1))
    ax.set_xlim(-0.2, 13.2)

    ax.tick_params(axis="y", labelsize=20)
    ax.tick_params(axis="x", labelsize=15)

    # Grid
    ax.grid(True, linestyle=":", alpha=0.3)

    return None


ds = load_ds('sif.std_plvl_radiosondes.profiles.level2.nc').sel(station='Fehmarn')

def main():

    k_index = ds['k_index']
    lifted_index = ds['li']
    totals_totals_index = ds['tt_index']
    cin = ds['cin']
    cape = ds['cape']
    showalter_index = ds['si']
    rackliff_index = ds['ri']
    jefferson_index = ds['ji']
    precipitable_water = ds['pw']


    fig, axes = plt.subplots(3, 3, figsize=(24, 20))

    plot_index(k_index, axes[0, 0])
    axes[0, 0].set_facecolor("lavenderblush")
    axes[0, 0].set_ylim(-12, 40)
    axes[0, 0].axhline(y=35, color="darkred", linestyle=":", linewidth=4)
    axes[0, 0].axhline(y=30, color="red", linestyle=":", linewidth=4)
    axes[0, 0].axhline(y=25, color="orange", linestyle=":", linewidth=4)
    axes[0, 0].axhline(y=20, color="yellow", linestyle=":", linewidth=8)

    plot_index(lifted_index, axes[0, 1])
    axes[0, 1].set_facecolor("aliceblue")
    axes[0, 1].set_ylim(-8, 16)
    axes[0, 1].axhline(y=-6, color="darkred", linestyle=":", linewidth=4)
    axes[0, 1].axhline(y=-4, color="red", linestyle=":", linewidth=4)
    axes[0, 1].axhline(y=-2, color="orange", linestyle=":", linewidth=4)
    axes[0, 1].axhline(y=0, color="yellow", linestyle=":", linewidth=8)
    axes[0, 1].axhline(y=3, color="green", linestyle=":", linewidth=4)
    axes[0, 1].axhline(y=6, color="lightgreen", linestyle=":", linewidth=4)

    plot_index(cin, axes[0, 2])
    axes[0, 2].set_facecolor("aliceblue")

    plot_index(cape, axes[1, 0])
    axes[1, 0].set_facecolor("lavenderblush")

    plot_index(totals_totals_index, axes[1, 1])
    axes[1, 1].set_facecolor("lavenderblush")
    axes[1, 1].set_ylim(18, 60)
    axes[1, 1].axhline(y=56, color="darkred", linestyle=":", linewidth=4)
    axes[1, 1].axhline(y=52, color="red", linestyle=":", linewidth=4)
    axes[1, 1].axhline(y=48, color="orange", linestyle=":", linewidth=4)
    axes[1, 1].axhline(y=45, color="yellow", linestyle=":", linewidth=8)
    axes[1, 1].axhline(y=42, color="green", linestyle=":", linewidth=4)


    plot_index(rackliff_index, axes[1, 2])
    axes[1, 2].set_facecolor("lavenderblush")
    axes[1, 2].axhline(y=32, color="darkred", linestyle=":", linewidth=4)
    axes[1, 2].axhline(y=30, color="red", linestyle=":", linewidth=4)
    axes[1, 2].axhline(y=29, color="orange", linestyle=":", linewidth=4)
    axes[1, 2].axhline(y=27, color="yellow", linestyle=":", linewidth=8)
    axes[1, 2].axhline(y=25, color="green", linestyle=":", linewidth=4)

    plot_index(showalter_index, axes[2, 0])
    axes[2, 0].set_facecolor("aliceblue")
    axes[2, 0].set_ylim(-8, 16)
    axes[2, 0].axhline(y=-6, color="darkred", linestyle=":", linewidth=4)
    axes[2, 0].axhline(y=-4, color="red", linestyle=":", linewidth=4)
    axes[2, 0].axhline(y=0, color="orange", linestyle=":", linewidth=4)
    axes[2, 0].axhline(y=3, color="yellow", linestyle=":", linewidth=8)

    plot_index(jefferson_index, axes[2, 1])
    axes[2, 1].set_facecolor("lavenderblush")
    axes[2, 1].axhline(y=30, color="darkred", linestyle=":", linewidth=4)
    axes[2, 1].axhline(y=29, color="red", linestyle=":", linewidth=4)
    axes[2, 1].axhline(y=28, color="orange", linestyle=":", linewidth=4)
    axes[2, 1].axhline(y=26, color="yellow", linestyle=":", linewidth=8)
    axes[2, 1].axhline(y=24, color="green", linestyle=":", linewidth=4)

    plot_index(precipitable_water, axes[2, 2])
    axes[2, 2].set_facecolor("lavenderblush")


    plt.tight_layout()
    plt.savefig(PLOT_DIR / "indices_comparisons_at_fehmarn", dpi=300)
    plt.show()


def plot_ri():
    launch_times = ds.launch_time.values
    sounding_nums = ds.sounding_num.values

    # Date/time labels for the x-axis.
    tick_labels = [
        mdates.num2date(mdates.date2num(time)).strftime(format="%d %HZ")
        for time in launch_times[sounding_nums]
    ]

    rackliff_index = ds['ri']

    fig, ax = plt.subplots(figsize=(12, 10))

    plot_index(rackliff_index, ax)

    ax.set_xlabel("August Launch time")
    ax.set_xticks(sounding_nums)
    ax.set_xticklabels(tick_labels, rotation=45, ha="right")
    ax.set_xlim(sounding_nums.min() - 0.2, sounding_nums.max() + 0.2)
    ax.tick_params(axis="y", which="major", labelsize=20)
    ax.tick_params(axis="x", which="major", labelsize=16)

    ax.set_facecolor("lavenderblush")
    ax.axhline(y=32, color="darkred", linestyle=":", linewidth=4)
    ax.axhline(y=30, color="red", linestyle=":", linewidth=4)
    ax.axhline(y=29, color="orange", linestyle=":", linewidth=4)
    ax.axhline(y=27, color="yellow", linestyle=":", linewidth=8)
    ax.axhline(y=25, color="green", linestyle=":", linewidth=4)

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "rackliff_index_at_fehmarn", dpi=300)
    plt.show()


if __name__ == "__main__":
    plot_ri()