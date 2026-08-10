import matplotlib.pyplot as plt

from plot import RadiosondePlotter
from radiosondes import Radiosonde

test_radiosonde = Radiosonde(
    storage_dir='../../data',
    filename="RS_TestData_Westermarkelsdorf_20220825_131825.mwx",
    extract_to="../../data/test_extract/"
)
test_radiosonde.extract_mwx()
ds_ptu = test_radiosonde.build_radiosonde()
test_radiosonde.summarize()

plotter = RadiosondePlotter(test_radiosonde)
plotter.plot_variable()

fig, axes = plt.subplots(ncols=2)
ax1, ax2 = axes.flatten()

ax1.plot(
    ds_ptu['ta'],
    ds_ptu['p']
)
ax1.invert_yaxis()
ax1.set_yscale("log")

ax2.plot(
    ds_ptu['rh'],
    ds_ptu['p']
)
ax2.set_yscale("log")
ax2.invert_yaxis()
ax2.set_yticks([1000, 850, 700, 500, 250, 100, 30])
ax2.set_yticklabels(["1000", "850", "700", "500", "250", "100", "30"])

plt.show()
