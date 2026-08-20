import numpy as np
import xarray as xr

from src.sif.utils.config import Constants
from pathlib import Path
from src.sif.utils.utils import CalcUtils, FileManagement

xr.set_options(use_new_combine_kwarg_defaults=True)

# The four weather stations of focus during SIF.
stations = Constants.STATIONS


class IFSLevelZero:
    """
    Build Level‑0 IFS radiosonde forecast datasets.

    This class collects raw IFS forecast files, loads them into xarray
    datasets, applies basic preprocessing (sorting, coordinate assignment,
    renaming), and concatenates them into a single Level‑0 dataset.
    """

    def __init__(self):
        """
        Initialize an IFSLevelZero instance.
        """
        self.data_dir = FileManagement.IFS_DIR

        self._ifs_path_list = []
        self._ifs_ds_list = []

        self.dataset: None | xr.Dataset = None
        self.dataset_filepath = (
            FileManagement.IFS_DIR / "ifs.radiosondes.profiles.level0.nc"
        )

    def collect_fc_file_paths(self) -> None:
        """
        Collect file paths for all IFS forecast files.

        The method searches the IFS directory for subdirectories matching
        `2026-08*` and collects all files beginning with `ALL*`.

        Returns
        -------
        None
        """
        for ifs_dir in self.data_dir.glob("2026-08*"):
            for fc_data in ifs_dir.glob("ALL*"):
                self._ifs_path_list.append(fc_data)

        return None

    def build_ifs_level_zero_ds(self) -> None:
        """
        Build the Level‑0 IFS dataset.

        This method loads each collected forecast file, sorts by `valid_time`,
        assigns forecast-hour coordinates (`12h`, `24h`, `48h`), computes the
        initialization time, renames key variables, and stores each processed
        dataset. Finally, all datasets are concatenated along the `valid_time`
        dimension.

        Returns
        -------
        None
        """
        for fc_data_path in sorted(self._ifs_path_list):
            ifs_ds = xr.open_dataset(fc_data_path)
            ifs_ds = ifs_ds.sortby("valid_time")

            # Assign forecast-hour coordinate
            ifs_ds = ifs_ds.assign_coords(
                forecast_hour=("valid_time", ["12h", "24h", "48h"])
            )

            # Compute initialization time
            init_time = ifs_ds.sel(
                forecast_hour="12h"
            ).valid_time.values - np.timedelta64(12, "h")

            ifs_ds = ifs_ds.assign_coords(
                init_time=("valid_time", [init_time, init_time, init_time])
            )

            # Rename variables
            ifs_ds = ifs_ds.rename(
                {
                    "isobaricInhPa": "p",
                    "t": "ta",
                }
            )

            self._ifs_ds_list.append(ifs_ds)

        self.dataset = xr.concat(self._ifs_ds_list, dim="valid_time")

        return None

    def export_ifs_level_zero_ds(self) -> None:
        """
        Export the Level‑0 dataset to NETCDF.

        Returns
        -------
        None
        """
        self.dataset.to_netcdf(self.dataset_filepath)
        return None


class IFSLevelOne:
    """
    Build Level‑1 IFS radiosonde forecast datasets.

    Level‑1 processing applies derived thermodynamic indices (CAPE, K‑index,
    TT‑index, Lifted Index) to the Level‑0 dataset and exports the result.
    """

    def __init__(self, ifs_level_zero: IFSLevelZero):
        """
        Initialize an IFSLevelOne instance.

        Parameters
        ----------
        ifs_level_zero : IFSLevelZero
            A fully initialized Level‑ 0 processor.

        Notes
        -----
        The Level‑ 0 dataset is loaded from disk and stored as `self.dataset`.
        """
        self.ifs_level_zero = ifs_level_zero

        self.dataset = xr.open_dataset(self.ifs_level_zero.dataset_filepath)
        self.dataset_filepath = (
            FileManagement.IFS_DIR / "ifs.radiosondes.profiles.level1.nc"
        )

    def build_ifs_level_one_ds(self) -> None:
        """
        Compute Level‑1 thermodynamic indices.

        This method applies several derived meteorological indices to the
        Level‑0 dataset:

        - Dewpoint Temperature
        - CAPE (Convective Available Potential Energy)
        - K‑index
        - TT‑index (Total Totals)
        - Lifted Index (LI)

        All calculations are delegated to `CalcUtils`.

        Returns
        -------
        None
        """
        self.dataset = CalcUtils.calculate_td_from_q(self.dataset)
        self.dataset = CalcUtils.calculate_height_from_geopotential(self.dataset)
        self.dataset = CalcUtils.calculate_cape(self.dataset)
        self.dataset = CalcUtils.calculate_k_index(self.dataset)
        self.dataset = CalcUtils.calculate_tt_index(self.dataset)
        self.dataset = CalcUtils.calculate_li(self.dataset)

        return None

    def export_ifs_level_one_ds(self) -> None:
        """
        Export the Level‑1 dataset to NETCDF.

        Returns
        -------
        None
        """
        self.dataset.to_netcdf(self.dataset_filepath)
        return None
