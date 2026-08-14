import numpy as np
import pandas as pd
import xarray as xr
import xml.etree.ElementTree as ET
import zipfile

from metpy.calc import dewpoint_from_relative_humidity
from metpy.units import units
from pathlib import Path
from xarray import DataTree
from utils import FileManagement


class Radiosonde:
    """
    Prepare and process a single radiosonde dataset from MWX-format input.

    This class extracts XML files contained within a `.mwx` archive and
    constructs NETCDF‑compliant datasets containing radiosonde measurements.
    """

    def __init__(
        self,
        filepath: str | Path,
    ):
        """
        Initialize a Radiosonde instance.

        Parameters
        ----------
        filepath : str

        Notes
        -----
        The constructor also defines default output filenames for processed
        NETCDF files.
        """
        self.filepath = Path(filepath)
        self.directory = self.filepath.parent / self.filepath.stem
        self.directory.mkdir(exist_ok=True)

    def extract_mwx(self) -> None:
        """
        Extract XML files from the `.mwx` archive.

        The `.mwx` file is treated as a ZIP archive. All contents are extracted
        into the directory specified by `extract_to`.

        Returns
        -------
        None
        """
        extraction_dir = Path(self.directory)
        extraction_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(self.filepath, "r") as z:
            z.extractall(self.directory)

        return None

    def _get_tree_from_xml(self, xml_filename: str) -> ET:
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
        xml_filepath = self.directory / xml_filename
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
        root = self._get_tree_from_xml("StdPressureLevels.xml").getroot()

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

        Stores the radiosonde data as a `.nc` file with the same name as the `.mwx` file.

        Returns
        -------
        None
        """
        root_sounding_data = self._get_tree_from_xml("SynchronizedSoundingData.xml")
        root_stability_index = self._get_tree_from_xml("StabilityIndex.xml")

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
            .set_index("p")
        )

        sounding_ds = (
            sounding_df.to_xarray()
            .sortby("p", ascending=False)
            .expand_dims(sounding_id=[sounding_id])
        )

        td = dewpoint_from_relative_humidity(
            temperature=sounding_ds['ta'] * units.kelvin,
            relative_humidity=sounding_ds['rh'] * units.percent
        )

        td = td.data.to(units('kelvin'))

        sounding_ds['td'] = (sounding_ds['ta'].dims, td)

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


class Radiosondes:
    """
    Process multiple radiosondes from a directory and generate a dataset containing all sondes.

    This class builds on the Radiosonde method, this time extract `.mwx` files from a directory then
    processing individual radiosondes and finally concatinating into a single dataset.
    """

    PRESSURE_GRID = np.arange(1000, 9, -1)

    def __init__(self, mwx_dir: str | Path = Path('../../data/'), filename: str = 'sif.radiosondes.nc'):
        """
        Initialise the radiosondes by providing a directory that contains the `.mwx` files.
        :param mwx_dir: The directory containing .mwx files that are processed.
        """

        self.mwx_dir = mwx_dir
        self.filename = filename
        self.rs_ds_list = []

    def build_sif_radiosondes(self, save_to: str | Path = '../../data/'):
        """
        Iterates through self.mwx_dir, builds each radiosonde, concatenates them and exports as a .nc file.
        :param save_to: The directory in which to store the sif_radiosondes .nc file.
        :return: None
        """

        for file in self.mwx_dir.glob('*.mwx'):

            rs = Radiosonde(
                filepath=file
            )
            rs.extract_mwx()
            rs_ds = rs.build_radiosonde()

            rs_ds = rs_ds.interp(p=self.PRESSURE_GRID)

            self.rs_ds_list.append(rs_ds)

        sif = xr.concat(self.rs_ds_list, dim='sounding_id', join='outer')
        sif.to_netcdf(Path(save_to) / self.filename)

        return None


