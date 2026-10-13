-- 04_weekly_monitoring.sql
-- Weekly late-delivery rate with a control limit, so an alert means
-- "this week is statistically unusual", not "the number went up".
--
-- Method: p-chart. The expected rate is the median of the prior 26 weeks
-- (a median over half a year, so a bad month does not drag the baseline up
-- and hide the next one). The upper control limit is expected + 3 standard
-- errors for that week's volume. SEV1 = more than double the limit.
with weekly as (
  select purchase_week,
         count(*)                                              as orders,
         count_if(is_delivered)                                as delivered,
         count_if(is_late)                                     as late,
         1.0 * count_if(is_late) / count_if(is_delivered)      as late_rate,
         1.0 * count_if(is_late_handoff) / count_if(has_handoff) as late_handoff_rate,
         1.0 * count_if(outcome = 'cancelled') / count(*)      as cancel_rate,
         median(promised_days)                                 as promised_days_p50,
         median(case when is_delivered then handoff_days end)  as handoff_days_p50,
         median(case when is_delivered then transit_days end)  as transit_days_p50,
         quantile_cont(case when is_delivered then transit_days end, 0.9) as transit_days_p90
  from fct_orders
  group by purchase_week
),
with_baseline as (
  select w.*,
         median(late_rate) over (
           order by purchase_week
           rows between 26 preceding and 1 preceding
         ) as expected_rate,
         count(*) over (
           order by purchase_week
           rows between 26 preceding and 1 preceding
         ) as baseline_weeks
  from weekly w
)
select purchase_week,
       orders,
       round(100 * late_rate, 2)          as late_pct,
       round(100 * expected_rate, 2)      as expected_pct,
       round(100 * (expected_rate + 3 * sqrt(expected_rate * (1 - expected_rate) / delivered)), 2) as upper_limit_pct,
       case when baseline_weeks < 12 then 'warming up'
            when late_rate > 2 * (expected_rate + 3 * sqrt(expected_rate * (1 - expected_rate) / delivered)) then 'SEV1'
            when late_rate > expected_rate + 3 * sqrt(expected_rate * (1 - expected_rate) / delivered)     then 'alert'
            else 'ok' end                 as status,
       round(100 * late_handoff_rate, 2)  as late_handoff_pct,
       round(100 * cancel_rate, 2)        as cancel_pct,
       round(promised_days_p50, 1)        as promised_days_p50,
       round(handoff_days_p50, 1)         as handoff_days_p50,
       round(transit_days_p50, 1)         as transit_days_p50,
       round(transit_days_p90, 1)         as transit_days_p90
from with_baseline
order by purchase_week;
