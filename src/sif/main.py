import src.sif.utils.plot as plot
import src.sif.observations.radiosondes as rs

from src.sif.models import forecast_radiosondes
from src.sif.utils.utils import FileManagement
from pathlib import Path

# Rename files so there are sorted by date.
FileManagement.rename_mwx(FileManagement.MWX_DIR)

# Read radiosondes and build level0 to level2 datasets.
radiosondes = rs.Radiosondes(
    mwx_dir=Path("../data/mwx/")
)

lvl0 = rs.RadiosondesLevel0(
    radiosondes=radiosondes
)
lvl0.build_ptu_radiosondes_lvl0()
lvl0.build_std_plvl_radiosondes_lvl0()

lvl1 = rs.RadiosondesLevel1(
    radiosondes_lvl0=lvl0
)
lvl1.build_ptu_radiosondes_lvl1()
lvl1.build_std_plvl_radiosondes_lvl1()

lvl2 = rs.RadiosondesLevel2(
    radiosondes_lvl1=lvl1
)
lvl2.build_ptu_radiosondes_lvl2()
lvl2.build_std_plvl_radiosondes_lvl2()

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
plotter.plot_indices_over_time()

