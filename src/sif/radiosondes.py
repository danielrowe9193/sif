import numpy as np
import pandas as pd
import xarray as xr
import xml.etree.ElementTree as ET
import zipfile

from pathlib import Path


class Radiosonde:
    """
    Object preparing a singular radiosonde from .mwx data.
    """

    def __init__(self, storage_dir: str | Path, filename: str, extract_to: str | Path):
        """
        Provide storage directory and filename for raw radiosonde data.
        :param storage_dir: The directory in which the raw radiosonde data is stored.
        :param filename: The filename of the raw radiosonde data. Expects the extension to be included.
        :param extract_to: The directory to extract the files to.
        """

        self.storage_dir = Path(storage_dir)
        self.filename = filename
        self.filepath = self.storage_dir / self.filename
        self.extract_to = Path(extract_to)

        self.filename_nc = 'clean.nc'
        self.filepath_nc = self.storage_dir / self.filename_nc

    def extract_mwx(self) -> None:
        """
        Extracts .xml from a given .mwx file to an input directory.
        :return: None.
        """

        extraction_dir = Path(self.extract_to)
        extraction_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(self.filepath, 'r') as z:
            z.extractall(self.extract_to)

        return None

    def get_tree_from_xml(self, xml_filename: str) -> ET:
        """
        Extract the tree from the .xml file, through a parsing method.
        :param xml_filename: The name of the xml file to be parsed.
        :return: An element tree.
        """

        xml_filepath = self.extract_to / xml_filename

        return ET.parse(xml_filepath)

    def build_std_pressure_lvl_radiosonde(self):
        """
        Constructs a dataset containing radiosonde variables on standard pressure values.
        :return: Dataset containing radiosonde variables.
        """

        root = self.get_tree_from_xml("StdPressureLevels.xml").getroot()

        data = [
            {
                "RadioRxTimePk": float(row.get("RadioRxTimePk")),
                "time": row.get("DataSrvTime"),
                "p": float(row.get("PressurePk")),
                'h': float(row.get("Height")),
                "t": float(row.get("Temperature")),
                "rh": float(row.get("Humidity")),
                "wdir": float(row.get("WindDirection")),
                "wspeed": float(row.get("WindSpeed")),
            }
            for row in root.findall("Row")
        ]

        df = pd.DataFrame(data)
        print(df.head())

    def print_tree(self, root, level=0):
        print("    " * level + root.tag)
        for child in root:
            self.print_tree(child, level + 1)
        return None

    def find_tags(self, root, tags=None):
        if tags is None:
            tags = set()
        tags.add(root.tag)

        for child in root:
            self.find_tags(child, tags)

        return tags
