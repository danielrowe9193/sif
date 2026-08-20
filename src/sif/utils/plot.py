import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from metpy.plots import Hodograph, SkewT
from metpy.units import units
from pathlib import Path
from .utils import FileManagement


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

        plt.savefig(
            FileManagement.PLOT_DIR / "fehmarn" / f"{self.plot_name}.{sounding_id}.png"
        )

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

    def __init__(self, sif_filepath: str | Path, ifs_filepath: str | Path):
        """
        Initialise the plotter with radiosonde data.
        :param sif_filepath: The path at which radiosonde data is stored.
        """

        self.sif_filepath = Path(sif_filepath)
        self.ifs_filepath = Path(ifs_filepath)
        self.plot_name = self.sif_filepath.stem

        self.sif_data = xr.open_dataset(self.sif_filepath)
        self.ifs_data = xr.open_dataset(self.ifs_filepath)

        self.launch_times = self.sif_data.isel(p=0).time.values

        self.ifs_data_12h = self.ifs_data.sel(
            station="Fehmarn", forecast_hour='12h'
        )
        self.ifs_data_12h = self.ifs_data_12h.sel(
            valid_time=np.sort(self.launch_times), method='nearest'
        )

        self.ifs_data_24h = self.ifs_data.sel(
            station="Fehmarn", forecast_hour='24h'
        )
        self.ifs_data_24h = self.ifs_data_24h.sel(
            valid_time=np.sort(self.launch_times), method='nearest'
        )

        self.ifs_data_48h = self.ifs_data.sel(
            station="Fehmarn", forecast_hour='48h'
        )
        self.ifs_data_48h = self.ifs_data_48h.sel(
            valid_time=np.sort(self.launch_times), method='nearest'
        )

    def plot_indices_over_time(self):
        """
        Plots CAPE, K-index, TT-index, LI as a function of time.
        :return:
        """

        fig, axes = plt.subplots(
            nrows=2, ncols=2, figsize=(10, 10), dpi=300, constrained_layout=True
        )
        ax1, ax2, ax3, ax4 = axes.flatten()

        sounding_id = self.sif_data.sounding_id.values
        sif_cape = self.sif_data["cape"]
        sif_k = self.sif_data["k_index"]
        sif_tt = self.sif_data["tt_index"]
        sif_li = self.sif_data["li"]

        ifs_12h_cape = self.ifs_data_12h['cape']
        ifs_12h_k = self.ifs_data_12h["k_index"]
        ifs_12h_tt = self.ifs_data_12h["tt_index"]
        ifs_12h_li = self.ifs_data_12h["li"]

        ifs_24h_cape = self.ifs_data_24h['cape']
        ifs_24h_k = self.ifs_data_24h["k_index"]
        ifs_24h_tt = self.ifs_data_24h["tt_index"]
        ifs_24h_li = self.ifs_data_24h["li"]

        ifs_48h_cape = self.ifs_data_48h['cape']
        ifs_48h_k = self.ifs_data_48h["k_index"]
        ifs_48h_tt = self.ifs_data_48h["tt_index"]
        ifs_48h_li = self.ifs_data_48h["li"]

        # Plot CAPE as a function of time.
        ax1.set_title("CAPE")
        ax1.scatter(sounding_id, sif_cape, color="k")
        ax1.plot(sounding_id, sif_cape, color="k")
        ax1.plot(
            sounding_id, ifs_12h_cape, color='brown', linewidth=2,
            label='ifs_12h'
        )
        ax1.plot(
            sounding_id, ifs_24h_cape, color='orange', linewidth=3,
            label='ifs_24h'
        )
        ax1.plot(
            sounding_id, ifs_48h_cape, color='r', linewidth=1,
            label='ifs_48h'
        )
        ax1.set_xlabel("sounding_index")
        ax1.set_xticks(sounding_id)
        ax1.set_ylabel("CAPE ")
        ax1.legend()

        ax2.set_title("K-index")
        ax2.scatter(sounding_id, sif_k, color="k")
        ax2.plot(sounding_id, sif_k, color="k")
        ax2.plot(
            sounding_id, ifs_12h_k, color='brown', linewidth=2,
            label='ifs_12h'
        )
        ax2.plot(
            sounding_id, ifs_24h_k, color='orange', linewidth=3,
            label='ifs_24h'
        )
        ax2.plot(
            sounding_id, ifs_48h_k, color='r', linewidth=1,
            label='ifs_48h'
        )
        ax2.set_xlabel("sounding_index")
        ax2.set_xticks(sounding_id)
        ax2.set_ylabel("K")
        ax2.legend()

        ax3.set_title("Total Totals")
        ax3.scatter(sounding_id, sif_tt, color="k")
        ax3.plot(sounding_id, sif_tt, color="k")
        ax3.plot(
            sounding_id, ifs_12h_tt, color='brown', linewidth=2,
            label='ifs_12h'
        )
        ax3.plot(
            sounding_id, ifs_24h_tt, color='orange', linewidth=3,
            label='ifs_24h'
        )
        ax3.plot(
            sounding_id, ifs_48h_tt, color='r', linewidth=1,
            label='ifs_48h'
        )
        ax3.set_xlabel("sounding_index")
        ax3.set_xticks(sounding_id)
        ax3.set_ylabel("Total Totals")
        ax3.legend()

        ax4.set_title("Lifted Index")
        ax4.scatter(sounding_id, sif_li, color="k")
        ax4.plot(sounding_id, sif_li, color="k")
        ax4.plot(
            sounding_id, ifs_12h_li, color='brown', linewidth=2,
            label='ifs_12h'
        )
        ax4.plot(
            sounding_id, ifs_24h_li, color='orange', linewidth=3,
            label='ifs_24h'
        )
        ax4.plot(
            sounding_id, ifs_48h_li, color='r', linewidth=1,
            label='ifs_48h'
        )
        ax4.set_xlabel("sounding_index")
        ax4.set_xticks(sounding_id)
        ax4.set_ylabel("LI ")
        ax4.legend()

        plt.savefig(
            FileManagement.PLOT_DIR
            / "fehmarn"
            / "sif.radiosondes.indices.time_series.png"
        )
