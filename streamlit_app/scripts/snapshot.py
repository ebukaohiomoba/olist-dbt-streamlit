"""Dump dbt marts from Postgres to parquet for cloud deploy.

Streamlit Community Cloud cannot reach localhost, so we ship a frozen snapshot
of the marts in the repo. Re-run after rebuilding marts to refresh the data.

Usage:
    ~/.venvs/streamlit-olist/bin/python streamlit_app/scripts/snapshot.py
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

POSTGRES_URL = (
    "postgresql+psycopg2://chukwuebukaohiomoba:1234"
    "@localhost:5432/target_ecommerce_raw"
)
SCHEMA = "analytics"

# Marts the dashboard needs. Keep in sync with utils/db.py loaders.
MARTS = [
    "dim_customers",
    "dim_customers_unique",
    "dim_products",
    "dim_sellers",
    "fct_orders",
    "fct_order_items",
    "fct_payments",
    "fct_reviews",
]

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "marts"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(POSTGRES_URL)
    with engine.connect() as conn:
        for table in MARTS:
            df = pd.read_sql(text(f'select * from {SCHEMA}."{table}"'), conn)
            out = OUT_DIR / f"{table}.parquet"
            df.to_parquet(out, index=False, compression="zstd", compression_level=9)
            print(f"  {table:<25} {len(df):>8,} rows -> {out.name}")
    print(f"\nDone. Snapshots in {OUT_DIR}")


if __name__ == "__main__":
    main()
