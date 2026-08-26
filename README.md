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
A key component of SIF is the concatenated datasets created from the observations and model outputs.

---
> ## Radiosonde Dataset Structure (Level‑0)

Level‑0 radiosonde datasets represent the **initial, harmonized, pressure‑indexed profiles** derived from raw MWX radiosonde files.  
All radiosondes are interpolated onto a **common pressure grid** ranging from **1000 hPa → 10 hPa**, enabling consistent vertical comparison across soundings.

Two datasets are produced:

- **PTU dataset** (`sif.ptu_radiosondes.profiles.level0.nc`)  
- **Standard Pressure Level dataset** (`sif.std_plvl_radiosondes.profiles.level0.nc`)

Both share the same conceptual structure but differ in origin and vertical resolution.

---

## What Level‑0 Represents

Level‑0 is the **first unified dataset** after extraction and interpolation.  
It contains:

- All physical measurements from the radiosonde (temperature, humidity, wind, etc.)  
- All geolocation information (latitude, longitude)  
- Time stamps for each measurement  
- A consistent pressure coordinate  
- One dimension per sounding  

Level‑0 does **not** include derived thermodynamic indices (CAPE, LI, TT, K‑index).

---

# Dimensions

### **`sounding_num`**
- Integer index identifying each radiosonde launch  
- Dimension length = number of radiosondes (e.g., 16)  
- No physical meaning; simply enumerates soundings

### **`p`**
- Pressure coordinate  
- Units: **hPa**  
- PTU dataset: 991 levels (1000 → 10 hPa)  
- STD‑PLVL dataset: 14 standard pressure levels  
- Used as the vertical axis for all variables

---

# PTU Dataset (`sif.ptu_radiosondes.profiles.level0.nc`)

This dataset contains **high‑resolution radiosonde profiles** interpolated onto the 1000–10 hPa grid.

### **Dimensions**
```
sounding_num: 16
p: 991
```

### **Coordinates**
- **p** — pressure levels (1000 → 10 hPa)

### **Variables**

| Variable | Description | Units |
|---------|-------------|-------|
| `altitude` | GPS altitude reported by the radiosonde | m |
| `height` | Height above ground level | m |
| `geometric_height` | Geopotential height | m |
| `ta` | Air temperature | °C |
| `rh` | Relative humidity | % |
| `wdir` | Wind direction | degrees |
| `wspeed` | Wind speed | m/s |
| `u` | Zonal wind component | m/s |
| `v` | Meridional wind component | m/s |
| `lat` | Latitude of measurement | degrees |
| `lon` | Longitude of measurement | degrees |
| `time` | Timestamp of measurement | ISO‑8601 string |

### **Purpose**
The PTU dataset provides **full‑resolution vertical profiles** suitable for:

- Thermodynamic calculations (CAPE, LI, TT, K‑index)  
- Vertical interpolation  
- Plotting skew‑T diagrams  
- Wind profile analysis  
- Radiosonde trajectory reconstruction  

---

# Standard Pressure Level Dataset (`sif.std_plvl_radiosondes.profiles.level0.nc`)

This dataset contains radiosonde measurements at **standard pressure levels**, typically used for synoptic meteorology and model verification.

### **Dimensions**
```
sounding_num: 16
p: 14
```

### **Coordinates**
- **p** — standard pressure levels  
  (1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30 hPa)

### **Variables**

| Variable | Description | Units |
|---------|-------------|-------|
| `RadioRxTime` | Time of radio reception | s or ISO‑8601 |
| `time` | Timestamp of measurement | ISO‑8601 string |
| `height` | Height at standard pressure level | m |
| `ta` | Air temperature | °C |
| `rh` | Relative humidity | % |
| `wdir` | Wind direction | degrees |
| `wspeed` | Wind speed | m/s |
| `lat` | Latitude | degrees |
| `lon` | Longitude | degrees |

### **Purpose**
The STD‑PLVL dataset is ideal for:

- Synoptic‑scale analysis  
- Model verification at standard pressure levels  
- Quick comparison between soundings  
- Climatological summaries  

---

# 🧩 Summary Table

| Dataset | Vertical Resolution | Source | Purpose |
|--------|---------------------|--------|---------|
| **PTU** | 991 levels (1000 → 10 hPa) | SynchronizedSoundingData.xml | High‑resolution thermodynamic and wind profiles |
| **STD‑PLVL** | 14 standard levels | StdPressureLevels.xml | Synoptic analysis, model verification |

---

> ## Radiosonde Dataset Structure (Level‑1)

Level‑1 radiosonde datasets represent the **quality‑controlled** version of the Level‑0 radiosonde profiles.  
During Level‑1 processing:

- Faulty or incomplete radiosondes are **removed**  
- Basic **quality control** is applied  
- Launch‑time metadata is added  
- The dataset is preserved on the same pressure grid as Level‑0  

Level‑1 is therefore the **cleaned, analysis‑ready** dataset.

Two datasets are produced:

- **PTU dataset** (`sif.ptu_radiosondes.profiles.level1.nc`)  
- **Standard Pressure Level dataset** (`sif.std_plvl_radiosondes.profiles.level1.nc`)  

Both share the same conceptual structure as Level‑0, but with fewer soundings and additional metadata.

---

## 🧭 What Level‑1 Represents

Level‑1 is the **post‑QC dataset**.  
It contains:

- All physical radiosonde measurements  
- Launch‑time metadata for each sounding  
- Only soundings that pass QC checks  
- A consistent pressure coordinate  
- No derived thermodynamic indices (those appear in Level‑2)

Level‑1 is ideal for:

- Statistical analysis  
- Vertical profile comparison  
- Model verification  
- Any workflow requiring clean, reliable radiosonde data  

---

## Dimensions

### **`sounding_num`**
- Integer index identifying each radiosonde launch  
- Dimension length is **smaller than Level‑0** (e.g., 14 instead of 16)  
- Soundings removed due to QC do not appear here

### **`p`**
- Pressure coordinate  
- Units: **hPa**  
- PTU dataset: 991 levels (1000 → 10 hPa)  
- STD‑PLVL dataset: 14 standard pressure levels  
- Used as the vertical axis for all variables

---

## New Metadata in Level‑1

### **`launch_time`**
- One timestamp per sounding  
- Represents the radiosonde launch time  
- Useful for grouping, filtering, and time‑series analysis  
- Stored as a coordinate on `sounding_num`

---

## PTU Dataset (`sif.ptu_radiosondes.profiles.level1.nc`)

This dataset contains **high‑resolution radiosonde profiles** after QC filtering.

### **Dimensions**
```
sounding_num: 14
p: 991
```

### **Coordinates**
- **launch_time** — timestamp of each radiosonde launch  
- **p** — pressure levels (1000 → 10 hPa)

### **Variables**

| Variable | Description | Units |
|---------|-------------|-------|
| `altitude` | GPS altitude | m |
| `height` | Height above ground level | m |
| `geometric_height` | Geopotential height | m |
| `ta` | Air temperature | °C |
| `rh` | Relative humidity | % |
| `wdir` | Wind direction | degrees |
| `wspeed` | Wind speed | m/s |
| `u` | Zonal wind component | m/s |
| `v` | Meridional wind component | m/s |
| `lat` | Latitude | degrees |
| `lon` | Longitude | degrees |
| `time` | Timestamp of measurement | ISO‑8601 string |

### **Purpose**
The Level‑1 PTU dataset is used for:

- Clean vertical profile analysis  
- Thermodynamic calculations (performed in Level‑2)  
- Wind profile diagnostics  
- Launch‑time‑based filtering and grouping  

---

## Standard Pressure Level Dataset (`sif.std_plvl_radiosondes.profiles.level1.nc`)

This dataset contains radiosonde measurements at **standard pressure levels**, after QC filtering.

### **Dimensions**
```
sounding_num: 14
p: 14
```

### **Coordinates**
- **launch_time** — timestamp of each radiosonde launch  
- **p** — standard pressure levels  
  (1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30 hPa)

### **Variables**

| Variable | Description | Units |
|---------|-------------|-------|
| `RadioRxTime` | Time of radio reception | s or ISO‑8601 |
| `time` | Timestamp of measurement | ISO‑8601 string |
| `height` | Height at standard pressure level | m |
| `ta` | Air temperature | °C |
| `rh` | Relative humidity | % |
| `wdir` | Wind direction | degrees |
| `wspeed` | Wind speed | m/s |
| `lat` | Latitude | degrees |
| `lon` | Longitude | degrees |

### **Purpose**
The Level‑1 STD‑PLVL dataset is ideal for:

- Synoptic‑scale analysis  
- Model verification at standard pressure levels  
- Climatological summaries  
- Quick comparison between soundings  

---

# 🧩 Summary Table

| Dataset | Vertical Resolution | QC Applied | Purpose |
|--------|---------------------|------------|---------|
| **PTU (Level‑1)** | 991 levels | Yes | High‑resolution, cleaned profiles |
| **STD‑PLVL (Level‑1)** | 14 levels | Yes | Synoptic analysis, model verification |

---

> ## Radiosonde Dataset Structure (Level‑2)

Level‑2 radiosonde datasets represent the **fully processed**, **derived‑variable‑enhanced**, and **analysis‑ready** radiosonde profiles.  
During Level‑2 processing:

- Dewpoint temperature (`td`) is computed from temperature and relative humidity  
- Thermodynamic stability indices are calculated:
  - **CAPE** (Convective Available Potential Energy)  
  - **CIN** (Convective Inhibition)  
  - **TT‑index** (Total Totals Index)  
  - **K‑index**  
  - **LI** (Lifted Index)  
- All indices are stored as **per‑sounding** variables  
- The dataset retains the same pressure grid and QC filtering from Level‑1  

Level‑2 is the dataset used for **meteorological diagnostics** and **forecast verification**

Two datasets are produced:

- **PTU dataset** (`sif.ptu_radiosondes.profiles.level2.nc`)  
- **Standard Pressure Level dataset** (`sif.std_plvl_radiosondes.profiles.level2.nc`)  

---

## What Level‑2 Represents

The Level‑2 dataset contains:

- All cleaned physical radiosonde measurements  
- Launch‑time metadata  
- Dewpoint temperature  
- Full suite of stability indices  
- A consistent pressure coordinate  
- Only soundings that passed Level‑1 QC  

Level‑2 is ideal for:

- Forecast model verification    
- Climatological studies  
- Any workflow requiring derived thermodynamic variables  

---

## Dimensions

### **`sounding_num`**
- Integer index identifying each radiosonde launch  
- Same number of soundings as Level‑1 (e.g., 14)  
- Each sounding has associated stability indices

### **`p`**
- Pressure coordinate  
- Units: **hPa**  
- PTU dataset: 991 levels (1000 → 10 hPa)  
- STD‑PLVL dataset: 14 standard pressure levels  
- Used as the vertical axis for all profile variables

---

## Metadata

### **`launch_time`**
- Timestamp of each radiosonde launch  
- Stored as a coordinate on `sounding_num`  
- Useful for time‑series analysis, grouping, and filtering

---

## PTU Dataset (`radiosondes.level2.nc`)

This dataset contains **high‑resolution radiosonde profiles** with **derived thermodynamic variables**.

### **Dimensions**
```
sounding_num: 14
p: 991
```

### **Coordinates**
- **sounding_num** — radiosonde identifier  
- **launch_time** — timestamp of each radiosonde launch  
- **p** — pressure levels (1000 → 10 hPa)

### **Variables**

#### **Physical variables (same as Level‑1)**

| Variable | Description | Units |
|---------|-------------|-------|
| `altitude` | GPS altitude | m |
| `height` | Height above ground level | m |
| `geometric_height` | Geopotential height | m |
| `ta` | Air temperature | °C |
| `rh` | Relative humidity | % |
| `wdir` | Wind direction | degrees |
| `wspeed` | Wind speed | m/s |
| `u` | Zonal wind component | m/s |
| `v` | Meridional wind component | m/s |
| `lat` | Latitude | degrees |
| `lon` | Longitude | degrees |
| `time` | Timestamp of measurement | ISO‑8601 string |

#### **New derived variables**

| Variable | Description | Units |
|---------|-------------|-------|
| `td` | Dewpoint temperature | °C |
| `cape` | Convective Available Potential Energy | J/kg |
| `cin` | Convective Inhibition | J/kg |
| `tt_index` | Total Totals Index | dimensionless |
| `k_index` | K‑Index | °C |
| `li` | Lifted Index | °C |

### **Purpose**
The Level‑2 PTU dataset is used for:

- Severe weather forecasting  
- Thermodynamic profiling  
- Atmospheric stability analysis  

---

## Standard Pressure Level Dataset (`std_plvl_radiosondes.level2.nc`)

This dataset contains radiosonde measurements at **standard pressure levels**, with **derived thermodynamic indices**.

### **Dimensions**
```
sounding_num: 14
p: 14
```

### **Coordinates**
- **sounding_num** — radiosonde identifier  
- **launch_time** — timestamp of each radiosonde launch  
- **p** — standard pressure levels  
  (1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30 hPa)

### **Variables**

#### **Physical variables (same as Level‑1)**

| Variable | Description | Units |
|---------|-------------|-------|
| `RadioRxTime` | Time of radio reception | s or ISO‑8601 |
| `time` | Timestamp of measurement | ISO‑8601 string |
| `height` | Height at standard pressure level | m |
| `ta` | Air temperature | °C |
| `rh` | Relative humidity | % |
| `wdir` | Wind direction | degrees |
| `wspeed` | Wind speed | m/s |
| `lat` | Latitude | degrees |
| `lon` | Longitude | degrees |

#### **New derived variables**

| Variable | Description | Units |
|---------|-------------|-------|
| `td` | Dewpoint temperature | °C |
| `cape` | Convective Available Potential Energy | J/kg |
| `cin` | Convective Inhibition | J/kg |
| `tt_index` | Total Totals Index | dimensionless |
| `k_index` | K‑Index | °C |
| `li` | Lifted Index | °C |

### **Purpose**
The Level‑2 STD‑PLVL dataset is ideal for:

- Synoptic‑scale convective diagnostics  
- Model verification at standard pressure levels  
- Climatological summaries of stability indices  
- Quick comparison between soundings  

---

# 🧩 Summary Table

| Dataset | Vertical Resolution | QC Applied | Derived Variables | Purpose |
|--------|---------------------|------------|-------------------|---------|
| **PTU (Level‑2)** | 991 levels | Yes | td, CAPE, CIN, TT, K, LI | High‑resolution convective diagnostics |
| **STD‑PLVL (Level‑2)** | 14 levels | Yes | td, CAPE, CIN, TT, K, LI | Synoptic‑scale stability analysis |

---

