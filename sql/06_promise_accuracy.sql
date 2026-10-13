-- 06_promise_accuracy.sql
-- Late rate has two inputs: how fast the order moved, and what the customer
-- was promised. This separates them.

-- (a) Overall: how much slack is in the promise?
select round(median(promised_days), 1)                                         as promised_days_p50,
       round(median(datediff('minute', purchased_at, delivered_at) / 1440.0), 1) as actual_days_p50,
       round(median(-hours_past_deadline / 24.0), 1)                           as days_early_p50,
       round(100.0 * count_if(hours_past_deadline <= -7 * 24) / count(*), 1)   as arrived_7plus_days_early_pct,
       round(100.0 * count_if(is_late) / count(*), 1)                          as late_pct
from fct_orders
where is_delivered;

-- (b) By month: when the promise moves, the late rate moves with it.
select date_trunc('month', purchased_at)::date                                  as purchase_month,
       count(*)                                                                 as delivered,
       round(median(promised_days), 1)                                          as promised_days_p50,
       round(median(datediff('minute', purchased_at, delivered_at) / 1440.0), 1) as actual_days_p50,
       round(100.0 * count_if(is_late) / count(*), 1)                           as late_pct
from fct_orders
where is_delivered
group by 1
order by 1;

-- (c) By destination: the same promise policy is far too loose in some
--     states and too tight in others.
select customer_state,
       count(*)                                                                 as delivered,
       round(median(promised_days), 1)                                          as promised_days_p50,
       round(median(datediff('minute', purchased_at, delivered_at) / 1440.0), 1) as actual_days_p50,
       round(median(-hours_past_deadline / 24.0), 1)                            as days_early_p50,
       round(100.0 * count_if(is_late) / count(*), 1)                           as late_pct
from fct_orders
where is_delivered
group by customer_state
having count(*) >= 1000
order by late_pct desc;
