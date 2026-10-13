-- 02_baseline_scorecard.sql
-- The headline numbers: where do 100 orders end up?
select count(*)                                                    as orders,
       count_if(outcome = 'delivered_on_time')                     as delivered_on_time,
       count_if(outcome = 'delivered_late')                        as delivered_late,
       count_if(outcome = 'cancelled')                             as cancelled,
       count_if(outcome = 'stalled')                               as stalled,
       round(100.0 * count_if(outcome = 'delivered_on_time') / count(*), 2) as perfect_order_pct,
       round(100.0 * count_if(outcome <> 'delivered_on_time') / count(*), 2) as defect_pct,
       round(100.0 * count_if(is_late) / count_if(is_delivered), 2)          as late_pct_of_delivered,
       round(100.0 * count_if(outcome = 'cancelled') / count(*), 2)          as cancel_pct,
       round(100.0 * count_if(outcome = 'stalled') / count(*), 2)            as stalled_pct,
       round(100.0 * count_if(is_late_handoff) / count_if(has_handoff), 2)   as late_handoff_pct
from fct_orders;
