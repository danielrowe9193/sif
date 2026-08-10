import matplotlib.pyplot as plt

from radiosondes import Radiosonde
from utils import FileManagement


class RadiosondePlotter:
    """
    Utilities for plotting data from Radiosonde instance.
    """

    def __init__(self, radiosonde: Radiosonde):
        """
        Initialise the plotter with radiosonde data.
        :param radiosonde: The radiosonde data to be plotted, of type Radiosonde.
        """

        self.radiosonde = radiosonde

        self.radiosonde_ds = self.radiosonde.build_radiosonde()

    def plot_variable(self, function_of: str = 'height', variable: str = 'ta'):

        fig, ax = plt.subplots(dpi=300, constrained_layout=True)

        ax.set_title(f"Profile of {variable} with {function_of}")

        ax.plot(
            self.radiosonde_ds[variable],
            self.radiosonde_ds[function_of],
            color='k'
        )

        plt.savefig(FileManagement.PLOT_DIR / f'{variable}.{function_of}.png')
        plt.close(fig)
