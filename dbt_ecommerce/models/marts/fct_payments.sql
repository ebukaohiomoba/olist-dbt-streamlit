{{ config (materialized='table')}}

with payments as (
    select
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    from {{ ref('stg_target_payments')}}
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
    p.order_id || '-' || p.payment_sequential as payment_key,
    p.order_id,
    p.payment_sequential,
    o.customer_id,
    o.order_status,
    o.order_purchase_ts,
    p.payment_type,
    p.payment_installments,
    p.payment_value,
    case when p.payment_installments > 1 then true else false end as is_installment_plan
from payments p
left join orders o
    on p.order_id = o.order_id
