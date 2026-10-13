-- 11_launch_scorecard.sql
-- Do new sellers have a rough first month?
-- A first look showed more cancellations for new sellers than veterans,
-- but that is probably confounded: cancellation rates fell across the
-- whole platform over time, and veteran-seller orders skew toward later
-- (lower-cancellation) months. Test it within the same calendar month.
--
-- "New" sellers: those whose first order anywhere in the full Olist data
-- (not just this project's 86-week window, which starts 2 Jan 2017, close
-- to when the data itself begins in Sep 2016) falls on or after 1 Mar
-- 2017. Sellers already active before the window starts would otherwise
-- look artificially "new" just because their earlier orders are outside it.

create or replace view seller_first_order as
select i.seller_id, min(o.order_purchase_timestamp) as first_order_at
from order_items i
join orders o on o.order_id = i.order_id
group by i.seller_id;

create or replace view v_new_seller_orders as
select fos.*,
       sf.first_order_at,
       datediff('day', sf.first_order_at::date, fos.purchased_at::date)         as seller_age_days,
       case when datediff('day', sf.first_order_at::date, fos.purchased_at::date) < 30 then 'First 30 days'
            when datediff('day', sf.first_order_at::date, fos.purchased_at::date) < 90 then 'Days 31 to 90'
            else                                                                      'After day 90' end as tenure_bucket
from fct_order_seller fos
join seller_first_order sf on sf.seller_id = fos.seller_id
where sf.first_order_at >= timestamp '2017-03-01';

-- (a) First look: defect rate by tenure bucket, ignoring calendar time.
select tenure_bucket,
       count(*)                                                     as orders,
       count_if(outcome = 'cancelled')                              as cancelled,
       round(100.0 * count_if(outcome = 'cancelled') / count(*), 2) as cancel_pct
from v_new_seller_orders
group by tenure_bucket
order by case tenure_bucket when 'First 30 days' then 1 when 'Days 31 to 90' then 2 else 3 end;

-- (b) The confound, visible: cancellation rate falls across calendar
--     months regardless of seller age.
select date_trunc('month', purchased_at)::date                      as purchase_month,
       tenure_bucket,
       count(*)                                                     as orders,
       round(100.0 * count_if(outcome = 'cancelled') / count(*), 2) as cancel_pct
from v_new_seller_orders
group by 1, 2
order by 1, 2;

-- (c) The controlled test: compare "first 30 days" orders only against
--     "after day 90" orders from the SAME calendar month, then combine
--     across months (same stratified method as query 08e).
with strata as (
  select date_trunc('month', purchased_at)   as purchase_month,
         tenure_bucket,
         count(*)                            as orders,
         count_if(outcome = 'cancelled')     as cancelled
  from v_new_seller_orders
  where tenure_bucket in ('First 30 days', 'After day 90')
  group by 1, 2
)
select sum(n.orders)                                                                  as new_seller_orders,
       sum(n.cancelled)                                                               as new_seller_cancelled,
       round(100.0 * sum(n.cancelled) / sum(n.orders), 2)                             as new_seller_cancel_pct,
       sum(v.orders)                                                                  as veteran_orders_in_matched_months,
       sum(v.cancelled)                                                               as veteran_cancelled_in_matched_months,
       round(100.0 * sum(n.orders * 1.0 * v.cancelled / v.orders) / sum(n.orders), 2) as veteran_matched_cancel_pct
from strata n
join strata v
  on v.purchase_month = n.purchase_month
 and v.tenure_bucket = 'After day 90'
where n.tenure_bucket = 'First 30 days'
  and v.orders >= 30;
