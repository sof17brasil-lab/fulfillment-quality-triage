# Dashboard plan

Rewritten to show the whole job in the posting end to end: the problem, the monitoring, the root cause, the customer impact, a worked escalation, a launch scorecard, the sized fixes, and a plan.

## Rules this page is built to

- Every chart carries a **finding headline** (states what it shows, not what it is) and **one or two short sentences** of "so what". Nothing longer than two sentences.
- **~600 words** of body text on the main page, total. Method, definitions, SQL and limits live on the Method and SQL page.
- **No hand-typed numbers.** Every figure reads from `out/*.json` via `site/data/`. New numbers get SQL + an independent pandas re-check + a ledger entry, like everything else.
- Outside facts come only from ticked rows in `sources/SOURCES.md`, enforced at build time by the fact gate in `scripts/build_site.py`.
- Never state or estimate Instacart's internal numbers, costs, defect rates, teams or tools.

## Design corrections carried in

- **At most 3 food photos**, in the hero only, well placed and clear of the text.
- **Exactly two fonts**: Inter Tight (body, headline) and Fjalla One (condensed display). No third face anywhere.
- **No rivet dots on the tags.** Plain cream plaque, dark text.
- **Tighter vertical spacing** throughout; sections breathe without dead space.
- **Larger, higher-contrast small text** — captions and sub-labels move up in size and off the faintest greys.

---

## New analysis this plan requires

| File | Question | Feeds |
|---|---|---|
| `sql/15_cancellation_trend.sql` | Is the cancellation rate moving over time? | §2 |
| `sql/16_order_timeline.sql` | Where do the days actually go: purchase → handoff → delivery, against the promise, per period? | §4a |
| `sql/17_escalation.sql` | The worked escalation: one flagged seller, and Rio de Janeiro, in detail | §6 |

Each gets a matching recomputation in `scripts/verify_pandas.py` sharing no logic with the SQL, ledger rows in `scripts/check.py`, and a re-freeze only after Sofia reviews any moved number.

Also new: `scripts/build_deck.py` → `site/deck.pdf`, a 6-slide insights deck generated from `out/*.json` so the deck can never disagree with the page.

---

## Page, top to bottom

### 1. Hero
One sentence: **"Most late deliveries weren't the seller's fault."**
One supporting line (**N18**, **N01**) and the credited CEO quote (**S01a**). Nothing else.
Three food photos, placed clear of the text. Byline and scroll cue.

### 2. The problem
**Headline:** Most orders are fine. The failures are concentrated.

- **Where 100 orders end up** — stacked bar (on time / late / stalled / cancelled) — `02_baseline_scorecard.json` — **N02–N05, N06**
- **Cancellations over time** — line, monthly — `15_cancellation_trend.json` — **new**
- **KPI tiles** move here (orders, on time, late, 1–2 star gap, bad stretches) — **N01, N06, N07, N09, N10, N20, N36**
- Public-scale strip (Instacart, Q2 2026) stays, gated by the fact check — **S01c, S01d, S01e, S02a**

### 3. The monitor
**Headline:** Eight weeks out of 86 were genuinely unusual.
Weekly late rate, shaded normal range (expected ± 3 SE), the 8 SEV1 weeks highlighted — `13_dashboard_cube.json[0]` — **N20, N36**
*So what:* those 8 weeks hold 41.5% of every late order in the window.

### 4. The diagnosis
**(a) Where the days go.** Grouped horizontal timeline: median days purchase → handoff → delivery, against the median promise, for Normal weeks / Black Friday 2017 / Feb–Mar 2018 — `16_order_timeline.json` — **new**, plus **N29, N30, N37, N38**
*So what:* in one episode the seller leg stretched; in the other it was transit.

**(b) Who caused the late orders.** Stacked bars by period (seller handoff / shared / carrier or promise) — `05_root_cause.json[1]` — **N15–N19, N22, N25, N26, N28**
*So what:* 72.3% had already left the seller on time.

**(c) Where it landed.** Late rate by destination state, normal vs episode, Rio highlighted — `05_root_cause.json[2]` — **N31–N35**
*So what:* Rio held 13.6% of volume and 29.8% of the excess.

### 5. Why it matters
- **The 3-day cliff** — low-star rate by days late — `03_customer_impact.json[1]` — **N13, N14, N09, N10**
- **Repeat purchase** — on-time vs late first order, 90 and 180 days, **counts printed on the chart** (n = 35 / 41) — `08_repeat_purchase.json` — **N47–N58**
*So what:* stated as a consistent signal with its counts, never as a proven effect size.

### 6. An escalation, worked
Two columns, same four beats each — **what happened / whose fault / what it cost / recommended action**:

| | Seller escalation | Lane escalation |
|---|---|---|
| Subject | The flagged seller with the most late handoffs | Rio de Janeiro, Feb–Mar 2018 |
| Fault | Seller handoff | Carrier transit |
| Reads | `17_escalation.json[0..1]` | `17_escalation.json[2..3]` |

Small sparkline-scale charts beside each. This is the section that shows the job being *done*, not just measured.

### 7. Launch scorecard
**Headline:** New sellers really do have a rough first month.
First 30 days vs day 90+, matched within calendar month, **counts printed** — `11_launch_scorecard.json` — **N80–N87**
*So what:* the gap survives the calendar-time control; 0.9% against a **month-matched** 0.39%.
Labelled explicitly as a month-matched rate, not a plain division of the counts beside it.

### 8. The fixes, sized
Ranked horizontal bars by late orders avoided — `10_initiative_sizing.json` — **N62–N79**

| Rank | Fix | Avoided | What it would take |
|---|---|---|---|
| 1 | Episode response (temporary longer promise) | 782 | Trigger on the monitor; cost in lost conversions is **not measurable here** |
| 2 | Seller handoff program | 231 | Reaches 21% of scored volume; smallest lever of the three |
| 3 | Lane-level promise | 142 | States picked from pre-episode data only, so honest and smaller |

Plus the **calculator**: reader's own orders/year, defect-rate reduction, cost per defect. Never a claimed Instacart saving.

### 9. The plan
Three recommendations, each with an owner, the metric to watch, and a timeline. Owners are **generic functional roles**, not Instacart team names, and the section is labelled a proposal.

| # | Recommendation | Owner (illustrative) | Metric to watch | Timeline |
|---|---|---|---|---|
| 1 | Wire the monitor to a weekly review with a defined SEV1 trigger | Marketplace Quality Analytics | Weeks to detection | 0–30 days |
| 2 | Run the episode-response playbook on the next flagged week | Fulfilment Operations | Late orders in flagged weeks | 30–60 days |
| 3 | Put the 89 flagged sellers on a handoff improvement track | Seller Operations | Flagged-seller late-handoff rate | 60–90 days |

**Downloadable 6-slide deck (PDF)** — situation, what the monitor caught, whose problem it was, what to do, what it's worth, limits — generated by `scripts/build_deck.py` from `out/*.json`.

### 10. Seller watchlist, then footer
- Scatter of all 425 scored sellers, the 89 flagged ones marked — **N40–N43**
- Sortable table of flagged sellers with inline bars — `13_dashboard_cube.json[4]`
- Footer: data credit, CC BY-NC-SA 4.0 (**S10c**), one line of scope (multi-day parcel shipping, Brazil, 2017–2018), "Independent portfolio project. Not affiliated with Instacart.", quiet link to Method and SQL.

---

## Dropped, and said so on the Method page

**The early-warning signal.** Query 12 tested whether stuck-in-transit parcels lead the late rate. They do not: the signal sits at "ok" in the week before both episodes (**N88, N89**). The brief said drop it if that happened, so it is named on the Method page as a tested-and-dropped lead, not shown as a fix.

---

## Method and SQL page

Definitions · the 16 validation checks with pass/fail · every SQL file · the limits from `docs/project_brief.md` · the sources table (ticked rows only) · how AI was used · the dropped leads · the month-matching weighting explained.
