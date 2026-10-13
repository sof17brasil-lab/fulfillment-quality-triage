-- 16_order_timeline.sql
-- Where do the days actually go?
-- An order has two legs: the seller leg (purchase to carrier handoff) and
-- the carrier leg (handoff to the customer's door). Laying both against the
-- promise, per period, shows which leg stretched in which episode. This is
-- the chart that separates "the sellers were slow" from "the carrier was".
--
-- Reads v_orders_period, the period view defined in 05_root_cause.sql.

-- (a) The timeline per period. Medians, because a handful of 100-day
--     outliers would drag a mean and hide the shape.
select period,
       count_if(is_delivered)                                                as delivered,
       round(median(case when is_delivered then handoff_days end), 1)        as seller_leg_days_p50,
       round(median(case when is_delivered then transit_days end), 1)        as carrier_leg_days_p50,
       round(median(case when is_delivered
                         then datediff('minute', purchased_at, delivered_at) / 1440.0
                    end), 1)                                                 as total_days_p50,
       round(median(promised_days), 1)                                       as promised_days_p50,
       round(median(case when is_delivered
                         then datediff('minute', purchased_at, delivered_at) / 1440.0
                    end) - median(promised_days), 1)                         as days_inside_promise_p50
from v_orders_period
group by period
order by total_days_p50;

-- (b) The 90th percentile of each leg, per period. The median says what a
--     typical order did; the tail says what the unlucky ones did, and it is
--     the tail that breaks a promise.
select period,
       round(quantile_cont(case when is_delivered then handoff_days end, 0.9), 1)  as seller_leg_days_p90,
       round(quantile_cont(case when is_delivered then transit_days end, 0.9), 1)  as carrier_leg_days_p90,
       round(quantile_cont(case when is_delivered
                                then datediff('minute', purchased_at, delivered_at) / 1440.0
                           end, 0.9), 1)                                           as total_days_p90
from v_orders_period
group by period
order by total_days_p90;

-- (c) How much each leg moved against normal weeks, in days. Positive means
--     slower than normal.
with per_period as (
  select period,
         median(case when is_delivered then handoff_days end)  as seller_leg,
         median(case when is_delivered then transit_days end)  as carrier_leg
  from v_orders_period
  group by period
)
select p.period,
       round(p.seller_leg  - n.seller_leg, 1)   as seller_leg_vs_normal_days,
       round(p.carrier_leg - n.carrier_leg, 1)  as carrier_leg_vs_normal_days
from per_period p
cross join (select * from per_period where period = 'Normal weeks') n
where p.period <> 'Normal weeks'
order by p.period;

-- (d) Each episode's late rate against normal weeks, as a difference in
--     percentage points. The two rates are already in the ledger; the gap
--     between them was not, and a stat card that shows a change needs the
--     change itself to be a checked number rather than arithmetic done in
--     the browser.
with by_period as (
  select period,
         count_if(is_delivered)                                as delivered,
         100.0 * count_if(is_late) / count_if(is_delivered)    as late_pct
  from v_orders_period
  group by period
)
select p.period,
       round(p.late_pct, 1)               as late_pct,
       round(n.late_pct, 1)               as normal_late_pct,
       round(p.late_pct - n.late_pct, 1)  as late_pct_vs_normal
from by_period p
cross join (select * from by_period where period = 'Normal weeks') n
where p.period <> 'Normal weeks'
order by p.period;
