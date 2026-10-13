# Project brief: Fulfillment Quality Triage

## One line

When a marketplace's on-time rate drops, find out fast whose problem it is, how big it is, and what fixing it is worth.

## Who it is for

The hiring manager and director of Instacart's Platform Excellence Ops Analytics team (Marketplace and Retailer pillar). Their posting describes the job as monitoring retailer performance, finding root causes of outliers, supporting retailer escalations and launches, sizing initiatives, and presenting insights decks (sources S05b to S05f).

The project shows that job done end to end on real data: detect, attribute, size, brief.

## The four parts

| Part | Question | Status |
|---|---|---|
| 1. Detect | Which weeks are statistically unusual, as opposed to noisy? | Built and checked (sql/04) |
| 2. Attribute | For each late order, whose side caused it: the seller, the delivery leg, or the promise? | Built and checked (sql/01, 05, 06, 07) |
| 3. Size | What is each fix worth in defects avoided, and what is a late order worth in lost repeat business? | Repeat test built and checked (sql/08). Initiative sizing still to build. |
| 4. Brief | A professional dashboard (charts, numbers, tables, very little text), with the method and SQL on a separate page, plus a short deck. | To build |

## Findings so far

Every number below is in `reference/numbers_ledger.csv` with the query it comes from. Numbers marked with an ID were computed twice, in SQL and again in separate pandas code, and matched.

**Baseline**
- 98,962 orders over 86 weeks (N01). 90.5% were delivered on time (N06). 6.8% of delivered orders were late (N07).
- A late order gets a 1 or 2 star review 62.4% of the time, against 9.2% for an on-time order (N09, N10).
- The damage is not gradual. Low reviews jump from 32.1% for orders 1 to 3 days late to 67.7% for orders 4 to 7 days late (N14, N13).

**Detect**
- A control chart on the weekly late rate flags 8 SEV1 weeks in two episodes: Black Friday 2017 (3 weeks) and February to March 2018 (5 weeks) (N20).
- Those 8 weeks out of 86 hold 41.5% of all late orders (N36).

**Attribute**
- Across the whole period, 72.3% of late orders had been handed to the carrier on time (N18). Only 12.4% would have been saved by an on-time handoff alone (N19).
- The two episodes look the same on a dashboard and have different causes:
  - Black Friday 2017: volume roughly doubled (2,266 orders a week, N23) and the late handoff rate rose to 14.1% from a normal 8.5% (N22, N28). Sellers were under strain.
  - February to March 2018: the late handoff rate was 9.1%, close to normal (N25). Median transit time rose from 7.0 to 11.1 days (N29, N30). 85.6% of late orders had left the seller on time (N26). Sellers were not the problem.
- The February to March episode was concentrated in Rio de Janeiro state: 42.2% of deliveries late against a normal 6.6% (N32, N31). Rio had 13.6% of volume and 29.8% of the excess late orders (N35, N34).
- So the obvious response, chasing slow sellers, would have missed most of the worst episode.

**Sellers**
- Of 425 sellers with enough volume to judge, 89 are flagged as reliably worse than the platform on handoff (N40, N41). They ship 21.4% of the scored orders and produce 58.2% of the late handoffs (N42, N43).
- Flagging uses a Wilson lower bound, so a seller is flagged only when their volume makes the bad rate believable. Ranking on the raw rate would put low-volume sellers at the top by chance.

**Promise**
- The median order is promised in 24.2 days and arrives in 10.2 (N37, N38). 78.9% arrive a week or more early (N39). The promise is very loose on average and still too tight for specific places and weeks. That is an accuracy problem, not only a speed problem.

**What a late order is worth**
- Customers whose first order arrived late came back less often: 1.34% against 1.87% within 180 days, a 28.3% relative drop (N49, N48, N51), and 0.79% against 1.18% within 90 days, a 33.2% drop (N54, N53, N56).
- The repeat rate falls as lateness grows: 1.52%, 1.40%, then 1.17% for first orders 1 to 3, 4 to 7, and 8 or more days late (N59 to N61). Each of those groups has only 10 to 13 repeat customers, so read the trend as suggestive.
- The gap holds when late customers are compared only with on-time customers from the same state and month: 1.34% against 1.76% (N58).
- **This is small-sample evidence.** Only 3.1% of customers in this marketplace ever reorder (N47), so the late groups contain 35 and 41 repeat customers (N50, N55). p = 0.050 at 180 days and 0.011 at 90 days (N52, N57). Present it as a consistent signal with its counts shown, never as a proven effect size.

## Leads that are not yet verified

Do not put these on the website until they have their own SQL file, an independent re-check, and a ledger entry.

1. **New sellers cancel more.** In a first look, sellers in their first 30 days had a 0.96% cancellation rate against 0.38% after day 90. This is probably confounded: cancellation rates fell across the whole platform over time, and veteran-seller orders skew later. Test it within the same calendar month. Report it only if it survives.
2. **A real-time early warning.** The late rate for a purchase week is only known about three weeks later, once those orders are due. A count of parcels that have been in transit more than 10 days, taken at each week's end, might fire sooner. In a first look that share rose from about 20 to 30% to over 40% in mid December 2017 and again in March 2018. Whether it leads the late rate by a useful margin is untested.
3. **Complaint themes (optional, only if Sofia asks).** 10,721 of 14,364 low-star reviews include written text, in Portuguese. Sofia reads Portuguese. These could be sorted into defect reasons, with a hand-labelled sample to measure how accurate the sorting is.

## How this maps to a grocery marketplace

This table is an inference. Instacart has not published its data model.

| In this data | Likely grocery equivalent |
|---|---|
| Seller | Retailer or store |
| Seller handoff deadline (shipping limit) | Order picked and ready on time |
| Carrier transit | Shopper delivery leg |
| Promised delivery date | Delivery window |
| Cancelled or unavailable order | Cancellation |
| New seller's first 30 days | New retailer launch |
| Nothing | Reschedules (this data has no reschedule events) |

## Limits to state openly on the website

1. This is multi-day parcel shipping, not same-day grocery. The methods transfer. The timescales and the specific numbers do not.
2. There are no reschedule events and no shopper-supply data, so two of the role's defect types cannot be shown.
3. Fault attribution uses timestamps. A seller who hands off late because the carrier missed a pickup would be blamed unfairly. With real operations data you would check pickup scans.
4. The data ends in 2018 and is one marketplace in one country.
5. The repeat-purchase result is observational and small. It suggests a direction. A company with frequent reorders could measure it properly in a day.
6. The monitor looks back at purchase weeks. A live version would need the early-warning signal in lead 2.

## What the reader should walk away believing

Sofia can take a messy operational dataset, define defects carefully, tell a real change from noise, find the cause instead of the obvious suspect, put a size on the fix, say plainly what the evidence cannot support, and prove every number.
