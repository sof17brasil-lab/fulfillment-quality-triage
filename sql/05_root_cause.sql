-- 05_root_cause.sql
-- Two SEV1 episodes came out of the monitor (query 04). Same symptom,
-- late deliveries. This file asks whether they share a cause.
--   Black Friday 2017 : purchase weeks 2017-11-20 to 2017-12-04 (3 weeks)
--   Feb-Mar 2018      : purchase weeks 2018-02-12 to 2018-03-12 (5 weeks)
--   Normal weeks      : the other 78 weeks

create or replace view v_orders_period as
select f.*,
       case when purchased_at >= timestamp '2017-11-20' and purchased_at < timestamp '2017-12-11' then 'Black Friday 2017'
            when purchased_at >= timestamp '2018-02-12' and purchased_at < timestamp '2018-03-19' then 'Feb-Mar 2018'
            else 'Normal weeks' end as period
from fct_orders f;

-- (a) The operating picture in each period. If volume and handoff move,
--     the problem starts with sellers. If only transit moves, it does not.
select period,
       count(distinct purchase_week)                                    as weeks,
       round(count(*) * 1.0 / count(distinct purchase_week))            as orders_per_week,
       round(100.0 * count_if(is_late) / count_if(is_delivered), 1)     as late_pct,
       round(100.0 * count_if(is_late_handoff) / count_if(has_handoff), 1) as late_handoff_pct,
       round(median(case when is_delivered then handoff_days end), 1)   as handoff_days_p50,
       round(median(case when is_delivered then transit_days end), 1)   as transit_days_p50,
       round(quantile_cont(case when is_delivered then transit_days end, 0.9), 1) as transit_days_p90,
       round(median(promised_days), 1)                                  as promised_days_p50
from v_orders_period
group by period
order by late_pct;

-- (b) Who caused the late orders in each period?
select period,
       late_cause,
       count(*)                                                         as late_orders,
       round(100.0 * count(*) / sum(count(*)) over (partition by period), 1) as share_pct
from v_orders_period
where is_late and late_cause <> 'unknown'
group by period, late_cause
order by period, late_orders desc;

-- (c) Where did the excess land? For each customer state: late orders
--     above what that state's own normal rate would have produced.
with by_state as (
  select customer_state,
         period,
         count_if(is_delivered) as delivered,
         count_if(is_late)      as late
  from v_orders_period
  group by customer_state, period
),
pivoted as (
  select e.customer_state,
         e.period,
         e.delivered,
         e.late,
         1.0 * n.late / n.delivered                  as normal_rate,
         e.late - e.delivered * (1.0 * n.late / n.delivered) as excess_late
  from by_state e
  join by_state n
    on n.customer_state = e.customer_state
   and n.period = 'Normal weeks'
  where e.period <> 'Normal weeks'
)
select period,
       customer_state,
       delivered,
       round(100 * normal_rate, 1)                  as normal_late_pct,
       round(100.0 * late / delivered, 1)           as episode_late_pct,
       round(excess_late)                           as excess_late_orders,
       round(100 * excess_late / sum(excess_late) over (partition by period), 1) as share_of_excess_pct,
       round(100.0 * delivered / sum(delivered) over (partition by period), 1)   as share_of_volume_pct
from pivoted
qualify row_number() over (partition by period order by excess_late desc) <= 6
order by period, excess_late desc;
