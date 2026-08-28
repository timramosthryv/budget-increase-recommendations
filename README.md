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

The "Last updated" stamp in the header is written by `build.py` in US Central and labeled `CT`.
GitHub runners are UTC, so without the conversion the dashboard would show a time several hours
ahead of the team.

## What the dashboard tracks

Sections pulled from Asana project `1207771164017257`:

| Asana section | Status shown |
| --- | --- |
| Reviewed - No Upgrade Yet | No Upgrade Yet |
| Reviewed - Upgraded 2026 | Upgraded |
| No Longer Counts 2026 | No Longer Counts |

Fields captured: Submitted By (Optimizer), Thryv Leads Cohort or Escalation Type, Date Recommended,
Date Upgrade Happened, Dollar Amount Recommended, Dollar Amount Increased. Business Name, EAID,
Campaign ID, Other Product Recommended, Date Reviewed Last, and Date No Longer Valid come along
for context.

**Optimizer** comes from the Submitted By custom field. **Coach** is always the Asana assignee.

If Submitted By is empty, the Optimizer column is left blank rather than guessed from the task title.
Those records still count in the totals but group under "Unassigned" in the Optimizer breakdowns, and
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

### Goal metrics vs. cohort analytics

These are two different populations and the dashboard reports them separately on purpose.
Adding them together produces a number that means nothing.

**Goal metrics** appear in the blue strip under the KPI tiles on the YTD, QTD, MTD, By
Optimizer and By Coach views, and follow the comp plan rules confirmed 2026-08-26.

*Recommendation goal.* A recommendation of **$100 or greater** counts toward the period it
was submitted in, permanently. Records later moved to `No Longer Counts 2026` still count,
because the 90-day closure voids kicker eligibility only, not the recommendation credit.
Verified against March 2026: counting them gives 176 against the manual tracker's 183,
while excluding them gives roughly 85.

*Submission deadline.* A recommendation must be entered in Asana by the **9th of the month
following** its Date Recommended, measured on Created At and inclusive of the 9th. Six records
in 2026 fail this, four of them Jean Rivera Tejeda's April recommendations entered on 5/13.
A record missing either date is not penalised, since the rule cannot be tested.

*Kicker.* **$50 per increase**, and the increase must land within **90 days** of its own
recommendation. It is payable only once the quarterly requirement is met, which is 30 for
PCSM and Senior PCSM roles and 5 for Escalation Associates and Reactive Optimization
Specialists. Meet the requirement and every eligible increase pays, including ones tied to
recommendations from an earlier quarter. The dashboard shows eligible increases and the
dollar figure but does **not** apply the goal gate, because the gate needs a ruling on
whether 29 against a requirement of 30 pays nothing.

An increase dated before its own recommendation is treated as a data error and excluded,
not as a fast conversion.

*Quarterly requirement.* Held in `KICKER_REQUIREMENT` near the top of the script in
`template.html`. 30 for PCSM and Senior PCSM roles, 5 for Escalation Associates and
Reactive Optimization Specialists. Keys use Asana's `Submitted By` spelling, which differs
from the roster in two places: the roster says Elias Ellison and Edgar Acosta, Asana records
Eli Ellison and Edgar Acost. **Anyone missing from that table reports as "not set" and pays
nothing** rather than defaulting to a number, because guessing a requirement decides whether
a person gets paid. Update this table when the roster changes.

*Records impacting the period.* Recommendations plus increases minus the ones counted in
both. This is the figure the manual tracker's monthly column represents. For June 2026 the
export gave 134 + 22 - 6 = 150, and the manual sheet 151, the difference being one record
the export dropped on a date boundary.

**Cohort analytics** are the KPI tiles: Cohort Upgrade Rate, Cohort Dollar Capture, Still
Open and No Longer Counts. These take every record recommended in the period regardless of
amount or status and show how that cohort resolved. No Longer Counts sits in the Cohort
Upgrade Rate denominator by design, which is why the tiles will not add up to the goal
figures.

### Recommendation Kickers tab

Ranks Optimizers by qualifying recommendations and calculates the payout. The Goal column
shows recommendations against the requirement, green when met. The Kicker column shows what
is earned. Where the goal was missed the row reads `$0`, with the eligible increases still
visible in the Upgrades column beside it. Someone with no requirement on the roster reads
`--` rather than `$0`, so an unrated person is never confused with someone who earned
nothing.

Opening a row shows the account detail. Each increase is marked either as paying $50 or as
not paying, with the reason: the day count when it fell outside the 90-day window, or
"upgrade predates rec" when the dates are the wrong way round, which is a data error rather
than a fast conversion.

Two figures to know when reading it. Applied to closed quarters, the gate would have held
$700 in Q1 2026 and $500 in Q2 2026. Both quarters were in fact paid un-gated, and the
un-gated totals match the manual tracker to the dollar, $1,600 and $2,650. So the written
rule and the practice do not currently agree, and that is a decision for the business rather
than something the dashboard should assume.

### Optimizers who have left

`FORMER_OPTIMIZERS` in `template.html` maps a name to the first day they were no longer in
the role. They drop out of any period **starting on or after** that date and keep every
period they actually worked, so history is not rewritten. On the YTD view the period starts
1 January, so someone who worked part of the year still appears there.

Currently: `Danilo Acosta` from `2026-07-01`. His last recommendation was 2026-06-30, so he
keeps Q1 and Q2 in full and drops out of Q3 onward. Adjust the date if HR has a different
one, and add a line per person as people leave.

Records belonging to a departed Optimizer are not silently dropped. They appear in the
integrity check as a data quality row naming the person, the account and the end date, so
the exclusion is auditable.

### Interpretations applied

The written criteria do not cover every case. Rather than bury the calls in code, the
Recommendation Kickers tab lists all eight on screen with what each is worth in the selected
period, and a running total at stake. Change any one and the kicker moves by the amount shown.

The two that carry real money in Q2 2026 are: an increase only counts when the record status
is Upgraded, so a No Longer Counts record whose increase landed inside the window pays nothing;
and repeat records on one campaign each pay, flagged in the integrity check but not
de-duplicated, because two increases on one account may be genuine.

### Name corrections

`NAME_FIXES` in `template.html` corrects Asana's `Submitted By` picklist on load, applied to
both the Optimizer and Coach fields so every count, grouping, requirement lookup and label
downstream uses the real name. Currently `Edgar Acost` renders as `Edgar Acosta`. Fix the
picklist in Asana and the entry becomes a harmless no-op. Separately, the roster's
`Elias Ellison` is `Eli Ellison` in Asana, which is correct as-is and needs no mapping.

### Integrity check

Sits under the tracker table on the Recommendation Kickers tab and re-runs on every
refresh. Asana is the system of record. The manual tracker may carry deliberate overrides,
so this does not attempt to match it. Its job is to prove the dashboard's figures stand on
their own and to name every record that needs fixing at source.

Eight checks, split by whether money moves:

**Affects pay**

- Increase landed outside the 90-day window, with the day count shown
- Increase dated before its own recommendation, which is a data error not a fast conversion
- Increase missing a date, so the window cannot be measured
- One campaign paying the kicker more than once in the period, matched on EAID plus
  Campaign ID within the same Optimizer. Records sharing an identical upgrade date are
  called out as likely duplicates; different dates may be two genuine increases
- One campaign credited to two different Optimizers in the same period
- A record with no `Submitted By` value, which cannot be credited to anyone

**Data quality**

- Recommendation below the $100 minimum, excluded from the goal count
- Active Optimizer with no quarterly requirement on the roster, so the goal cannot be
  evaluated and nothing pays
- Record belonging to a departed Optimizer, excluded from the period

A summary strip shows the count for each check plus the total kicker dollars affected. When
a period is clean it says so rather than showing an empty table.

### Date boundaries

Period membership is decided on the `Month Recommended` and `Month Upgraded` strings, which
`fetch_asana.py` builds from the year and month of each date. There is no inclusive or
exclusive comparison anywhere, so a record dated the first or last day of a month cannot
fall out of its own period. Any hand-built export feeding this process should use the same
approach.


- **Cohort upgrade rate** = upgraded records / all records recommended in the period, including No Longer Counts. Not goal attainment
- **Cohort dollar capture** = Dollar Amount Increased / Dollar Amount Recommended, counting only the records that upgraded
- **Still open** = dollars recommended on records sitting in Reviewed - No Upgrade Yet
- **No longer counts** = dollars recommended on records closed without an upgrade
- Recommendation volume and dollars plot to the month of **Date Recommended**
- Upgrade volume and dollars plot to the month of **Date Upgrade Happened**
- The MTD tab applies the same definitions to a single month, so the reconciliation identity
  holds within the month as well

Win rate and capture are reported as two separate figures rather than one blended
percentage. A single ratio of dollars upgraded to dollars recommended is misleading for two
reasons. First, it cannot distinguish a low number caused by few wins from one caused by small
wins, and in this data those pull in opposite directions: only about one recommendation in eight
converts, but the ones that do land well above the amount recommended. Second, the numerator and
denominator are dated on different fields, so they describe overlapping but non-identical sets of
records.

The three outcome tiles reconcile against the total by construction. Every recommendation resolves
to exactly one of upgraded, still open, or no longer counts, so those three dollar figures always
sum to dollars recommended. The dashboard prints that identity under the KPI row and flags it if
it ever fails to balance.

Because the two metrics use different dates, a recommendation made in June that upgrades in
August shows in June on the recommended series and August on the upgraded series. That is
intentional and is called out on the chart.

## Tabs

1. **YTD Summary** — headline totals, monthly recommended vs upgraded, Optimizer and Coach scorecards, status mix, cohort performance, full account detail
2. **QTD Summary** — same view scoped to a selected quarter
3. **MTD Summary** — same view scoped to a single month, selectable from any month with activity
4. **By Optimizer** — per-person drill-down with YTD and QTD toggle
5. **By Coach** — per-coach drill-down with a Optimizer roll-up
6. **Recommendation Kickers** — Optimizers ranked by number of recommendations submitted, highest
   first, with a QTD and YTD toggle. Each row expands to the account level detail behind the
   count: account name, Thryv Leads cohort or escalation type, date recommended, and dollar
   amount recommended. Modeled on the SaaS Growth kicker tracker.
7. **Raw Data** — filterable table, CSV export, and data source notes

The Optimizer and Coach scorecards are read left to right: recommendations on the left, upgrades that
actually landed on the right, with the capture rate on the far right.

A second kicker tab for upgrades can be added alongside the first when the rules are defined.

### Kicker credit rules

Confirmed with the director. Two credits, each on its own clock:

**Recommendation credit is permanent.** It is earned when the Optimizer submits and is never taken
back. A recommendation that later moves to No Longer Counts still counts. It lands in the period
of Date Recommended.

**Upgrade credit lands in the period the upgrade happened**, keyed on Date Upgrade Happened, not
on when the recommendation was made. A Q2 recommendation that upgrades in Q3 gives the
recommendation credit to Q2 and the upgrade credit to Q3.

Because the two credits use different dates, the Recommendations and Upgrades columns describe
overlapping but different sets of records. That is intentional. Rows where the upgrade carried in
from an earlier period are marked "carried" next to the upgrade count, and the expanded detail
labels every record as Recommendation, Rec + Upgrade, or Upgrade only.

A useful consequence: because upgrades are credited on upgrade date, the kicker upgrade totals
agree with the Dollars Upgraded tile on the By Coach and By Optimizer tabs. An earlier build credited
upgrades on the recommendation date, which made those two tabs disagree.

### Kicker payout

The payout column reads "Pending" and the payout KPI shows a dash. No qualifying threshold or
tier table has been defined for recommendation kickers, and inventing one would put numbers in
front of leaders that nobody agreed to. Everything else on the tab is live.

For reference, the SaaS Growth dashboard pays on a quarterly threshold: kickers are earned on
each opportunity beyond the third in a quarter, with tiered amounts by dollar band and a flat
rate for certain growth types. If recommendation kickers follow a similar shape, the rule drops
into one function and the column fills in with no other changes.


## Setup

1. **Add the files.** Upload everything in this folder to the repo root, keeping
   `.github/workflows/` intact. Create the two workflow files with Add file, Create new file and
   type the full path, since drag and drop is unreliable with dotted folders.
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
