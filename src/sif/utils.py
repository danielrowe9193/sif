import metpy.calc as mpcalc
import numpy as np
import xarray as xr

from metpy.units import units
from pathlib import Path


class CalcUtils:
    """Utilities for calculations during the experiment."""

    @staticmethod
    def calculate_cape(profile: xr.Dataset | xr.DataTree):
        """
        Calculate CAPE and CIN from a collection of soundings.

        Parameters
        ----------
        profile : xr.Dataset | xr.DataTree
            Dataset containing p, ta and td with dimensions
            (sounding_id, p).

        Returns
        -------
        xr.Dataset
            Original dataset with CAPE and CIN added as variables
            with dimension (sounding_id,).
        """

        p = profile["p"]
        t = profile["ta"]
        td = profile["td"]

        def cape_cin(p, t, td):
            p = p * units.hPa
            t = t * units.kelvin
            td = td * units.kelvin

            parcel = mpcalc.parcel_profile(p, t[0], td[0]).to("degC")

            cape, cin = mpcalc.cape_cin(p, t.to("degC"), td.to("degC"), parcel)

            return cape.magnitude, cin.magnitude

        cape, cin = xr.apply_ufunc(
            cape_cin,
            p,
            t,
            td,
            input_core_dims=[["p"], ["p"], ["p"]],
            output_core_dims=[[], []],
            vectorize=True,
            dask="parallelized",
            output_dtypes=[float, float],
        )

        profile["cape"] = cape
        profile["cin"] = cin

        return profile

    @staticmethod
    def calculate_k_index(profile: xr.Dataset | xr.DataTree):

        p = profile["p"]
        t = profile["ta"]
        td = profile["td"]

        def k_index(p, t, td):
            p = p * units.hPa
            t = t * units.kelvin
            td = td * units.kelvin

            return mpcalc.k_index(p, t, td).magnitude

        k = xr.apply_ufunc(
            k_index,
            p,
            t,
            td,
            input_core_dims=[["p"], ["p"], ["p"]],
            output_core_dims=[[]],
            vectorize=True,
            dask="parallelized",
            output_dtypes=[float],
        )

        profile["k_index"] = k

        return profile

    @staticmethod
    def calculate_tt_index(profile: xr.Dataset | xr.DataTree):
        p = profile["p"]
        t = profile["ta"]
        td = profile["td"]

        def tt_index(p, t, td):
            p = p * units.hPa
            t = t * units.kelvin
            td = td * units.kelvin

            return mpcalc.total_totals_index(p, t, td).magnitude

        tt = xr.apply_ufunc(
            tt_index,
            p,
            t,
            td,
            input_core_dims=[["p"], ["p"], ["p"]],
            output_core_dims=[[]],
            vectorize=True,
            dask="parallelized",
            output_dtypes=[float],
        )

        profile["tt_index"] = tt

        return profile

    @staticmethod
    def calculate_li(profile: xr.Dataset | xr.DataTree):
        p = profile.p.values
        t = profile.ta.values
        td = profile.td.values
        h = profile.height.values

        def li(p, t, td, h):
            # Attach units
            p = p * units.hPa
            t = t * units.kelvin
            td = td * units.kelvin
            h = h * units.m

            # Convert temperature to Celsius
            t = t.to("degC")
            td = td.to("degC")

            # Calculate 500-m mixed parcel
            parcel_p, parcel_t, parcel_td = mpcalc.mixed_parcel(
                p, t, td, depth=500 * units.m, height=h
            )

            # Select levels above the mixed layer
            above = h > 500 * units.m

            # Replace lowest 500 m with mixed values
            press = np.concatenate([[parcel_p], p[above]])

            temp = np.concatenate([[parcel_t], t[above]])

            # Calculate parcel profile
            mixed_prof = mpcalc.parcel_profile(press, parcel_t, parcel_td)

            # Calculate Lifted Index
            li = mpcalc.lifted_index(press, temp, mixed_prof)

            return li.magnitude

        li = xr.apply_ufunc(
            li,
            p,
            t,
            td,
            h,
            input_core_dims=[["p"], ["p"], ["p"], ["p"]],
            output_core_dims=[[]],
            vectorize=True,
            output_dtypes=[float],
        )

        profile["li"] = li

        return profile


class PlotUtils:
    """Utilities for plotting measurements taken during the experiment."""

    ...


class FileManagement:
    """Utilities for handling files gathered during the experiment."""

    PACKAGE_DIR = Path(__file__).resolve().parent
    PROJECT_DIR = PACKAGE_DIR.parent.parent

    DATA_DIR = PROJECT_DIR / "data/"
    PLOT_DIR = PROJECT_DIR / "plots/"

    MWX_DIR = DATA_DIR / "mwx"
    XML_DIR = DATA_DIR / "xml"
    IGRA_DIR = DATA_DIR / "igra"
    IFS_DIR = DATA_DIR / "ifs"
    ICON_DIR = DATA_DIR / "icon"
    GFS_DIR = DATA_DIR / "gfs"
    NETCDF_DIR = DATA_DIR / "netcdf"
    ZIP_DIR = DATA_DIR / "zip"

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

        ds = xr.open_dataset(filename_or_obj=path_to_data)

        print(
            f"Summary of {path_to_data.stem}.nc:\n"
            f"{ds}\n"
            f"{ds.dims}\n"
            f"{ds.coords}\n"
            f"{ds.data_vars}"
        )

        return None

    @staticmethod
    def rename_mwx(path_to_data: str | Path = MWX_DIR) -> None:
        """
        Rename all `.mwx` files in a directory so that each filename begins
        with its date and time stamp.

        This function is idempotent: running it multiple times will not
        modify files that already follow the `{YYYYMMDD_HHMMSS}_rest.mwx`
        naming convention. Filenames that do not match either the original
        pattern or the target pattern are skipped safely.

        Parameters
        ----------
        path_to_data : str or pathlib.Path, optional
            Path to the directory containing `.mwx` files. Defaults to
            `MWX_DIR`.

        Returns
        -------
        None
            This function performs in-place renaming and does not return
            a value.

        Notes
        -----
        The function expects filenames to end with a date and time stamp
        in the form `YYYYMMDD_HHMMSS`. These components are moved to the
        front of the filename to ensure consistent chronological sorting.
        Files that already begin with an 8-digit date are left unchanged.
        """

        data_dir = Path(path_to_data)

        for file in data_dir.glob("*.mwx"):
            stem = file.stem
            parts = stem.split("_")

            # Case 1: filename already starts with a date (YYYYMMDD)
            #         → do nothing
            if len(parts[0]) == 8 and parts[0].isdigit():
                print(f"Skipping (already renamed): {file.name}")
                continue

            # Case 2: filename ends with date + time → move them to the front
            # Example: Westermarkelsdorf_RS92_20260811_114920.mwx
            if len(parts[-2]) == 8 and parts[-2].isdigit() and len(parts[-1]) == 6 and parts[-1].isdigit():
                date = parts[-2] + "_" + parts[-1]
                rest = "_".join(parts[:-2])
                new_name = f"{date}_{rest}{file.suffix}"
                file.rename(file.with_name(new_name))
                print(f"Renamed: {file.name} → {new_name}")
                continue

            # If neither pattern matches, skip safely
            print(f"Skipping (unrecognized pattern): {file.name}")

            return None
