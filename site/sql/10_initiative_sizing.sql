-- 10_initiative_sizing.sql
-- What is each fix worth? Three options, sized side by side in late
-- orders avoided and low reviews avoided (where that can be estimated
-- from the data), then ranked.

-- (a) Seller handoff program. Bring each flagged seller's late-handoff
--     rate down to the platform rate (8.96%, query 02). Only late orders
--     where an on-time handoff alone would have saved them (late_cause =
--     'seller_handoff') count as avoidable, scaled by how much of that
--     seller's late handoffs sit above the platform rate.
create or replace table initiative_seller_program as
with flagged as (
  select seller_id, platform_rate, handoffs, late_handoffs, seller_caused_late
  from seller_scorecard
  where is_flagged
),
review_rate as (
  select 1.0 * count_if(fo.review_score <= 2) / nullif(count(fo.review_score), 0) as low_review_rate
  from fct_order_seller fo
  join flagged f on f.seller_id = fo.seller_id
  where fo.late_cause = 'seller_handoff'
)
select 'Seller handoff program'                                        as initiative,
       round(sum(greatest(f.late_handoffs - f.handoffs * f.platform_rate, 0)
                 / nullif(f.late_handoffs, 0) * f.seller_caused_late))  as late_orders_avoided,
       round(sum(greatest(f.late_handoffs - f.handoffs * f.platform_rate, 0)
                 / nullif(f.late_handoffs, 0) * f.seller_caused_late)
             * max(r.low_review_rate))                                 as low_reviews_avoided
from flagged f cross join review_rate r;

select * from initiative_seller_program;

-- (b) Episode response. During the two flagged episodes, how many late
--     orders were late by 3 days or less, and by 7 days or less? That is
--     what a temporary longer promise would have covered. The two
--     episodes are not equally actionable, so they are sized separately:
--       - Black Friday is a calendar event a team can plan for ahead of
--         time, so it is counted in full.
--       - Feb-Mar 2018 was not predictable, and the early-warning test
--         (query 12) found no useful lead time. A purchase week's late
--         rate is not actually known until its orders are due, so only
--         orders purchased after that point could realistically have
--         gotten a longer promise. The real detection delay is taken from
--         the dataset's own median promise length (24.2 days, query 06a):
--         the episode's first SEV1 week (12 Feb 2018) would not have been
--         confirmed as a problem until about 8 Mar 2018.
--     It cannot price the lost conversions from offering a longer promise
--     up front, so that cost is not sized here.
create or replace table initiative_episode_response as
with detection as (
  select date '2018-02-12'
         + cast(round((select median(promised_days) from fct_orders)) as integer) * interval 1 day
         as feb_mar_detected_at
),
parts as (
  select 'Black Friday 2017 (planned ahead, counted in full)'             as part,
         count_if(is_late and days_late <= 7)                            as late_orders_avoided,
         count_if(is_late and days_late <= 3)                            as late_orders_avoided_3d_cap,
         count_if(is_late and days_late <= 7 and review_score <= 2)      as low_reviews_avoided
  from fct_orders
  where purchased_at >= timestamp '2017-11-20' and purchased_at < timestamp '2017-12-11'
  union all
  select 'Feb-Mar 2018 (orders purchased after the real detection delay)' as part,
         count_if(is_late and days_late <= 7)                            as late_orders_avoided,
         count_if(is_late and days_late <= 3)                            as late_orders_avoided_3d_cap,
         count_if(is_late and days_late <= 7 and review_score <= 2)      as low_reviews_avoided
  from fct_orders, detection
  where purchased_at >= timestamp '2018-02-12' and purchased_at < timestamp '2018-03-19'
    and purchased_at >= feb_mar_detected_at
)
select 'Episode response (temporary longer promise)' as initiative, part,
       late_orders_avoided, late_orders_avoided_3d_cap, low_reviews_avoided
from parts
union all
select 'Episode response (temporary longer promise)', 'Total (both parts)',
       sum(late_orders_avoided), sum(late_orders_avoided_3d_cap), sum(low_reviews_avoided)
from parts;

select * from initiative_episode_response;

-- (c) Lane-level promise. The same question, limited to the destination
--     states with the highest late rate -- but picked from data BEFORE
--     each episode, not the episode weeks themselves, so the pick is
--     something a team could actually have made in advance. Each episode
--     gets its own top-5 list from its own history (at least 300
--     delivered orders in that state beforehand, so the rate is not a
--     small-sample fluke), then the two are sized and totalled the same
--     way as the episode-response option above (Black Friday in full,
--     Feb-Mar from the real detection delay onward).
create or replace table initiative_lane_promise as
with detection as (
  select date '2018-02-12'
         + cast(round((select median(promised_days) from fct_orders)) as integer) * interval 1 day
         as feb_mar_detected_at
),
state_rates_before_bf as (
  select customer_state,
         count_if(is_delivered)                          as delivered,
         1.0 * count_if(is_late) / count_if(is_delivered) as late_rate
  from fct_orders
  where purchased_at < timestamp '2017-11-20'
  group by customer_state
  having count_if(is_delivered) >= 300
),
top_states_bf as (
  select customer_state from state_rates_before_bf order by late_rate desc limit 5
),
state_rates_before_fm as (
  select customer_state,
         count_if(is_delivered)                          as delivered,
         1.0 * count_if(is_late) / count_if(is_delivered) as late_rate
  from fct_orders
  where purchased_at < timestamp '2018-02-12'
  group by customer_state
  having count_if(is_delivered) >= 300
),
top_states_fm as (
  select customer_state from state_rates_before_fm order by late_rate desc limit 5
),
parts as (
  select 'Black Friday 2017 (states picked from data before 20 Nov 2017, counted in full)' as part,
         count_if(o.is_late and o.days_late <= 7)                         as late_orders_avoided,
         count_if(o.is_late and o.days_late <= 3)                         as late_orders_avoided_3d_cap,
         count_if(o.is_late and o.days_late <= 7 and o.review_score <= 2) as low_reviews_avoided
  from fct_orders o
  join top_states_bf ts on ts.customer_state = o.customer_state
  where o.purchased_at >= timestamp '2017-11-20' and o.purchased_at < timestamp '2017-12-11'
  union all
  select 'Feb-Mar 2018 (states picked from data before 12 Feb 2018; orders after the real detection delay)' as part,
         count_if(o.is_late and o.days_late <= 7)                         as late_orders_avoided,
         count_if(o.is_late and o.days_late <= 3)                         as late_orders_avoided_3d_cap,
         count_if(o.is_late and o.days_late <= 7 and o.review_score <= 2) as low_reviews_avoided
  from fct_orders o
  join top_states_fm ts on ts.customer_state = o.customer_state
  cross join detection
  where o.purchased_at >= timestamp '2018-02-12' and o.purchased_at < timestamp '2018-03-19'
    and o.purchased_at >= feb_mar_detected_at
)
select 'Lane-level promise (top 5 late-rate states, picked beforehand)' as initiative, part,
       late_orders_avoided, late_orders_avoided_3d_cap, low_reviews_avoided
from parts
union all
select 'Lane-level promise (top 5 late-rate states, picked beforehand)', 'Total (both parts)',
       sum(late_orders_avoided), sum(late_orders_avoided_3d_cap), sum(low_reviews_avoided)
from parts;

select * from initiative_lane_promise;

-- (d) Which states were picked for each episode, for reference -- each
--     list comes only from data before that episode started.
select 'Before Black Friday 2017 (used for that episode)' as used_for, customer_state,
       delivered, round(100 * late_rate, 1) as late_pct
from (
  select customer_state,
         count_if(is_delivered)                          as delivered,
         1.0 * count_if(is_late) / count_if(is_delivered) as late_rate
  from fct_orders
  where purchased_at < timestamp '2017-11-20'
  group by customer_state
  having count_if(is_delivered) >= 300
)
order by late_rate desc
limit 5;

select 'Before Feb-Mar 2018 (used for that episode)' as used_for, customer_state,
       delivered, round(100 * late_rate, 1) as late_pct
from (
  select customer_state,
         count_if(is_delivered)                          as delivered,
         1.0 * count_if(is_late) / count_if(is_delivered) as late_rate
  from fct_orders
  where purchased_at < timestamp '2018-02-12'
  group by customer_state
  having count_if(is_delivered) >= 300
)
order by late_rate desc
limit 5;

-- (e) Rank the three by late orders avoided (the episode-response and
--     lane-level totals, both episodes combined).
select initiative, late_orders_avoided, low_reviews_avoided,
       rank() over (order by late_orders_avoided desc) as rank_by_late_orders_avoided
from (
  select initiative, late_orders_avoided, low_reviews_avoided from initiative_seller_program
  union all
  select initiative, late_orders_avoided, low_reviews_avoided from initiative_episode_response where part = 'Total (both parts)'
  union all
  select initiative, late_orders_avoided, low_reviews_avoided from initiative_lane_promise where part = 'Total (both parts)'
)
order by late_orders_avoided desc;
