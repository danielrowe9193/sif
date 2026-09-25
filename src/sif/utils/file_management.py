import xarray as xr

from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent.parent.parent

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
        if (
            len(parts[-2]) == 8
            and parts[-2].isdigit()
            and len(parts[-1]) == 6
            and parts[-1].isdigit()
        ):
            date = parts[-2] + "_" + parts[-1]
            rest = "_".join(parts[:-2])
            new_name = f"{date}_{rest}{file.suffix}"
            file.rename(file.with_name(new_name))
            print(f"Renamed: {file.name} → {new_name}")
            continue

        # If neither pattern matches, skip safely
        print(f"Skipping (unrecognized pattern): {file.name}")

        return None