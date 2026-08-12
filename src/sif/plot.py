import matplotlib.pyplot as plt
import xarray as xr

from metpy.plots import Hodograph, SkewT
from metpy.units import units
from pathlib import Path
from utils import FileManagement


class FehmarnRadiosondePlotter:
    """
    Utilities for plotting data from Radiosonde instance.

    Expects data to be radiosondes launched from Fehmarn during the Stability Indices at Fehmarn (SIF) field campaign.
    """

    def __init__(self, filepath:  str):
        """
        Initialise the plotter with radiosonde data.
        :param filepath: The path at which radiosonde data is stored.
        """

        self.filepath = Path(filepath)
        self.plot_name = self.filepath.stem

        self.data = xr.open_dataset(self.filepath)

    def plot_skewt(self):
        """
        Plots a skew-t diagram of a radiosonde launched at Fehmarn.

        Provides quick looks at the data.
        :return: None
        """

        p = self.data['p'].isel(sounding_id=0)
        ta = self.data['ta'].isel(sounding_id=0)
        td = self.data['td'].isel(sounding_id=0)
        u = self.data['u'].isel(sounding_id=0)
        v = self.data['v'].isel(sounding_id=0)

        mask = (p <= 1000) & (p >= 100)

        p = p.where(mask, drop=True) * units.hPa
        ta = (ta.where(mask, drop=True) - 273.15) * units.degC
        td = (td.where(mask, drop=True) - 273.15) * units.degC
        u = (u.where(mask, drop=True).data * (units.meter / units.second)).to(units.knots)
        v = (v.where(mask, drop=True).data * (units.meter / units.second)).to(units.knots)

        fig = plt.figure(figsize=(14, 9), dpi=300, constrained_layout=True)
        skew = SkewT(fig, rotation=45)

        plt.title(self.plot_name)
        plt.xlabel(r'Temperature \ $^\circ C$')
        plt.ylabel(r'Pressure \ $hPa$')

        skew.plot(p, ta, color='darkorange', linewidth=2.5, label='T')
        skew.plot(p, td, color='navy', linewidth=2.5, label='Td')

        skew.plot_barbs(p[::200], u[::200], v[::200])

        skew.ax.set_xlim(-30, 40)
        skew.ax.tick_params(axis='both', labelsize=14)

        skew.ax.axvline(0, color='k', linewidth=1, alpha=0.5)
        skew.plot_dry_adiabats(alpha=0.3)
        skew.plot_moist_adiabats(alpha=0.3)

        skew.ax.legend(fontsize=14)

        # Create a hodograph
        ax = plt.axes((0.75, 0.65, 0.2, 0.2))
        h = Hodograph(ax, component_range=60)
        h.add_grid(increment=20)
        h.plot(u, v)

        plt.savefig(FileManagement.PLOT_DIR / f'{self.plot_name}.png')

        return None

    def plot_profile(self, var: str):
        """
        Plots a profile of a given variable as a function of height.
        :param var: The variable to be plotted.
        :return: None
        """

        height = self.data['height']
        variable = self.data[var].isel(sounding_id=0)

        plt.plot(variable, height)

        plt.show()

