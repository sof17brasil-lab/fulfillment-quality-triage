-- 13_dashboard_cube.sql
-- The data behind the filters. Pre-aggregated so the dashboard can filter
-- by week, destination state, outcome, and late cause without a server,
-- plus the seller watchlist table.

-- (a) By week, with the same control-chart band as the monitor (query 04),
--     so the chart can shade the normal range without recomputing it.
with weekly as (
  select purchase_week,
         count(*)                                                as orders,
         count_if(is_delivered)                                  as delivered,
         count_if(is_late)                                       as late,
         1.0 * count_if(is_late) / count_if(is_delivered)        as late_rate,
         count_if(outcome = 'cancelled')                         as cancelled,
         1.0 * count_if(is_late_handoff) / count_if(has_handoff) as late_handoff_rate
  from fct_orders
  group by purchase_week
),
with_baseline as (
  select w.*,
         median(late_rate) over (
           order by purchase_week rows between 26 preceding and 1 preceding
         )                                                        as expected_rate,
         count(*) over (
           order by purchase_week rows between 26 preceding and 1 preceding
         )                                                        as baseline_weeks
  from weekly w
)
select purchase_week,
       orders, delivered, late,
       round(100 * late_rate, 2)                              as late_pct,
       cancelled,
       round(100.0 * cancelled / orders, 2)                   as cancel_pct,
       round(100 * late_handoff_rate, 2)                      as late_handoff_pct,
       round(100 * expected_rate, 2)                          as expected_pct,
       round(100 * (expected_rate + 3 * sqrt(expected_rate * (1 - expected_rate) / delivered)), 2) as upper_limit_pct,
       case when baseline_weeks < 12 then 'warming up'
            when late_rate > 2 * (expected_rate + 3 * sqrt(expected_rate * (1 - expected_rate) / delivered)) then 'SEV1'
            when late_rate > expected_rate + 3 * sqrt(expected_rate * (1 - expected_rate) / delivered)       then 'alert'
            else 'ok' end                                     as status
from with_baseline
order by purchase_week;

-- (b) By destination state.
select customer_state,
       count(*)                                                     as orders,
       count_if(is_delivered)                                       as delivered,
       count_if(is_late)                                            as late,
       round(100.0 * count_if(is_late) / count_if(is_delivered), 2) as late_pct,
       count_if(outcome = 'cancelled')                              as cancelled
from fct_orders
group by customer_state
order by orders desc;

-- (c) By outcome.
select outcome,
       count(*)                                                            as orders,
       count(review_score)                                                 as reviewed,
       round(avg(review_score), 2)                                         as avg_review,
       round(100.0 * count_if(review_score <= 2) / count(review_score), 1) as low_review_pct
from fct_orders
group by outcome
order by orders desc;

-- (d) By late cause, platform-wide.
select late_cause,
       count(*)                                           as late_orders,
       round(100.0 * count(*) / sum(count(*)) over (), 1) as share_pct
from fct_orders
where is_late
group by late_cause
order by late_orders desc;

-- (e) All scored sellers (not just flagged), for the dot chart that shows
--     the flagged ones glowing among the rest. The dashboard filters this
--     client-side to build the flagged-only watchlist table (same rows as
--     query 07b), so one export covers both.
select left(seller_id, 8)                                  as seller,
       seller_state,
       handoffs                                            as orders,
       late_handoffs,
       round(100 * late_handoff_rate, 1)                   as late_handoff_pct,
       round(100 * wilson_lower, 1)                        as wilson_lower_pct,
       round(100.0 * late_deliveries / handoffs, 1)        as late_delivery_pct,
       seller_caused_late + shared_late                    as late_orders_with_late_handoff,
       round(100.0 * low_reviews / nullif(reviewed, 0), 1) as low_review_pct,
       is_flagged
from seller_scorecard
order by late_handoffs desc;
