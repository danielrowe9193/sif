from src.sif.models import forecast_radiosondes
from src.sif.utils import utils

from src.sif.utils.plot import FehmarnRadiosondeIndicesPlotter

# Rename files so there are sorted by date.
utils.FileManagement.rename_mwx(utils.FileManagement.MWX_DIR)

# # Read radiosondes and
# radiosondes = Radiosondes().build_sif_radiosonde_profiles_ds_lvl0()
# print(radiosondes)

# Create IFS level-0 and level-1 datasets
ifs_level_zero = forecast_radiosondes.IFSLevelZero()
# ifs_level_zero.collect_fc_file_paths()
# ifs_level_zero.build_ifs_level_zero_ds()
# ifs_level_zero.export_ifs_level_zero_ds()

ifs_level_one = forecast_radiosondes.IFSLevelOne(ifs_level_zero)
# ifs_level_one.build_ifs_level_one_ds()
# ifs_level_one.export_ifs_level_one_ds()

# Plot skew-t for each radiosonde
# profile_plotter = FehmarnRadiosondeProfilePlotter(
#     filepath="../../data/netcdf/sif.radiosondes.profiles.nc"
# )
# for sounding in radiosondes.sounding_id.values:
#     profile_plotter.plot_skewt(sounding)

# Plot indices
plotter = FehmarnRadiosondeIndicesPlotter(
    sif_filepath="../../data/netcdf/sif.radiosondes.profiles.nc",
    ifs_filepath="../../data/ifs/ifs.radiosondes.profiles.level1.nc"
)
plotter.plot_indices_over_time()
