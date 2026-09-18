# sif
_Stability Indices at Fehmarn_

# Reading Radiosondes
Radiosondes are prepared using the `radiosondes.py` module. Here, `.mwx` files are extracted to a given folder, and radiosondes are built using the different files available. In the end, a `.nc` file is built, which contains profile data and sounding indices for the given radiosonde.

# Plotting Radiosondes
Radiosondes variables can be plotted using the `plot.py` module. It reads the `.nc` file generated and allows for plots of the radiosonde.

# Example
A brief example of building the radiosonde and plotting is shown below:

```python
import utils

from plot import FehmarnRadiosondeProfilePlotter, FehmarnRadiosondeIndicesPlotter
from radiosondes import Radiosonde, Radiosondes

# Rename files so there are sorted by date.
utils.FileManagement.rename_mwx(utils.FileManagement.MWX_DIR)

# Read radiosondes and
radiosondes = Radiosondes().build_sif_radiosonde_profiles_ds()
print(radiosondes)

# Plot skew-t for each radiosonde
profile_plotter = FehmarnRadiosondeProfilePlotter(
    filepath="../../data/netcdf/sif.radiosondes.profiles.nc"
)
for sounding in radiosondes.sounding_id.values:
    profile_plotter.plot_skewt(sounding)

# Plot indices
plotter = FehmarnRadiosondeIndicesPlotter(
    filepath="../../data/netcdf/sif.radiosondes.profiles.nc"
)
plotter.plot_indices_over_time()
```

where the resulting skew-t diagrams and indices over time are stored in the `plots/` directory. 

# Data
A key component of SIF is the concatenated datasets created from the observations and model outputs. These concatenated
datasets follow a pipeline and increase in detail and complexity with each version. Each version serves a different
purpose and the documentation instructs how each dataset should be used.

## `LevelZero` Radiosonde Datasets
`LevelZero` radiosonde datasets represent the initial, harmonized, pressure indexed profiles derived from raw MWX radiosonde files.
It contains all physical measurements from the radiosonde, and all geospatial and temporal information for each measurement.
`LevelZero` radiosonde datasets contain no calculations and no quality control.

There are 2 main datasets under the `LevelZero` umbrella.

### PTU Dataset `sif.ptu_radiosondes.profiles.level0.nc`
This dataset contains high resolution radiosonde profiles, interpolated onto a 1000 hPa to 10 hPa grid (1 hPa intervals).

**Dimensions and Coordinates**

| Dimension     | Description                                     | Units |
|---------------|-------------------------------------------------|-------|
| `sounding_num` | Integer index identifying each radiosonde launch | None  |
| `p`           | Pressure coordinate, 991 levels (1000 → 10 hPa) | hPa   |

**Variables**

| Variable | Description | Units           |
|---------|-------------|-----------------|
| `altitude` | GPS altitude reported by the radiosonde | m               |
| `height` | Height above ground level | m               |
| `geometric_height` | Geopotential height | m               |
| `ta` | Air temperature | Kelvin          |
| `rh` | Relative humidity | %               |
| `wdir` | Wind direction | degrees         |
| `wspeed` | Wind speed | m/s             |
| `u` | Zonal wind component | m/s             |
| `v` | Meridional wind component | m/s             |
| `lat` | Latitude of measurement | degrees         |
| `lon` | Longitude of measurement | degrees         |
| `time` | Timestamp of measurement | ISO‑8601 string |

### Standard Pressure Level Dataset `sif.std_plvl_radiosondes.profiles.level0.nc`
This dataset contains radiosonde measurements at standard pressure levels, typically used for synoptic meteorology and model verification.

| Dimension     | Description                                      | Units |
|---------------|--------------------------------------------------|-------|
| `sounding_num` | Integer index identifying each radiosonde launch | None  |
| `p`           | Pressure coordinate, 14 levels (1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30)   | hPa   |

**Variables**

| Variable | Description | Units           |
|---------|-------------|-----------------|
| `RadioRxTime` | Time of radio reception | s or ISO‑8601   |
| `time` | Timestamp of measurement | ISO‑8601 string |
| `height` | Height at standard pressure level | m               |
| `ta` | Air temperature | Kelvin          |
| `rh` | Relative humidity | %               |
| `wdir` | Wind direction | degrees         |
| `wspeed` | Wind speed | m/s             |
| `lat` | Latitude | degrees         |
| `lon` | Longitude | degrees         |


## `LevelOne` Radiosonde Datasets
`LevelOne` radiosonde datasets represent the **quality‑controlled** version of the `LevelZero` radiosonde profiles.
During `LevelOne` processing, faulty/incomplete radiosondes are removed, basic quality control is applied, launch time metadata is added, while preserving
the same pressure grid as `LevelOne`. Hence, `LevelOne` is the cleaned analysis ready dataset. No calculations are included in the `LevelOne` datasets.

There are 2 main datasets under the `LevelOne` umbrella.

### PTU Dataset `sif.ptu_radiosondes.profiles.level1.nc`
This dataset contains high resolution radiosonde profiles, interpolated onto a 1000 hPa to 10 hPa grid (1 hPa intervals).

**Dimensions and Coordinates**

| Dimension      | Description                                      | Units |
|----------------|--------------------------------------------------|-------|
| `station`      | The station the radiosonde was launched from     | None  |
| `sounding_num` | Integer index identifying each radiosonde launch | None  |
| `p`            | Pressure coordinate, 991 levels (1000 → 10 hPa)  | hPa   |

**Variables**

| Variable | Description | Units           |
|---------|-------------|-----------------|
| `altitude` | GPS altitude reported by the radiosonde | m               |
| `height` | Height above ground level | m               |
| `geometric_height` | Geopotential height | m               |
| `ta` | Air temperature | Kelvin          |
| `rh` | Relative humidity | %               |
| `wdir` | Wind direction | degrees         |
| `wspeed` | Wind speed | m/s             |
| `u` | Zonal wind component | m/s             |
| `v` | Meridional wind component | m/s             |
| `lat` | Latitude of measurement | degrees         |
| `lon` | Longitude of measurement | degrees         |
| `time` | Timestamp of measurement | ISO‑8601 string |

### Standard Pressure Level Dataset `sif.std_plvl_radiosondes.profiles.level1.nc`
This dataset contains radiosonde measurements at standard pressure levels, typically used for synoptic meteorology and model verification.

| Dimension     | Description                                      | Units |
|---------------|--------------------------------------------------|-------|
| `station`      | The station the radiosonde was launched from     | None  |
| `sounding_num` | Integer index identifying each radiosonde launch | None  |
| `p`           | Pressure coordinate, 14 levels (1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30)   | hPa   |

**Variables**

| Variable | Description | Units           |
|---------|-------------|-----------------|
| `RadioRxTime` | Time of radio reception | s or ISO‑8601   |
| `time` | Timestamp of measurement | ISO‑8601 string |
| `height` | Height at standard pressure level | m               |
| `ta` | Air temperature | Kelvin          |
| `rh` | Relative humidity | %               |
| `wdir` | Wind direction | degrees         |
| `wspeed` | Wind speed | m/s             |
| `lat` | Latitude | degrees         |
| `lon` | Longitude | degrees         |


## `LevelTwo` Radiosonde Datasets
`LevelTwo` radiosonde datasets represent the fully processed and analysis‑ready version of the `LevelOne` radiosonde profiles.  
During `LevelTwo` processing, dewpoint temperature is computed, and a suite of thermodynamic stability indices is added. All indices are stored as per‑sounding variables
, while the pressure grid and QC filtering from `LevelOne` are preserved.  
`LevelTwo` datasets are used for meteorological diagnostics, convective analysis, and forecast verification.

There are 2 main datasets under the `LevelTwo` umbrella.

### PTU Dataset `sif.ptu_radiosondes.profiles.level2.nc`
This dataset contains high‑resolution radiosonde profiles (1000 hPa → 10 hPa, 1 hPa intervals), enriched with derived thermodynamic variables.

**Dimensions and Coordinates**

| Dimension      | Description                                      | Units |
|----------------|--------------------------------------------------|-------|
| `station`      | The station the radiosonde was launched from     | None  |
| `sounding_num` | Integer index identifying each radiosonde launch | None  |
| `p`            | Pressure coordinate, 991 levels (1000 → 10 hPa)  | hPa   |

**Variables**

#### Physical Variables (same as `LevelOne`)

| Variable | Description | Units |
|---------|-------------|-------|
| `altitude` | GPS altitude reported by the radiosonde | m |
| `height` | Height above ground level | m |
| `geometric_height` | Geopotential height | m |
| `ta` | Air temperature | Kelvin |
| `rh` | Relative humidity | % |
| `wdir` | Wind direction | degrees |
| `wspeed` | Wind speed | m/s |
| `u` | Zonal wind component | m/s |
| `v` | Meridional wind component | m/s |
| `lat` | Latitude of measurement | degrees |
| `lon` | Longitude of measurement | degrees |
| `time` | Timestamp of measurement | ISO‑8601 string |

#### Thermodynamic Variables (added in LevelTwo)

| Variable | Description | Units |
| --- | --- | --- |
| ``theta`` | Potential temperature | Kelvin |
| ``td`` | Dewpoint temperature | Kelvin |
| ``theta_w`` | Wet‑bulb potential temperature | Kelvin |

#### Derived Variables (added in `LevelTwo`)

| Variable | Description                           | Units |
| --- |---------------------------------------| --- |
| ``cape`` | Convective Available Potential Energy | J/kg |
| ``cin`` | Convective Inhibition                 | J/kg |
| ``tt_index`` | Total Totals Index                    | dimensionless |
| ``k_index`` | K‑Index                               | Kelvin |
| ``li`` | Lifted Index                          | Kelvin |
| ``si`` | Showalter Index                       | Kelvin |
| ``ri`` | Richardson Number (bulk)              | dimensionless |
| ``ji`` | Jet Index (custom diagnostic)         | dimensionless |
| ``pw`` | Precipitable water                    | kg/m² |
| ``weather_index`` | Weather State Index                   | integer code |

### Standard Pressure Level Dataset `sif.std_plvl_radiosondes.profiles.level2.nc`

This dataset contains radiosonde measurements at standard pressure levels, enriched with derived thermodynamic indices.

**Dimensions and Coordinates**

| Dimension      | Description                                      | Units |
|----------------|--------------------------------------------------|-------|
| `station`      | The station the radiosonde was launched from     | None  |
| `sounding_num` | Integer index identifying each radiosonde launch | None  |
| `p`            | Pressure coordinate, 14 levels (1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30) | hPa |

**Variables**

#### Physical Variables (same as `LevelOne`)

| Variable | Description | Units |
|---------|-------------|-------|
| `RadioRxTime` | Time of radio reception | s or ISO‑8601 |
| `time` | Timestamp of measurement | ISO‑8601 string |
| `height` | Height at standard pressure level | m |
| `ta` | Air temperature | Kelvin |
| `rh` | Relative humidity | % |
| `wdir` | Wind direction | degrees |
| `wspeed` | Wind speed | m/s |
| `lat` | Latitude | degrees |
| `lon` | Longitude | degrees |

#### Thermodynamic Variables (added in LevelTwo)

| Variable | Description | Units |
| --- | --- | --- |
| ``theta`` | Potential temperature | Kelvin |
| ``td`` | Dewpoint temperature | Kelvin |
| ``theta_w`` | Wet‑bulb potential temperature | Kelvin |

#### Derived Variables (added in `LevelTwo`)

| Variable | Description | Units |
| --- | --- | --- |
| ``cape`` | Convective Available Potential Energy | J/kg |
| ``cin`` | Convective Inhibition | J/kg |
| ``tt_index`` | Total Totals Index | dimensionless |
| ``k_index`` | K‑Index | Kelvin |
| ``li`` | Lifted Index | Kelvin |
| ``si`` | Showalter Index | Kelvin |
| ``ri`` | Richardson Number (bulk) | dimensionless |
| ``ji`` | Jet Index (custom diagnostic) | dimensionless |
| ``pw`` | Precipitable water | kg/m² |
| ``weather_index`` | Composite weather severity index | integer code |


> ## IFS Forecast Dataset Structure (Level‑0)

Level‑0 IFS forecast datasets represent the **raw, station‑based ECMWF forecast output**, preprocessed into a unified xarray structure.  
This dataset contains:

- Forecast fields for multiple surface and atmospheric variables  
- Vertical wind profiles on standard pressure levels  
- Soil‑layer variables (not important for SIF)
- Metadata describing forecast initialization and lead time  
- Four target weather stations used in the SIF campaign  

Level‑0 is the **first harmonized forecast dataset** before any derived calculations or quality control.

---

## What Level‑0 Represents

IFS Level‑0 is the **direct model output**, converted from GRIB to CF‑compliant NETCDF.  
It contains:

- All available forecast variables for each station  
- Multiple forecast lead times (`valid_time`)  
- Pressure‑level wind fields (`u`, `v`)  
- Soil‑layer variables (not important for SIF)
- Surface meteorological fields  
- Full ECMWF metadata (centre, edition, conventions, history)

This dataset is ideal for:

- Model verification against radiosondes  
- Time‑series analysis at fixed stations  
- Vertical wind profile comparison  
- Any workflow requiring raw forecast fields

---

## Dimensions

### **`valid_time`**
- Forecast timestamps  
- Length: 120 forecast steps  
- Represents the time at which the forecast is valid  
- Paired with:
  - `step` — forecast lead time (timedelta)  
  - `forecast_hour` — categorical forecast hour label  
  - `init_time` — model initialization time  

### **`station`**
- The four SIF campaign weather stations  
- Example values: `"Norderney"`, `"Schleswig"`, `"Fehmarn"`, `"Griefswald"`  
- Each station has associated metadata:
  - `latitude`, `longitude`  
  - `surface`  
  - `heightAboveGround`  
  - `entireAtmosphere`  
  - `mostUnstableParcel`  
  - `nominalTop`  
  - `meanSea`

### **`p`**
- Pressure levels for wind fields  
- Length: 14  
- Standard ECMWF pressure levels (e.g., 1000, 925, 850, …, 30 hPa)

---

## Variables

The dataset contains **43 forecast variables**, including:

### **Atmospheric Variables**
| Variable | Description | Units |
|---------|-------------|-------|
| `u` | Zonal wind at pressure levels | m/s |
| `v` | Meridional wind at pressure levels | m/s |
| `t` | Temperature | K |
| `q` | Specific humidity | kg/kg |

*(Variable names may differ depending on ECMWF parameter codes.)*

---

## Coordinates & Metadata

### **Forecast Metadata**
| Coordinate | Description |
|-----------|-------------|
| `valid_time` | Time the forecast is valid |
| `step` | Forecast lead time (timedelta) |
| `forecast_hour` | Label for forecast hour (e.g., `"12h"`, `"24h"`, `"48h"`) |
| `init_time` | Model initialization time |

### **Station Metadata**
| Field | Description |
|-------|-------------|
| `latitude`, `longitude` | Station location |
| `surface` | Surface height |
| `heightAboveGround` | Sensor height |
| `entireAtmosphere` | Full atmospheric column |
| `mostUnstableParcel` | Parcel used for CAPE/CIN |
| `nominalTop` | Model top |
| `meanSea` | Sea‑level reference |

---

## Summary Table

| Dataset | Dimensions | Vertical Resolution | Purpose |
|--------|------------|---------------------|---------|
| **IFS Level‑0** | valid_time × station × soilLayer × p | 14 pressure levels | Raw ECMWF forecast fields for verification & analysis |

---

> ## IFS Forecast Dataset Structure (Level‑1)

Level‑1 IFS forecast datasets represent the **first derived‑variable layer** built on top of the raw ECMWF IFS Level‑0 forecast fields.  
During Level‑1 processing:

- Thermodynamic stability indices are computed for each station and forecast time:
  - **CAPE** (Convective Available Potential Energy)  
  - **CIN** (Convective Inhibition)  
  - **TT‑index** (Total Totals Index)  
  - **K‑index**  
  - **LI** (Lifted Index)  
- Geopotential height fields are calculated from pressure and temperature fields  
- All original Level‑0 variables are preserved  
- The dataset remains fully CF‑compliant and station‑based  

Level‑1 is the **analysis‑ready forecast dataset**, suitable for convective diagnostics, model verification, and comparison with radiosonde‑derived Level‑2 datasets.

---

## What Level‑1 Represents

IFS Level‑1 is the **enhanced forecast dataset**, containing:

- All raw ECMWF forecast fields from Level‑0  
- Derived thermodynamic indices for each station and forecast time
- Geopotential height for each station and forecast time, and at each pressure level
- Pressure‑level wind fields (`u`, `v`)  
- Height fields on pressure levels  
- Full ECMWF metadata (centre, edition, conventions, history)

This dataset is ideal for:

- Convective environment analysis  
- Forecast skill evaluation  
- Comparing model‑derived indices with radiosonde‑derived indices  
- Time‑series analysis at fixed stations  
- Synoptic and mesoscale meteorological studies  

---

## Dimensions

### **`valid_time`**
- Forecast timestamps  
- Length: 120 forecast steps  
- Represents the time at which the forecast is valid  
- Paired with:
  - `step` — forecast lead time (timedelta)  
  - `forecast_hour` — categorical forecast hour label  
  - `init_time` — model initialization time  

### **`station`**
- The four SIF campaign weather stations  
- Example values: `"Norderney"`, `"Schleswig"`, `"Fehmarn"`, `"Griefswald"`  
- Each station has associated metadata:
  - `latitude`, `longitude`  
  - `surface`  
  - `heightAboveGround`  
  - `entireAtmosphere`  
  - `mostUnstableParcel`  
  - `nominalTop`  
  - `meanSea`

### **`p`**
- Pressure levels for wind and height fields  
- Length: 14  
- Standard ECMWF pressure levels (e.g., 1000, 925, 850, …, 30 hPa)

---

## Variables

The Level‑1 dataset contains **50 forecast variables**, including all Level‑0 fields plus derived indices.


### **Atmospheric Variables**
| Variable | Description                            | Units   |
|---------|----------------------------------------|---------|
| `u` | Zonal wind at pressure levels          | m/s     |
| `v` | Meridional wind at pressure levels     | m/s     |
| `height` | Geopotential Height at pressure levels | m^2/s^2 |
| `t` | Temperature                            | K       |
| `q` | Specific humidity                      | kg/kg   |

---

## Derived Thermodynamic Indices (Level‑1 Additions)

These variables are computed for each station and forecast time:

| Variable | Description | Units |
|---------|-------------|-------|
| `cape` | Convective Available Potential Energy | J/kg |
| `cin` | Convective Inhibition | J/kg |
| `tt_index` | Total Totals Index | dimensionless |
| `k_index` | K‑Index | °C |
| `li` | Lifted Index | °C |

These indices allow direct comparison with radiosonde Level‑2 stability indices.

---

## Coordinates & Metadata

### **Forecast Metadata**
| Coordinate | Description |
|-----------|-------------|
| `valid_time` | Time the forecast is valid |
| `step` | Forecast lead time (timedelta) |
| `forecast_hour` | Label for forecast hour (e.g., `"12h"`, `"24h"`, `"48h"`) |
| `init_time` | Model initialization time |

### **Station Metadata**
| Field | Description |
|-------|-------------|
| `latitude`, `longitude` | Station location |
| `surface` | Surface height |
| `heightAboveGround` | Sensor height |
| `entireAtmosphere` | Full atmospheric column |
| `mostUnstableParcel` | Parcel used for CAPE/CIN |
| `nominalTop` | Model top |
| `meanSea` | Sea‑level reference |

---

## Summary Table

| Dataset | Dimensions | Derived Variables | Purpose |
|--------|------------|-------------------|---------|
| **IFS Level‑1** | valid_time × station × soilLayer × p | CAPE, CIN, TT, K, LI | Convective diagnostics & model verification |

---





