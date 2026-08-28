import src.sif.utils.plot as plot
import src.sif.observations.radiosondes as rs

from src.sif.models import forecast_radiosondes
from src.sif.utils.utils import FileManagement as fm

# Rename files so there are sorted by date.
fm.rename_mwx(fm.MWX_DIR)

# Read radiosondes and build level0 to level2 datasets. Save the datasets.
radiosondes_pipeline = rs.RadiosondePipeline(
    mwx_dir=fm.MWX_DIR
)
radiosondes_pipeline.run_ptu_pipeline()
radiosondes_pipeline.run_std_plvl_pipeline()

# Create IFS level-0 and level-1 datasets
ifs_level_zero = forecast_radiosondes.IFSLevelZero()
# ifs_level_zero.collect_fc_file_paths()
# ifs_level_zero.build_ifs_level_zero_ds()
# ifs_level_zero.export_ifs_level_zero_ds()

ifs_level_one = forecast_radiosondes.IFSLevelOne(ifs_level_zero)
# ifs_level_one.build_ifs_level_one_ds()
# ifs_level_one.export_ifs_level_one_ds()

# Plot skew-t for each radiosonde
profile_plotter = plot.FehmarnRadiosondeProfilePlotter(
    filepath="../../data/netcdf/sif.radiosondes.profiles.nc"
)
# for sounding in radiosondes.sounding_id.values:
#     profile_plotter.plot_skewt(sounding)

# profile_plotter.plot_trajectories()
# profile_plotter.plot_all_profiles(var='rh')
profile_plotter.plot_heights()

# Plot indices
plotter = plot.FehmarnRadiosondeIndicesPlotter(
    sif_filepath="../../data/netcdf/sif.radiosondes.profiles.nc",
    ifs_filepath="../../data/ifs/ifs.radiosondes.profiles.level1.nc"
)
# plotter.plot_indices_over_time()

