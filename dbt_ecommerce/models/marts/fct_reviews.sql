{{ config (materialized='table')}}

with reviews as (
    select
        review_id,
        order_id,
        review_score,
        review_comment_title,
        review_creation_ts,
        review_answer_ts
    from {{ ref('stg_target_order_reviews')}}
),

orders as (
    select
        order_id,
        customer_id,
        order_status,
        order_purchase_ts,
        order_delivered_customer_ts
    from {{ ref('stg_target_orders')}}
)

select
    r.review_id || '-' || r.order_id as review_key,
    r.review_id,
    r.order_id,
    o.customer_id,
    o.order_status,
    r.review_score,
    case
        when r.review_score >= 4 then 'positive'
        when r.review_score = 3 then 'neutral'
        when r.review_score <= 2 then 'negative'
    end as review_sentiment,
    r.review_comment_title,
    case when r.review_comment_title is not null and r.review_comment_title <> '' then true else false end as has_comment_title,
    r.review_creation_ts,
    r.review_answer_ts,
    extract(epoch from (r.review_answer_ts - r.review_creation_ts)) / 3600.0 as hours_to_response,
    extract(epoch from (r.review_creation_ts - o.order_delivered_customer_ts)) / 86400.0 as days_after_delivery
from reviews r
left join orders o
    on r.order_id = o.order_id
