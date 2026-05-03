"""Data access layer.

Two modes:
- Postgres: when [postgres] is set in secrets.toml, queries the live warehouse.
- Parquet:  fallback for cloud deploys where localhost is unreachable.
            Reads parquet files from data/marts/<table>.parquet.
"""

from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

PARQUET_DIR = Path(__file__).resolve().parent.parent / "data" / "marts"


@st.cache_resource
def _engine():
    cfg = st.secrets["postgres"]
    schema = cfg.get("schema", "analytics")
    url = (
        f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"options": f"-csearch_path={schema}"},
    )


def _has_postgres() -> bool:
    try:
        return "postgres" in st.secrets
    except Exception:
        return False


@st.cache_data(ttl=600, show_spinner=False)
def query(sql: str) -> pd.DataFrame:
    """Run a SQL query against Postgres. Use only when _has_postgres()."""
    with _engine().connect() as conn:
        return pd.read_sql(text(sql), conn)


@st.cache_data(ttl=600, show_spinner=False)
def load_table(table: str) -> pd.DataFrame:
    """Load a full mart, from Postgres or parquet fallback."""
    if _has_postgres():
        schema = st.secrets["postgres"].get("schema", "analytics")
        return query(f'select * from {schema}."{table}"')
    path = PARQUET_DIR / f"{table}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"No Postgres config and no parquet snapshot at {path}. "
            f"Either configure .streamlit/secrets.toml or generate snapshots."
        )
    return pd.read_parquet(path)
