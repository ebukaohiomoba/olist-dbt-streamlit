{{ config (materialized='table')}}

with orders as (
    select
        order_id,
        customer_id,
        order_status,
        order_purchase_ts,
        order_approved_ts,
        order_delivered_carrier_ts,
        order_delivered_customer_ts,
        order_estimated_delivery_ts
    from {{ ref('stg_target_orders')}}
),

item_totals as (
    select
        order_id,
        count(*) as item_count,
        count(distinct product_id) as distinct_product_count,
        count(distinct seller_id) as distinct_seller_count,
        sum(price) as items_subtotal,
        sum(freight_value) as freight_total
    from {{ ref('stg_target_order_items')}}
    group by order_id
),

payment_totals as (
    select
        order_id,
        count(*) as payment_count,
        sum(payment_value) as payment_total,
        max(payment_installments) as max_installments
    from {{ ref('stg_target_payments')}}
    group by order_id
),

review_summary as (
    select
        order_id,
        avg(review_score) as avg_review_score,
        max(review_score) as latest_review_score,
        count(*) as review_count
    from {{ ref('stg_target_order_reviews')}}
    group by order_id
)

select
    o.order_id,
    o.customer_id,
    o.order_status,

    o.order_purchase_ts,
    o.order_approved_ts,
    o.order_delivered_carrier_ts,
    o.order_delivered_customer_ts,
    o.order_estimated_delivery_ts,

    -- delivery deltas
    extract(epoch from (o.order_approved_ts - o.order_purchase_ts)) / 3600.0 as hours_to_approval,
    extract(epoch from (o.order_delivered_customer_ts - o.order_purchase_ts)) / 86400.0 as days_to_delivery,
    extract(epoch from (o.order_delivered_customer_ts - o.order_estimated_delivery_ts)) / 86400.0 as days_late_vs_estimate,
    case
        when o.order_delivered_customer_ts is null then null
        when o.order_delivered_customer_ts <= o.order_estimated_delivery_ts then true
        else false
    end as delivered_on_time,

    -- item-level rollups
    coalesce(it.item_count, 0) as item_count,
    coalesce(it.distinct_product_count, 0) as distinct_product_count,
    coalesce(it.distinct_seller_count, 0) as distinct_seller_count,
    it.items_subtotal,
    it.freight_total,

    -- payment-level rollups
    coalesce(pt.payment_count, 0) as payment_count,
    pt.payment_total,
    pt.max_installments,

    -- review summary
    rs.avg_review_score,
    rs.latest_review_score,
    coalesce(rs.review_count, 0) as review_count

from orders o
left join item_totals it       on o.order_id = it.order_id
left join payment_totals pt    on o.order_id = pt.order_id
left join review_summary rs    on o.order_id = rs.order_id
