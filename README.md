# Olist E-Commerce — dbt + Streamlit

End-to-end analytics pipeline on the Olist Brazilian e-commerce dataset (2016-2018, ~100K orders): raw CSVs → Postgres → dbt models → Streamlit dashboard.

**Live dashboard:** **https://olist-analytics-reporting.streamlit.app**

## Stack

- **Source:** Olist public dataset on [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) loaded into local Postgres
- **Transform:** dbt (Postgres adapter) — staging views over the raw schema, then star-schema marts
- **Serve:** Streamlit + Plotly, querying Postgres in dev and parquet snapshots in cloud deploy

## Repo layout

```
dbt_ecommerce/         # dbt project
  models/
    sources/           # raw schema definitions
    staging/target/    # typed staging views
    marts/             # star-schema dims + facts
  seeds/               # category translation seed
  data/                # raw Olist CSVs (gitignored — download from Kaggle)

streamlit_app/         # dashboard
  app.py               # executive overview
  utils/db.py          # Postgres-or-parquet loader
  data/marts/          # parquet snapshots used in deploy
  scripts/snapshot.py  # dump marts -> parquet for cloud deploy
  requirements.txt
```

## Mart layer

| Model | Grain |
|---|---|
| `dim_customers` | per-order customer record |
| `dim_customers_unique` | stable customer identity (use for CLV / retention) |
| `dim_products` | product, with cleaned category names from translation seed |
| `dim_sellers` | seller |
| `fct_orders` | one row per order, with item / payment / review rollups + delivery deltas |
| `fct_order_items` | one row per order line |
| `fct_payments` | one row per payment record |
| `fct_reviews` | one row per review with sentiment bucket and timing deltas |

## Run locally

**Prereqs:** Postgres running locally, Python 3.11+, `dbt-postgres` and a venv with the streamlit deps.

1. **Load raw data:** download the Olist dataset from Kaggle into `dbt_ecommerce/data/`, then load each CSV into a `raw` schema in your Postgres database `target_ecommerce_raw`.
2. **Build the marts:**
   ```bash
   cd dbt_ecommerce
   dbt seed
   dbt build
   ```
3. **Run the dashboard:**
   ```bash
   cp streamlit_app/.streamlit/secrets.toml.example streamlit_app/.streamlit/secrets.toml
   # edit secrets.toml with your Postgres password
   cd streamlit_app
   streamlit run app.py
   ```

## Deploy

The Streamlit dashboard is deployed to Streamlit Community Cloud. Cloud apps cannot reach localhost, so the dashboard reads from parquet snapshots in `streamlit_app/data/marts/` instead of querying Postgres directly. To refresh the deployed data:

```bash
python streamlit_app/scripts/snapshot.py
git add streamlit_app/data/marts/
git commit -m "Refresh mart snapshots"
git push
```
