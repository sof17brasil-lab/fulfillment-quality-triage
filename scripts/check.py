"""Step 4. Prove the numbers.

    python scripts/check.py            # check this run
    python scripts/check.py --freeze   # save this run as the new reference (only after review)

Three tests, all must pass:
  1. every row in sql/09_validation_checks.sql says PASS
  2. the SQL result and the independent pandas result agree for every ledger number
  3. this run matches the frozen reference in reference/numbers_ledger.csv

It also writes out/numbers_ledger.csv: one row per number used in the write-up,
with where it comes from. Any number on the website must be in that file.
"""
import csv
import json
import pathlib
import sys
from math import erf, sqrt

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
REF = ROOT / "reference" / "numbers_ledger.csv"


def load(name):
    return json.loads((OUT / f"{name}.json").read_text())


def row(result_set, **where):
    matches = [r for r in result_set if all(r[k] == v for k, v in where.items())]
    assert len(matches) == 1, f"expected exactly one row for {where}, found {len(matches)}"
    return matches[0]


def two_proportion_p(a, n1, b, n2):
    """Two-sided p-value for the difference between a/n1 and b/n2."""
    pooled = (a + b) / (n1 + n2)
    se = sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    z = (a / n1 - b / n2) / se
    return round(2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2)))), 3)


def rel_drop(a, n1, b, n2):
    """How much lower b/n2 is than a/n1, in percent, from the raw counts."""
    return round(100 * (1 - (b / n2) / (a / n1)), 1)


q02 = load("02_baseline_scorecard")[0][0]
q03 = load("03_customer_impact")
q04 = load("04_weekly_monitoring")[0]
q05 = load("05_root_cause")
q06 = load("06_promise_accuracy")
q07 = load("07_seller_scorecard")
q08 = load("08_repeat_purchase")
q09 = load("09_validation_checks")
q10 = load("10_initiative_sizing")
q11 = load("11_launch_scorecard")
q12 = load("12_early_warning")
q15 = load("15_cancellation_trend")
q16 = load("16_order_timeline")
q17 = load("17_escalation")
P = load("pandas_recheck")  # independent recomputation

cause_sql = {}
late_by_period_sql = {}
for r in q05[1]:
    cause_sql[r["late_cause"]] = cause_sql.get(r["late_cause"], 0) + r["late_orders"]
    late_by_period_sql[r["period"]] = late_by_period_sql.get(r["period"], 0) + r["late_orders"]
late_total = q02["delivered_late"]
r180 = {r["first_order"]: r for r in q08[1]}
r90 = {r["first_order"]: r for r in q08[2]}
ON, LATE = "On-time first order", "Late first order"
sev1_weeks = [r["purchase_week"] for r in q04 if r["status"] == "SEV1"]
launch_first_look = {r["tenure_bucket"]: r for r in q11[0]}
early_warning_runup = {(r["episode"], r["weeks_before_late_rate_sev1"]): r for r in q12[1]}
episode_parts = {r["part"]: r for r in q10[1]}
lane_parts = {r["part"]: r for r in q10[2]}
EP_BF, EP_FM, EP_TOT = ("Black Friday 2017 (planned ahead, counted in full)",
                        "Feb-Mar 2018 (orders purchased after the real detection delay)",
                        "Total (both parts)")
LN_BF = "Black Friday 2017 (states picked from data before 20 Nov 2017, counted in full)"
LN_FM = "Feb-Mar 2018 (states picked from data before 12 Feb 2018; orders after the real detection delay)"
LN_TOT = "Total (both parts)"
halves = {r["half"]: r for r in q15[1]}
tl = {r["period"]: r for r in q16[0]}
tl90 = {r["period"]: r for r in q16[1]}
tlvs = {r["period"]: r for r in q16[2]}
esc = q17[0][0]
rj = {r["period"]: r for r in q17[2]}
hr_plat = {r["handoff"]: r for r in q17[5]}
hr_sell = {r["handoff"]: r for r in q17[6]}
hw = {r["handoff"]: r for r in q17[7]}
lvn = {r["period"]: r for r in q16[3]}
rjvn = q17[8][0]
ONH, LTH = "On-time handoff", "Late handoff"
NORM, BF, FM = "Normal weeks", "Black Friday 2017", "Feb-Mar 2018"

# id, claim, unit, value from SQL, value from pandas (None = no independent check), source
L = [
 ("N01", "Orders analysed (86 complete weeks, 2 Jan 2017 to 26 Aug 2018)", "orders", q02["orders"], P["orders"], "02"),
 ("N02", "Delivered on time", "orders", q02["delivered_on_time"], P["outcomes"]["delivered_on_time"], "02"),
 ("N03", "Delivered late", "orders", q02["delivered_late"], P["outcomes"]["delivered_late"], "02"),
 ("N04", "Cancelled (canceled + unavailable)", "orders", q02["cancelled"], P["outcomes"]["cancelled"], "02"),
 ("N05", "Stalled (paid, never delivered by the snapshot)", "orders", q02["stalled"], P["outcomes"]["stalled"], "02"),
 ("N06", "Perfect order rate (delivered on time / all orders)", "%", q02["perfect_order_pct"], round(100 * P["outcomes"]["delivered_on_time"] / P["orders"], 2), "02"),
 ("N07", "Late rate (late / delivered)", "%", q02["late_pct_of_delivered"], P["late_pct_of_delivered"], "02"),
 ("N08", "Late seller handoff rate (after shipping limit / orders with a handoff)", "%", q02["late_handoff_pct"], P["late_handoff"]["pct"], "02"),
 ("N09", "Low reviews (1 or 2 stars) on late orders", "%", row(q03[0], outcome="delivered_late")["low_review_pct"], P["review"]["delivered_late"]["low_pct"], "03a"),
 ("N10", "Low reviews (1 or 2 stars) on on-time orders", "%", row(q03[0], outcome="delivered_on_time")["low_review_pct"], P["review"]["delivered_on_time"]["low_pct"], "03a"),
 ("N11", "Average review, late orders", "stars", row(q03[0], outcome="delivered_late")["avg_review"], P["review"]["delivered_late"]["avg"], "03a"),
 ("N12", "Average review, on-time orders", "stars", row(q03[0], outcome="delivered_on_time")["avg_review"], P["review"]["delivered_on_time"]["avg"], "03a"),
 ("N13", "Low reviews on orders 4 to 7 days late (the cliff)", "%", row(q03[1], lateness="4 to 7 days late")["low_review_pct"], None, "03b"),
 ("N14", "Low reviews on orders 1 to 3 days late", "%", row(q03[1], lateness="1 to 3 days late")["low_review_pct"], None, "03b"),
 ("N15", "Late orders handed off on time (cause: carrier or promise)", "orders", cause_sql["carrier_or_promise"], P["late_cause"]["carrier_or_promise"], "05b"),
 ("N16", "Late orders an on-time handoff would have saved (cause: seller)", "orders", cause_sql["seller_handoff"], P["late_cause"]["seller_handoff"], "05b"),
 ("N17", "Late orders with late handoff AND slow transit (cause: shared)", "orders", cause_sql["shared"], P["late_cause"]["shared"], "05b"),
 ("N18", "Share of late orders handed off on time", "%", round(100 * cause_sql["carrier_or_promise"] / late_total, 1), round(100 * P["late_cause"]["carrier_or_promise"] / P["outcomes"]["delivered_late"], 1), "05b / 02"),
 ("N19", "Share of late orders caused by the seller alone", "%", round(100 * cause_sql["seller_handoff"] / late_total, 1), round(100 * P["late_cause"]["seller_handoff"] / P["outcomes"]["delivered_late"], 1), "05b / 02"),
 ("N20", "SEV1 weeks flagged by the monitor", "weeks", len(sev1_weeks), None, "04"),
 ("N21", "Black Friday 2017: late rate", "%", row(q05[0], period="Black Friday 2017")["late_pct"], P["periods"]["Black Friday 2017"]["late_pct"], "05a"),
 ("N22", "Black Friday 2017: late handoff rate", "%", row(q05[0], period="Black Friday 2017")["late_handoff_pct"], P["periods"]["Black Friday 2017"]["late_handoff_pct"], "05a"),
 ("N23", "Black Friday 2017: orders per week", "orders", row(q05[0], period="Black Friday 2017")["orders_per_week"], round(P["periods"]["Black Friday 2017"]["orders"] / 3), "05a"),
 ("N24", "Feb-Mar 2018: late rate", "%", row(q05[0], period="Feb-Mar 2018")["late_pct"], P["periods"]["Feb-Mar 2018"]["late_pct"], "05a"),
 ("N25", "Feb-Mar 2018: late handoff rate", "%", row(q05[0], period="Feb-Mar 2018")["late_handoff_pct"], P["periods"]["Feb-Mar 2018"]["late_handoff_pct"], "05a"),
 ("N26", "Feb-Mar 2018: share of late orders handed off on time", "%", row(q05[1], period="Feb-Mar 2018", late_cause="carrier_or_promise")["share_pct"], P["periods"]["Feb-Mar 2018"]["on_time_handoff_share_of_late"], "05b"),
 ("N27", "Normal weeks: late rate", "%", row(q05[0], period="Normal weeks")["late_pct"], P["periods"]["Normal weeks"]["late_pct"], "05a"),
 ("N28", "Normal weeks: late handoff rate", "%", row(q05[0], period="Normal weeks")["late_handoff_pct"], P["periods"]["Normal weeks"]["late_handoff_pct"], "05a"),
 ("N29", "Normal weeks: median transit days", "days", row(q05[0], period="Normal weeks")["transit_days_p50"], None, "05a"),
 ("N30", "Feb-Mar 2018: median transit days", "days", row(q05[0], period="Feb-Mar 2018")["transit_days_p50"], None, "05a"),
 ("N31", "Rio de Janeiro (RJ) late rate, normal weeks", "%", row(q05[2], period="Feb-Mar 2018", customer_state="RJ")["normal_late_pct"], P["RJ"]["Normal weeks"], "05c"),
 ("N32", "Rio de Janeiro (RJ) late rate, Feb-Mar 2018", "%", row(q05[2], period="Feb-Mar 2018", customer_state="RJ")["episode_late_pct"], P["RJ"]["Feb-Mar 2018"], "05c"),
 ("N33", "Rio de Janeiro (RJ) late rate, Black Friday 2017", "%", row(q05[2], period="Black Friday 2017", customer_state="RJ")["episode_late_pct"], P["RJ"]["Black Friday 2017"], "05c"),
 ("N34", "RJ share of excess late orders, Feb-Mar 2018", "%", row(q05[2], period="Feb-Mar 2018", customer_state="RJ")["share_of_excess_pct"], None, "05c"),
 ("N35", "RJ share of delivered volume, Feb-Mar 2018", "%", row(q05[2], period="Feb-Mar 2018", customer_state="RJ")["share_of_volume_pct"], None, "05c"),
 ("N36", "Share of all late orders that fall in the two SEV1 episodes (8 of 86 weeks)", "%", round(100 * (late_by_period_sql["Black Friday 2017"] + late_by_period_sql["Feb-Mar 2018"]) / late_total, 1), round(100 * (P["periods"]["Black Friday 2017"]["late"] + P["periods"]["Feb-Mar 2018"]["late"]) / P["outcomes"]["delivered_late"], 1), "05b / 02"),
 ("N37", "Median promised delivery time", "days", q06[0][0]["promised_days_p50"], P["promise"]["promised_p50"], "06a"),
 ("N38", "Median actual delivery time", "days", q06[0][0]["actual_days_p50"], P["promise"]["actual_p50"], "06a"),
 ("N39", "Delivered orders arriving 7+ days before the promise", "%", q06[0][0]["arrived_7plus_days_early_pct"], P["promise"]["early7_pct"], "06a"),
 ("N40", "Sellers scored (50+ orders with a handoff)", "sellers", q07[0][0]["scored_sellers"], P["sellers"]["scored"], "07a"),
 ("N41", "Sellers flagged (Wilson lower bound above platform rate)", "sellers", q07[0][0]["flagged_sellers"], P["sellers"]["flagged"], "07a"),
 ("N42", "Flagged sellers' share of scored orders", "%", q07[0][0]["flagged_share_of_orders_pct"], P["sellers"]["flagged_share_orders"], "07a"),
 ("N43", "Flagged sellers' share of late handoffs", "%", q07[0][0]["flagged_share_of_late_handoffs_pct"], P["sellers"]["flagged_share_late_handoffs"], "07a"),
 ("N44", "Late delivery rate after a late handoff", "%", row(q07[2], handoff="Late handoff")["late_delivery_pct"], None, "07c"),
 ("N45", "Late delivery rate after an on-time handoff", "%", row(q07[2], handoff="On-time handoff")["late_delivery_pct"], None, "07c"),
 ("N46", "Customers in the window", "customers", q08[0][0]["customers"], P["customers"], "08a"),
 ("N47", "Customers who ordered more than once", "%", q08[0][0]["ordered_more_than_once_pct"], P["repeat_any_pct"], "08a"),
 ("N48", "Repeat within 180 days, on-time first order", "%", r180[ON]["repeat_pct"], P["repeat_180"]["on_time"]["pct"], "08b"),
 ("N49", "Repeat within 180 days, late first order", "%", r180[LATE]["repeat_pct"], P["repeat_180"]["late"]["pct"], "08b"),
 ("N50", "Repeaters behind N49 (late first order, 180 days)", "customers", r180[LATE]["repeaters"], P["repeat_180"]["late"]["repeaters"], "08b"),
 ("N51", "Relative drop in 180-day repeat rate after a late first order", "%", rel_drop(r180[ON]["repeaters"], r180[ON]["customers"], r180[LATE]["repeaters"], r180[LATE]["customers"]), rel_drop(P["repeat_180"]["on_time"]["repeaters"], P["repeat_180"]["on_time"]["customers"], P["repeat_180"]["late"]["repeaters"], P["repeat_180"]["late"]["customers"]), "08b"),
 ("N52", "p-value for the 180-day difference (two-proportion z-test)", "p", two_proportion_p(r180[ON]["repeaters"], r180[ON]["customers"], r180[LATE]["repeaters"], r180[LATE]["customers"]), two_proportion_p(P["repeat_180"]["on_time"]["repeaters"], P["repeat_180"]["on_time"]["customers"], P["repeat_180"]["late"]["repeaters"], P["repeat_180"]["late"]["customers"]), "08b + check.py"),
 ("N53", "Repeat within 90 days, on-time first order", "%", r90[ON]["repeat_pct"], P["repeat_90"]["on_time"]["pct"], "08c"),
 ("N54", "Repeat within 90 days, late first order", "%", r90[LATE]["repeat_pct"], P["repeat_90"]["late"]["pct"], "08c"),
 ("N55", "Repeaters behind N54 (late first order, 90 days)", "customers", r90[LATE]["repeaters"], P["repeat_90"]["late"]["repeaters"], "08c"),
 ("N56", "Relative drop in 90-day repeat rate after a late first order", "%", rel_drop(r90[ON]["repeaters"], r90[ON]["customers"], r90[LATE]["repeaters"], r90[LATE]["customers"]), rel_drop(P["repeat_90"]["on_time"]["repeaters"], P["repeat_90"]["on_time"]["customers"], P["repeat_90"]["late"]["repeaters"], P["repeat_90"]["late"]["customers"]), "08c"),
 ("N57", "p-value for the 90-day difference (two-proportion z-test)", "p", two_proportion_p(r90[ON]["repeaters"], r90[ON]["customers"], r90[LATE]["repeaters"], r90[LATE]["customers"]), two_proportion_p(P["repeat_90"]["on_time"]["repeaters"], P["repeat_90"]["on_time"]["customers"], P["repeat_90"]["late"]["repeaters"], P["repeat_90"]["late"]["customers"]), "08c + check.py"),
 ("N58", "Late repeat rate vs matched on-time rate, same state and month (180 days)", "% vs %", f'{q08[4][0]["late_repeat_pct"]} vs {q08[4][0]["matched_on_time_repeat_pct"]}', None, "08e"),
 ("N59", "Repeat within 180 days, first order 1 to 3 days late (12 repeaters)", "%", row(q08[3], lateness="1 to 3 days late")["repeat_pct"], None, "08d"),
 ("N60", "Repeat within 180 days, first order 4 to 7 days late (10 repeaters)", "%", row(q08[3], lateness="4 to 7 days late")["repeat_pct"], None, "08d"),
 ("N61", "Repeat within 180 days, first order 8+ days late (13 repeaters)", "%", row(q08[3], lateness="8+ days late")["repeat_pct"], None, "08d"),
 ("N62", "Seller handoff program: late orders avoided", "orders", q10[0][0]["late_orders_avoided"], P["initiative_seller"]["late_orders_avoided"], "10a"),
 ("N63", "Seller handoff program: low reviews avoided", "orders", q10[0][0]["low_reviews_avoided"], P["initiative_seller"]["low_reviews_avoided"], "10a"),
 ("N64", "Episode response, Black Friday 2017 (planned ahead, counted in full): late orders avoided (promise +7 days)", "orders", episode_parts[EP_BF]["late_orders_avoided"], P["initiative_episode"]["black_friday"]["late_orders_avoided"], "10b"),
 ("N65", "Episode response, Black Friday 2017: late orders avoided (promise +3 days)", "orders", episode_parts[EP_BF]["late_orders_avoided_3d_cap"], P["initiative_episode"]["black_friday"]["late_orders_avoided_3d_cap"], "10b"),
 ("N66", "Episode response, Black Friday 2017: low reviews avoided", "orders", episode_parts[EP_BF]["low_reviews_avoided"], P["initiative_episode"]["black_friday"]["low_reviews_avoided"], "10b"),
 ("N67", "Episode response, Feb-Mar 2018 (orders purchased after the real detection delay only): late orders avoided (promise +7 days)", "orders", episode_parts[EP_FM]["late_orders_avoided"], P["initiative_episode"]["feb_mar"]["late_orders_avoided"], "10b"),
 ("N68", "Episode response, Feb-Mar 2018 (detection delay applied): late orders avoided (promise +3 days)", "orders", episode_parts[EP_FM]["late_orders_avoided_3d_cap"], P["initiative_episode"]["feb_mar"]["late_orders_avoided_3d_cap"], "10b"),
 ("N69", "Episode response, Feb-Mar 2018 (detection delay applied): low reviews avoided", "orders", episode_parts[EP_FM]["low_reviews_avoided"], P["initiative_episode"]["feb_mar"]["low_reviews_avoided"], "10b"),
 ("N70", "Episode response: late orders avoided, both parts combined (promise +7 days)", "orders", episode_parts[EP_TOT]["late_orders_avoided"], P["initiative_episode"]["total"]["late_orders_avoided"], "10b"),
 ("N71", "Episode response: low reviews avoided, both parts combined", "orders", episode_parts[EP_TOT]["low_reviews_avoided"], P["initiative_episode"]["total"]["low_reviews_avoided"], "10b"),
 ("N72", "Lane-level promise, Black Friday 2017 (states picked from data before 20 Nov 2017, counted in full): late orders avoided (promise +7 days)", "orders", lane_parts[LN_BF]["late_orders_avoided"], P["initiative_lane"]["black_friday"]["late_orders_avoided"], "10c"),
 ("N73", "Lane-level promise, Black Friday 2017: late orders avoided (promise +3 days)", "orders", lane_parts[LN_BF]["late_orders_avoided_3d_cap"], P["initiative_lane"]["black_friday"]["late_orders_avoided_3d_cap"], "10c"),
 ("N74", "Lane-level promise, Black Friday 2017: low reviews avoided", "orders", lane_parts[LN_BF]["low_reviews_avoided"], P["initiative_lane"]["black_friday"]["low_reviews_avoided"], "10c"),
 ("N75", "Lane-level promise, Feb-Mar 2018 (states picked from data before 12 Feb 2018; detection delay applied): late orders avoided (promise +7 days)", "orders", lane_parts[LN_FM]["late_orders_avoided"], P["initiative_lane"]["feb_mar"]["late_orders_avoided"], "10c"),
 ("N76", "Lane-level promise, Feb-Mar 2018 (detection delay applied): late orders avoided (promise +3 days)", "orders", lane_parts[LN_FM]["late_orders_avoided_3d_cap"], P["initiative_lane"]["feb_mar"]["late_orders_avoided_3d_cap"], "10c"),
 ("N77", "Lane-level promise, Feb-Mar 2018 (detection delay applied): low reviews avoided", "orders", lane_parts[LN_FM]["low_reviews_avoided"], P["initiative_lane"]["feb_mar"]["low_reviews_avoided"], "10c"),
 ("N78", "Lane-level promise: late orders avoided, both parts combined (promise +7 days)", "orders", lane_parts[LN_TOT]["late_orders_avoided"], P["initiative_lane"]["total"]["late_orders_avoided"], "10c"),
 ("N79", "Lane-level promise: low reviews avoided, both parts combined", "orders", lane_parts[LN_TOT]["low_reviews_avoided"], P["initiative_lane"]["total"]["low_reviews_avoided"], "10c"),
 ("N80", "New-seller cancel rate, first 30 days (first look, not calendar-controlled)", "%", launch_first_look["First 30 days"]["cancel_pct"], P["launch"]["first_look"]["First 30 days"]["cancel_pct"], "11a"),
 ("N81", "New-seller cancel rate, after day 90 (first look, not calendar-controlled)", "%", launch_first_look["After day 90"]["cancel_pct"], P["launch"]["first_look"]["After day 90"]["cancel_pct"], "11a"),
 ("N82", "New-seller orders behind N84 (first 30 days, matched calendar months)", "orders", q11[2][0]["new_seller_orders"], P["launch"]["controlled"]["new_seller_orders"], "11c"),
 ("N83", "New-seller cancelled orders behind N84", "orders", q11[2][0]["new_seller_cancelled"], P["launch"]["controlled"]["new_seller_cancelled"], "11c"),
 ("N84", "New-seller cancel rate, first 30 days, matched to the same calendar month as the comparison", "%", q11[2][0]["new_seller_cancel_pct"], P["launch"]["controlled"]["new_seller_cancel_pct"], "11c"),
 ("N85", "Veteran-seller (after day 90) orders behind N87, same matched calendar months", "orders", q11[2][0]["veteran_orders_in_matched_months"], P["launch"]["controlled"]["veteran_orders_in_matched_months"], "11c"),
 ("N86", "Veteran-seller cancelled orders behind N87", "orders", q11[2][0]["veteran_cancelled_in_matched_months"], P["launch"]["controlled"]["veteran_cancelled_in_matched_months"], "11c"),
 ("N87", "Veteran-seller (after day 90) cancel rate, weighted to match new sellers' calendar months -- NOT N86/N85, which is a smaller unweighted rate (0.37%)", "%", q11[2][0]["veteran_matched_cancel_pct"], P["launch"]["controlled"]["veteran_matched_cancel_pct"], "11c"),
 ("N88", "Transit 10+ day share, week before Black Friday 2017's late-rate SEV1 start (status stayed 'ok': no warning)", "%", early_warning_runup[("Black Friday 2017", 1)]["share_10plus_pct"], P["early_warning"]["black_friday_week_before_pct"], "12b"),
 ("N89", "Transit 10+ day share, week before Feb-Mar 2018's late-rate SEV1 start (status stayed 'ok': no warning)", "%", early_warning_runup[("Feb-Mar 2018", 1)]["share_10plus_pct"], P["early_warning"]["feb_mar_week_before_pct"], "12b"),

 # --- cancellation trend (15) ---
 ("N90", "Cancellation rate, first half of the window (split at the median purchase date)", "%", halves["First half"]["cancel_pct"], P["cancel_trend"]["First half"]["cancel_pct"], "15b"),
 ("N91", "Cancellation rate, second half of the window", "%", halves["Second half"]["cancel_pct"], P["cancel_trend"]["Second half"]["cancel_pct"], "15b"),
 ("N92", "Worst single month for cancellations (Feb 2017), months of 500+ orders only", "%", q15[2][0]["cancel_pct"], P["cancel_trend"]["worst_month"]["cancel_pct"], "15c"),

 # --- order timeline (16) ---
 ("N93", "Normal weeks: median days, purchase to carrier handoff (seller leg)", "days", tl[NORM]["seller_leg_days_p50"], P["timeline"][NORM]["seller_leg_p50"], "16a"),
 ("N94", "Normal weeks: median days, handoff to delivery (carrier leg)", "days", tl[NORM]["carrier_leg_days_p50"], P["timeline"][NORM]["carrier_leg_p50"], "16a"),
 ("N95", "Normal weeks: median days, purchase to delivery (total)", "days", tl[NORM]["total_days_p50"], P["timeline"][NORM]["total_p50"], "16a"),
 ("N96", "Black Friday 2017: median seller leg", "days", tl[BF]["seller_leg_days_p50"], P["timeline"][BF]["seller_leg_p50"], "16a"),
 ("N97", "Black Friday 2017: median carrier leg", "days", tl[BF]["carrier_leg_days_p50"], P["timeline"][BF]["carrier_leg_p50"], "16a"),
 ("N98", "Black Friday 2017: median total", "days", tl[BF]["total_days_p50"], P["timeline"][BF]["total_p50"], "16a"),
 ("N99", "Feb-Mar 2018: median seller leg", "days", tl[FM]["seller_leg_days_p50"], P["timeline"][FM]["seller_leg_p50"], "16a"),
 ("N100", "Feb-Mar 2018: median carrier leg", "days", tl[FM]["carrier_leg_days_p50"], P["timeline"][FM]["carrier_leg_p50"], "16a"),
 ("N101", "Feb-Mar 2018: median total", "days", tl[FM]["total_days_p50"], P["timeline"][FM]["total_p50"], "16a"),
 ("N102", "Black Friday 2017: seller leg against normal weeks", "days", tlvs[BF]["seller_leg_vs_normal_days"], P["timeline"][BF]["seller_leg_vs_normal"], "16c"),
 ("N103", "Black Friday 2017: carrier leg against normal weeks", "days", tlvs[BF]["carrier_leg_vs_normal_days"], P["timeline"][BF]["carrier_leg_vs_normal"], "16c"),
 ("N104", "Feb-Mar 2018: seller leg against normal weeks (barely moved)", "days", tlvs[FM]["seller_leg_vs_normal_days"], P["timeline"][FM]["seller_leg_vs_normal"], "16c"),
 ("N105", "Feb-Mar 2018: carrier leg against normal weeks", "days", tlvs[FM]["carrier_leg_vs_normal_days"], P["timeline"][FM]["carrier_leg_vs_normal"], "16c"),
 ("N106", "Normal weeks: 90th percentile carrier leg", "days", tl90[NORM]["carrier_leg_days_p90"], P["timeline"][NORM]["carrier_leg_p90"], "16b"),
 ("N107", "Feb-Mar 2018: 90th percentile carrier leg", "days", tl90[FM]["carrier_leg_days_p90"], P["timeline"][FM]["carrier_leg_p90"], "16b"),

 # --- escalation: the flagged seller (17) ---
 ("N108", "Escalation seller: scored orders", "orders", esc["scored_orders"], P["escalation_seller"]["scored_orders"], "17a"),
 ("N109", "Escalation seller: late handoffs", "orders", esc["late_handoffs"], P["escalation_seller"]["late_handoffs"], "17a"),
 ("N110", "Escalation seller: late handoff rate (platform rate is N08)", "%", esc["late_handoff_pct"], P["escalation_seller"]["late_handoff_pct"], "17a"),
 ("N111", "Escalation seller: late delivery rate", "%", esc["late_delivery_pct"], P["escalation_seller"]["late_delivery_pct"], "17a"),
 ("N112", "Escalation seller: late deliveries an on-time handoff alone would have saved", "orders", esc["seller_caused_late"], P["escalation_seller"]["seller_caused_late"], "17a"),
 ("N113", "Escalation seller: 1-2 star review rate", "%", esc["low_review_pct"], P["escalation_seller"]["low_review_pct"], "17a"),
 ("N114", "Escalation seller: reviewed orders behind N113", "orders", esc["reviewed"], P["escalation_seller"]["reviewed"], "17a"),

 # --- escalation: the Rio de Janeiro lane (17) ---
 ("N115", "Rio de Janeiro: median carrier leg, normal weeks", "days", rj[NORM]["carrier_leg_days_p50"], P["escalation_rj"][NORM]["carrier_leg_p50"], "17c"),
 ("N116", "Rio de Janeiro: median carrier leg, Feb-Mar 2018", "days", rj[FM]["carrier_leg_days_p50"], P["escalation_rj"][FM]["carrier_leg_p50"], "17c"),
 ("N117", "Rio de Janeiro: late handoff rate, normal weeks", "%", rj[NORM]["late_handoff_pct"], P["escalation_rj"][NORM]["late_handoff_pct"], "17c"),
 ("N118", "Rio de Janeiro: late handoff rate, Feb-Mar 2018 (sellers were not the problem)", "%", rj[FM]["late_handoff_pct"], P["escalation_rj"][FM]["late_handoff_pct"], "17c"),
 ("N119", "Rio de Janeiro: late orders above its own normal rate, Feb-Mar 2018", "orders", q17[4][0]["excess_late_orders"], P["escalation_rj"]["excess_late_orders"], "17e"),
 ("N120", "Escalation seller: late deliveries with both a late handoff and slow transit (shared cause)", "orders", esc["shared_late"], P["escalation_seller"]["shared_late"], "17a"),

 # --- does a late handoff cost reviews even on an on-time delivery? (17f, 17g) ---
 ("N121", "On-time deliveries after an on-time handoff: 1-2 star rate", "%", hr_plat[ONH]["low_review_pct"], P["handoff_reviews_platform"]["on_time_handoff"]["low_review_pct"], "17f"),
 ("N122", "On-time deliveries after a LATE handoff: 1-2 star rate (lateness cannot explain this, they all arrived on time)", "%", hr_plat[LTH]["low_review_pct"], P["handoff_reviews_platform"]["late_handoff"]["low_review_pct"], "17f"),
 ("N123", "Reviewed on-time deliveries behind N121", "orders", hr_plat[ONH]["reviewed"], P["handoff_reviews_platform"]["on_time_handoff"]["reviewed"], "17f"),
 ("N124", "Reviewed on-time deliveries behind N122", "orders", hr_plat[LTH]["reviewed"], P["handoff_reviews_platform"]["late_handoff"]["reviewed"], "17f"),
 ("N125", "Average review, on-time delivery after an on-time handoff", "stars", hr_plat[ONH]["avg_review"], P["handoff_reviews_platform"]["on_time_handoff"]["avg_review"], "17f"),
 ("N126", "Average review, on-time delivery after a late handoff", "stars", hr_plat[LTH]["avg_review"], P["handoff_reviews_platform"]["late_handoff"]["avg_review"], "17f"),
 ("N127", "Escalation seller: reviewed on-time deliveries that followed a late handoff -- too small to measure a review effect for this seller alone", "orders", hr_sell[LTH]["reviewed"], P["handoff_reviews_seller"]["late_handoff"]["reviewed"], "17g"),
 ("N128", "Escalation seller: 1-2 star rate on those (N127) orders -- 2 low reviews, reported only to show the sample is too small", "%", hr_sell[LTH]["low_review_pct"], P["handoff_reviews_seller"]["late_handoff"]["low_review_pct"], "17g"),

 # --- the likely mechanism behind N121 vs N122 (17h) ---
 ("N129", "On-time deliveries after an on-time handoff: median days purchase to door", "days", hw[ONH]["total_days_p50"], P["handoff_wait"]["on_time_handoff"]["total_days_p50"], "17h"),
 ("N130", "On-time deliveries after a late handoff: median days purchase to door", "days", hw[LTH]["total_days_p50"], P["handoff_wait"]["late_handoff"]["total_days_p50"], "17h"),
 ("N131", "On-time deliveries after an on-time handoff: median days arriving before the deadline", "days", hw[ONH]["days_early_p50"], P["handoff_wait"]["on_time_handoff"]["days_early_p50"], "17h"),
 ("N132", "On-time deliveries after a late handoff: median days arriving before the deadline (less slack left)", "days", hw[LTH]["days_early_p50"], P["handoff_wait"]["late_handoff"]["days_early_p50"], "17h"),

 # --- episode late rate against normal weeks, in percentage points (16d, 17i) ---
 ("N133", "Black Friday 2017 late rate above normal weeks", "pp", lvn[BF]["late_pct_vs_normal"], P["late_vs_normal"][BF]["late_pct_vs_normal"], "16d"),
 ("N134", "Feb-Mar 2018 late rate above normal weeks", "pp", lvn[FM]["late_pct_vs_normal"], P["late_vs_normal"][FM]["late_pct_vs_normal"], "16d"),
 ("N135", "Rio de Janeiro, Feb-Mar 2018: late rate above Rio's own normal rate", "pp", rjvn["late_pct_vs_normal"], P["rj_vs_normal"]["late_pct_vs_normal"], "17i"),
]

rows = []
for id_, claim, unit, sql_value, pandas_value, source in L:
    if pandas_value is None:
        agreement = "SQL only"
    else:
        agreement = "MATCH" if float(sql_value) == float(pandas_value) else "MISMATCH"
    rows.append(dict(id=id_, claim=claim, value=sql_value, unit=unit, sql_source=source,
                     pandas_value="" if pandas_value is None else pandas_value, agreement=agreement))

fields = ["id", "claim", "value", "unit", "sql_source", "pandas_value", "agreement"]
with open(OUT / "numbers_ledger.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

failures = []
# test 1
bad = [c["check_name"] for c in q09[0] if c["status"] != "PASS"]
print(f"1. validation checks: {len(q09[0]) - len(bad)} of {len(q09[0])} PASS")
failures += [f"validation check failed: {b}" for b in bad]
# test 2
mism = [r["id"] for r in rows if r["agreement"] == "MISMATCH"]
checked = [r for r in rows if r["agreement"] != "SQL only"]
print(f"2. SQL vs independent pandas: {len(checked) - len(mism)} of {len(checked)} MATCH "
      f"({len(rows) - len(checked)} numbers are SQL only)")
failures += [f"SQL and pandas disagree on {m}" for m in mism]
# test 3
if "--freeze" in sys.argv:
    REF.parent.mkdir(exist_ok=True)
    REF.write_text((OUT / "numbers_ledger.csv").read_text())
    print(f"3. reference frozen at {REF}")
elif REF.exists():
    ref = {r["id"]: r["value"] for r in csv.DictReader(open(REF))}
    diff = [r["id"] for r in rows if str(r["value"]) != ref.get(r["id"])]
    print(f"3. this run vs frozen reference: {len(rows) - len(diff)} of {len(rows)} identical")
    failures += [f"{d} differs from the frozen reference" for d in diff]
else:
    print("3. no frozen reference yet (run with --freeze after review)")

print("SEV1 weeks:", ", ".join(sev1_weeks))
if failures:
    print("\nFAILED:")
    for f_ in failures:
        print("  -", f_)
    sys.exit(1)
print("\nALL CHECKS PASSED")
