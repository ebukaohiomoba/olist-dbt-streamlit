{{ config (materialized='table')}}

with customers as (
    select
        customer_id,
        customer_unique_id,
        customer_state,
        customer_city,
        customer_zip_code_prefix
    from {{ ref('dim_customers')}}
),

orders as (
    select
        order_id,
        customer_id,
        order_purchase_ts,
        order_status,
        item_count,
        items_subtotal,
        freight_total,
        payment_total
    from {{ ref('fct_orders')}}
),

joined as (
    select
        c.customer_unique_id,
        o.order_id,
        o.order_purchase_ts,
        o.order_status,
        o.item_count,
        o.items_subtotal,
        o.freight_total,
        o.payment_total,
        c.customer_state,
        c.customer_city,
        c.customer_zip_code_prefix
    from orders o
    join customers c on o.customer_id = c.customer_id
)

select
    customer_unique_id,
    count(distinct order_id)                                                          as total_orders,
    sum(case when order_status = 'delivered' then 1 else 0 end)                       as delivered_orders,
    sum(case when order_status = 'canceled'  then 1 else 0 end)                       as canceled_orders,
    min(order_purchase_ts)                                                            as first_order_ts,
    max(order_purchase_ts)                                                            as last_order_ts,
    extract(epoch from (max(order_purchase_ts) - min(order_purchase_ts))) / 86400.0   as days_active,
    sum(item_count)                                                                    as lifetime_item_count,
    sum(items_subtotal)                                                                as lifetime_items_subtotal,
    sum(freight_total)                                                                 as lifetime_freight_total,
    sum(payment_total)                                                                 as lifetime_payment_total,
    -- latest known location wins
    (array_agg(customer_state         order by order_purchase_ts desc nulls last))[1] as latest_customer_state,
    (array_agg(customer_city          order by order_purchase_ts desc nulls last))[1] as latest_customer_city,
    (array_agg(customer_zip_code_prefix order by order_purchase_ts desc nulls last))[1] as latest_customer_zip_code_prefix,
    count(distinct customer_state)                                                    as distinct_states_ordered_from
from joined
group by customer_unique_id
