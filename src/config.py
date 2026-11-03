"""Shared constants for the whole project (paths, years, seeds, column names)."""
from pathlib import Path

# Repository root: src/config.py -> parent of src/. No absolute paths anywhere.
ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = ROOT / "input_data"
RESULTS_DIR: Path = ROOT / "results"
DOCS_DIR: Path = ROOT / "docs"
CACHE_DIR: Path = ROOT / "cache"  # git-ignored

# Bump whenever src/data.py changes how the combined data is built.
CACHE_SCHEMA_VERSION: int = 1

SEED: int = 42
MIN_SUPPORT: int = 10  # used in Step 3
Z_CLIP: float = 10.0  # Step 3: scaled values are clipped to +-Z_CLIP (constant, not learned)

ALL_YEARS: tuple[int, ...] = tuple(range(2014, 2022))
TRAIN_YEARS: tuple[int, ...] = (2014, 2015, 2016)
TEST_YEARS: tuple[int, ...] = (2017, 2018, 2019, 2020, 2021)
TUNE_TRAIN_YEARS: tuple[int, ...] = (2014, 2015)
TUNE_VAL_YEAR: int = 2016

N_RAW_COLUMNS: int = 1849  # apkname + 1,848 API-call features
ID_COL: str = "apkname"
LABEL_COL: str = "label"
YEAR_COL: str = "year"
