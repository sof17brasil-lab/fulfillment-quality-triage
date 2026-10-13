-- 14_customer_reviews.sql
-- Which real reviews should the "what customers said" section show? A
-- fair, documented rule: among low-star (1-2) reviews on late orders that
-- have review text and mention the delay (the words "atras-" or "demor-",
-- which cover "atraso/atrasou/atrasado" and "demora/demorou/demorado"),
-- order deterministically by a hash of the review id with a fixed salt
-- (so the same 8 reviews come out every run) and take the top 8. The
-- dashboard shows a subset of these after Sofia reads and approves the
-- translations; none are hand-picked for drama.
select r.order_id,
       f.days_late,
       r.review_score,
       r.review_comment_title,
       r.review_comment_message
from fct_orders f
join order_reviews r on r.order_id = f.order_id
where f.is_late
  and r.review_score <= 2
  and r.review_comment_message is not null
  and length(trim(r.review_comment_message)) > 0
  and (lower(r.review_comment_message) like '%atras%'
    or lower(r.review_comment_message) like '%demor%')
order by hash(r.review_id || 'fulfillment-quality-triage-2026')
limit 8;
