-- 07_seller_scorecard.sql
-- Which sellers have a real handoff problem, as opposed to a few bad orders?
--
-- A seller with 3 late handoffs out of 10 is not provably worse than
-- the platform. So instead of ranking on the raw rate, each seller gets a
-- Wilson 95% lower bound: the lowest late-handoff rate that is still
-- plausible given their volume. A seller is flagged only when even that
-- lower bound sits above the platform rate.
create or replace table seller_scorecard as
with platform as (
  select 1.0 * count_if(is_late_handoff) / count_if(has_handoff) as platform_rate
  from fct_orders
),
per_seller as (
  select seller_id,
         seller_state,
         count(*)                                   as orders,
         count_if(has_handoff)                      as handoffs,
         count_if(is_late_handoff)                  as late_handoffs,
         count_if(is_late)                          as late_deliveries,
         count_if(late_cause = 'seller_handoff')    as seller_caused_late,
         count_if(late_cause = 'shared')            as shared_late,
         count_if(outcome = 'cancelled')            as cancelled,
         count_if(review_score <= 2)                as low_reviews,
         count(review_score)                        as reviewed
  from fct_order_seller
  group by seller_id, seller_state
  having count_if(has_handoff) >= 50               -- minimum volume to be scored
),
scored as (
  select s.*,
         p.platform_rate,
         1.0 * late_handoffs / handoffs             as late_handoff_rate,
         -- Wilson score interval, lower bound, z = 1.96
         ( (1.0 * late_handoffs / handoffs) + 1.96 * 1.96 / (2 * handoffs)
           - 1.96 * sqrt( ( (1.0 * late_handoffs / handoffs) * (1 - 1.0 * late_handoffs / handoffs)
                            + 1.96 * 1.96 / (4 * handoffs) ) / handoffs )
         ) / (1 + 1.96 * 1.96 / handoffs)           as wilson_lower
  from per_seller s
  cross join platform p
)
select *,
       (wilson_lower > platform_rate)               as is_flagged
from scored;

-- (a) How concentrated is the problem?
select count(*)                                                        as scored_sellers,
       count_if(is_flagged)                                            as flagged_sellers,
       round(100.0 * count_if(is_flagged) / count(*), 1)               as flagged_seller_pct,
       sum(handoffs)                                                   as scored_orders,
       round(100.0 * sum(case when is_flagged then handoffs end) / sum(handoffs), 1)           as flagged_share_of_orders_pct,
       round(100.0 * sum(case when is_flagged then late_handoffs end) / sum(late_handoffs), 1) as flagged_share_of_late_handoffs_pct,
       round(100 * max(platform_rate), 2)                              as platform_late_handoff_pct,
       round(100 * median(late_handoff_rate), 2)                       as median_seller_late_handoff_pct,
       round(100.0 * sum(case when is_flagged then late_handoffs end) / sum(case when is_flagged then handoffs end), 1) as flagged_late_handoff_pct
from seller_scorecard;

-- (b) The watchlist: flagged sellers ranked by late handoffs, the number
--     an account manager can act on.
select left(seller_id, 8)                              as seller,
       seller_state,
       handoffs                                        as orders,
       late_handoffs,
       round(100 * late_handoff_rate, 1)               as late_handoff_pct,
       round(100 * wilson_lower, 1)                    as wilson_lower_pct,
       round(100.0 * late_deliveries / handoffs, 1)    as late_delivery_pct,
       seller_caused_late + shared_late                as late_orders_with_late_handoff,
       round(100.0 * low_reviews / nullif(reviewed, 0), 1) as low_review_pct
from seller_scorecard
where is_flagged
order by late_handoffs desc
limit 15;

-- (c) Does a late handoff predict a late delivery? Platform level.
select case when is_late_handoff then 'Late handoff' else 'On-time handoff' end as handoff,
       count(*)                                        as delivered,
       round(100.0 * count_if(is_late) / count(*), 1)  as late_delivery_pct,
       round(100.0 * count_if(review_score <= 2) / count(review_score), 1) as low_review_pct
from fct_orders
where is_delivered and has_handoff
group by 1
order by 1 desc;
