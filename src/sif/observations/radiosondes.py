import numpy as np
import pandas as pd
import src.sif.utils.utils as utils
import xarray as xr
import xml.etree.ElementTree as ET
import zipfile

from metpy.calc import dewpoint_from_relative_humidity
from metpy.units import units
from pathlib import Path


class Radiosonde:
    """
    Represents a single radiosonde observation stored as a .mwx archive.

    Extracts the .mwx and provides access to .xml files within.
    """

    def __init__(
            self,
            filepath: str | Path,
    ):
        """
        Initialize a Radiosonde instance.

        Parameters
        ----------
        filepath : str | Path

        Notes
        -----
        Uses the package default XML_DIR as the directory to store
        extracted .xml files.
        """
        self.filepath = Path(filepath)
        self.extraction_dir = utils.FileManagement.XML_DIR / self.filepath.stem
        self.extraction_dir.mkdir(exist_ok="True")

    def extract_mwx(self) -> None:
        """
        Extract XML files from the `.mwx` archive.

        The `.mwx` file is treated as a ZIP archive. All contents are extracted
        into the xml/ directory.

        Returns
        -------
        None
        """

        with zipfile.ZipFile(self.filepath, "r") as z:
            z.extractall(self.extraction_dir)

        return None

    def get_xml_tree(self, xml_filename: str) -> ET.ElementTree:
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

        xml_filepath = self.extraction_dir / xml_filename
        return ET.parse(xml_filepath)


class StdPressureRadiosonde:
    """
    Build standard pressure level dataset from a Radiosonde.
    Pressure-indexed dataset from StdPressureLevels.xml.
    """

    def __init__(self, radiosonde: Radiosonde):
        self.radiosonde = radiosonde
        self.root = self.radiosonde.get_xml_tree("StdPressureLevels.xml").getroot()

        self.data = [
            {
                "RadioRxTime": float(row.get("RadioRxTime")),
                "sounding_id": row.get("SoundingIdPk"),
                "time": row.get("DataSrvTime"),
                "height": float(row.get("Height")),
                "p": float(row.get("PressurePk")),
                "ta": float(row.get("Temperature")),
                "rh": float(row.get("Humidity")),
                "wdir": float(row.get("WindDirection")),
                "wspeed": float(row.get("WindSpeed")),
                "lat": float(row.get("Latitude")),
                "lon": float(row.get("Longitude"))
            }
            for row in self.root.findall("Row")
        ]

        self.sounding_id: str | None = None

    def build_dataset(self) -> xr.Dataset:
        """
        Construct a dataset of radiosonde variables on standard pressure levels.

        The standard pressure levels are:
            [
                1000, 925, 850, 700, 500, 400,
                300, 250, 200, 150, 100, 70, 50
            ]
        in hPa.

        Acts as a one-to-one comparison of weather forecast models, which are coarse.

        The method extracts all rows, and builds a xarray.Dataset indexed by pressure.
        Also extracts and sets the sounding_id of the radiosonde.

        Returns
        -------
        xarray.Dataset
            Dataset containing radiosonde variables on standard pressure levels.
        """

        df = pd.DataFrame(self.data)

        self.sounding_id = df["sounding_id"].iloc[0]

        df = df.drop(columns="sounding_id").set_index("p")

        ds = df.to_xarray().sortby("p", ascending=False)

        return ds


class PTURadiosonde:
    """
    Build PTU profile dataset from a Radiosonde.
    Pressure-indexed dataset from StdPressureLevels.xml.
    """

    def __init__(self, radiosonde: Radiosonde):
        self.radiosonde = radiosonde
        self.root = self.radiosonde.get_xml_tree("SynchronizedSoundingData.xml").getroot()

        self.data = [
            {
                "altitude": float(row.get("Altitude")),
                "height": float(row.get("Height")),
                "geometric_height": float(row.get("GeometricHeight")),
                "p": float(row.get("Pressure")),
                "time": row.get("DataSrvTime"),
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
            for row in self.root.findall("Row")
        ]
        self.sounding_id: str | None = None

    def build_dataset(self) -> xr.Dataset:
        """
        Construct a radiosonde profile dataset from synchronized PTU observations.

        This method reads `SynchronizedSoundingData.xml`, extracts all rows, and
        constructs a xarray.Dataset indexed by height. The sounding_id is established.

        Returns
        -------
        xarray.Dataset
            Dataset containing radiosonde variables during radiosonde ascent.
        """

        df = pd.DataFrame(self.data)
        self.sounding_id = df["sounding_id"].iloc[0]

        df = df.drop(columns="sounding_id").set_index("p")

        ds = df.to_xarray().sortby("p", ascending=False)

        # ds['time'] = xr.apply_ufunc(
        #     pd.to_datetime,
        #     ds['time']
        # )

        return ds


class Radiosondes:
    """
    Represents a collection of Radiosonde observations.
    Responsible for scanning directories and instantiating Radiosonde objects.
    """

    def __init__(self, mwx_dir: str | Path):
        self.mwx_dir = mwx_dir

    def load_all(self) -> list[Radiosonde]:
        """Return list of Radiosonde objects for all .mwx files."""

        radiosonde_list = []

        for file in self.mwx_dir.glob("*.mwx"):
            rs = Radiosonde(filepath=file)
            rs.extract_mwx()
            radiosonde_list.append(rs)

        return radiosonde_list
    
    def iter_radiosondes(self):
        """
        Yield Radiosonde objects one by one.
        
        The advantage is that each radiosonde is loaded into memory only one time,
        instead of the entire list of radiosondes being loaded. This improves scalability
        of script.
        """
        
        for file in self.mwx_dir.glob("*.mwx"):
            yield Radiosonde(filepath=file)


class RadiosondesLevel0:
    """
    Initial radiosonde dataset.
    Produces a combined xarray dataset.
    Radiosondes are interpolated onto a common pressure grid from
    1000 hPa to 10 hPa.
    
    Produces radiosondes.level0.nc and std_plvl_radiosondes.level0.nc.
    """
    
    PRESSURE_GRID = np.arange(1000, 9, -1)
    
    def __init__(self, radiosondes: Radiosondes):
        
        self.radiosondes = radiosondes

        self.ptu_radiosonde_ds: xr.Dataset | None = None
        self.std_plvl_radiosonde_ds: xr.Dataset | None = None
    
    def build_ptu_radiosondes_lvl0(self) -> xr.Dataset:
        """Interpolate to 1000–10 hPa grid, harmonize coordinates."""
        
        ptu_radiosonde_ds_list = []
        
        for index, radiosonde in enumerate(self.radiosondes.iter_radiosondes()):
            ptu_radiosonde_ds = PTURadiosonde(radiosonde).build_dataset()
            ptu_radiosonde_ds = ptu_radiosonde_ds.interp(p=self.PRESSURE_GRID)
            ptu_radiosonde_ds_list.append(ptu_radiosonde_ds)
        
        ptu_radiosonde_ds = xr.concat(
            ptu_radiosonde_ds_list, dim="sounding_num", join="outer"
        )

        self.ptu_radiosonde_ds = ptu_radiosonde_ds
        
        return ptu_radiosonde_ds        
            
    def build_std_plvl_radiosondes_lvl0(self) -> xr.Dataset:
        """
        Builds a dataset for standard pressure level radiosondes.

        Harmonizes coordinates and interpolates onto the common pressure grid.
        :return:
        """
        
        std_plvl_radiosonde_ds_list = []
    
        for index, radiosonde in enumerate(self.radiosondes.iter_radiosondes()):
            std_plvl_radiosonde_ds = StdPressureRadiosonde(radiosonde).build_dataset()
            std_plvl_radiosonde_ds_list.append(std_plvl_radiosonde_ds)
                
        std_plvl_radiosonde_ds = xr.concat(
            std_plvl_radiosonde_ds_list, dim="sounding_num", join="outer"
        )

        std_plvl_radiosonde_ds = std_plvl_radiosonde_ds.sortby(
            'p', ascending=False
        )

        self.std_plvl_radiosonde_ds = std_plvl_radiosonde_ds
        
        return std_plvl_radiosonde_ds


class RadiosondesLevel1:
    """
    Level 1 Processing of radiosonde dataset.

    Removes bad radiosondes and applies quality control.
    """

    BAD_SOUNDING_INDICES = [0, 10]

    def __init__(self, radiosondes_lvl0: RadiosondesLevel0):
        """

        :param radiosondes_lvl0:
        """

        self.radiosondes_lvl0 = radiosondes_lvl0

        self.ptu_radiosonde_ds: xr.Dataset | None = None
        self.std_plvl_radiosonde_ds: xr.Dataset | None = None

    def build_ptu_radiosondes_lvl1(self):
        """
        Constructs the level 1 dataset.

        Removes the bad radiosondes from the dataset.
        :return:
        """

        # Drop bad radiosondes
        ptu_radiosonde_ds = self.radiosondes_lvl0.ptu_radiosonde_ds.drop_isel(
            sounding_num=self.BAD_SOUNDING_INDICES
        )

        ptu_radiosonde_ds['rh'] = ptu_radiosonde_ds['rh'].where(
            (ptu_radiosonde_ds['rh'] >= 0) &
            (ptu_radiosonde_ds['rh'] <= 1.1),
            np.nan
        )

        ptu_radiosonde_ds = ptu_radiosonde_ds.assign_coords(
            launch_time=(
                'sounding_num', ptu_radiosonde_ds['time'].isel(p=0).data
            )
        )

        self.ptu_radiosonde_ds = ptu_radiosonde_ds

        return ptu_radiosonde_ds

    def build_std_plvl_radiosondes_lvl1(self):
        """
        Construct level 1 dataset on standard pressure levels.

        Removes bad radiosondes from the dataset.
        :return:
        """

        std_plvl_radiosonde_ds = self.radiosondes_lvl0.std_plvl_radiosonde_ds.drop_isel(
            sounding_num=self.BAD_SOUNDING_INDICES
        )

        std_plvl_radiosonde_ds['rh'] = std_plvl_radiosonde_ds['rh'].where(
            (std_plvl_radiosonde_ds['rh'] >= 0) &
            (std_plvl_radiosonde_ds['rh'] <= 1.1),
            np.nan
        )

        std_plvl_radiosonde_ds = std_plvl_radiosonde_ds.assign_coords(
            launch_time=(
                'sounding_num', std_plvl_radiosonde_ds['time'].isel(p=0).data
            )
        )

        self.std_plvl_radiosonde_ds = std_plvl_radiosonde_ds

        return std_plvl_radiosonde_ds


class RadiosondesLevel2:

    def __init__(self, radiosondes_lvl1: RadiosondesLevel1):

        self.radiosondes_lvl1 = radiosondes_lvl1

        self.ptu_radiosonde_ds: xr.Dataset | None = None
        self.std_plvl_radiosonde_ds: xr.Dataset | None = None

    def build_ptu_radiosondes_lvl2(self):
        """
        Constructs the level 2 dataset.

        Perform relevant calculations.
        :return:
        """

        # Perform calculations
        self.ptu_radiosonde_ds = utils.CalcUtils.calculate_td_from_rh(self.radiosondes_lvl1.ptu_radiosonde_ds)

        # self.ptu_radiosonde_ds = utils.CalcUtils.calculate_cape(self.ptu_radiosonde_ds)
        # self.ptu_radiosonde_ds = utils.CalcUtils.calculate_tt_index(self.ptu_radiosonde_ds)
        # self.ptu_radiosonde_ds = utils.CalcUtils.calculate_k_index(self.ptu_radiosonde_ds)
        # self.ptu_radiosonde_ds = utils.CalcUtils.calculate_li(self.ptu_radiosonde_ds)

        return self.ptu_radiosonde_ds

    def build_std_plvl_radiosondes_lvl2(self):
        """
        Construct level 1 dataset on standard pressure levels.

        Removes bad radiosondes from the dataset.
        :return:
        """

        # Perform calculations
        self.std_plvl_radiosonde_ds = utils.CalcUtils.calculate_td_from_rh(self.radiosondes_lvl1.std_plvl_radiosonde_ds)

        # self.std_plvl_radiosonde_ds = utils.CalcUtils.calculate_cape(self.std_plvl_radiosonde_ds)
        # self.std_plvl_radiosonde_ds = utils.CalcUtils.calculate_tt_index(self.std_plvl_radiosonde_ds)
        # self.std_plvl_radiosonde_ds = utils.CalcUtils.calculate_k_index(self.std_plvl_radiosonde_ds)
        # self.std_plvl_radiosonde_ds = utils.CalcUtils.calculate_li(self.std_plvl_radiosonde_ds)

        return self.std_plvl_radiosonde_ds


# class Radiosonde:
#     """
#     Prepare and process a single radiosonde dataset from MWX-format input.
#
#     This class extracts XML files contained within a `.mwx` archive and
#     constructs NETCDF‑compliant datasets containing radiosonde measurements.
#     """
#
#     def __init__(
#         self,
#         filepath: str | Path,
#     ):
#         """
#         Initialize a Radiosonde instance.
#
#         Parameters
#         ----------
#         filepath : str
#
#         Notes
#         -----
#         The constructor also defines default output filenames for processed
#         NETCDF files.
#         """
#         self.filepath = Path(filepath)
#         self.extraction_dir = utils.FileManagement.XML_DIR / self.filepath.stem
#         self.extraction_dir.mkdir(exist_ok="True")
#
#     def extract_mwx(self) -> None:
#         """
#         Extract XML files from the `.mwx` archive.
#
#         The `.mwx` file is treated as a ZIP archive. All contents are extracted
#         into the xml/ directory.
#
#         Returns
#         -------
#         None
#         """
#
#         with zipfile.ZipFile(self.filepath, "r") as z:
#             z.extractall(self.extraction_dir)
#
#         return None
#
#     def _get_tree_from_xml(self, xml_filename: str) -> ET:
#         """
#         Parse an XML file and return its element tree.
#
#         Parameters
#         ----------
#         xml_filename : str
#             Name of the XML file to parse. The file must exist inside the
#             extraction directory.
#
#         Returns
#         -------
#         xml.etree.ElementTree.ElementTree
#             Parsed XML element tree.
#         """
#
#         xml_filepath = self.extraction_dir / xml_filename
#         return ET.parse(xml_filepath)
#
#     def build_std_pressure_lvl_radiosonde(self) -> xr.Dataset:
#         """
#         Construct a dataset of radiosonde variables on standard pressure levels.
#
#         The method reads `StdPressureLevels.xml`, extracts all rows, and builds
#         an xarray dataset indexed by geometric height.
#
#         Returns
#         -------
#         xarray.Dataset
#             Dataset containing radiosonde variables on standard pressure levels.
#         """
#         root = self._get_tree_from_xml("StdPressureLevels.xml").getroot()
#
#         data = [
#             {
#                 "RadioRxTimePk": row.get("RadioRxTimePk"),
#                 "time": row.get("DataSrvTime"),
#                 "height": float(row.get("Height")),
#                 "p": float(row.get("PressurePk")),
#                 "h": float(row.get("Height")),
#                 "ta": float(row.get("Temperature")),
#                 "rh": float(row.get("Humidity")),
#                 "wdir": float(row.get("WindDirection")),
#                 "wspeed": float(row.get("WindSpeed")),
#             }
#             for row in root.findall("Row")
#         ]
#
#         df = pd.DataFrame(data)
#         df = df.set_index("height")
#
#         ds = df.to_xarray()
#         ds = ds.sortby("height")
#
#         return ds
#
#     def build_radiosonde_profile_ds(self) -> xr.Dataset:
#         """
#         Construct a radiosonde profile dataset from synchronized PTU.
#
#         This method reads `SynchronizedSoundingData.xml` and `StabilityIndex.xml`,
#         extracts all rows, and constructs an xarray dataset indexed by height.
#         Stability indices are merged into the same dataset under a shared
#         `sounding_id` dimension.
#
#         Stores the radiosonde data as a `.nc` file with the same name as the `.mwx` file.
#
#         Returns
#         -------
#         None
#         """
#         root_sounding_data = self._get_tree_from_xml("SynchronizedSoundingData.xml")
#
#         sounding_data = [
#             {
#                 "altitude": float(row.get("Altitude")),
#                 "height": float(row.get("Height")),
#                 "geometric_height": float(row.get("GeometricHeight")),
#                 "p": float(row.get("Pressure")),
#                 "ta": float(row.get("Temperature")),
#                 "rh": float(row.get("Humidity")),
#                 "wdir": float(row.get("WindDir")),
#                 "wspeed": float(row.get("WindSpeed")),
#                 "u": float(row.get("WindEast")),
#                 "v": float(row.get("WindNorth")),
#                 "lat": float(row.get("Latitude")),
#                 "lon": float(row.get("Longitude")),
#                 "sounding_id": row.get("SoundingIdPk"),
#                 "time": row.get("DataSrvTime"),
#             }
#             for row in root_sounding_data.findall("Row")
#         ]
#
#         sounding_df = pd.DataFrame(sounding_data)
#         sounding_id = sounding_df["sounding_id"].iloc[0]
#
#         sounding_df = sounding_df.drop(columns="sounding_id").set_index("p")
#
#         sounding_ds = sounding_df.to_xarray().sortby("p", ascending=False)
#
#         td = dewpoint_from_relative_humidity(
#             temperature=sounding_ds["ta"] * units.kelvin,
#             relative_humidity=sounding_ds["rh"] * units.percent,
#         )
#
#         td = td.data.to(units("kelvin"))
#
#         td = td.magnitude
#
#         sounding_ds["td"] = (sounding_ds["ta"].dims, td)
#
#         sounding_ds = utils.CalcUtils.calculate_k_index(sounding_ds)
#         sounding_ds = utils.CalcUtils.calculate_cape(sounding_ds)
#         sounding_ds = utils.CalcUtils.calculate_tt_index(sounding_ds)
#         sounding_ds = utils.CalcUtils.calculate_li(sounding_ds)
#
#         return sounding_ds
#
#     def build_radiosonde_stability_indices_ds(self):
#         """
#
#         :return:
#         """
#
#         root_stability_index = self._get_tree_from_xml("StabilityIndex.xml")
#
#         stability_index_data = [
#             {
#                 "indices": row.get("NamePk"),
#                 "value": row.get("Value"),
#                 "sounding_id": row.get("SoundingIdPk"),
#                 "time": row.get("DataSrvTime"),
#             }
#             for row in root_stability_index.findall("Row")
#         ]
#
#         stability_index_df = pd.DataFrame(stability_index_data)
#         sounding_id = stability_index_df["sounding_id"].iloc[0]
#
#         stability_index_df = stability_index_df.drop(columns="sounding_id").set_index(
#             "indices"
#         )
#
#         stability_index_df["value"] = pd.to_numeric(
#             stability_index_df["value"], errors="coerce"
#         )
#
#         stability_index_ds = stability_index_df.to_xarray()
#
#         return stability_index_ds
#
#
# class Radiosondes:
#     """
#     Process multiple radiosondes from a directory and generate a dataset containing all sondes.
#
#     This class builds on the Radiosonde method, this time extract `.mwx` files from a directory then
#     processing individual radiosondes and finally concatinating into a single dataset.
#     """
#
#     PRESSURE_GRID = np.arange(1000, 9, -1)
#
#     def __init__(
#         self,
#         mwx_dir: str | Path = utils.FileManagement.MWX_DIR,
#         profiles_filename: str = "sif.radiosondes.profiles.nc",
#         indices_filename: str = "sif.radiosondes.indices.nc",
#     ):
#         """
#         Initialise the radiosondes by providing a directory that contains the `.mwx` files.
#         :param mwx_dir: The directory containing .mwx files that are processed.
#         """
#
#         self.mwx_dir = mwx_dir
#         self.profiles_filename = profiles_filename
#         self.indices_filename = indices_filename
#
#     def build_sif_radiosonde_profiles_ds_lvl0(
#         self, save_to: str | Path = utils.FileManagement.NETCDF_DIR
#     ) -> xr.Dataset:
#         """
#         Constructs the level 0 dataset for radiosondes launched during SIF.
#
#         The level 0 dataset contains all radiosondes, interpolated on a common pressure grid. Faulty radiosondes
#         are not removed from this dataset.
#
#         Iterates through self.mwx_dir, builds each radiosonde profile, concatenates them and exports as a .nc file.
#         :param save_to: The directory in which to store the sif_radiosondes .nc file.
#         :return: None
#         """
#
#         rs_ds_list = []
#
#         for file in self.mwx_dir.glob("*.mwx"):
#             rs = Radiosonde(filepath=file)
#             rs.extract_mwx()
#             rs_ds = rs.build_radiosonde_profile_ds()
#
#             rs_ds = rs_ds.interp(p=self.PRESSURE_GRID)
#
#             rs_ds_list.append(rs_ds)
#
#         sif = xr.concat(rs_ds_list, dim="sounding_id", join="outer")
#         sif.to_netcdf(Path(save_to) / self.profiles_filename)
#
#         return sif
#
#     def build_sif_radiosonde_indices_ds(
#         self, save_to: str | Path = utils.FileManagement.XML_DIR
#     ):
#         """
#
#         :param save_to:
#         :return:
#         """
#
#         rs_ds_list = []
#
#         for file in self.mwx_dir.glob("*.mwx"):
#             rs = Radiosonde(filepath=file)
#             rs.extract_mwx()
#             rs_ds = rs.build_radiosonde_stability_indices_ds()
#
#             rs_ds_list.append(rs_ds)
#
#         sif = xr.concat(rs_ds_list, dim="sounding_id", join="outer")
#         sif.to_netcdf(Path(save_to) / self.indices_filename)
#
#         return None
