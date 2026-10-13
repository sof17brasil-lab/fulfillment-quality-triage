-- 15_cancellation_trend.sql
-- Is the cancellation rate moving over time, or is it flat?
-- Cancellations are a defect the customer feels immediately, and the launch
-- scorecard (query 11) leans on the fact that the platform rate fell over
-- the window. This file measures that fall directly so the claim is not
-- resting on a side effect of another query.

-- (a) Monthly cancellation and stall rates.
select date_trunc('month', purchased_at)::date                        as purchase_month,
       count(*)                                                       as orders,
       count_if(outcome = 'cancelled')                                as cancelled,
       round(100.0 * count_if(outcome = 'cancelled') / count(*), 2)   as cancel_pct,
       count_if(outcome = 'stalled')                                  as stalled,
       round(100.0 * count_if(outcome = 'stalled') / count(*), 2)     as stalled_pct
from fct_orders
group by 1
order by 1;

-- (b) First half of the window against the second half. Splitting on the
--     median purchase date keeps the two sides comparable in order count
--     rather than in calendar length, since volume grew a lot.
with halves as (
  select case when purchased_at < (select median(purchased_at) from fct_orders)
              then 'First half' else 'Second half' end                as half,
         outcome
  from fct_orders
)
select half,
       count(*)                                                       as orders,
       count_if(outcome = 'cancelled')                                as cancelled,
       round(100.0 * count_if(outcome = 'cancelled') / count(*), 2)   as cancel_pct
from halves
group by half
order by half;

-- (c) The worst single month, for the callout.
select date_trunc('month', purchased_at)::date                        as purchase_month,
       count(*)                                                       as orders,
       count_if(outcome = 'cancelled')                                as cancelled,
       round(100.0 * count_if(outcome = 'cancelled') / count(*), 2)   as cancel_pct
from fct_orders
group by 1
having count(*) >= 500          -- ignore the thin opening months
qualify row_number() over (order by 100.0 * count_if(outcome = 'cancelled') / count(*) desc) = 1;
