from pathlib import Path


ROOT = Path(__file__).parents[2]

DATA_DIR = Path("data")

ZIP_DIR = ROOT / DATA_DIR


class Constants:
    """Object that holds constants necessary for the project."""
    ...