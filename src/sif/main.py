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
