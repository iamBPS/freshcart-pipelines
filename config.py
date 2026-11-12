
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data"
LANDING_DIR = DATA_DIR / "landing"
WAREHOUSE_DIR = DATA_DIR / "warehouse"

DB_PATH = WAREHOUSE_DIR / "freshcart.duckdb"

SQL_DIR = PROJECT_ROOT / "sql"

# Create directories automatically
for folder in [LANDING_DIR, WAREHOUSE_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

DATABASE_MODE = "duckdb"
