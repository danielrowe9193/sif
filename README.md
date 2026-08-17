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
