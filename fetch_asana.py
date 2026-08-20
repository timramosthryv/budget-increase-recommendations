#!/usr/bin/env python3
"""
fetch_asana.py - Pull Budget Increase Recommendations tasks from Asana into data.xlsx.

Requires environment variable ASANA_TOKEN (a personal access token).
Output: data.xlsx with a single 'Raw Data' sheet, ready for build.py.

Pulls three sections of the Budget Increase Recommendations project, paginating
through all results. Timestamps are converted to US Central time.

PCSM comes from the 'Submitted By' custom field. Coach is always the task assignee.
If Submitted By is empty the PCSM column is left blank rather than guessed, so the
gap shows up on the dashboard and can be fixed in Asana.
"""
import os, sys, time, json, urllib.request, urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo
import openpyxl

TOKEN = os.environ.get('ASANA_TOKEN')
if not TOKEN:
    print("ERROR: ASANA_TOKEN environment variable not set")
    sys.exit(1)

PROJECT_GID = "1207771164017257"

# Section name -> Asana section GID. Only these three sections are pulled.
SECTIONS = {
    "Reviewed - No Upgrade Yet": "1207771164017261",
    "Reviewed - Upgraded 2026": "1212774875058696",
    "No Longer Counts 2026": "1212774880488463",
}

# Short status label used by the dashboard.
STATUS_MAP = {
    "Reviewed - No Upgrade Yet": "No Upgrade Yet",
    "Reviewed - Upgraded 2026": "Upgraded",
    "No Longer Counts 2026": "No Longer Counts",
}

OPT_FIELDS = ("name,assignee.name,created_at,due_on,modified_at,completed_at,completed,"
              "parent.name,permalink_url,memberships.project.gid,memberships.section.name,"
              "custom_fields.name,custom_fields.display_value")

CENTRAL = ZoneInfo("America/Chicago")

HEADERS = ["Task ID", "Section", "Status", "Task Name", "Account Name", "PCSM", "Coach",
           "Cohort or Escalation Type", "Other Product Recommended",
           "Date Recommended", "Month Recommended", "Quarter Recommended",
           "Date Upgrade Happened", "Month Upgraded", "Quarter Upgraded",
           "Date Reviewed Last", "Date No Longer Valid",
           "Dollar Amount Recommended", "Dollar Amount Increased",
           "EAID", "Campaign ID", "Created At", "Modified At", "Task URL"]

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def api_get(url):
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def fetch_section(gid):
    tasks = []
    url = (f"https://app.asana.com/api/1.0/tasks?section={gid}&limit=100"
           f"&opt_fields={urllib.parse.quote(OPT_FIELDS, safe=',.')}")
    while url:
        data = api_get(url)
        tasks.extend(data.get("data", []))
        nxt = data.get("next_page")
        url = nxt["uri"] if nxt else None
        time.sleep(0.2)
    return tasks


def to_central(iso):
    if not iso:
        return ""
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.astimezone(CENTRAL).strftime("%Y-%m-%d %H:%M:%S")


def to_date(v):
    """Asana date custom fields arrive as 2026-08-13 or 2026-08-13T00:00:00.000Z."""
    return (v or "")[:10]


def month_label(d):
    """2026-07-09 -> 'Jul 2026'"""
    if not d or len(d) < 7:
        return ""
    try:
        y, m = int(d[0:4]), int(d[5:7])
        return f"{MONTH_ABBR[m - 1]} {y}"
    except (ValueError, IndexError):
        return ""


def quarter_label(d):
    """2026-07-09 -> 'Q3 2026'"""
    if not d or len(d) < 7:
        return ""
    try:
        y, m = int(d[0:4]), int(d[5:7])
        return f"Q{(m - 1) // 3 + 1} {y}"
    except ValueError:
        return ""


def to_num(v):
    try:
        n = float(str(v).replace(",", "").replace("$", ""))
        return int(n) if n == int(n) else round(n, 2)
    except (ValueError, TypeError, AttributeError):
        return ""


def account_from_task_name(name):
    """Task names follow 'PCSM Name, Account Name'. Used only as an account fallback
    when the Business Name field is empty. PCSM never comes from the task name."""
    if not name:
        return ""
    return name.split(",", 1)[1].strip() if "," in name else name.strip()


def row_for(t, section_name):
    cf = {c["name"]: (c.get("display_value") or "") for c in (t.get("custom_fields") or [])}

    # Prefer the section returned by Asana memberships; fall back to the section we queried.
    section = section_name
    for m in (t.get("memberships") or []):
        proj = (m.get("project") or {}).get("gid")
        if proj == PROJECT_GID and m.get("section"):
            section = m["section"]["name"]

    task_name = t.get("name", "") or ""

    # PCSM is the Submitted By field only. Left blank if the field is empty.
    pcsm = (cf.get("Submitted By") or "").strip()
    account = (cf.get("Business Name") or "").strip() or account_from_task_name(task_name)
    coach = (t.get("assignee") or {}).get("name", "") if t.get("assignee") else ""

    d_rec = to_date(cf.get("Date Recommended"))
    d_up = to_date(cf.get("Date Upgrade Happened"))

    return [
        t.get("gid", ""),
        section,
        STATUS_MAP.get(section, section),
        task_name,
        account,
        pcsm,
        coach,
        cf.get("Thryv Leads Cohort or Escalation Type", ""),
        cf.get("Other Product Recommended", ""),
        d_rec,
        month_label(d_rec),
        quarter_label(d_rec),
        d_up,
        month_label(d_up),
        quarter_label(d_up),
        to_date(cf.get("Date Reviewed Last")),
        to_date(cf.get("Date No Longer Valid")),
        to_num(cf.get("Dollar Amount Recommended")),
        to_num(cf.get("Dollar Amount Increased")),
        (cf.get("EAID", "") or "").strip(),
        (cf.get("Campaign ID", "") or "").strip(),
        to_central(t.get("created_at")),
        to_central(t.get("modified_at")),
        t.get("permalink_url", ""),
    ]


def main():
    rows = []
    seen = set()
    for name, gid in SECTIONS.items():
        tasks = fetch_section(gid)
        print(f"  {name}: {len(tasks)} tasks")
        for t in tasks:
            gid_t = t.get("gid")
            if gid_t in seen:
                continue
            seen.add(gid_t)
            rows.append(row_for(t, name))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Raw Data"
    ws.append(HEADERS)
    for r in rows:
        ws.append(r)
    wb.save("data.xlsx")
    print(f"data.xlsx written: {len(rows)} rows")

    pcsm_i, coach_i = HEADERS.index("PCSM"), HEADERS.index("Coach")
    no_pcsm = sum(1 for r in rows if not r[pcsm_i])
    no_coach = sum(1 for r in rows if not r[coach_i])
    if no_pcsm:
        print(f"  WARNING: {no_pcsm} task(s) have no Submitted By value")
    if no_coach:
        print(f"  WARNING: {no_coach} task(s) have no assignee")


if __name__ == "__main__":
    main()
