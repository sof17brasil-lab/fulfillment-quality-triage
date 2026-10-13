# Design brief

Read this together with `design/inspiration/notes.md` and the screenshots in `design/inspiration/`. Sofia's notes describe the vision section by section. This brief sets the standards that make it look sophisticated and run smoothly.

## The goal

A scroll-driven, dark, visually rich data story that a director and a hiring manager would be impressed by. Big statements, beautiful charts, subtle motion, very little text. Every visual is a real chart or a real number from the project.

## Look

**Palette: Instacart-inspired, not Instacart's.** Starting values, adjust for contrast:

| Role | Starting colour |
|---|---|
| Page background | Near-black #0E0F0D |
| Card surfaces | Charcoal #1A1C19 |
| Main text | Warm off-white #F4F1EA |
| Secondary text | Soft grey #A9ADA4 |
| Primary: on time, normal, good | Fresh green #34C26B |
| Accent: late, problem, alerts | Carrot orange #FF8A2A |
| Supporting colours for the four fix panels | Deep green, leaf green, carrot orange, warm cream, or similar harmonious set |

- Do not use Instacart's logo, exact brand colour codes, brand font, or any Instacart artwork.
- Every text and chart colour must pass WCAG AA contrast on the dark background (4.5:1 for text).
- Green means good, orange means a problem, everywhere on the page. Never swap them.

**Type.** A modern, friendly, rounded geometric sans-serif from Google Fonts (for example Plus Jakarta Sans or DM Sans), one family throughout. Very large, heavy weights for statements. Tabular figures for numbers so they line up.

**Imagery.** Food in the background: produce such as carrots, lemons, tomatoes, leafy greens, avocado, bread.
- Prefer clean illustrated SVGs, or photos with a free licence that allows this use (for example the Unsplash licence). Record each image's source and licence in `design/image_credits.md`.
- Keep files small (SVG or WebP).
- Images sit behind the content at low prominence. They must never reduce the readability of a chart or a number.

## Scroll story, top to bottom

Follow the order in `notes.md`: title, headline numbers, method timeline, stacking finding cards, choose your fix, seller watchlist, customer reviews, calculator, footer. Plus a separate Method and SQL page reached by one quiet link in the header and footer.

## Text budget

- The title section: one huge statement, one short supporting line, the credited CEO quote.
- Each chart card: a title of ten words or fewer that states the finding, and at most one caption of twenty words or fewer.
- No paragraphs on the main page. Nothing on the main page about how a number was calculated. That lives on the Method and SQL page.
- Target for the main page, not counting chart labels and numbers: under 250 words.

## Motion

Subtle, quick, and purposeful. It should feel premium, not playful.

- **Floating food:** gentle parallax. Items drift at different speeds as the page scrolls, and a few fade or pop in softly as new sections arrive. Slow, small movements only.
- **KPI tiles:** numbers count up once when they first appear, about 0.8 seconds.
- **Method timeline:** the icon travels left to right along the 1, 2, 3 line in step with scrolling, and each step lights up as the icon reaches it.
- **Stacking cards:** each finding card slides up and stacks on the previous one, leaving the earlier cards visible as thin title strips (sticky positioning).
- **Charts:** animate in the first time they appear. Lines draw left to right, bars grow from the baseline, about 0.6 to 0.8 seconds.
- **Fix panels:** on hover (or tap on a phone), the panel expands or flips to reveal its explanation, about 0.3 seconds.
- **Filters and hovers:** values move smoothly to their new positions. Tooltips fade in within 0.15 seconds.
- Nothing loops. Nothing blocks the numbers. Every animation finishes within one second.
- If the visitor's device is set to reduce motion, turn off parallax and scroll effects and show everything in place.

## Runs smoothly

- Animate only `transform` and `opacity`, so motion stays at 60 frames per second.
- Start chart and image work only when a section comes into view (IntersectionObserver), and lazy-load images below the first screen.
- One charting library, loaded once. No heavy frameworks the page does not need.
- Target a Lighthouse performance score of 90 or more on desktop. Report the actual score.
- Test in Chrome and Safari, on a laptop and on a phone. On a phone, cards stack in one column, the fix panels open on tap, and the background food is reduced.

## Charts

- Titles state the finding, not the metric.
- Label values directly instead of relying on a legend wherever possible.
- Light gridlines, no chart borders, generous spacing.
- Never rely on colour alone. Add a label or a pattern.
- Small-sample results print their counts on the chart (for example n = 35).
- Hover shows exact values.

## The calculator

Inputs the reader types: orders per year, expected reduction in defect rate (percentage points), cost per defect. Output: defects avoided per year and value per year. All inputs start empty. Orders per year may offer a button "Use Instacart's public scale" that fills in the annualised Q2 2026 figure from source S01c, labelled as public information, with the result labelled illustrative. Never pre-fill a cost.

## Customer reviews section

- Real reviews from the dataset, on late orders, chosen by a fair stated rule (for example a random draw with a fixed seed among low-star reviews on late orders that mention the delay), not the most dramatic.
- Show the original Portuguese, an English translation, the star rating, and how many days late the order was.
- Sofia approves every translation before publishing.
- Reviews are anonymous in the data. Never show any identifier.

## Honesty, in compact form

- The footer names the data (Brazilian E-Commerce Public Dataset by Olist, via Kaggle), its licence (CC BY-NC-SA 4.0), and one line on the main limit: multi-day parcel shipping in Brazil, 2017 to 2018.
- The footer says: "Independent portfolio project. Not affiliated with Instacart."
- Instacart facts appear only if they are ticked in `sources/SOURCES.md`, each with its source and date.
