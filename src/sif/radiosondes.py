import numpy as np
import pandas as pd
import xarray as xr
import xml.etree.ElementTree as ET
import zipfile

from pathlib import Path
from utils import FileManagement
from xarray import DataTree


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
        extract_to: str | Path = FileManagement.DATA_DIR / "radiosonde/"
    ):
        """
        Initialize a Radiosonde instance.

        Parameters
        ----------
        storage_dir : str or Path, optional
            Directory containing the raw `.mwx` radiosonde file. Defaults to
            the project's data directory.
        filename : str, optional
            Name of the `.mwx` file, including its extension.
        extract_to : str or Path, optional
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

        self.filename_nc = "clean.nc"
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

        with zipfile.ZipFile(self.filepath, "r") as z:
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

    def build_std_pressure_lvl_radiosonde(self) -> xr.Dataset:
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
                "height": float(row.get("Height")),
                "p": float(row.get("PressurePk")),
                "h": float(row.get("Height")),
                "ta": float(row.get("Temperature")),
                "rh": float(row.get("Humidity")),
                "wdir": float(row.get("WindDirection")),
                "wspeed": float(row.get("WindSpeed")),
            }
            for row in root.findall("Row")
        ]

        df = pd.DataFrame(data)
        df = df.set_index("height")

        ds = df.to_xarray()
        ds = ds.sortby("height")

        return ds

    def build_radiosonde(self) -> DataTree:
        """
        Construct a radiosonde dataset from synchronized PTU and stability index data.

        This method reads `SynchronizedSoundingData.xml` and `StabilityIndex.xml`,
        extracts all rows, and constructs an xarray dataset indexed by height.
        Stability indices are merged into the same dataset under a shared
        `sounding_id` dimension.

        Returns
        -------
        xarray.Dataset
            Dataset containing PTU‑derived radiosonde variables and stability indices.
        """
        root_sounding_data = self.get_tree_from_xml("SynchronizedSoundingData.xml")
        root_stability_index = self.get_tree_from_xml("StabilityIndex.xml")

        sounding_data = [
            {
                "altitude": float(row.get("Altitude")),
                "height": float(row.get("Height")),
                "geometric_height": float(row.get("GeometricHeight")),
                "time": np.datetime64(row.get("DataSrvTime")),
                "p": float(row.get("Pressure")),
                "ta": float(row.get("Temperature")),
                "rh": float(row.get("Humidity")),
                "wdir": float(row.get("WindDir")),
                "wspeed": float(row.get("WindSpeed")),
                "u": float(row.get("WindEast")),
                "v": float(row.get("WindNorth")),
                "lat": float(row.get("Latitude")),
                "lon": float(row.get("Longitude")),
                "sounding_id": row.get("SoundingIdPk"),
            }
            for row in root_sounding_data.findall("Row")
        ]

        stability_index_data = [
            {
                "indices": row.get("NamePk"),
                "value": row.get("Value"),
                "sounding_id": row.get("SoundingIdPk"),
            }
            for row in root_stability_index.findall("Row")
        ]

        sounding_df = pd.DataFrame(sounding_data)
        sounding_id = sounding_df["sounding_id"].iloc[0]

        sounding_df = (
            sounding_df.drop(columns="sounding_id")
            .set_index("height")
        )

        sounding_ds = (
            sounding_df.to_xarray()
            .sortby("height")
            .expand_dims(sounding_id=[sounding_id])
        )

        stability_index_df = pd.DataFrame(stability_index_data)
        stability_index_df = (
            stability_index_df.drop(columns="sounding_id")
            .set_index("indices")
        )

        stability_index_df["value"] = pd.to_numeric(
            stability_index_df["value"], errors="coerce"
        )

        stability_index_ds = (
            stability_index_df.to_xarray()
            .expand_dims(sounding_id=[sounding_id])
        )

        radiosonde = xr.merge([sounding_ds, stability_index_ds])

        return radiosonde

    def summarize(self) -> None:
        """
        Print a summary of the radiosonde datasets.

        This method prints both the standard‑pressure‑level dataset and the
        full radiosonde dataset containing PTU and stability index data.

        Returns
        -------
        None
        """
        print(
            f"{self.build_std_pressure_lvl_radiosonde()}\n\n"
            f"{self.build_radiosonde()}"
        )
