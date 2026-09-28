import src.sif.models.forecast_radiosondes as fr
import src.sif.utils.file_management as fm
import src.sif.utils.plot as plot
import src.sif.observations.radiosondes as rs

# Rename files so there are sorted by date.
fm.rename_mwx(fm.MWX_DIR)

# Read radiosondes and build level0 to level2 datasets. Save the datasets.
radiosondes_pipeline = rs.RadiosondePipeline(
    mwx_dir=fm.MWX_DIR
)
radiosondes_pipeline.run_sif_ptu_pipeline()
radiosondes_pipeline.run_sif_std_plvl_pipeline()
radiosondes_pipeline.run_igra_pipeline()

# Build level 0 to level 1 datasets for forecast data.
forecast_radiosondes_pipeline = fr.ForecastRadiosondePipeline()
forecast_radiosondes_pipeline.run_ifs_pipeline()
forecast_radiosondes_pipeline.run_gfs_pipeline()
forecast_radiosondes_pipeline.run_icon_pipeline()

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

