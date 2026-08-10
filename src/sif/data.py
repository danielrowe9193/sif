import numpy as np
import xml.etree.ElementTree as ET
import zipfile

from netCDF4 import Dataset
from pathlib import Path


class Radiosonde:
    """
    Object preparing a singular radiosonde from .mwx data.
    """

    def __init__(self, storage_dir: str | Path, filename: str):
        """
        Provide storage directory and filename for raw radiosonde data.
        :param storage_dir: The directory in which the raw radiosonde data is stored.
        :param filename: The filename of the raw radiosonde data. Expects the extension to be included.
        """

        self.storage_dir = Path(storage_dir)
        self.filename = filename
        self.filepath = self.storage_dir / self.filename

        self.filename_nc = 'clean.nc'
        self.filepath_nc = self.storage_dir / self.filename_nc

    def extract_mwx(self, mwx_filepath: str | Path, xml_file_name: str) -> Path:
        """
        Extracts .xml from a given .mwx file and stores it at a given output directory
        :param mwx_filepath: The filepath on which the .mwx file is stored.
        :param xml_file_name: The name of the .xml file, including the extension.
        :return: Filepath of .xml extracted from  .mwx file.
        """

        with zipfile.ZipFile(mwx_filepath, 'r') as z:
            z.extractall(self.storage_dir)

        return self.storage_dir / xml_file_name

    @staticmethod
    def print_tree(element, level=0):
        print("    " * level + element.tag)
        for child in element:
            print_tree(child, level + 1)


# find the path file to data folder
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data/raw"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# data file name
filename = "RS_TestData_Westermarkelsdorf_20220825_131825.mwx"
mwx_file = DATA_DIR / filename

nc_file = "clean.nc"

# path for output
output_path = BASE_DIR / "data" / "temp"
output_path.mkdir(parents=True, exist_ok=True)

output_file = output_path / nc_file

# unzip mwx
def extract_mwx(mwx, output):
    with zipfile.ZipFile(mwx, 'r') as z:
        z.extractall(output)

# look at XML 
def print_tree(element, level=0):
    print("    "*level + element.tag)
    for child in element:
        print_tree(child, level+1)

# find tags automatically
def find_tags(element, tags=None):
    if tags is None:
        tags = set()
    tags.add(element.tag)

    for child in element:
        find_tags(child, tags)

    return tags

# create netcdf file
def make_netcdf(tags, nc_file):
    nc = Dataset("output.nc","w",format="NETCDF4")
    nc.createDimension("level",len(altitude))
    #make variables
    z = nc.createVariable(
        "altitude",
        "f4",
        ("level",)
    )

    p = nc.createVariable(
        "pressure",
        "f4",
        ("level",)
    )

    t = nc.createVariable(
        "temperature",
        "f4",
        ("level",)
    )

    rh = nc.createVariable(
        "humidity",
        "f4",
        ("level",)
    )

    # write data

    z[:] = altitude
    p[:] = pressure
    t[:] = temperature
    rh[:] = humidity

    # write metadata
    z.units = "m"
    p.units = "hPa"
    t.units = "degC"
    rh.units = "%"

    # nc.title = "Converted data"

    nc.close()
    print(f"Saved {nc_file}")

def convert(file):
    pass

def main():
    extract_mwx(mwx_file, output_path)
    xml_file = output_path / "StabilityIndex.xml"

    tree = ET.parse(xml_file)
    root = tree.getroot()

    print_tree(root)
    
    # tags = find_tags(root)

    # print("Tags found:")
    # for tag in sorted(tags):
    #     print(tag)


if __name__ == "__main__":
    main()
