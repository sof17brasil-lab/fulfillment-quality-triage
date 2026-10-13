-- 08_repeat_purchase.sql
-- What is a late order worth? Test: after a customer's FIRST delivered
-- order, do they come back less often when that order was late?
--
-- Fair-comparison rules:
--   * the clock starts at delivery, when the customer knows the outcome
--   * every customer gets the same follow-up window (90 or 180 days)
--   * customers whose window runs past the end of the data are excluded,
--     otherwise recent customers would look like non-repeaters
create or replace table fct_customer_first as
with ranked as (
  select f.*,
         row_number() over (partition by customer_unique_id
                            order by purchased_at, order_id) as order_rank
  from fct_orders f
)
select r.customer_unique_id,
       r.order_id,
       r.customer_state,
       r.purchased_at,
       r.delivered_at,
       r.is_late,
       r.days_late,
       exists (select 1 from fct_orders n
               where n.customer_unique_id = r.customer_unique_id
                 and n.purchased_at >  r.delivered_at
                 and n.purchased_at <= r.delivered_at + interval '90 day')  as repeated_90,
       exists (select 1 from fct_orders n
               where n.customer_unique_id = r.customer_unique_id
                 and n.purchased_at >  r.delivered_at
                 and n.purchased_at <= r.delivered_at + interval '180 day') as repeated_180
from ranked r
where r.order_rank = 1
  and r.is_delivered;

-- (a) Context: how often does anyone reorder at all?
select count(distinct customer_unique_id)                                    as customers,
       round(100.0 * count(distinct case when n > 1 then customer_unique_id end)
                   / count(distinct customer_unique_id), 2)                  as ordered_more_than_once_pct
from (select customer_unique_id, count(*) over (partition by customer_unique_id) as n
      from fct_orders);

-- (b) Repeat rate within 180 days, late vs on-time first order
select case when is_late then 'Late first order' else 'On-time first order' end as first_order,
       count(*)                                         as customers,
       count_if(repeated_180)                           as repeaters,
       round(100.0 * count_if(repeated_180) / count(*), 2) as repeat_pct
from fct_customer_first
where delivered_at + interval '180 day' <= timestamp '2018-08-27'
group by 1
order by 1 desc;

-- (c) Same test with a 90-day window (more customers qualify)
select case when is_late then 'Late first order' else 'On-time first order' end as first_order,
       count(*)                                         as customers,
       count_if(repeated_90)                            as repeaters,
       round(100.0 * count_if(repeated_90) / count(*), 2) as repeat_pct
from fct_customer_first
where delivered_at + interval '90 day' <= timestamp '2018-08-27'
group by 1
order by 1 desc;

-- (d) Dose-response: does it get worse as the order gets later?
select case when days_late <= 0 then '0 On time'
            when days_late <= 3 then '1 to 3 days late'
            when days_late <= 7 then '4 to 7 days late'
            else                     '8+ days late' end as lateness,
       min(days_late)                                   as sort_key,
       count(*)                                         as customers,
       count_if(repeated_180)                           as repeaters,
       round(100.0 * count_if(repeated_180) / count(*), 2) as repeat_pct
from fct_customer_first
where delivered_at + interval '180 day' <= timestamp '2018-08-27'
group by 1
order by sort_key;

-- (e) Control for where and when. Late orders cluster in certain states
--     and months, and those customers might reorder less anyway. So compare
--     each late customer only with on-time customers from the same state
--     and purchase month, then add up.
with strata as (
  select customer_state,
         date_trunc('month', purchased_at) as purchase_month,
         is_late,
         count(*)               as customers,
         count_if(repeated_180) as repeaters
  from fct_customer_first
  where delivered_at + interval '180 day' <= timestamp '2018-08-27'
  group by 1, 2, 3
)
select sum(l.customers)                                              as late_customers,
       sum(l.repeaters)                                              as late_repeaters_actual,
       round(sum(l.customers * 1.0 * o.repeaters / o.customers), 1)  as late_repeaters_expected_if_on_time,
       round(100.0 * sum(l.repeaters) / sum(l.customers), 2)         as late_repeat_pct,
       round(100.0 * sum(l.customers * 1.0 * o.repeaters / o.customers) / sum(l.customers), 2) as matched_on_time_repeat_pct
from strata l
join strata o
  on o.customer_state = l.customer_state
 and o.purchase_month = l.purchase_month
 and not o.is_late
where l.is_late
  and o.customers >= 30;   -- need a reasonable comparison group
