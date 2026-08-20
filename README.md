# Budget Increase Recommendations Dashboard

Live dashboard for the Asana project **Budget Increase Recommendations**, built on the same
pattern as the SaaS Growth dashboard: Asana export to `data.xlsx`, `build.py` injects the data
into `template.html`, and the result is committed as a self-contained `index.html`.

Target URL once Pages is enabled: `https://timramosthryv.github.io/budget-increase-recommendations/`

## Files

| File | Purpose |
| --- | --- |
| `fetch_asana.py` | Pulls the three tracked sections from Asana and writes `data.xlsx` |
| `build.py` | Injects `data.xlsx` into `template.html` and writes `index.html` |
| `template.html` | Dashboard design and logic, with a `@@DATA_INJECTION@@` placeholder |
| `index.html` | Generated file that GitHub Pages serves. Do not edit by hand |
| `data.xlsx` | Latest raw export. Overwrite it manually if you ever need an off-cycle refresh |
| `.github/workflows/refresh.yml` | Scheduled Asana export, twice daily |
| `.github/workflows/build.yml` | Rebuilds `index.html` whenever data or the template changes |

## What the dashboard tracks

Sections pulled from Asana project `1207771164017257`:

| Asana section | Status shown |
| --- | --- |
| Reviewed - No Upgrade Yet | No Upgrade Yet |
| Reviewed - Upgraded 2026 | Upgraded |
| No Longer Counts 2026 | No Longer Counts |

Fields captured: Submitted By (PCSM), Thryv Leads Cohort or Escalation Type, Date Recommended,
Date Upgrade Happened, Dollar Amount Recommended, Dollar Amount Increased. Business Name, EAID,
Campaign ID, Other Product Recommended, Date Reviewed Last, and Date No Longer Valid come along
for context.

**PCSM** comes from the Submitted By custom field. **Coach** is always the Asana assignee.

If Submitted By is empty, the PCSM column is left blank rather than guessed from the task title.
Those records still count in the totals but group under "Unassigned" in the PCSM breakdowns, and
the Raw Data tab reports how many are affected so they can be corrected in Asana. The export log
in Actions prints the same warning. Business Name falls back to the text after the first comma in
the task title, since that field is only used for labeling accounts.

## Branding

The Thryv logo sits in the header at 28px tall, left of the title, separated by a hairline rule.
It is embedded in `template.html` as a base64 data URI, so `index.html` stays self-contained and
renders even if an external image host is unreachable.

The supplied file was the primary logo: black wordmark, orange swoosh, transparent background.
Black would not have been legible on the navy header, so the wordmark was recolored to white and
the orange swoosh left untouched. This is the standard reverse treatment for a dark background.
If Brand has an official reverse asset, swapping it in is a single change to the `src` on the
`img.brand-logo` element.

To replace the logo later, base64 encode the new file and paste it over the existing data URI:

```
python -c "import base64;print('data:image/png;base64,'+base64.b64encode(open('logo.png','rb').read()).decode())"
```

## Exports

Two paths, both producing a CSV with a fixed column order and a UTF-8 byte order mark so Excel
opens it cleanly:

- **Export Raw Data** in the header, available from every tab, writes every tracked record. This
  is the one to use for end-of-quarter goal reporting.
- **Export Filtered View** on the Raw Data tab writes only what the current filters show.

Filenames are date stamped, for example `budget-increase-recommendations_all_2026-08-20.csv`.

## Metric definitions

- **Dollar capture rate** = Dollar Amount Increased / Dollar Amount Recommended
- **Upgrade conversion rate** = upgraded records / all reviewed records, including No Longer Counts
- Recommendation volume and dollars plot to the month of **Date Recommended**
- Upgrade volume and dollars plot to the month of **Date Upgrade Happened**

Because the two metrics use different dates, a recommendation made in June that upgrades in
August shows in June on the recommended series and August on the upgraded series. That is
intentional and is called out on the chart.

## Tabs

1. **YTD Summary** — headline totals, monthly recommended vs upgraded, PCSM and Coach scorecards, status mix, cohort performance, full account detail
2. **QTD Summary** — same view scoped to a selected quarter
3. **By PCSM** — per-person drill-down with YTD and QTD toggle
4. **By Coach** — per-coach drill-down with a PCSM roll-up
5. **Kicker** — placeholder, waiting on the qualifying rules and payout tiers
6. **Raw Data** — filterable table, CSV export, and data source notes

The PCSM and Coach scorecards are read left to right: recommendations on the left, upgrades that
actually landed on the right, with the capture rate on the far right.

## Setup

1. **Add the files.** Upload everything in this folder to the repo root, keeping
   `.github/workflows/` intact. Do not upload `index-sample-preview.html` or `data-sample.xlsx`;
   those are local test artifacts.
2. **Create the Asana token.** In Asana, go to your profile settings, Apps, Personal access
   tokens, and create one for this dashboard.
3. **Store the token.** In the repo, go to Settings, Secrets and variables, Actions, then
   New repository secret. Name it exactly `ASANA_TOKEN` and paste the value.
4. **Allow Actions to commit.** Settings, Actions, General, Workflow permissions, select
   "Read and write permissions" and save.
5. **First run.** Actions tab, "Refresh from Asana", Run workflow. This creates `data.xlsx`
   and `index.html`.
6. **Turn on Pages.** Settings, Pages, Source = Deploy from a branch, Branch = `main`, folder
   = `/ (root)`. The site is live a minute or two later.

## Refresh schedule

`refresh.yml` runs at 12:00 AM and 12:00 PM US Central. GitHub cron only accepts UTC, so four
UTC times are scheduled and a gate step keeps only the two that land on midnight and noon
Central. That keeps the schedule correct across daylight saving changes with no cron edits.

GitHub can delay scheduled runs when its queue is busy. A delay longer than an hour pushes a run
outside its window and it gets skipped until the next one. Run workflow on the Actions tab
forces an immediate refresh any time.

## A note on visibility

This repo is public, which means account names, EAIDs, and dollar amounts are readable by
anyone with the URL. The SaaS Growth dashboard has the same exposure. Switching the repo to
private disables GitHub Pages on a free plan, so if the data should not be public the options
are a paid plan with private Pages, or replacing business names with EAIDs only. Worth a decision
before this gets shared widely.
