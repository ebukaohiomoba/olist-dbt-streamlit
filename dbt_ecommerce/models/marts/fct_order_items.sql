{{ config (materialized='table')}}

with order_items as (
    select
        order_id,
        order_item_id,
        product_id,
        seller_id,
        shipping_limit_ts,
        price,
        freight_value
    from {{ ref('stg_target_order_items')}}
),

orders as (
    select
        order_id,
        customer_id,
        order_status,
        order_purchase_ts
    from {{ ref('stg_target_orders')}}
)

select
    oi.order_id || '-' || oi.order_item_id as order_item_key,
    oi.order_id,
    oi.order_item_id,
    o.customer_id,
    oi.product_id,
    oi.seller_id,
    o.order_status,
    o.order_purchase_ts,
    oi.shipping_limit_ts,
    oi.price,
    oi.freight_value,
    (oi.price + oi.freight_value) as item_total
from order_items oi
left join orders o
    on oi.order_id = o.order_id
