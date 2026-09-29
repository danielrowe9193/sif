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
            s=80,
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
    plot_index(lifted_index, axes[0, 1])
    plot_index(cin, axes[0, 2])
    plot_index(cape, axes[1, 0])
    plot_index(totals_totals_index, axes[1, 1])
    plot_index(rackliff_index, axes[1, 2])
    plot_index(showalter_index, axes[2, 0])
    plot_index(jefferson_index, axes[2, 1])
    plot_index(precipitable_water, axes[2, 2])


    plt.tight_layout()
    plt.savefig(PLOT_DIR / "indices_comparisons_at_fehmarn", dpi=300)
    plt.show()


if __name__ == "__main__":
    main()