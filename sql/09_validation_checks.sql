-- 09_validation_checks.sql
-- Every check returns one row: what was expected, what was found, PASS or FAIL.
-- Run this after any change. If a row says FAIL, no number on the site
-- can be trusted until it is explained.
select n, check_name, expected, actual,
       case when expected = actual then 'PASS' else 'FAIL' end as status
from (
  -- raw files are complete (row counts published with the dataset)
  select 1 as n, 'raw orders rows' as check_name, 99441 as expected, (select count(*) from orders) as actual
  union all select 2, 'raw order_items rows', 112650, (select count(*) from order_items)
  union all select 3, 'raw sellers rows', 3095, (select count(*) from sellers)
  union all select 4, 'raw customers rows', 99441, (select count(*) from customers)
  union all select 5, 'raw order_reviews rows', 99224, (select count(*) from order_reviews)
  -- grain: one row per order, nothing duplicated by a join
  union all select 6, 'fct_orders has one row per order (duplicates)', 0,
            (select count(*) - count(distinct order_id) from fct_orders)
  union all select 7, 'review staging has one row per order (duplicates)', 0,
            (select count(*) - count(distinct order_id) from stg_reviews)
  -- window: only the 86 complete weeks
  union all select 8, 'distinct purchase weeks', 86, (select count(distinct purchase_week) from fct_orders)
  union all select 9, 'orders outside the window', 0,
            (select count(*) from fct_orders
              where purchased_at < timestamp '2017-01-02' or purchased_at >= timestamp '2018-08-27')
  -- outcomes: every order lands in exactly one bucket
  union all select 10, 'orders with no outcome', 0, (select count(*) from fct_orders where outcome is null)
  union all select 11, 'outcome buckets add up to all orders (difference)', 0,
            (select count(*) - count_if(outcome in ('delivered_on_time','delivered_late','cancelled','stalled')) from fct_orders)
  -- the late flag agrees with a plain calendar-day comparison
  union all select 12, 'late flag disagrees with date comparison', 0,
            (select count(*) from fct_orders
              where is_delivered and is_late <> (delivered_at::date > promised_date::date))
  -- promises are whole calendar days, which the deadline logic relies on
  union all select 13, 'promised dates not at midnight', 0,
            (select count(*) from fct_orders where promised_date <> date_trunc('day', promised_date))
  -- every late order has a cause
  union all select 14, 'late orders with no cause assigned', 0,
            (select count(*) from fct_orders where is_late and late_cause is null)
  union all select 15, 'causes add up to late orders (difference)', 0,
            (select count_if(is_late) - count_if(late_cause is not null) from fct_orders)
  -- seller grain equals the distinct order-seller pairs in the window
  union all select 16, 'fct_order_seller rows vs distinct order-seller pairs (difference)', 0,
            (select (select count(*) from fct_order_seller)
                  - (select count(*) from (select distinct i.order_id, i.seller_id
                                           from order_items i join fct_orders f using (order_id))))
) checks
order by n;

-- Known oddities in the source data. Not failures, but they are disclosed.
select 'delivered orders with no delivery timestamp (counted as stalled)' as note,
       count(*) as orders
from fct_orders where order_status = 'delivered' and delivered_at is null
union all
select 'delivered before handed to carrier (timestamps out of order)',
       count(*) from fct_orders where is_delivered and delivered_at < handed_to_carrier_at
union all
select 'cancelled or unavailable orders with no line items (cannot be tied to a seller)',
       count(*) from fct_orders where outcome = 'cancelled' and item_count is null
union all
select 'orders with items from more than one seller',
       count(*) from fct_orders where seller_count > 1;
