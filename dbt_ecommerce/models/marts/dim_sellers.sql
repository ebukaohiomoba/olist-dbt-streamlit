{{ config (materialized='table')}}

with sellers as (
    select
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state
    from {{ ref('stg_target_sellers')}}
)

select *
from sellers
