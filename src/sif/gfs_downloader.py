# GFS Forecast Data
"""
This file pulls data from the National Oceanic and Atmospheric Administration
Website: https://nomads.ncep.noaa.gov/gribfilter.php?ds=gfs_0p25
"""

from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
import time


BASE_URL = ("https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl")

# GFS cycles to download
CYCLES = [ "00", "06", "12", "18"]

# Forecast files
FORECAST_FILES = [".anl", ".f012", ".f024", ".f048"]

def set_settings():
    """
    Define the geographic region and GRIB variables/levels.
    """

    return {
        # Geographic region
        "leftlon": 5,
        "rightlon": 20,
        "bottomlat": 50,
        "toplat": 57,

        "all_var": "on",
        "all_lev": "on",

        "subregion": "on",
    }

def get_date():
    """
    Ask the user for a date.
    """

    while True:
        date_input = input("Enter date (YYYY-MM-DD): ").strip()

        try:
            date_obj = datetime.strptime(date_input,"%Y-%m-%d")
            return date_obj

        except ValueError:
            print(
                "Invalid date. "
                "Please use YYYY-MM-DD."
            )

def download_file(url, output_file):
    """
    Download a GRIB2 file

    The first four bytes are checked to make sure the server
    actually returned GRIB2 data.
    """

    try:
        request = Request(
            url,
            headers={"User-Agent": "GFS downloader"}
        )

        with urlopen(
            request,
            timeout=120
        ) as response:
 
            # Check response
            content_type = response.headers.get("Content-Type","")

            # Read the first four bytes.
            # A GRIB2 file should start with b"GRIB".
            first_bytes = response.read(4)
            if first_bytes != b"GRIB":

                # The response is probably an HTML error page.
                error_content = response.read(1000)

                try:
                    error_text = error_content.decode(
                        "utf-8",
                        errors="replace"
                    )
                except Exception:
                    error_text = repr(error_content)

                print(
                    "    ERROR: Server did not return "
                    "a GRIB2 file."
                )

                print(
                    f"    Content-Type: {content_type}"
                )

                print(
                    f"    First bytes: {first_bytes!r}"
                )

                print(
                    "    Server response:"
                )

                print(
                    f"    {error_text[:500]}"
                )

                return False

            total_size = response.headers.get(
                "Content-Length"
            )

            if total_size:
                total_size = int(total_size)

            downloaded = 4

            chunk_size = 1024 * 1024  # 1 MB

            # write file
            with open(
                output_file,
                "wb"
            ) as f:

                # Write the four bytes we already read
                f.write(first_bytes)

                while True:

                    chunk = response.read(
                        chunk_size
                    )

                    if not chunk:
                        break

                    f.write(chunk)

                    downloaded += len(chunk)

                    if total_size:

                        percent = (downloaded / total_size* 100)

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


def build_url(date_string, cycle, filename,settings):
    """
    Build the NOMADS GFS 0.25 degree GRIB filter URL.

    Example structure:
    https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl
        ?file=gfs.t00z.pgrb2.0p25.f012
        &all_var=on
        &all_lev=on
        &subregion=on
        &leftlon=5
        &rightlon=20
        &toplat=57
        &bottomlat=50
        &dir=/gfs.YYYYMMDD/00/atmos
    """

    yyyymmdd = date_string.replace("-", "")

    directory = (
        f"/gfs.{yyyymmdd}/"
        f"{cycle}/"
        f"atmos"
    )

    params = {
        "file": filename,

        "all_var": settings["all_var"],

        # Levels
        "all_lev": settings["all_lev"],

        # Geographic subset
        "subregion": settings["subregion"],
        "leftlon": settings["leftlon"],
        "rightlon": settings["rightlon"],
        "toplat": settings["toplat"],
        "bottomlat": settings["bottomlat"],

        # Source directory
        "dir": directory,
    }

    return (
        f"{BASE_URL}?"
        f"{urlencode(params)}"
    )


# ============================================================
# Download one GFS cycle
# ============================================================

def download_cycle(date_string, cycle, output_dir, settings):
    """
    Download the GFS analysis and 12, 24 and 48 hour
    forecast files for one cycle.

    Data is geographically subset to the region defined
    in settings.
    """

    success_all = True

    for name in FORECAST_FILES:

        filename = (
            f"gfs.t{cycle}z."
            f"pgrb2.0p25"
            f"{name}"
        )
        # build url
        url = build_url(date_string, cycle, filename, settings)

        output_file = Path(output_dir) / filename

        print(
            f"Downloading cycle "
            f"{cycle} UTC"
        )

        print(
            f"    File: {filename}"
        )
        # check if it already exists
        if output_file.exists():

            size_mb = (
                output_file.stat().st_size
                / (1024 ** 2)
            )
            # check
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

        print(f"    URL: {url}")

        success = download_file(url, output_file)

        if success:
            size_mb = (output_file.stat().st_size / (1024 ** 2))

            print(f"    Saved: {output_file}")

            print(
                f"    Size: "
                f"{size_mb:,.1f} MB"
            )

        else:
            # Remove invalid/incomplete file
            if output_file.exists():
                output_file.unlink()

            print("    Download failed.")

            success_all = False

    return success_all


# Download all cycles
def download_all_cycles(date_string, output_dir, settings):
    """
    Download GFS data for all configured cycles.
    NOMADS recommends a delay between repeated requests.
    """

    print("Starting downloads...")

    all_success = True

    for i, cycle in enumerate(CYCLES):
        
        print(f"[{i + 1}/{len(CYCLES)}]")

        success = download_cycle(date_string, cycle, output_dir, settings)

        if not success:
            all_success = False
        # wait
        if i < len(CYCLES) - 1:
            print("Waiting 10 seconds before next cycle...")
            time.sleep(10)
    return all_success

if __name__ == "__main__":

    settings = set_settings()

    date_obj = get_date()

    date_string = date_obj.strftime("%Y-%m-%d")

    BASE_PATH = Path(__file__).resolve().parent.parent.parent / "data"

    output_dir = (BASE_PATH / "GFS" / date_string)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading GFS data for {date_string}")
    # download
    success = download_all_cycles(date_string, output_dir, settings)

    if success:
        print("All downloads completed successfully.")
    else:
        print("One or more downloads failed.")

    print("Finished.")
