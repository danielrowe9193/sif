# sif
_Stability Indices at Fehmarn_

# Reading Radiosondes
Radiosondes are prepared using the `radiosondes.py` module. Here, `.mwx` files are extracted to a given folder, and radiosondes are built using the different files available.

To load radiosonde data and store as a `.nc` file:
```python
from radiosondes import Radiosonde

radiosonde = Radiosonde(
    storage_dir='dir/to/store/data',
    filename='name_of_radiosonde.mwx',
    extract_to='dir/to/extract/to'
)

radiosonde.extract_mwx()
radiosonde.build_radiosonde().to_netcdf('store/netcdf.nc')
```
