# Olist Streamlit Dashboard

Streamlit dashboards on top of the dbt-modeled Olist Brazilian e-commerce dataset.

## Stack

- **Source data:** Olist 2016-2018 orders loaded into local Postgres
- **Transform layer:** dbt project at `../dbt_ecommerce/` (8 marts: `dim_customers`, `dim_customers_unique`, `dim_products`, `dim_sellers`, `fct_orders`, `fct_order_items`, `fct_payments`, `fct_reviews`)
- **App:** Streamlit + Plotly, queries Postgres directly in dev, parquet snapshots in deploy

## Run locally

```bash
source ~/.venvs/streamlit-olist/bin/activate
cd streamlit_app
streamlit run app.py
```

`.streamlit/secrets.toml` controls the data source — if `[postgres]` is set, the app queries the live warehouse; otherwise it falls back to parquet files in `data/marts/`.
