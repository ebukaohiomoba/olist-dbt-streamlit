{{ config (materialized='table')}}

with products as (
    select
        product_id,
        product_category,
        product_name_length,
        product_description_length,
        product_photos_qty,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm,
        (product_length_cm * product_height_cm * product_width_cm) as product_volume_cm3
    from {{ ref('stg_target_products')}}
),

category_map as (
    select
        product_category_raw,
        category_clean,
        category_group
    from {{ ref('seed_product_category_clean')}}
)

select
    p.product_id,
    p.product_category as product_category_raw,
    coalesce(cm.category_clean, 'Unknown')   as product_category,
    coalesce(cm.category_group, 'Unknown')   as category_group,
    p.product_name_length,
    p.product_description_length,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    p.product_volume_cm3
from products p
left join category_map cm
    on coalesce(p.product_category, '') = coalesce(cm.product_category_raw, '')
