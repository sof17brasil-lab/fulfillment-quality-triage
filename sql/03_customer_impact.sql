-- 03_customer_impact.sql
-- What does each defect cost in customer experience?
-- Review scores are 1 to 5; "low" means 1 or 2 stars.

-- (a) by outcome
select outcome,
       count(*)                                                      as orders,
       count(review_score)                                           as reviewed,
       round(avg(review_score), 2)                                   as avg_review,
       round(100.0 * count_if(review_score <= 2) / count(review_score), 1) as low_review_pct
from fct_orders
group by outcome
order by avg_review desc;

-- (b) by how late: where is the cliff?
select case when days_late <= 0  then '0 On time'
            when days_late <= 3  then '1 to 3 days late'
            when days_late <= 7  then '4 to 7 days late'
            when days_late <= 14 then '8 to 14 days late'
            else                      '15+ days late' end            as lateness,
       min(days_late)                                                as sort_key,
       count(*)                                                      as orders,
       round(avg(review_score), 2)                                   as avg_review,
       round(100.0 * count_if(review_score <= 2) / count(review_score), 1) as low_review_pct
from fct_orders
where is_delivered
group by 1
order by sort_key;
