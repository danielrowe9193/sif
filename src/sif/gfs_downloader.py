# GFS Forecast Data
"""
This file pulls data from the National Oceanic and Atmospheric Administration
Website: https://nomads.ncep.noaa.gov/gribfilter.php?ds=gfs_0p25
"""

from pathlib import Path
import time
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# 00z, 06z, 12z, 18z
CYCLES = ["00", "06", "12", "18"]
# 12, 24, and 48 hour forecasts
STEPS = [12, 24, 48]

BASE_URL = ("https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl")

def set_settings():
    return {
        # latitude and longitude
        "leftlon": 5,
        "rightlon": 20,
        "bottomlat": 50,
        "toplat": 57,

        # all variables and levels
        "all_var": "on",
        "all_lev": "on",
        "subregion": "",
    }


def get_date():
    """
    Ask for a date
    """

    while True:
        date_input = input("Enter date (YYYY-MM-DD): ").strip()
        try:
            date_obj = datetime.strptime(date_input,"%Y-%m-%d")
            return date_obj

        except ValueError:
            print("Invalid date. "
            "Please use YYYY-MM-DD."
            )

def download_file(url, output_file):
    """
    Download a file and display a progress indicator.
    """

    try:
        request = Request(url,headers={
                "User-Agent": "GFS downloader"
            }
        )

        with urlopen(request,timeout=60) as response:

            total_size = response.headers.get("Content-Length")

            if total_size:
                total_size = int(total_size)

            downloaded = 0
            chunk_size = 1024 * 1024  # 1 MB

            with open(output_file,"wb") as f:

                while True:
                    chunk = response.read(chunk_size )
                    if not chunk:
                        break

                    f.write(chunk)

                    downloaded += len(chunk)

                    if total_size:

                        percent = (downloaded / total_size *100)
                        downloaded_mb = (downloaded / (1024 ** 2))
                        total_mb = (total_size / (1024 ** 2))

                        print(
                            f"\r    "
                            f"{downloaded_mb:,.1f} / "
                            f"{total_mb:,.1f} MB "
                            f"({percent:5.1f}%)",
                            end="",
                            flush=True
                        )

                    else:
                        downloaded_mb = (downloaded / (1024 ** 2))

                        print(
                            f"\r    "
                            f"{downloaded_mb:,.1f} MB",
                            end="",
                            flush=True
                        )
        print()

        return True

    except HTTPError as e:

        print(
            f"\n    HTTP error "
            f"{e.code}: {e.reason}"
        )

        return False

    except URLError as e:

        print(
            f"\n    URL error: "
            f"{e.reason}"
        )

        return False

    except Exception as e:

        print(
            f"\n    Error: {e}"
        )

        return False


def download_cycle(date_string,cycle,output_dir):
    """
    Download the GFS 12, 24, and 48 hour forecast and analysis files for one cycle.
    """

    yyyymmdd = date_string.replace("-","")

    forecast_files = [
        ".anl",
        ".f012",
        ".f024",
        ".f048",
    ]

    for name in forecast_files:
        filename = (
            f"gfs.t{cycle}z."
            f"pgrb2.0p25{name}"
        )

        url = (
            f"{BASE_URL}/"
            f"gfs.{yyyymmdd}/"
            f"{cycle}/"
            f"atmos/"
            f"{filename}"
        )

        output_file = Path(output_dir) / filename

        print(f"Downloading cycle {cycle} UTC")

        print(f"    File: {filename}")

        # check if file exists already
        if output_file.exists():

            size_mb = (output_file.stat().st_size / (1024 ** 2))

            if size_mb > 0.1:

                print(
                    f"    Already exists "
                    f"({size_mb:,.1f} MB)"
                )

                print("    Skipping download.")

                continue

            else:

                print(
                    "    Existing file appears "
                    "incomplete."
                )

                print("    Downloading again.")

                output_file.unlink()

        # variable to check if file downloaded
        success = download_file(url, output_file)

        if success:

            size_mb = (output_file.stat().st_size / (1024 ** 2))

            print(
                f"    Saved: {output_file}"
            )

            print(
                f"    Size: "
                f"{size_mb:,.1f} MB"
            )

        else:
            # Remove incomplete file
            if output_file.exists():
                output_file.unlink()
            print("    Download failed.")
            return False

def download_all_cycles(date_string,output_dir):
    """
    Download GFS analysis files for
    00, 06, 12 and 18 UTC.
    """

    print("Starting downloads...")

    for i, cycle in enumerate(CYCLES):
        print("--------------------------------------------------")

        print(f"[{i + 1}/{len(CYCLES)}]")

        success = download_cycle(
            date_string,
            cycle,
            output_dir
        )

        # wait
        if i < len(CYCLES) - 1:
            print(
                "Waiting 10 seconds "
                "before next download..."
            )
            time.sleep(10)

    print("--------------------------------------------------")

if __name__ == "__main__":
    
    # set configurations
    settings = set_settings()
    print("Configured geographic area:")

    print(
        f"    Longitude: "
        f"{settings['leftlon']}° "
        f"to "
        f"{settings['rightlon']}°"
    )

    print(
        f"    Latitude: "
        f"{settings['bottomlat']}° "
        f"to "
        f"{settings['toplat']}°"
    )

    # get date
    date_obj = get_date()
    date_string = date_obj.strftime( "%Y-%m-%d")
    yyyymmdd = date_obj.strftime( "%Y%m%d")

    BASE_PATH = Path(__file__).resolve().parent.parent.parent / "data" 
    output_dir = BASE_PATH / "GFS" / f"{date_string}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Downloading GFS analysis "
        f"files for {date_string}"
    )

    # download all the cycles
    download_all_cycles(date_string,output_dir)

    print("Finished.")
