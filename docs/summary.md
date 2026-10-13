# Fulfillment Quality Triage — plain-English summary

## The data

The Brazilian E-Commerce Public Dataset by Olist, from Kaggle (CC BY-NC-SA 4.0 licence). It's real marketplace order data: 98,962 orders over 86 complete weeks, 2 January 2017 to 26 August 2018. Each order records which seller it came from, when it was promised, when the seller handed it to the carrier, when it actually arrived, which state the customer is in, and the review the customer left.

## The question

When a marketplace's on-time rate drops, how do you find out fast whose problem it is, how big it is, and what fixing it is worth? That's the job this project does end to end: **detect** the unusual week, **attribute** each late order to whoever caused it, and **size** what each fix is worth. It's the same loop a fulfillment-quality analytics team runs — spot the outlier, find the root cause instead of chasing the obvious suspect, and put a number on the response.

## The findings

- **Lateness is rare but damaging.** 90.5% of orders arrive on time; only 6.8% of delivered orders are late. But a late order gets a 1 or 2 star review 62.4% of the time, against 9.2% for an on-time order — and the damage isn't gradual: low reviews jump from 32.1% at 1–3 days late to 67.7% at 4–7 days late.
- **The monitor catches real trouble, not noise.** A control chart on the weekly late rate flags 8 unusual weeks out of 86, in two episodes (Black Friday 2017 and February–March 2018). Those 8 weeks alone hold 41.5% of all late orders in the whole period.
- **Sellers aren't the main problem.** Across the full period, 72.3% of late orders had already left the seller on time — only 12.4% of lateness would have been fixed by faster seller handoff. The two bad episodes even have different causes: Black Friday was genuine seller strain (late handoff rate rose to 14.1%), but February–March was not (handoff rate stayed near normal at 9.1%) and was instead a carrier/transit problem concentrated in one state, Rio de Janeiro, where the late rate hit 42.2% against a normal 6.6%.
- **A small group of sellers is responsible for an outsized share of late handoffs.** Of 425 sellers with enough volume to judge fairly, 89 are reliably worse than the platform average on handoff speed. They handle about 21% of scored orders but cause 58% of the late handoffs.
- **Late orders cost repeat business.** Customers whose first order arrived late came back 28–33% less often within 90–180 days than customers whose first order was on time. This is a small-sample, statistically significant signal (35–41 repeat customers), not a proven effect size — it should be read as suggestive, not definitive.

## What the dashboard will show

- Five headline KPI tiles (orders, on-time rate, late rate, review gap, episodes caught)
- A method timeline: Detect → Attribute → Size
- Stacking finding cards covering each result above, each with its chart
- A "choose your fix" comparison of the sizable interventions, ranked by impact
- A seller watchlist of the 89 flagged sellers
- A few real (anonymised) customer reviews from late orders
- A calculator so a reader can size the opportunity using their own cost assumptions

## What it cannot claim

- This is multi-day parcel shipping in Brazil, 2017–2018 — not same-day grocery delivery. The method transfers; the specific numbers and timescales do not.
- There are no reschedule events and no shopper-supply data in this dataset, so two defect types a real fulfillment team tracks can't be shown here.
- Fault attribution relies on timestamps, not pickup scans — a seller who hands off late because a carrier missed a pickup would be blamed unfairly.
- The repeat-purchase result rests on a small sample (35–41 repeat customers) and is observational, not a controlled experiment.
- No Instacart-internal numbers, costs, or defect rates appear anywhere — none are public. Savings are shown only through a calculator that uses the reader's own inputs.
