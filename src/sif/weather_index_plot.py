import textwrap

from matplotlib.patches import Rectangle
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt

from src.sif.utils.file_management import PLOT_DIR


weather_colors = {
    1: "lightgreen",
    2: "green",
    3: "yellow",
    4: "orange",
    5: "red",
    6: "darkred",
}


weather_index_description = {
    1: "Cloudless / strong ridging / strong inversion",
    2: "Fair weather Cu / Shallow convection / fair weather",
    3: "Good weather / Larger Cu / Sc / Isolated light precipitation",
    4: "Moderate weather / TCU / Heavy Precipitation / Isolated TS",
    5: "Bad weather / CBs / Heavy rainfall",
    6: "Severe weather / Hail / Tornadoes / Damaging winds",
}


fig, ax = plt.subplots(figsize=(14, 5), facecolor='lightyellow')


for i in range(1, 7):

    # Two columns
    column = (i - 1) % 2
    row = (i - 1) // 2

    x = 0.04 + column * 0.50
    y = 2.35 - row * 1.05

    # Wrap description onto two lines
    description = textwrap.fill(
        weather_index_description[i],
        width=30,
    )

    # Colored rectangle
    rectangle = Rectangle(
        (x, y),
        0.10,
        0.70,
        facecolor=weather_colors[i],
        edgecolor="darkgrey",
        linewidth=1.0,
    )

    ax.add_patch(rectangle)

    # Index number
    ax.text(
        x + 0.05,
        y + 0.35,
        str(i),
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        color="white",
        path_effects=[
            pe.withStroke(linewidth=3, foreground="black")
        ],
    )

    # Description
    ax.text(
        x + 0.12,
        y + 0.35,
        description,
        ha="left",
        va="center",
        fontsize=20,
        linespacing=1.25,
    )


# Title
ax.text(
    0.49,
    3.25,
    "The Stability Score",
    ha="center",
    va="bottom",
    fontsize=35,
    fontweight="bold",
)


# Formatting
ax.set_xlim(0, 1)
ax.set_ylim(-0.25, 3.55)

ax.axis("off")


plt.tight_layout()
plt.savefig(PLOT_DIR / "weather_index.png", dpi=300)
plt.show()