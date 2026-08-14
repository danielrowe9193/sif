from pathlib import Path
from datetime import datetime, timedelta
import requests
import time


BASE_URL = "https://data.ecmwf.int/forecasts"

ARCHIVE_ROOT = Path(__file__).resolve().parent.parent.parent / "data/IFS" # points to the data folder
ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)

# 00, 06, 12, 18 zz cycles
CYCLES = [0, 6, 12, 18]

# only 12, 24, and 48 hour forecasts
steps = [12, 24, 48]


def download_file(url: str, destination: Path, retries: int = 5):
    """
    Download one file, resuming an existing partial download where possible.
    """

    destination.parent.mkdir(parents=True, exist_ok=True)

    # Already downloaded
    if destination.exists():
        print(f"EXISTS  {destination}")
        return

    partial = destination.with_suffix(destination.suffix + ".part")

    for attempt in range(1, retries + 1):

        try:
            existing_size = partial.stat().st_size if partial.exists() else 0

            headers = {}

            if existing_size:
                headers["Range"] = f"bytes={existing_size}-"

            print(
                f"DOWNLOAD {url} "
                f"(attempt {attempt}/{retries})"
            )

            with requests.get(
                url,
                headers=headers,
                stream=True,
                timeout=120,
            ) as response:

                # if requested but server ignored, start over 
                if existing_size and response.status_code == 200:
                    existing_size = 0
                    partial.unlink(missing_ok=True)

                response.raise_for_status()

                mode = "ab" if existing_size else "wb"

                with open(partial, mode) as f:
                    for chunk in response.iter_content(
                        chunk_size=8 * 1024 * 1024
                    ):
                        if chunk:
                            f.write(chunk)

            partial.rename(destination)

            print(f"OK      {destination}")
            return

        except Exception as e:
            print(f"ERROR   {e}")

            if attempt < retries:
                sleep_time = 2 ** attempt
                print(f"Retrying in {sleep_time}s...")
                time.sleep(sleep_time)

    raise RuntimeError(f"Failed to download {url}")


def download_cycle(date, cycle):
    """
    Download 12, 24, and 48 hour IFS oper forecast cycle.
    """

    cycle_string = f"{cycle:02d}z"
    cycle_timestamp = (
        f"{date:%Y%m%d}{cycle:02d}0000"
    )

    directory = (
    ARCHIVE_ROOT
    / f"{date:%Y-%m-%d}"
    / cycle_string
    / "ifs"
    # / "forecast"
)

    for step in steps:

        filename = (
            f"{cycle_timestamp}"
            f"-{step}h-oper-fc.grib2"
        )

        url = (
            f"{BASE_URL}/"
            f"{date:%Y%m%d}/"
            f"{cycle_string}/"
            f"ifs/0p25/oper/"
            f"{filename}"
        )

        destination = directory / filename

        download_file(url, destination)

        # Download the index too
        index_url = url.replace(".grib2", ".index")
        index_destination = destination.with_suffix(".index")

        download_file(index_url, index_destination)


def download_date(date):
    print("=" * 70)
    print(f"Downloading IFS oper: {date:%Y-%m-%d}")
    print("=" * 70)

    for cycle in CYCLES:
        print()
        print(f"===== {cycle:02d} UTC =====")

        download_cycle(date, cycle)

if __name__ == "__main__":

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

    download_date(date)
