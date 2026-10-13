-- 01_base_model.sql
-- Builds the two fact tables every other query reads from.
--   fct_orders        one row per order           (platform metrics)
--   fct_order_seller  one row per order x seller  (seller scorecards)
-- Dialect: DuckDB. Uses only functions that also exist in Snowflake
-- (date_trunc, datediff, count_if, qualify), so it ports with minimal edits.

-- Latest review per order. The raw table has 551 orders with more than one
-- review row, so joining it directly would double count those orders.
create or replace view stg_reviews as
select order_id, review_score, review_comment_message
from order_reviews
qualify row_number() over (
          partition by order_id
          order by review_answer_timestamp desc, review_id
        ) = 1;

-- Collapse line items to the order: the latest shipping limit is the
-- deadline the seller side had to meet for the whole order.
create or replace view stg_order_shipping as
select order_id,
       count(*)                 as item_count,
       count(distinct seller_id) as seller_count,
       max(shipping_limit_date) as shipping_limit_at,
       sum(price)               as item_value,
       sum(freight_value)       as freight_value
from order_items
group by order_id;

create or replace table fct_orders as
with base as (
  select o.order_id,
         o.order_status,
         o.order_purchase_timestamp                          as purchased_at,
         o.order_delivered_carrier_date                      as handed_to_carrier_at,
         o.order_delivered_customer_date                     as delivered_at,
         o.order_estimated_delivery_date                     as promised_date,
         -- the promise is a calendar day, so the deadline is the end of that day
         o.order_estimated_delivery_date + interval '1 day'  as promise_deadline_at,
         date_trunc('week', o.order_purchase_timestamp)::date as purchase_week,
         c.customer_unique_id,   -- the person; customer_id is unique per order in this data
         c.customer_state,
         s.item_count, s.seller_count, s.shipping_limit_at, s.item_value, s.freight_value,
         r.review_score
  from orders o
  join customers c               on c.customer_id = o.customer_id
  left join stg_order_shipping s on s.order_id = o.order_id
  left join stg_reviews r        on r.order_id = o.order_id
  -- 86 complete Monday-to-Sunday weeks. Earlier and later weeks hold a
  -- handful of orders each and would distort every rate.
  where o.order_purchase_timestamp >= timestamp '2017-01-02'
    and o.order_purchase_timestamp <  timestamp '2018-08-27'
)
select b.*,
       -- outcome: every order lands in exactly one bucket
       case when order_status in ('canceled', 'unavailable')              then 'cancelled'
            when order_status = 'delivered' and delivered_at is not null
                 and delivered_at >= promise_deadline_at                  then 'delivered_late'
            when order_status = 'delivered' and delivered_at is not null  then 'delivered_on_time'
            else 'stalled'   -- paid for, never delivered by the data snapshot
       end as outcome,
       (order_status = 'delivered' and delivered_at is not null)          as is_delivered,
       (order_status = 'delivered' and delivered_at is not null
          and delivered_at >= promise_deadline_at)                        as is_late,
       datediff('day', promised_date::date, delivered_at::date)           as days_late,
       datediff('minute', promise_deadline_at, delivered_at) / 60.0       as hours_past_deadline,
       -- seller handoff: did the parcel reach the carrier by the shipping limit?
       (handed_to_carrier_at is not null and shipping_limit_at is not null) as has_handoff,
       (handed_to_carrier_at > shipping_limit_at)                         as is_late_handoff,
       datediff('minute', shipping_limit_at, handed_to_carrier_at) / 60.0 as handoff_delay_hours,
       -- the three clocks
       datediff('minute', purchased_at, promise_deadline_at) / 1440.0     as promised_days,
       datediff('minute', purchased_at, handed_to_carrier_at) / 1440.0    as handoff_days,
       datediff('minute', handed_to_carrier_at, delivered_at) / 1440.0    as transit_days
from base b;

-- Who caused each late delivery? Counterfactual test: if the seller had
-- handed off exactly at the shipping limit, would the order have arrived
-- inside the promise?
alter table fct_orders add column late_cause varchar;
update fct_orders
set late_cause = case
      when not is_late                                   then null
      when not has_handoff                               then 'unknown'
      when is_late_handoff
           and handoff_delay_hours >= hours_past_deadline then 'seller_handoff'   -- on-time handoff would have saved it
      when is_late_handoff                                then 'shared'           -- late handoff AND slow transit
      else                                                     'carrier_or_promise' -- handed off on time, still late
    end;

-- Seller grain. An order with items from two sellers counts once for each
-- (1.3% of orders), so never sum this table to get platform totals.
create or replace table fct_order_seller as
select distinct
       i.seller_id,
       s.seller_state,
       f.*
from order_items i
join fct_orders f on f.order_id = i.order_id
join sellers s    on s.seller_id = i.seller_id;
