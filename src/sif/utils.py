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

