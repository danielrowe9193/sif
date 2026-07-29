# libraries

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from netCDF4 import Dataset

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
