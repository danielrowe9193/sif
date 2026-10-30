import metpy.calc as mpcalc
import numpy as np
import xarray as xr

from metpy.units import units
from numpy import concatenate

data = xr.open_dataset("C:..\\data\\netcdf\\sif.radiosondes.profiles.nc")

li_list = []

print(data)
for sounding in data.sounding_id.values:
    try:
        radiosonde = data.isel(sounding_id=sounding).sel(p=slice(1000, 200))

        p = radiosonde.p.values * units.hPa
        t = radiosonde.ta.values * units.kelvin
        td = radiosonde.td.values * units.kelvin
        h = radiosonde.height.values * units.m

        t = t.to("degC")
        td = td.to("degC")

        print(p, t, td, h)

        parcel_p, parcel_t, parcel_td = mpcalc.mixed_parcel(
            p, t, td, depth=500 * units.m, height=h
        )

        # Replace sounding temp/pressure in lowest 500m with mixed values
        above = h > 500 * units.m
        press = concatenate([[parcel_p], p[above]])
        temp = concatenate([[parcel_t], t[above]])

        # Calculate parcel profile from our new mixed parcel
        mixed_prof = mpcalc.parcel_profile(press, parcel_t, parcel_td)

        # Calculate lifted index using our mixed profile
        li = mpcalc.lifted_index(press, temp, mixed_prof)

        li_list.append(li)

    except:
        li_list.append(np.nan)


print(li_list)

# data = data.isel(sounding_id=slice(1, 9))

# li_list = []

# for sounding in range(len(data.sounding_id.values)):
#
#     radiosonde = data.isel(sounding_id=sounding).sel(p=slice(1000, 200))
#
#     p = radiosonde.p.values * units.hPa
#     t = radiosonde.ta.values * units.kelvin
#     td = radiosonde.td.values * units.kelvin
#     h = radiosonde.height.values * units.m
#
#     t = t.to('degC')
#     td = td.to('degC')
#
#     parcel_p, parcel_t, parcel_td = mpcalc.mixed_parcel(p, t, td, depth=500 * units.m, height=h)
#
#     # Replace sounding temp/pressure in lowest 500m with mixed values
#     above = h > 500 * units.m
#     press = concatenate([[parcel_p], p[above]])
#     temp = concatenate([[parcel_t], t[above]])
#
#     # Calculate parcel profile from our new mixed parcel
#     mixed_prof = mpcalc.parcel_profile(press, parcel_t, parcel_td)
#
#     # Calculate lifted index using our mixed profile
#     li = mpcalc.lifted_index(press, temp, mixed_prof)
#
#     print(li)
#
#     li_list.append(li)
#
# print(li_list)
