# sif
_Stability Indices at Fehmarn_

# Reading Radiosondes
Radiosondes are prepared using the `radiosondes.py` module. Here, `.mwx` files are extracted to a given folder, and radiosondes are built using the different files available. In the end, a `.nc` file is built, which contains profile data and sounding indices for the given radiosonde.

# Plotting Radiosondes
Radiosondes variables can be plotted using the `plot.py` module. It reads the `.nc` file generated and allows for plots of the radiosonde.

# Example
A brief example of building the radiosonde and plotting is shown below:

```python
import xarray as xr

from plot import FehmarnRadiosondePlotter
from radiosondes import Radiosonde

stem = "RS_TestData_Westermarkelsdorf_20220825_131825"

# Construct radiosonde from .mwx data.
radiosonde = Radiosonde(
    filepath=f"../../data/{stem}.mwx"
)
radiosonde.extract_mwx()
radiosonde.build_radiosonde()
radiosonde.summarize()

# Can load radiosonde data as xarray dataset, if desired.
ds = xr.open_dataset(f'../../data/{stem}.nc')

# Plot a skew-t diagram of the radiosonde.
plotter = FehmarnRadiosondePlotter(
    filepath=f'../../data/{stem}.nc'
)
plotter.plot_skewt()
```

where the resulting skew-t diagram is stored in the `plots/` directory. 
