-- 12_early_warning.sql
-- Can we see an episode coming? The late rate for a purchase week is only
-- known about three weeks later, once those orders are past their promise
-- deadline. A parcel stuck in transit can be seen the moment it happens.
-- This tests whether the share of parcels that have been in transit more
-- than 10 days, measured at each week's end, rises before the late-rate
-- monitor (query 04) flags the same episode.

-- For each of the 86 week-ending snapshots, look at every order handed to
-- the carrier by that point but not yet delivered (still "in transit" as
-- of that moment), and what share of them have been in transit more than
-- 10 days.
create or replace view v_weekly_transit as
with weeks as (
  select distinct purchase_week, purchase_week + interval 6 day as week_end
  from fct_orders
),
snapshot as (
  select w.purchase_week,
         w.week_end,
         count(*)                                                                       as in_transit,
         count_if(datediff('day', o.handed_to_carrier_at::date, w.week_end::date) > 10)  as in_transit_10plus
  from weeks w
  join fct_orders o
    on o.handed_to_carrier_at is not null
   and o.handed_to_carrier_at <= w.week_end
   and (o.delivered_at is null or o.delivered_at > w.week_end)
  group by w.purchase_week, w.week_end
)
select purchase_week, week_end, in_transit, in_transit_10plus
from snapshot
order by purchase_week;

-- (a) The weekly series with a control limit, the same p-chart method as
--     the late-rate monitor (query 04): expected = median of the prior 26
--     weeks, SEV1 = more than double the upper control limit.
create or replace table early_warning_weekly as
with with_baseline as (
  select t.*,
         1.0 * in_transit_10plus / in_transit                         as share_10plus,
         median(1.0 * in_transit_10plus / in_transit) over (
           order by purchase_week
           rows between 26 preceding and 1 preceding
         )                                                             as expected_share,
         count(*) over (
           order by purchase_week
           rows between 26 preceding and 1 preceding
         )                                                             as baseline_weeks
  from v_weekly_transit t
)
select purchase_week,
       week_end,
       in_transit,
       round(100 * share_10plus, 2)                                    as share_10plus_pct,
       round(100 * expected_share, 2)                                  as expected_pct,
       round(100 * (expected_share + 3 * sqrt(expected_share * (1 - expected_share) / in_transit)), 2) as upper_limit_pct,
       case when baseline_weeks < 12 then 'warming up'
            when share_10plus > 2 * (expected_share + 3 * sqrt(expected_share * (1 - expected_share) / in_transit)) then 'SEV1'
            when share_10plus > expected_share + 3 * sqrt(expected_share * (1 - expected_share) / in_transit)       then 'alert'
            else 'ok' end                                              as status
from with_baseline
order by purchase_week;

select * from early_warning_weekly;

-- (b) The 4 weeks immediately before each episode's late-rate SEV1 start
--     (same boundaries as queries 05 and 10), so the run-up is visible. A
--     useful early warning would show sustained 'alert' or 'SEV1' status
--     building in the weeks just before the late-rate monitor itself
--     fires -- not an isolated blip that fades again before the episode.
select 'Black Friday 2017'                                      as episode,
       purchase_week,
       datediff('week', purchase_week, date '2017-11-20')       as weeks_before_late_rate_sev1,
       share_10plus_pct,
       status
from early_warning_weekly
where purchase_week between date '2017-11-20' - interval 4 week and date '2017-11-20' - interval 1 week
union all
select 'Feb-Mar 2018',
       purchase_week,
       datediff('week', purchase_week, date '2018-02-12'),
       share_10plus_pct,
       status
from early_warning_weekly
where purchase_week between date '2018-02-12' - interval 4 week and date '2018-02-12' - interval 1 week
order by episode, purchase_week;
