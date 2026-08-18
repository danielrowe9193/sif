"""
API to pull data from ICON model.
Website: https://open-meteo.com/en/docs/dwd-api

Code was provided on the website and was edited to suit our requirements
"""

import openmeteo_requests

import pandas as pd
import xarray as xr
from datetime import datetime, timedelta

# Add function to selct date
def get_date():
    while True: 
        date_string = input(
            "Enter date to download (YYYY-MM-DD): "
        ).strip()

        try:

            date = datetime.strptime(
                date_string,
                "%Y-%m-%d",
            )
            break

        except ValueError:
            print(
                "Invalid date format. "
                "Please use YYYY-MM-DD, for example 2026-08-11."
            )
    return date_string
            
date_input = get_date()

openmeteo = openmeteo_requests.Client()
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": [54.527846, 54.528, 54.097, 53.712],
	"longitude": [11.060437, 9.55, 13.405, 7.152],
	"hourly": ["temperature_50hPa", "geopotential_height_50hPa", "relative_humidity_50hPa", "wind_speed_50hPa", "wind_direction_50hPa", "surface_pressure", "temperature_2m", "relative_humidity_2m", "wind_speed_180m", "wind_direction_180m", "temperature_180m", "lightning_potential", "cape", "temperature_30hPa", "relative_humidity_30hPa", "wind_speed_30hPa", "wind_direction_30hPa", "geopotential_height_30hPa", "dew_point_2m", "wind_speed_10m", "wind_direction_10m", "wind_speed_80m", "wind_speed_120m", "wind_direction_80m", "wind_direction_120m", "temperature_80m", "temperature_120m", "freezing_level_height", "temperature_1000hPa", "temperature_975hPa", "temperature_950hPa", "temperature_925hPa", "geopotential_height_800hPa", "geopotential_height_200hPa", "geopotential_height_250hPa", "geopotential_height_300hPa", "geopotential_height_400hPa", "geopotential_height_500hPa", "geopotential_height_600hPa", "geopotential_height_700hPa", "geopotential_height_150hPa", "geopotential_height_100hPa", "geopotential_height_70hPa", "geopotential_height_850hPa", "geopotential_height_925hPa", "geopotential_height_900hPa", "geopotential_height_950hPa", "geopotential_height_975hPa", "geopotential_height_1000hPa", "wind_direction_1000hPa", "wind_direction_975hPa", "wind_direction_950hPa", "wind_direction_925hPa", "wind_direction_900hPa", "wind_direction_850hPa", "wind_direction_800hPa", "wind_direction_200hPa", "wind_direction_250hPa", "wind_direction_300hPa", "wind_direction_400hPa", "wind_direction_500hPa", "wind_direction_600hPa", "wind_direction_700hPa", "wind_direction_150hPa", "wind_direction_100hPa", "wind_direction_70hPa", "wind_speed_1000hPa", "wind_speed_975hPa", "wind_speed_950hPa", "wind_speed_925hPa", "wind_speed_900hPa", "wind_speed_850hPa", "wind_speed_800hPa", "wind_speed_200hPa", "wind_speed_250hPa", "wind_speed_300hPa", "wind_speed_400hPa", "wind_speed_500hPa", "wind_speed_600hPa", "wind_speed_700hPa", "wind_speed_150hPa", "wind_speed_100hPa", "wind_speed_70hPa", "relative_humidity_1000hPa", "relative_humidity_975hPa", "relative_humidity_950hPa", "relative_humidity_925hPa", "relative_humidity_900hPa", "relative_humidity_850hPa", "relative_humidity_800hPa", "relative_humidity_200hPa", "relative_humidity_250hPa", "relative_humidity_300hPa", "relative_humidity_400hPa", "relative_humidity_500hPa", "relative_humidity_600hPa", "relative_humidity_700hPa", "relative_humidity_150hPa", "relative_humidity_100hPa", "relative_humidity_70hPa", "temperature_900hPa", "temperature_850hPa", "temperature_800hPa", "temperature_200hPa", "temperature_300hPa", "temperature_250hPa", "temperature_400hPa", "temperature_500hPa", "temperature_600hPa", "temperature_700hPa", "temperature_150hPa", "temperature_100hPa", "temperature_70hPa", "updraft"],
	"models": "dwd_icon_seamless",
	"minutely_15": ["cape", "lightning_potential", "freezing_level_height"],
	"timezone": "Europe/Berlin",
	"wind_speed_unit": "ms",
	"start_date": f"{date_input}",
	"end_date": f"{date_input}",
}
responses = openmeteo.weather_api(url, params = params)

# Process 4 locations
for response in responses:
    print(f"\nCoordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

    # Process minutely_15 data. The order of variables needs to be the same as requested.
    minutely_15 = response.Minutely15()
    minutely_15_cape = minutely_15.Variables(0).ValuesAsNumpy()
    minutely_15_lightning_potential = minutely_15.Variables(1).ValuesAsNumpy()
    minutely_15_freezing_level_height = minutely_15.Variables(2).ValuesAsNumpy()

    minutely_15_data = {
        "date": pd.date_range(
            start = pd.to_datetime(minutely_15.Time(), unit = "s", utc = True),
            end =  pd.to_datetime(minutely_15.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = minutely_15.Interval()),
            inclusive = "left"
        ).tz_convert(response.Timezone().decode())
    }

    minutely_15_data["cape"] = minutely_15_cape
    minutely_15_data["lightning_potential"] = minutely_15_lightning_potential
    minutely_15_data["freezing_level_height"] = minutely_15_freezing_level_height

    minutely_15_dataframe = pd.DataFrame(data = minutely_15_data)
    print("\nMinutely15 data\n", minutely_15_dataframe)

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_50hPa = hourly.Variables(0).ValuesAsNumpy()
    hourly_geopotential_height_50hPa = hourly.Variables(1).ValuesAsNumpy()
    hourly_relative_humidity_50hPa = hourly.Variables(2).ValuesAsNumpy()
    hourly_wind_speed_50hPa = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_direction_50hPa = hourly.Variables(4).ValuesAsNumpy()
    hourly_surface_pressure = hourly.Variables(5).ValuesAsNumpy()
    hourly_temperature_2m = hourly.Variables(6).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(7).ValuesAsNumpy()
    hourly_wind_speed_180m = hourly.Variables(8).ValuesAsNumpy()
    hourly_wind_direction_180m = hourly.Variables(9).ValuesAsNumpy()
    hourly_temperature_180m = hourly.Variables(10).ValuesAsNumpy()
    hourly_lightning_potential = hourly.Variables(11).ValuesAsNumpy()
    hourly_cape = hourly.Variables(12).ValuesAsNumpy()
    hourly_temperature_30hPa = hourly.Variables(13).ValuesAsNumpy()
    hourly_relative_humidity_30hPa = hourly.Variables(14).ValuesAsNumpy()
    hourly_wind_speed_30hPa = hourly.Variables(15).ValuesAsNumpy()
    hourly_wind_direction_30hPa = hourly.Variables(16).ValuesAsNumpy()
    hourly_geopotential_height_30hPa = hourly.Variables(17).ValuesAsNumpy()
    hourly_dew_point_2m = hourly.Variables(18).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(19).ValuesAsNumpy()
    hourly_wind_direction_10m = hourly.Variables(20).ValuesAsNumpy()
    hourly_wind_speed_80m = hourly.Variables(21).ValuesAsNumpy()
    hourly_wind_speed_120m = hourly.Variables(22).ValuesAsNumpy()
    hourly_wind_direction_80m = hourly.Variables(23).ValuesAsNumpy()
    hourly_wind_direction_120m = hourly.Variables(24).ValuesAsNumpy()
    hourly_temperature_80m = hourly.Variables(25).ValuesAsNumpy()
    hourly_temperature_120m = hourly.Variables(26).ValuesAsNumpy()
    hourly_freezing_level_height = hourly.Variables(27).ValuesAsNumpy()
    hourly_temperature_1000hPa = hourly.Variables(28).ValuesAsNumpy()
    hourly_temperature_975hPa = hourly.Variables(29).ValuesAsNumpy()
    hourly_temperature_950hPa = hourly.Variables(30).ValuesAsNumpy()
    hourly_temperature_925hPa = hourly.Variables(31).ValuesAsNumpy()
    hourly_geopotential_height_800hPa = hourly.Variables(32).ValuesAsNumpy()
    hourly_geopotential_height_200hPa = hourly.Variables(33).ValuesAsNumpy()
    hourly_geopotential_height_250hPa = hourly.Variables(34).ValuesAsNumpy()
    hourly_geopotential_height_300hPa = hourly.Variables(35).ValuesAsNumpy()
    hourly_geopotential_height_400hPa = hourly.Variables(36).ValuesAsNumpy()
    hourly_geopotential_height_500hPa = hourly.Variables(37).ValuesAsNumpy()
    hourly_geopotential_height_600hPa = hourly.Variables(38).ValuesAsNumpy()
    hourly_geopotential_height_700hPa = hourly.Variables(39).ValuesAsNumpy()
    hourly_geopotential_height_150hPa = hourly.Variables(40).ValuesAsNumpy()
    hourly_geopotential_height_100hPa = hourly.Variables(41).ValuesAsNumpy()
    hourly_geopotential_height_70hPa = hourly.Variables(42).ValuesAsNumpy()
    hourly_geopotential_height_850hPa = hourly.Variables(43).ValuesAsNumpy()
    hourly_geopotential_height_925hPa = hourly.Variables(44).ValuesAsNumpy()
    hourly_geopotential_height_900hPa = hourly.Variables(45).ValuesAsNumpy()
    hourly_geopotential_height_950hPa = hourly.Variables(46).ValuesAsNumpy()
    hourly_geopotential_height_975hPa = hourly.Variables(47).ValuesAsNumpy()
    hourly_geopotential_height_1000hPa = hourly.Variables(48).ValuesAsNumpy()
    hourly_wind_direction_1000hPa = hourly.Variables(49).ValuesAsNumpy()
    hourly_wind_direction_975hPa = hourly.Variables(50).ValuesAsNumpy()
    hourly_wind_direction_950hPa = hourly.Variables(51).ValuesAsNumpy()
    hourly_wind_direction_925hPa = hourly.Variables(52).ValuesAsNumpy()
    hourly_wind_direction_900hPa = hourly.Variables(53).ValuesAsNumpy()
    hourly_wind_direction_850hPa = hourly.Variables(54).ValuesAsNumpy()
    hourly_wind_direction_800hPa = hourly.Variables(55).ValuesAsNumpy()
    hourly_wind_direction_200hPa = hourly.Variables(56).ValuesAsNumpy()
    hourly_wind_direction_250hPa = hourly.Variables(57).ValuesAsNumpy()
    hourly_wind_direction_300hPa = hourly.Variables(58).ValuesAsNumpy()
    hourly_wind_direction_400hPa = hourly.Variables(59).ValuesAsNumpy()
    hourly_wind_direction_500hPa = hourly.Variables(60).ValuesAsNumpy()
    hourly_wind_direction_600hPa = hourly.Variables(61).ValuesAsNumpy()
    hourly_wind_direction_700hPa = hourly.Variables(62).ValuesAsNumpy()
    hourly_wind_direction_150hPa = hourly.Variables(63).ValuesAsNumpy()
    hourly_wind_direction_100hPa = hourly.Variables(64).ValuesAsNumpy()
    hourly_wind_direction_70hPa = hourly.Variables(65).ValuesAsNumpy()
    hourly_wind_speed_1000hPa = hourly.Variables(66).ValuesAsNumpy()
    hourly_wind_speed_975hPa = hourly.Variables(67).ValuesAsNumpy()
    hourly_wind_speed_950hPa = hourly.Variables(68).ValuesAsNumpy()
    hourly_wind_speed_925hPa = hourly.Variables(69).ValuesAsNumpy()
    hourly_wind_speed_900hPa = hourly.Variables(70).ValuesAsNumpy()
    hourly_wind_speed_850hPa = hourly.Variables(71).ValuesAsNumpy()
    hourly_wind_speed_800hPa = hourly.Variables(72).ValuesAsNumpy()
    hourly_wind_speed_200hPa = hourly.Variables(73).ValuesAsNumpy()
    hourly_wind_speed_250hPa = hourly.Variables(74).ValuesAsNumpy()
    hourly_wind_speed_300hPa = hourly.Variables(75).ValuesAsNumpy()
    hourly_wind_speed_400hPa = hourly.Variables(76).ValuesAsNumpy()
    hourly_wind_speed_500hPa = hourly.Variables(77).ValuesAsNumpy()
    hourly_wind_speed_600hPa = hourly.Variables(78).ValuesAsNumpy()
    hourly_wind_speed_700hPa = hourly.Variables(79).ValuesAsNumpy()
    hourly_wind_speed_150hPa = hourly.Variables(80).ValuesAsNumpy()
    hourly_wind_speed_100hPa = hourly.Variables(81).ValuesAsNumpy()
    hourly_wind_speed_70hPa = hourly.Variables(82).ValuesAsNumpy()
    hourly_relative_humidity_1000hPa = hourly.Variables(83).ValuesAsNumpy()
    hourly_relative_humidity_975hPa = hourly.Variables(84).ValuesAsNumpy()
    hourly_relative_humidity_950hPa = hourly.Variables(85).ValuesAsNumpy()
    hourly_relative_humidity_925hPa = hourly.Variables(86).ValuesAsNumpy()
    hourly_relative_humidity_900hPa = hourly.Variables(87).ValuesAsNumpy()
    hourly_relative_humidity_850hPa = hourly.Variables(88).ValuesAsNumpy()
    hourly_relative_humidity_800hPa = hourly.Variables(89).ValuesAsNumpy()
    hourly_relative_humidity_200hPa = hourly.Variables(90).ValuesAsNumpy()
    hourly_relative_humidity_250hPa = hourly.Variables(91).ValuesAsNumpy()
    hourly_relative_humidity_300hPa = hourly.Variables(92).ValuesAsNumpy()
    hourly_relative_humidity_400hPa = hourly.Variables(93).ValuesAsNumpy()
    hourly_relative_humidity_500hPa = hourly.Variables(94).ValuesAsNumpy()
    hourly_relative_humidity_600hPa = hourly.Variables(95).ValuesAsNumpy()
    hourly_relative_humidity_700hPa = hourly.Variables(96).ValuesAsNumpy()
    hourly_relative_humidity_150hPa = hourly.Variables(97).ValuesAsNumpy()
    hourly_relative_humidity_100hPa = hourly.Variables(98).ValuesAsNumpy()
    hourly_relative_humidity_70hPa = hourly.Variables(99).ValuesAsNumpy()
    hourly_temperature_900hPa = hourly.Variables(100).ValuesAsNumpy()
    hourly_temperature_850hPa = hourly.Variables(101).ValuesAsNumpy()
    hourly_temperature_800hPa = hourly.Variables(102).ValuesAsNumpy()
    hourly_temperature_200hPa = hourly.Variables(103).ValuesAsNumpy()
    hourly_temperature_300hPa = hourly.Variables(104).ValuesAsNumpy()
    hourly_temperature_250hPa = hourly.Variables(105).ValuesAsNumpy()
    hourly_temperature_400hPa = hourly.Variables(106).ValuesAsNumpy()
    hourly_temperature_500hPa = hourly.Variables(107).ValuesAsNumpy()
    hourly_temperature_600hPa = hourly.Variables(108).ValuesAsNumpy()
    hourly_temperature_700hPa = hourly.Variables(109).ValuesAsNumpy()
    hourly_temperature_150hPa = hourly.Variables(110).ValuesAsNumpy()
    hourly_temperature_100hPa = hourly.Variables(111).ValuesAsNumpy()
    hourly_temperature_70hPa = hourly.Variables(112).ValuesAsNumpy()
    hourly_updraft = hourly.Variables(113).ValuesAsNumpy()

    hourly_data = {
        "date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        ).tz_convert(response.Timezone().decode())
    }

    hourly_data["temperature_50hPa"] = hourly_temperature_50hPa
    hourly_data["geopotential_height_50hPa"] = hourly_geopotential_height_50hPa
    hourly_data["relative_humidity_50hPa"] = hourly_relative_humidity_50hPa
    hourly_data["wind_speed_50hPa"] = hourly_wind_speed_50hPa
    hourly_data["wind_direction_50hPa"] = hourly_wind_direction_50hPa
    hourly_data["surface_pressure"] = hourly_surface_pressure
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["wind_speed_180m"] = hourly_wind_speed_180m
    hourly_data["wind_direction_180m"] = hourly_wind_direction_180m
    hourly_data["temperature_180m"] = hourly_temperature_180m
    hourly_data["lightning_potential"] = hourly_lightning_potential
    hourly_data["cape"] = hourly_cape
    hourly_data["temperature_30hPa"] = hourly_temperature_30hPa
    hourly_data["relative_humidity_30hPa"] = hourly_relative_humidity_30hPa
    hourly_data["wind_speed_30hPa"] = hourly_wind_speed_30hPa
    hourly_data["wind_direction_30hPa"] = hourly_wind_direction_30hPa
    hourly_data["geopotential_height_30hPa"] = hourly_geopotential_height_30hPa
    hourly_data["dew_point_2m"] = hourly_dew_point_2m
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
    hourly_data["wind_direction_10m"] = hourly_wind_direction_10m
    hourly_data["wind_speed_80m"] = hourly_wind_speed_80m
    hourly_data["wind_speed_120m"] = hourly_wind_speed_120m
    hourly_data["wind_direction_80m"] = hourly_wind_direction_80m
    hourly_data["wind_direction_120m"] = hourly_wind_direction_120m
    hourly_data["temperature_80m"] = hourly_temperature_80m
    hourly_data["temperature_120m"] = hourly_temperature_120m
    hourly_data["freezing_level_height"] = hourly_freezing_level_height
    hourly_data["temperature_1000hPa"] = hourly_temperature_1000hPa
    hourly_data["temperature_975hPa"] = hourly_temperature_975hPa
    hourly_data["temperature_950hPa"] = hourly_temperature_950hPa
    hourly_data["temperature_925hPa"] = hourly_temperature_925hPa
    hourly_data["geopotential_height_800hPa"] = hourly_geopotential_height_800hPa
    hourly_data["geopotential_height_200hPa"] = hourly_geopotential_height_200hPa
    hourly_data["geopotential_height_250hPa"] = hourly_geopotential_height_250hPa
    hourly_data["geopotential_height_300hPa"] = hourly_geopotential_height_300hPa
    hourly_data["geopotential_height_400hPa"] = hourly_geopotential_height_400hPa
    hourly_data["geopotential_height_500hPa"] = hourly_geopotential_height_500hPa
    hourly_data["geopotential_height_600hPa"] = hourly_geopotential_height_600hPa
    hourly_data["geopotential_height_700hPa"] = hourly_geopotential_height_700hPa
    hourly_data["geopotential_height_150hPa"] = hourly_geopotential_height_150hPa
    hourly_data["geopotential_height_100hPa"] = hourly_geopotential_height_100hPa
    hourly_data["geopotential_height_70hPa"] = hourly_geopotential_height_70hPa
    hourly_data["geopotential_height_850hPa"] = hourly_geopotential_height_850hPa
    hourly_data["geopotential_height_925hPa"] = hourly_geopotential_height_925hPa
    hourly_data["geopotential_height_900hPa"] = hourly_geopotential_height_900hPa
    hourly_data["geopotential_height_950hPa"] = hourly_geopotential_height_950hPa
    hourly_data["geopotential_height_975hPa"] = hourly_geopotential_height_975hPa
    hourly_data["geopotential_height_1000hPa"] = hourly_geopotential_height_1000hPa
    hourly_data["wind_direction_1000hPa"] = hourly_wind_direction_1000hPa
    hourly_data["wind_direction_975hPa"] = hourly_wind_direction_975hPa
    hourly_data["wind_direction_950hPa"] = hourly_wind_direction_950hPa
    hourly_data["wind_direction_925hPa"] = hourly_wind_direction_925hPa
    hourly_data["wind_direction_900hPa"] = hourly_wind_direction_900hPa
    hourly_data["wind_direction_850hPa"] = hourly_wind_direction_850hPa
    hourly_data["wind_direction_800hPa"] = hourly_wind_direction_800hPa
    hourly_data["wind_direction_200hPa"] = hourly_wind_direction_200hPa
    hourly_data["wind_direction_250hPa"] = hourly_wind_direction_250hPa
    hourly_data["wind_direction_300hPa"] = hourly_wind_direction_300hPa
    hourly_data["wind_direction_400hPa"] = hourly_wind_direction_400hPa
    hourly_data["wind_direction_500hPa"] = hourly_wind_direction_500hPa
    hourly_data["wind_direction_600hPa"] = hourly_wind_direction_600hPa
    hourly_data["wind_direction_700hPa"] = hourly_wind_direction_700hPa
    hourly_data["wind_direction_150hPa"] = hourly_wind_direction_150hPa
    hourly_data["wind_direction_100hPa"] = hourly_wind_direction_100hPa
    hourly_data["wind_direction_70hPa"] = hourly_wind_direction_70hPa
    hourly_data["wind_speed_1000hPa"] = hourly_wind_speed_1000hPa
    hourly_data["wind_speed_975hPa"] = hourly_wind_speed_975hPa
    hourly_data["wind_speed_950hPa"] = hourly_wind_speed_950hPa
    hourly_data["wind_speed_925hPa"] = hourly_wind_speed_925hPa
    hourly_data["wind_speed_900hPa"] = hourly_wind_speed_900hPa
    hourly_data["wind_speed_850hPa"] = hourly_wind_speed_850hPa
    hourly_data["wind_speed_800hPa"] = hourly_wind_speed_800hPa
    hourly_data["wind_speed_200hPa"] = hourly_wind_speed_200hPa
    hourly_data["wind_speed_250hPa"] = hourly_wind_speed_250hPa
    hourly_data["wind_speed_300hPa"] = hourly_wind_speed_300hPa
    hourly_data["wind_speed_400hPa"] = hourly_wind_speed_400hPa
    hourly_data["wind_speed_500hPa"] = hourly_wind_speed_500hPa
    hourly_data["wind_speed_600hPa"] = hourly_wind_speed_600hPa
    hourly_data["wind_speed_700hPa"] = hourly_wind_speed_700hPa
    hourly_data["wind_speed_150hPa"] = hourly_wind_speed_150hPa
    hourly_data["wind_speed_100hPa"] = hourly_wind_speed_100hPa
    hourly_data["wind_speed_70hPa"] = hourly_wind_speed_70hPa
    hourly_data["relative_humidity_1000hPa"] = hourly_relative_humidity_1000hPa
    hourly_data["relative_humidity_975hPa"] = hourly_relative_humidity_975hPa
    hourly_data["relative_humidity_950hPa"] = hourly_relative_humidity_950hPa
    hourly_data["relative_humidity_925hPa"] = hourly_relative_humidity_925hPa
    hourly_data["relative_humidity_900hPa"] = hourly_relative_humidity_900hPa
    hourly_data["relative_humidity_850hPa"] = hourly_relative_humidity_850hPa
    hourly_data["relative_humidity_800hPa"] = hourly_relative_humidity_800hPa
    hourly_data["relative_humidity_200hPa"] = hourly_relative_humidity_200hPa
    hourly_data["relative_humidity_250hPa"] = hourly_relative_humidity_250hPa
    hourly_data["relative_humidity_300hPa"] = hourly_relative_humidity_300hPa
    hourly_data["relative_humidity_400hPa"] = hourly_relative_humidity_400hPa
    hourly_data["relative_humidity_500hPa"] = hourly_relative_humidity_500hPa
    hourly_data["relative_humidity_600hPa"] = hourly_relative_humidity_600hPa
    hourly_data["relative_humidity_700hPa"] = hourly_relative_humidity_700hPa
    hourly_data["relative_humidity_150hPa"] = hourly_relative_humidity_150hPa
    hourly_data["relative_humidity_100hPa"] = hourly_relative_humidity_100hPa
    hourly_data["relative_humidity_70hPa"] = hourly_relative_humidity_70hPa
    hourly_data["temperature_900hPa"] = hourly_temperature_900hPa
    hourly_data["temperature_850hPa"] = hourly_temperature_850hPa
    hourly_data["temperature_800hPa"] = hourly_temperature_800hPa
    hourly_data["temperature_200hPa"] = hourly_temperature_200hPa
    hourly_data["temperature_300hPa"] = hourly_temperature_300hPa
    hourly_data["temperature_250hPa"] = hourly_temperature_250hPa
    hourly_data["temperature_400hPa"] = hourly_temperature_400hPa
    hourly_data["temperature_500hPa"] = hourly_temperature_500hPa
    hourly_data["temperature_600hPa"] = hourly_temperature_600hPa
    hourly_data["temperature_700hPa"] = hourly_temperature_700hPa
    hourly_data["temperature_150hPa"] = hourly_temperature_150hPa
    hourly_data["temperature_100hPa"] = hourly_temperature_100hPa
    hourly_data["temperature_70hPa"] = hourly_temperature_70hPa
    hourly_data["updraft"] = hourly_updraft

    hourly_dataframe = pd.DataFrame(data = hourly_data)

    # save as netCDF 
    # hourly_dataframe = hourly_dataframe.set_index(["time", "lat", "lon"])
    # ds = xr.Dataset.from_dataframe(hourly_dataframe)
    # ds.to_netcdf(f"icon-{date_input}.nc")
    
    hourly_dataframe = hourly_dataframe.set_index(["time", "lat", "lon"])

    ds = xr.Dataset.from_dataframe(hourly_dataframe)
    ds.to_netcdf(f"icon-{date_input}.nc")

    # print("\nHourly data\n", hourly_dataframe)


