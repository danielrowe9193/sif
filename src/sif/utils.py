import numpy as np
import xarray as xr

from pathlib import Path


class CalcUtils:
    """Utilities for calculations during the experiment."""



class PlotUtils:
    """Utilities for plotting measurements taken during the experiment."""
    ...


class FileManagement:
    """Utilities for handling files gathered during the experiment."""

    PACKAGE_DIR = Path(__file__).resolve().parent
    PROJECT_DIR = PACKAGE_DIR.parent.parent

    DATA_DIR = PROJECT_DIR / 'data/'
    PLOT_DIR = PROJECT_DIR / 'plots/'

    @staticmethod
    def summarize(path_to_data: str | Path) -> None:
        """
        Print a summary of a dataset.

        This method prints the dims, coordinates and datavars of
        the radiosonde dataset.

        Returns
        -------
        None
        """

        path_to_data = Path(path_to_data)

        ds = xr.open_dataset(
            filename_or_obj=path_to_data
        )

        print(
            f"Summary of {path_to_data.stem}.nc:\n"
            f"{ds.dims}\n"
            f"{ds.coords}\n"
            f"{ds.data_vars}"
        )

        return None
