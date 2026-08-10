import pathlib
import zipfile


class CalcUtils:
    """Utilities for calculations during the experiment."""
    ...


class PlotUtils:
    """Utilities for plotting measurements taken during the experiment."""
    ...


class FileManagement:
    """Utilities for handling files gathered during the experiment."""

    PACKAGE_DIR = pathlib.Path(__file__).resolve().parent
    PROJECT_DIR = PACKAGE_DIR.parent.parent

    DATA_DIR = PROJECT_DIR / 'data/'
    PLOT_DIR = PROJECT_DIR / 'plots/'

    @staticmethod
    def make_directories():
        """Creates data/ and plots/ directories if currently non-existant."""

        ...

    @staticmethod
    def convert_mwx_to_zip():
        """
        Method that converts mwx to zip files.
        :return: None
        """

        ...

    @staticmethod
    def unzip():
        """
        Method that unzips data after it has been converted to zip.
        :return: None
        """

        ...

