import radiosondes
import pandas as pd

test_radiosonde = radiosondes.Radiosonde(
    storage_dir="../../data/",
    filename="RS_TestData_Westermarkelsdorf_20220825_131825.mwx",
    extract_to="../../data/test_extract/"
)
test_radiosonde.extract_mwx()

root = test_radiosonde.get_tree_from_xml("RawPtu.xml").getroot()

data = [
    {
        "RadioRxTimePk": float(row.get("RadioRxTimePk")),
        "time": row.get("DataSrvTime"),
        "p": float(row.get("Pressure")),
        "t": float(row.get("Temperature")),
        "rh1": float(row.get("Humidity1")),
        "rh2": float(row.get("Humidity2"))
    }
    for row in root.findall("Row")
]

df = pd.DataFrame(data)
print(df.head())
