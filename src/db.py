
import duckdb
from config import DB_PATH


def get_connection():
    """Create a connection to the local FreshCart database."""
    return duckdb.connect(str(DB_PATH))


def execute_sql(sql):
    """Execute a SQL statement."""
    with get_connection() as conn:
        return conn.execute(sql)


def query_df(sql):
    """Execute SQL and return a Pandas DataFrame."""
    with get_connection() as conn:
        return conn.execute(sql).df()


def run_sql_file(file_path):
    """Execute a SQL file."""
    with get_connection() as conn:
        conn.execute(file_path.read_text(encoding="utf-8"))


def initialize_database():
    """Initialize the local database."""
    with get_connection() as conn:
        conn.execute("""
            CREATE SCHEMA IF NOT EXISTS bronze;
            CREATE SCHEMA IF NOT EXISTS silver;
            CREATE SCHEMA IF NOT EXISTS dim;
            CREATE SCHEMA IF NOT EXISTS ref;
            CREATE SCHEMA IF NOT EXISTS gold;
            CREATE SCHEMA IF NOT EXISTS quarantine;
        """)

    print("FreshCart DuckDB database initialized.")
