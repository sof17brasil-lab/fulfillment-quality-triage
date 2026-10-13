# Paste this into Claude Code

Open Claude Code inside the `Instacart` folder (the one that contains this file), then copy everything below the line and paste it as your first message.

---

I'm Sofia Mota, a recent business analytics graduate. I'm applying for the Data Analyst, Platform Excellence Ops Analytics role at Instacart, and this folder is the portfolio project I'm sending with my application.

## What I want from you

Do the work for me: all the SQL, the checks, the analysis, and the website. I don't want lessons or quizzes, and I don't want walkthroughs of how each query works. When you report back, give me short plain-English summaries of what you found and what it means for the business.

The end product is a professional analytics dashboard: mostly charts, numbers, and tables, with very little text. It should look like something an analytics team would actually use, not like a blog post or a tutorial.

## What this project is

A case study called Fulfillment Quality Triage. It uses real marketplace order data (the public Olist dataset) to show the job in the posting done end to end: detect an unusual week, work out whose side caused each late order, and size what a fix is worth. The audience is a hiring manager and a director who run a fulfillment-quality analytics team. They will give the page about two minutes.

The analysis core already exists and has been checked. You verify it runs on my machine, summarize it for me, finish the remaining analysis, and build the dashboard.

## Read these first, in this order

1. `CLAUDE.md` for the rules of this project. They matter more than anything in this message.
2. `docs/project_brief.md` for the findings so far, the unverified leads, and the limits.
3. `reference/numbers_ledger.csv` for every number and where it comes from.
4. `sources/SOURCES.md` for every outside fact and how well it has been checked.
5. `design/design_brief.md` and everything in `design/inspiration/`, including `notes.md`.
6. The files in `sql/` and `scripts/`.

## Checkpoints

Work on your own between checkpoints. Stop and wait for me only at these four:

1. after the summary in Phase 1
2. after the findings from Phase 2
3. after the dashboard plan in Phase 3, before you build
4. before anything leaves my computer (GitHub, deploying)

If something would change a number or the story and you're unsure what I'd want, ask. Otherwise decide, and tell me what you decided.

If I ask for a claim the data can't support, tell me, and give me the strongest wording that is still true.

## Phase 0: Set up and prove the starting point

1. Check that Python is available and install `requirements.txt`.
2. Check that the eight CSV files are in `data/raw/`. If they aren't, point me to `data/README.md` and wait.
3. Run `python scripts/load.py`, `python scripts/run.py`, `python scripts/verify_pandas.py`, and `python scripts/check.py`.
4. The last command must report 16 of 16 validation checks passing, 48 of 48 SQL and pandas numbers matching, 61 of 61 identical to the frozen reference, and end with ALL CHECKS PASSED. If anything differs, stop and sort it out before touching anything else, because every later number would be in doubt.

Go straight on to Phase 1.

## Phase 1: Tell me what this is all about

Write `docs/summary.md` and show it to me. One page, plain English, no SQL, no jargon:

- **The data**: what it is, where it comes from, how many orders, what period, what each order records.
- **The question**: what the project sets out to answer, and why a fulfillment-quality team would care.
- **The findings**: the five or six things the data shows, each in one or two sentences with its key number.
- **What the dashboard will show**: the main views, in one line each.
- **What it cannot claim**: the limits, briefly.

Checkpoint 1. Stop here.

## Phase 2: Finish the analysis

Build all of these, then report once at the end. For each new file: write the query, add an independent recomputation of its headline numbers to `scripts/verify_pandas.py`, add the numbers to the ledger in `scripts/check.py`, and run the full check.

**`sql/10_initiative_sizing.sql`. What is each fix worth?** Size three options side by side, in late deliveries avoided and low reviews avoided:
- Seller handoff program: bring the flagged sellers down to the platform late-handoff rate. Count only late orders whose cause is `seller_handoff` as avoidable.
- Episode response: during the flagged weeks, how many late orders were late by 3 days or less, and by 7 days or less? That is what a temporary longer promise would have covered. The cost in lost conversions cannot be measured here, so say so.
- Lane-level promise: the same question for the destination states with the highest late rates.
Rank them. If the seller program turns out to be the smallest lever, say so plainly.

**`sql/11_launch_scorecard.sql`. Do new sellers have a rough first month?** Compare defect rates in a seller's first 30 days, days 31 to 90, and after. A first look showed more cancellations for new sellers, probably confounded by calendar time. Test it within the same calendar month. Only sellers whose first order is on or after 1 March 2017 count as new. If the gap disappears, drop it from the dashboard.

**`sql/12_early_warning.sql`. Can we see an episode coming?** Test whether the share of parcels in transit for more than 10 days, measured at each week's end, rises before the late rate does for the two flagged episodes. Report how many weeks of warning it gives, or that it gives none. If none, drop it.

**`sql/13_dashboard_cube.sql`. The data behind the filters.** Pre-aggregate what the dashboard needs so its filters work without a server: counts by week, destination state, outcome, and late cause, plus the seller table.

Then give me a short findings report: what held up, what was dropped and why, and the ranked list of fixes with their sizes.

Checkpoint 2. Stop here.

## Phase 3: Plan the dashboard

Look at every image in `design/inspiration/` and read `notes.md`. Then write `docs/dashboard_plan.md`:

- every tile, chart, table, and filter on the page, top to bottom, each with the ledger IDs or query it reads from
- the one-line title each chart will carry
- two visual directions described in a few lines each, based on my screenshots and the palette in the design brief

Checkpoint 3. I pick a direction and approve the plan.

## Phase 4: Build the dashboard

Follow `design/design_brief.md`. The essentials:

- **Dashboard first.** KPI tiles, charts, a sortable table, filters, hover details. It should feel like a professional analytics product.
- **Very little text.** One headline sentence at the top. Each chart gets a short title that states its finding and at most one short caption. No paragraphs on the main page. Do not explain how numbers were calculated on the main page.
- **A separate Method and SQL page**, reached by one quiet link in the header and footer. That is where the definitions, the validation checks, the SQL, the limits, the sources, and the note on how AI was used live. A reader who wants proof finds it there. A reader who doesn't never sees it.
- **Honesty stays, in compact form.** Small-sample results show their counts right on the chart (for example n = 35). A slim footer names the data source and states in one or two lines that this is multi-day parcel shipping data from Brazil, 2017 to 2018.
- A static site (HTML, CSS, JavaScript, no server) in `site/`, so it can be hosted free on GitHub Pages.
- Every number and every chart reads from JSON copied from `out/` by a build script. Nothing is typed into the HTML by hand.
- One mature charting library, used consistently.
- Looks right on a laptop first, and still works on a phone.
- No Instacart logo, colours, or wording that suggests I work with them.

Show me the first complete draft as soon as it runs, then refine from my reactions.

## Phase 5: Check it like a sceptic

- Write a script that pulls every number shown on the site and confirms each one is in the ledger with the same value.
- Check every outside fact on the site against `sources/SOURCES.md`. Anything without a ticked box comes off the page.
- Check every link, every filter combination, the phone layout, and the page in a second browser.
- Look at it as a director with two minutes. Fix whatever looks amateur: misaligned tiles, inconsistent number formats, crowded axes, weak chart titles.

## Phase 6: Publish

Checkpoint 4. With my go-ahead:

- Write a short README for GitHub: what the project is, the findings in five lines, how to reproduce every number, the limits.
- Create the repository, push, and turn on GitHub Pages. Confirm the raw data and my saved source PDFs are not in the repository.

## Phase 7: One page of talking points

Write `docs/talking_points.md`, a single page I can read before an interview:

- the project in three sentences
- the five numbers that matter and what each means
- for each chart, one sentence on what it shows and one on why a fulfillment team would care
- the three hardest questions someone might ask, with honest short answers
- the limits, in my own plain words

Then outline a six-slide deck: situation, what the monitor caught, whose problem it was, what to do, what it is worth, limits and next steps.

## To start

Read the files listed above, then begin Phase 0.
