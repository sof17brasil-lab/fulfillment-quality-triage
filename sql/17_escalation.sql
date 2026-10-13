-- 17_escalation.sql
-- Two escalations, worked end to end, because the two bad episodes had
-- different culprits and a quality team has to handle both:
--   1. a seller escalation  -- the flagged seller with the most late handoffs
--   2. a lane escalation    -- Rio de Janeiro during Feb-Mar 2018
--
-- Reads seller_scorecard (07) and v_orders_period (05).

-- The subject of the seller escalation, picked by the least flattering
-- rule available: of the flagged sellers, the one whose late handoffs
-- actually caused the most late deliveries. Ranking on late handoffs alone
-- would pick a seller whose handoff misses mostly got absorbed by slack in
-- the promise; ranking this way picks the one where fixing the handoff
-- genuinely saves the most orders, so the example cannot be accused of
-- being chosen to flatter the result.
create or replace table escalation_seller as
select *
from seller_scorecard
where is_flagged
qualify row_number() over (order by seller_caused_late desc, seller_id) = 1;

-- (a) The seller's case file.
select left(seller_id, 8)                                     as seller,
       seller_state,
       handoffs                                               as scored_orders,
       late_handoffs,
       round(100 * late_handoff_rate, 1)                      as late_handoff_pct,
       round(100 * platform_rate, 1)                          as platform_late_handoff_pct,
       round(100 * wilson_lower, 1)                           as wilson_lower_pct,
       late_deliveries,
       round(100.0 * late_deliveries / handoffs, 1)           as late_delivery_pct,
       seller_caused_late,
       shared_late,
       reviewed,
       round(100.0 * low_reviews / nullif(reviewed, 0), 1)    as low_review_pct
from escalation_seller;

-- (b) That seller month by month, so the escalation can say whether this is
--     a bad patch or a standing problem.
select date_trunc('month', f.purchased_at)::date                                      as month,
       count(*)                                                                       as orders,
       count_if(f.is_late_handoff)                                                    as late_handoffs,
       round(100.0 * count_if(f.is_late_handoff) / nullif(count_if(f.has_handoff), 0), 1) as late_handoff_pct
from fct_order_seller f
join escalation_seller e on e.seller_id = f.seller_id
group by 1
order by 1;

-- (c) The lane case file: Rio de Janeiro in each period, with both legs, so
--     the carrier story is visible rather than asserted.
select period,
       count_if(is_delivered)                                                   as delivered,
       count_if(is_late)                                                        as late,
       round(100.0 * count_if(is_late) / count_if(is_delivered), 1)             as late_pct,
       round(100.0 * count_if(is_late_handoff) / count_if(has_handoff), 1)      as late_handoff_pct,
       round(median(case when is_delivered then handoff_days end), 1)           as seller_leg_days_p50,
       round(median(case when is_delivered then transit_days end), 1)           as carrier_leg_days_p50
from v_orders_period
where customer_state = 'RJ'
group by period
order by late_pct;

-- (d) Rio month by month, to show the episode starting and ending.
select date_trunc('month', purchased_at)::date                                  as month,
       count_if(is_delivered)                                                   as delivered,
       round(100.0 * count_if(is_late) / nullif(count_if(is_delivered), 0), 1)  as late_pct,
       round(median(case when is_delivered then transit_days end), 1)           as carrier_leg_days_p50
from fct_orders
where customer_state = 'RJ'
group by 1
order by 1;

-- (e) What the lane escalation is worth: Rio's late orders during Feb-Mar
--     2018 above what Rio's own normal rate would have produced.
with rj as (
  select period,
         count_if(is_delivered) as delivered,
         count_if(is_late)      as late
  from v_orders_period
  where customer_state = 'RJ'
  group by period
)
select e.delivered                                              as episode_delivered,
       e.late                                                   as episode_late,
       round(100.0 * n.late / n.delivered, 1)                   as normal_late_pct,
       round(e.late - e.delivered * (1.0 * n.late / n.delivered)) as excess_late_orders
from rj e
cross join (select * from rj where period = 'Normal weeks') n
where e.period = 'Feb-Mar 2018';

-- (f) Does a late handoff cost reviews even when the parcel still arrives
--     inside the promise? Restricted to ON-TIME deliveries only, so
--     lateness cannot be doing the work. If the gap survives here, the
--     handoff miss is a defect in its own right, not just a lateness risk
--     factor -- which is what makes the seller escalation worth having
--     even though its lateness impact is small.
select case when is_late_handoff then 'Late handoff' else 'On-time handoff' end as handoff,
       count(*)                                                            as on_time_deliveries,
       count(review_score)                                                 as reviewed,
       round(avg(review_score), 2)                                         as avg_review,
       count_if(review_score <= 2)                                         as low_reviews,
       round(100.0 * count_if(review_score <= 2) / count(review_score), 1) as low_review_pct
from fct_orders
where is_delivered and not is_late and has_handoff
group by 1
order by 1 desc;

-- (g) The same test for the escalation seller alone. Small base, so the
--     counts are reported beside the rate and the page shows them.
select case when f.is_late_handoff then 'Late handoff' else 'On-time handoff' end as handoff,
       count(*)                                                                as on_time_deliveries,
       count(f.review_score)                                                   as reviewed,
       round(avg(f.review_score), 2)                                           as avg_review,
       count_if(f.review_score <= 2)                                           as low_reviews,
       round(100.0 * count_if(f.review_score <= 2) / nullif(count(f.review_score), 0), 1) as low_review_pct
from fct_order_seller f
join escalation_seller e on e.seller_id = f.seller_id
where f.is_delivered and not f.is_late and f.has_handoff
group by 1
order by 1 desc;

-- (h) The likely mechanism behind (f). These orders all arrived inside the
--     promise, so none of them is "late" -- but if a late handoff still
--     means the parcel turns up closer to the deadline, the customer
--     waited longer, which is the plausible reason the reviews are worse.
--     This measures the waiting, it does not prove the reviews follow
--     from it.
select case when is_late_handoff then 'Late handoff' else 'On-time handoff' end as handoff,
       count(*)                                                                    as on_time_deliveries,
       round(median(datediff('minute', purchased_at, delivered_at) / 1440.0), 1)   as total_days_p50,
       round(median(datediff('minute', delivered_at, promise_deadline_at) / 1440.0), 1) as days_early_p50
from fct_orders
where is_delivered and not is_late and has_handoff
group by 1
order by 1 desc;

-- (i) Rio's episode late rate against its own normal rate, as a difference
--     in percentage points, for the same reason as 16(d): the gap has to be
--     a checked number, not browser arithmetic.
with rj as (
  select period,
         100.0 * count_if(is_late) / count_if(is_delivered) as late_pct
  from v_orders_period
  where customer_state = 'RJ'
  group by period
)
select round(e.late_pct, 1)               as episode_late_pct,
       round(n.late_pct, 1)               as normal_late_pct,
       round(e.late_pct - n.late_pct, 1)  as late_pct_vs_normal
from rj e
cross join (select * from rj where period = 'Normal weeks') n
where e.period = 'Feb-Mar 2018';
