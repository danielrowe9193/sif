import numpy as np
import pandas as pd
import xarray as xr
import xml.etree.ElementTree as ET
import zipfile

from pathlib import Path
from utils import FileManagement


class Radiosonde:
    """
    Prepare and process a single radiosonde dataset from MWX-format input.

    This class extracts XML files contained within a `.mwx` archive and
    constructs NETCDF‑compliant datasets containing radiosonde measurements.
    """

    def __init__(
            self,
            storage_dir: str | Path = FileManagement.DATA_DIR,
            filename: str = None,
            extract_to: str | Path = FileManagement.DATA_DIR / 'radiosonde/'
    ):
        """
        Initialize a Radiosonde instance.

        Parameters
        ----------
        storage_dir : str or Path
            Directory containing the raw `.mwx` radiosonde file. Defaults to data directory.
        filename : str
            Name of the `.mwx` file, including its extension.
        extract_to : str or Path
            Directory where extracted XML files will be written.

        Notes
        -----
        The constructor also defines default output filenames for processed
        NETCDF files.
        """

        self.storage_dir = Path(storage_dir)
        self.filename = filename
        self.filepath = self.storage_dir / self.filename
        self.extract_to = Path(extract_to)

        self.filename_nc = 'clean.nc'
        self.filepath_nc = self.storage_dir / self.filename_nc

    def extract_mwx(self) -> None:
        """
        Extract XML files from the `.mwx` archive.

        The `.mwx` file is treated as a ZIP archive. All contents are extracted
        into the directory specified by `extract_to`.

        Returns
        -------
        None
        """

        extraction_dir = Path(self.extract_to)
        extraction_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(self.filepath, 'r') as z:
            z.extractall(self.extract_to)

        return None

    def get_tree_from_xml(self, xml_filename: str) -> ET:
        """
        Parse an XML file and return its element tree.

        Parameters
        ----------
        xml_filename : str
            Name of the XML file to parse. The file must exist inside the
            extraction directory.

        Returns
        -------
        xml.etree.ElementTree.ElementTree
            Parsed XML element tree.
        """

        xml_filepath = self.extract_to / xml_filename

        return ET.parse(xml_filepath)

    def build_std_pressure_lvl_radiosonde(self):
        """
        Construct a dataset of radiosonde variables on standard pressure levels.

        The method reads `StdPressureLevels.xml`, extracts all rows, and builds
        an xarray dataset indexed by geometric height.

        Returns
        -------
        xarray.Dataset
            Dataset containing radiosonde variables on standard pressure levels.
        """

        root = self.get_tree_from_xml("StdPressureLevels.xml").getroot()

        data = [
            {
                "RadioRxTimePk": row.get("RadioRxTimePk"),
                "time": row.get("DataSrvTime"),
                'height': float(row.get("Height")),
                "p": float(row.get("PressurePk")),
                'h': float(row.get("Height")),
                "ta": float(row.get("Temperature")),
                "rh": float(row.get("Humidity")),
                "wdir": float(row.get("WindDirection")),
                "wspeed": float(row.get("WindSpeed")),
            }
            for row in root.findall("Row")
        ]

        df = pd.DataFrame(data)

        df = df.set_index('height')

        ds = df.to_xarray()

        ds = ds.sortby('height')

        print(ds)

        return ds

    def build_radiosonde(self):
        """
        Construct a radiosonde dataset from synchronized PTU (pressure,
        temperature, humidity) data.

        The method reads `SynchronizedSoundingData.xml`, extracts all rows, and
        builds an xarray dataset indexed by height.

        Returns
        -------
        xarray.Dataset
            Dataset containing PTU‑derived radiosonde variables.
        """

        root = self.get_tree_from_xml(xml_filename="SynchronizedSoundingData.xml")

        data = [
            {
                'altitude': float(row.get('Altitude')),
                'height': float(row.get('Height')),
                'geometric_height': float(row.get('GeometricHeight')),
                'time': np.datetime64(row.get('DataSrvTime')),
                'p': float(row.get('Pressure')),
                'ta': float(row.get('Temperature')),
                'rh': float(row.get('Humidity')),
                'wdir': float(row.get('WindDir')),
                'wspeed': float(row.get('WindSpeed')),
                'u': float(row.get('WindEast')),
                'v': float(row.get('WindNorth')),
                'lat': float(row.get('Latitude')),
                'lon': float(row.get('Longitude')),
            }
            for row in root.findall("Row")
        ]

        df = pd.DataFrame(data)

        df = df.set_index('height')

        ds = df.to_xarray()

        ds = ds.sortby('height')

        print(ds)

        return ds

    def summarize(self):
        """
        Prints the datasets that were created to provide a summary of the radiosondes.
        :return: None
        """

        print(
            f"{self.build_std_pressure_lvl_radiosonde()}\n\n{self.build_radiosonde()}"
        )

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
