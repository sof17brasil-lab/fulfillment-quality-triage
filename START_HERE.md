# Start here

This folder is a starter kit for your Instacart portfolio project. The analysis core is built and checked. Claude Code finishes the analysis and builds the dashboard for you.

## What is in the folder

| Item | What it is |
|---|---|
| `START_HERE.md` | This file. |
| `CLAUDE_CODE_PROMPT.md` | The message you paste into Claude Code to begin. |
| `CLAUDE.md` | Project rules. Claude Code reads this automatically every session. |
| `docs/project_brief.md` | The project in one page: findings so far, open leads, limits. |
| `sources/SOURCES.md` | Every outside fact with its link, exact words, and check status. |
| `reference/numbers_ledger.csv` | Every number in the project, the query behind it, and whether two methods agreed. Opens in Excel or Google Sheets. |
| `reference/expected_results/` | Full output of each query from the reference run. |
| `sql/` | Nine working SQL files. |
| `scripts/` | Four small programs: load the data, run the SQL, re-check independently, prove the numbers. |
| `data/README.md` | Where to download the data and how to confirm you got the right files. |
| `design/` | The design brief, plus a folder for your screenshots. |

## Your steps

### 1. Put the folder somewhere permanent
Unzip `Instacart.zip`. It gives you a folder called `Instacart`. Move that folder to the place you keep projects, for example `Documents/`. Do not leave it in Downloads. Everything below goes inside it.

### 2. Get the data (10 minutes)
Follow `data/README.md`. In short: download the Olist dataset from Kaggle, unzip it, and move eight CSV files into `data/raw/`. Write down the license you see on the Kaggle page.

### 3. Add your design ideas (15 minutes)
Yes, screenshot them. Save each screenshot into `design/inspiration/` and write one line per image in `design/inspiration/notes.md` saying which part you like. The note matters as much as the picture.

You can also paste a screenshot straight into Claude Code later (drag it in, or copy and paste). The folder is better for anything you want it to remember across days.

### 4. Check the sources yourself (30 to 45 minutes)
Open `sources/SOURCES.md`. For each row, open the link, find the exact words, tick the box, and save a PDF into `sources/originals/`. Start with the job posting (S05), since postings get taken down.

This is the one job nobody can do for you. When an interviewer asks "where does that come from?", you will have opened the page yourself.

### 5. Open Claude Code in the folder
Open the `Instacart` folder in Claude Code (the folder that contains `CLAUDE.md`). If you have not set it up yet, the guide is at https://docs.claude.com/en/docs/claude-code/overview.

### 6. Paste the prompt
Open `CLAUDE_CODE_PROMPT.md`, copy everything below the line, and paste it as your first message.

### 7. Let it work, and answer at four checkpoints
Claude Code does the SQL, the checks, and the website for you. It stops only four times.

| Phase | What Claude Code does | Your part |
|---|---|---|
| 0 | Runs the checks on your machine | Nothing, unless it reports a problem |
| 1 | Writes a one-page plain-English summary: the data, the findings, what the dashboard will show | **Checkpoint 1.** Read it. Say continue. |
| 2 | Finishes the analysis: sizing of each fix, new-seller scorecard, early warning | **Checkpoint 2.** Read the short findings report. Say continue. |
| 3 | Plans the dashboard from your screenshots and proposes two looks | **Checkpoint 3.** Pick a look. Approve the plan. |
| 4 | Builds the dashboard and the separate Method and SQL page | React to the draft: what you like, what to change |
| 5 | Checks every number, link, and filter | Nothing |
| 6 | Publishes to GitHub Pages | **Checkpoint 4.** Say yes before anything goes public. |
| 7 | Writes one page of talking points and a deck outline | Read the page before any interview |

### 8. If you come back another day
Open Claude Code in the same folder and say: "Read CLAUDE.md and docs/project_brief.md, then tell me which phase we are in and what is next." It can also resume the previous conversation.

## A realistic schedule

The posting went up on 3 October, so speed matters. Apply early in the week with a tailored resume, and send the project as soon as it is solid.

| Day | Goal |
|---|---|
| 1 | Steps 1 to 6. Phases 0 and 1. Submit the application. |
| 2 | Phases 2 and 3. |
| 3 | Phases 4 and 5. |
| 4 | Phases 6 and 7. Send the link to a person on the team. |

A finished project sent this week beats a bigger one sent next week.

## Rules to protect yourself

1. **Read the talking points page before any interview.** The posting asks for advanced SQL, so expect questions about how the numbers were built. The page gives you honest short answers.
2. **No number without a ledger row. No outside fact without a ticked source.**
3. **Do not claim a dollar saving for Instacart.** Their costs are not public. The calculator lets the reader use their own.
4. **Say what the data is.** Multi-day parcel shipping in Brazil, 2017 to 2018. The method is what transfers.
5. **Be open that you used AI.** The posting asks for it, together with validation. Your validation is the strong part: two independent computations that agree, sixteen checks that pass.

## What the starter numbers already show

- 98,962 real orders. 6.8% of delivered orders arrived late.
- Late orders get 1 or 2 stars 62.4% of the time. On-time orders, 9.2%.
- Two bad episodes covering 8 of 86 weeks hold 41.5% of all late orders.
- Across the period, 72.3% of late orders had left the seller on time. In the worst episode it was 85.6%, concentrated in one state where 42.2% of deliveries were late against a normal 6.6%.
- So chasing slow sellers, the obvious fix, would have missed most of the problem.
- Customers whose first order was late came back about 28% to 33% less often. This rests on 35 to 41 repeat customers, so it is a signal, not a proven effect.

## When the project is done

Bring it back for the resume tailored to this posting, the two-line note to someone on the team, and the six-slide deck.
