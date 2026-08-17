import matplotlib.pyplot as plt
import xarray as xr

from metpy.plots import Hodograph, SkewT
from metpy.units import units
from pathlib import Path
from utils import FileManagement


class FehmarnRadiosondeProfilePlotter:
    """
    Utilities for plotting data from Radiosonde instance.

    Expects data to be radiosondes launched from Fehmarn during the Stability Indices at Fehmarn (SIF) field campaign.
    """

    def __init__(self, filepath: str):
        """
        Initialise the plotter with radiosonde data.
        :param filepath: The path at which radiosonde data is stored.
        """

        self.filepath = Path(filepath)
        self.plot_name = self.filepath.stem

        self.data = xr.open_dataset(self.filepath)

    def plot_skewt(self, sounding_id: int):
        """
        Plots a skew-t diagram of a radiosonde launched at Fehmarn.

        Provides quick looks at the data.
        :param sounding_id: The sounding to be plotted.
        :return: None
        """

        p = self.data["p"]
        plotting_data = self.data.isel(sounding_id=sounding_id)
        ta = plotting_data["ta"]
        td = plotting_data["td"]
        u = plotting_data["u"]
        v = plotting_data["v"]

        mask = (p <= 1000) & (p >= 100)

        p = p.where(mask, drop=True) * units.hPa
        ta = (ta.where(mask, drop=True) - 273.15) * units.degC
        td = (td.where(mask, drop=True) - 273.15) * units.degC
        u = (u.where(mask, drop=True).data * (units.meter / units.second)).to(
            units.knots
        )
        v = (v.where(mask, drop=True).data * (units.meter / units.second)).to(
            units.knots
        )

        fig = plt.figure(figsize=(14, 9), dpi=300, constrained_layout=True)
        skew = SkewT(
            fig,
            rotation=45,
        )

        plt.title(f"{self.plot_name}.{sounding_id + 1}.{plotting_data.time.values[0]}")
        plt.xlabel(r"Temperature \ $^\circ C$")
        plt.ylabel(r"Pressure \ $hPa$")

        skew.plot(p, ta, color="darkorange", linewidth=2.5, label="T")
        skew.plot(p, td, color="navy", linewidth=2.5, label="Td")

        skew.plot_barbs(p[::100], u[::100], v[::100])

        skew.ax.set_xlim(-30, 40)
        skew.ax.tick_params(axis="both", labelsize=14)

        skew.ax.axvline(0, color="k", linewidth=1, alpha=0.5)
        skew.plot_dry_adiabats(alpha=0.3)
        skew.plot_moist_adiabats(alpha=0.3)

        skew.ax.legend(fontsize=14)

        # Create a hodograph
        ax = plt.axes((0.75, 0.65, 0.2, 0.2))
        h = Hodograph(ax, component_range=60)
        h.add_grid(increment=20)
        h.plot(u, v)

        plt.savefig(FileManagement.PLOT_DIR / 'fehmarn' / f"{self.plot_name}.{sounding_id}.png")

        return None

    def plot_profile(self, var: str):
        """
        Plots a profile of a given variable as a function of height.
        :param var: The variable to be plotted.
        :return: None
        """

        height = self.data["height"]
        variable = self.data[var].isel(sounding_id=0)

        plt.plot(variable, height)

        plt.show()


class FehmarnRadiosondeIndicesPlotter:
    """
    Utilities for plotting stability indices calculated from radiosondes launched at Fehmarn.
    """

    def __init__(self, filepath: str):
        """
        Initialise the plotter with radiosonde data.
        :param filepath: The path at which radiosonde data is stored.
        """

        self.filepath = Path(filepath)
        self.plot_name = self.filepath.stem

        self.data = xr.open_dataset(self.filepath)

    def plot_indices_over_time(self):
        """
        Plots CAPE, K-index, TT-index, LI as a function of time.
        :return:
        """

        fig, axes = plt.subplots(
            nrows=2, ncols=2, figsize=(10, 10), dpi=300, constrained_layout=True
        )
        ax1, ax2, ax3, ax4 = axes.flatten()

        sounding_id = self.data.sounding_id.values
        cape = self.data["cape"]
        k = self.data["k_index"]
        tt_index = self.data["tt_index"]
        li = self.data['li']

        # Plot CAPE as a function of time.
        ax1.set_title("CAPE")
        ax1.scatter(sounding_id, cape, color="k")
        ax1.plot(sounding_id, cape, color="k")
        ax1.set_xlabel("sounding_index")
        ax1.set_ylabel("CAPE ")

        ax2.set_title("K-index")
        ax2.scatter(sounding_id, k, color="k")
        ax2.plot(sounding_id, k, color="k")
        ax2.set_xlabel("sounding_index")
        ax2.set_ylabel("K ")

        ax3.set_title("Total Totals")
        ax3.scatter(sounding_id, tt_index, color="k")
        ax3.plot(sounding_id, tt_index, color="k")
        ax3.set_xlabel("sounding_index")
        ax3.set_ylabel("Total Totals ")

        ax4.set_title("Lifted Index")
        ax4.scatter(sounding_id, li, color="k")
        ax4.plot(sounding_id, li, color="k")
        ax4.set_xlabel("sounding_index")
        ax4.set_ylabel("LI ")

        plt.savefig(
            FileManagement.PLOT_DIR
            / "fehmarn"
            / "sif.radiosondes.indices.time_series.png"
        )
