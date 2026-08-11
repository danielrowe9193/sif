import matplotlib.pyplot as plt
import xarray as xr

from utils import FileManagement


class RadiosondePlotter:
    """
    Utilities for plotting data from Radiosonde instance.
    """

    def __init__(self, filepath:  str):
        """
        Initialise the plotter with radiosonde data.
        :param filepath: The path at which radiosonde data is stored.
        """

        self.filepath = filepath

        self.data = xr.open_dataset(self.filepath)

    def plot_variable(self, function_of: str = 'height', variable: str = 'ta'):

        fig, ax = plt.subplots(dpi=300, constrained_layout=True)

        ax.set_title(f"Profile of {variable} with {function_of}")

        ax.plot(
            self.data[variable],
            self.data[function_of],
            color='k'
        )

        plt.savefig(FileManagement.PLOT_DIR / f'{variable}.{function_of}.png')
        plt.close(fig)
