"""
Phase 4 - Step 3: raw_tasks.csv
----------------------------------
Adds all task-master fields on top of the Phase 3 task framework,
following the business rules we reviewed and revised together.
"""

import pandas as pd
import numpy as np
from datetime import timedelta

np.random.seed(42)  # reproducible output — same result every run

# ---------------------------------------------------------------
# Load Step 1 outputs
# ---------------------------------------------------------------
tasks_df = pd.read_csv("task_framework_draft.csv")
vendors_df = pd.read_csv("vendors.csv")

from datetime import datetime
OPENING_DATE = datetime(2027, 3, 1)
PRE_OPENING_WEEKS = 12
PROJECT_START = OPENING_DATE - timedelta(weeks=PRE_OPENING_WEEKS)

# =================================================================
# RULE 1 — Task_ID
# =================================================================
tasks_df["Task_ID"] = (
    tasks_df.groupby("Department_ID").cumcount() + 1
).astype(str).str.zfill(3)
tasks_df["Task_ID"] = tasks_df["Department_ID"] + "-" + tasks_df["Task_ID"]

# =================================================================
# RULE 2 — Owner (one role per Workstream, not random people)
# =================================================================
OWNER_BY_WORKSTREAM = {
    "Network & Infrastructure": "Network Infrastructure Lead",
    "Systems Integration (PMS/POS)": "Systems Integration Manager",
    "Security & End-User Support": "IT Support & Security Manager",
    "MEP Systems": "MEP Engineer",
    "Life Safety Systems": "Life Safety Systems Engineer",
    "Building Commissioning": "Chief Engineer",
    "Recruitment & Staffing": "Talent Acquisition Manager",
    "Onboarding & Training": "Training & Development Manager",
    "Employee Welfare & Compliance": "HR Compliance Manager",
    "Room Readiness": "Housekeeping Operations Manager",
    "Linen & Laundry Operations": "Laundry Operations Supervisor",
    "SOPs & Equipment": "Executive Housekeeper",
    "Guest Systems & Reservations": "Reservations Manager",
    "SOPs & Training": "Front Office Manager",
    "Guest Experience Readiness": "Guest Experience Manager",
    "Kitchen Commissioning": "Executive Chef",
    "Outlet Setup & Menu Development": "F&B Director",
    "Supplier & Service Readiness": "F&B Operations Manager",
    "Surveillance & Access Control": "Security Systems Manager",
    "Emergency & Safety Procedures": "Security Operations Manager",
    "Staff Training & Licensing": "Chief Security Officer",
    "Systems & Controls Setup": "Financial Controller",
    "Budgeting & Reporting Readiness": "Finance Manager",
    "Audit & Compliance": "Compliance & Audit Manager",
    "Vendor Onboarding & Contracts": "Procurement Manager",
    "FF&E Procurement": "FF&E Procurement Lead",
    "OS&E (Operating Supplies)": "OS&E Procurement Lead",
    "Brand & Digital Presence": "Digital Marketing Manager",
    "Pre-Opening Sales & Partnerships": "Director of Sales",
    "Launch & PR Readiness": "PR & Communications Manager",
}
tasks_df["Owner"] = tasks_df["Workstream"].map(OWNER_BY_WORKSTREAM)
assert tasks_df["Owner"].isna().sum() == 0, "Some workstream has no Owner mapping!"

# =================================================================
# RULE 3 — Vendor assignment (Internal_Likelihood, not keyword block)
# =================================================================
INTERNAL_LIKELIHOOD = {
    "Network & Infrastructure": 0.30, "Systems Integration (PMS/POS)": 0.25,
    "Security & End-User Support": 0.55, "MEP Systems": 0.15,
    "Life Safety Systems": 0.20, "Building Commissioning": 0.70,
    "Recruitment & Staffing": 0.60, "Onboarding & Training": 0.55,
    "Employee Welfare & Compliance": 0.85, "Room Readiness": 0.80,
    "Linen & Laundry Operations": 0.35, "SOPs & Equipment": 0.65,
    "Guest Systems & Reservations": 0.55, "SOPs & Training": 0.85,
    "Guest Experience Readiness": 0.75, "Kitchen Commissioning": 0.35,
    "Outlet Setup & Menu Development": 0.55, "Supplier & Service Readiness": 0.30,
    "Surveillance & Access Control": 0.35, "Emergency & Safety Procedures": 0.80,
    "Staff Training & Licensing": 0.75, "Systems & Controls Setup": 0.70,
    "Budgeting & Reporting Readiness": 0.90, "Audit & Compliance": 0.55,
    "Vendor Onboarding & Contracts": 0.90, "FF&E Procurement": 0.15,
    "OS&E (Operating Supplies)": 0.20, "Brand & Digital Presence": 0.40,
    "Pre-Opening Sales & Partnerships": 0.75, "Launch & PR Readiness": 0.50,
}
DEFAULT_CATEGORY_BY_WORKSTREAM = {
    "Network & Infrastructure": "IT Systems Integration",
    "Systems Integration (PMS/POS)": "IT Systems Integration",
    "Security & End-User Support": "IT Systems Integration",
    "MEP Systems": "MEP Contractor",
    "Life Safety Systems": "Fire & Life Safety",
    "Building Commissioning": "MEP Contractor",
    "Recruitment & Staffing": "Training & Recruitment Agency",
    "Onboarding & Training": "Training & Recruitment Agency",
    "Employee Welfare & Compliance": "Professional Services",
    "Room Readiness": "OS&E Supplier",
    "Linen & Laundry Operations": "Laundry & Linen",
    "SOPs & Equipment": "OS&E Supplier",
    "Guest Systems & Reservations": "IT Systems Integration",
    "SOPs & Training": "Training & Recruitment Agency",
    "Guest Experience Readiness": "Marketing & Digital Agency",
    "Kitchen Commissioning": "Kitchen Equipment",
    "Outlet Setup & Menu Development": "Kitchen Equipment",
    "Supplier & Service Readiness": "F&B Supplier",
    "Surveillance & Access Control": "Security Systems",
    "Emergency & Safety Procedures": "Fire & Life Safety",
    "Staff Training & Licensing": "Training & Recruitment Agency",
    "Systems & Controls Setup": "IT Systems Integration",
    "Budgeting & Reporting Readiness": "Professional Services",
    "Audit & Compliance": "Professional Services",
    "Vendor Onboarding & Contracts": "Professional Services",
    "FF&E Procurement": "FF&E Supplier",
    "OS&E (Operating Supplies)": "OS&E Supplier",
    "Brand & Digital Presence": "Marketing & Digital Agency",
    "Pre-Opening Sales & Partnerships": "Marketing & Digital Agency",
    "Launch & PR Readiness": "PR Agency",
}

# Narrow keyword overrides — ONLY for choosing category, applied to a small,
# specific set of tasks whose true category differs from their workstream default.
def resolve_category(task_name, workstream):
    name_lower = task_name.lower()
    if "elevator" in name_lower:
        return "Vertical Transportation"
    if any(k in name_lower for k in ["sprinkler", "fire ", "fire alarm", "smoke extraction"]):
        return "Fire & Life Safety"
    if "audit" in name_lower or "insurance" in name_lower:
        return "Professional Services"
    return DEFAULT_CATEGORY_BY_WORKSTREAM[workstream]

# Hard exceptions: government/regulatory bodies are not market vendors
HARD_NULL_TASKS = {
    "Civil defense inspection and approval",
    "VAT and tax registration compliance",
}

vendor_pool_by_category = {
    cat: sub["Vendor_ID"].tolist()
    for cat, sub in vendors_df.groupby("Vendor_Category")
}

def assign_vendor(row):
    if row["Task_Name"] in HARD_NULL_TASKS:
        return None
    p_internal = INTERNAL_LIKELIHOOD[row["Workstream"]]
    if np.random.random() < p_internal:
        return None
    category = resolve_category(row["Task_Name"], row["Workstream"])
    pool = vendor_pool_by_category.get(category)
    if not pool:
        return None
    return np.random.choice(pool)

tasks_df["Vendor_ID"] = tasks_df.apply(assign_vendor, axis=1)

# =================================================================
# RULE 4 — Priority (topic-based, not document-type-based)
# =================================================================
LIFE_SAFETY_KEYWORDS = ["fire", "sprinkler", "smoke", "civil defense", "elevator",
                         "life safety", "food safety", "haccp", "licensing", "regulatory",
                         "certification", "certified", "cybersecurity", "anti-money laundering",
                         "labor law", "vat and tax", "insurance", "statutory", "compliance"]
CORE_SYSTEMS_KEYWORDS = ["pms", "pos ", "pos integration", "network", "backbone", "firewall",
                          "door lock", "revenue management", "reservation system",
                          "central reservation", "payment gateway", "kitchen equipment",
                          "hvac", "chiller", "generator", "switchgear", "building management",
                          "access control", "cctv"]
GUEST_CRITICAL_KEYWORDS = ["check-in", "check-out", "key card", "guest journey", "guest arrival",
                            "room readiness sign-off", "guest profile", "wake-up call", "guest privacy"]
ADMIN_KEYWORDS = ["collateral", "roadshow", "trade show", "welcome kit", "community engagement",
                   "loyalty program partnership", "photography", "social media"]

PRIORITY_WEIGHTS = {
    "life_safety":    {"Critical": 0.35, "High": 0.45, "Medium": 0.15, "Low": 0.05},
    "core_systems":   {"Critical": 0.15, "High": 0.50, "Medium": 0.30, "Low": 0.05},
    "guest_critical": {"Critical": 0.10, "High": 0.40, "Medium": 0.40, "Low": 0.10},
    "standard":       {"Critical": 0.03, "High": 0.22, "Medium": 0.50, "Low": 0.25},
    "admin":          {"Critical": 0.02, "High": 0.13, "Medium": 0.35, "Low": 0.50},
}

def classify_topic(task_name):
    n = task_name.lower()
    if any(k in n for k in LIFE_SAFETY_KEYWORDS):
        return "life_safety"
    if any(k in n for k in CORE_SYSTEMS_KEYWORDS):
        return "core_systems"
    if any(k in n for k in GUEST_CRITICAL_KEYWORDS):
        return "guest_critical"
    if any(k in n for k in ADMIN_KEYWORDS):
        return "admin"
    return "standard"

def assign_priority(task_name):
    topic = classify_topic(task_name)
    weights = PRIORITY_WEIGHTS[topic]
    return np.random.choice(list(weights.keys()), p=list(weights.values()))

tasks_df["Priority_Topic"] = tasks_df["Task_Name"].apply(classify_topic)  # kept temporarily for review
tasks_df["Priority"] = tasks_df["Task_Name"].apply(assign_priority)

# =================================================================
# RULE 5 — Critical_Path_Flag (explicit curated whitelist, 5 categories)
# =================================================================
CRITICAL_PATH_WHITELIST = {
    # 1. Network Core
    "Core network design and cabling installation",
    "Backbone switch and router configuration",
    "Network uptime and failover testing",
    # 2. PMS / Core Systems Go-Live
    "PMS installation",
    "PMS interface testing with Front Office",
    "User acceptance testing for core systems",
    "Door lock system integration with PMS",
    "Guest key card operational testing and acceptance",
    "POS system installation for F&B outlets",
    "POS integration with PMS for guest billing",
    # 3. Life Safety Approvals
    "Fire alarm system testing and certification",
    "Civil defense inspection and approval",
    "Elevator load and safety testing",
    "Fire pump system testing",
    "Sprinkler system pressure testing",
    "Smoke extraction system testing",
    "Food safety certification and inspection",
    "F&B licensing and regulatory approvals",
    "Security guard licensing verification",
    # 4. Power / MEP Commissioning
    "Backup generator installation",
    "Generator load testing",
    "Electrical switchgear installation",
    "Building management system integration",
    "HVAC system installation and commissioning",
    # 5. Final Readiness / UAT
    "Final IT systems readiness testing",
    "Front Office end-to-end guest journey test",
    "Housekeeping room readiness trial",
    "F&B full service simulation",
    "Security emergency readiness drill",
    "Engineering final operational readiness inspection",
}
tasks_df["Critical_Path_Flag"] = tasks_df["Task_Name"].isin(CRITICAL_PATH_WHITELIST)

# Consistency rule (one direction only):
#   Critical_Path_Flag = True  =>  Priority must be at least High.
# The reverse is NOT enforced — a task can be High/Critical priority
# without being on the opening-blocking critical path.
PRIORITY_RANK = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
needs_bump = tasks_df["Critical_Path_Flag"] & (tasks_df["Priority"].map(PRIORITY_RANK) < PRIORITY_RANK["High"])
tasks_df.loc[needs_bump, "Priority"] = "High"

# =================================================================
# RULE 6 — Planned_Start_Date / Planned_End_Date
# =================================================================
# (start_week_min, start_week_max) — week 1 = PROJECT_START, week 12 = 1 week before opening
PHASE_WINDOW = {
    "Network & Infrastructure": (1, 3), "Systems Integration (PMS/POS)": (3, 6),
    "Security & End-User Support": (5, 8), "MEP Systems": (1, 3),
    "Life Safety Systems": (2, 5), "Building Commissioning": (7, 10),
    "Recruitment & Staffing": (1, 3), "Onboarding & Training": (5, 9),
    "Employee Welfare & Compliance": (2, 5), "Room Readiness": (8, 11),
    "Linen & Laundry Operations": (4, 7), "SOPs & Equipment": (3, 6),
    "Guest Systems & Reservations": (3, 6), "SOPs & Training": (7, 10),
    "Guest Experience Readiness": (8, 11), "Kitchen Commissioning": (2, 5),
    "Outlet Setup & Menu Development": (4, 7), "Supplier & Service Readiness": (7, 10),
    "Surveillance & Access Control": (3, 6), "Emergency & Safety Procedures": (5, 8),
    "Staff Training & Licensing": (6, 9), "Systems & Controls Setup": (1, 3),
    "Budgeting & Reporting Readiness": (2, 5), "Audit & Compliance": (6, 9),
    "Vendor Onboarding & Contracts": (1, 2), "FF&E Procurement": (1, 4),
    "OS&E (Operating Supplies)": (2, 5), "Brand & Digital Presence": (1, 4),
    "Pre-Opening Sales & Partnerships": (3, 7), "Launch & PR Readiness": (8, 11),
}
FINAL_READINESS_TASKS = {
    "Final IT systems readiness testing", "Front Office end-to-end guest journey test",
    "Housekeeping room readiness trial", "F&B full service simulation",
    "Security emergency readiness drill", "Engineering final operational readiness inspection",
}

def duration_days(task_name):
    n = task_name.lower()
    if any(k in n for k in ["documentation", "manual", "policy", "checklist", "matrix", "chart", "report"]):
        return np.random.randint(3, 8)
    if any(k in n for k in ["training", "program", "simulation", "drill", "trial", "test", "testing"]):
        return np.random.randint(5, 11)
    if any(k in n for k in ["installation", "setup", "procurement", "integration", "commissioning", "deployment"]):
        return np.random.randint(10, 26)
    return np.random.randint(7, 15)

def assign_dates(row):
    if row["Task_Name"] in FINAL_READINESS_TASKS:
        start_week = np.random.randint(10, 12)
    else:
        lo, hi = PHASE_WINDOW[row["Workstream"]]
        start_week = np.random.randint(lo, hi + 1)
    start_date = PROJECT_START + timedelta(weeks=start_week - 1, days=int(np.random.randint(0, 5)))
    dur = duration_days(row["Task_Name"])
    end_date = start_date + timedelta(days=dur)
    # Cap: Opening_Date itself is a milestone, not a task execution day.
    # Every task must finish on or before OPENING_DATE - 1 day.
    max_end_date = OPENING_DATE - timedelta(days=1)
    if end_date > max_end_date:
        end_date = max_end_date - timedelta(days=int(np.random.randint(0, 3)))
        if end_date <= start_date:
            start_date = end_date - timedelta(days=2)
    return pd.Series({"Planned_Start_Date": start_date.date(), "Planned_End_Date": end_date.date()})

tasks_df[["Planned_Start_Date", "Planned_End_Date"]] = tasks_df.apply(assign_dates, axis=1)

# =================================================================
# RULE 7 — Planned_Cost
# =================================================================
COST_RANGE_BY_DEPT = {
    "IT": (15000, 120000), "ENG": (20000, 250000), "HR": (3000, 40000),
    "HK": (3000, 60000), "FO": (3000, 50000), "FB": (10000, 150000),
    "SEC": (5000, 80000), "FIN": (3000, 40000), "PRC": (5000, 100000),
    "SM": (5000, 90000),
}

def assign_cost(row):
    lo, hi = COST_RANGE_BY_DEPT[row["Department_ID"]]
    cost = np.exp(np.random.uniform(np.log(lo), np.log(hi)))
    if pd.notna(row["Vendor_ID"]):
        cost *= np.random.uniform(1.2, 1.6)
    return round(cost / 100) * 100  # round to nearest 100 SAR

tasks_df["Planned_Cost"] = tasks_df.apply(assign_cost, axis=1)

# =================================================================
# Save + Verification
# =================================================================
final_cols = ["Task_ID", "Task_Name", "Department_ID", "Department_Name", "Workstream",
              "Owner", "Vendor_ID", "Priority", "Critical_Path_Flag",
              "Planned_Start_Date", "Planned_End_Date", "Planned_Cost"]
raw_tasks_df = tasks_df[final_cols]
raw_tasks_df.to_csv("raw_tasks.csv", index=False)

print("=== BASIC CHECKS ===")
print(f"Total tasks: {len(raw_tasks_df)}")
print(f"Unique Task_IDs: {raw_tasks_df['Task_ID'].nunique()}")
print()
print("=== Vendor assignment ===")
print(f"Tasks with a Vendor: {raw_tasks_df['Vendor_ID'].notna().sum()} ({raw_tasks_df['Vendor_ID'].notna().mean():.0%})")
print(f"Tasks internal (NULL): {raw_tasks_df['Vendor_ID'].isna().sum()} ({raw_tasks_df['Vendor_ID'].isna().mean():.0%})")
print()
print("=== Priority distribution ===")
print(raw_tasks_df["Priority"].value_counts())
print()
print("=== Priority topic distribution (for review) ===")
print(tasks_df["Priority_Topic"].value_counts())
print()
print("=== Critical Path ===")
print(f"Critical path tasks: {raw_tasks_df['Critical_Path_Flag'].sum()} ({raw_tasks_df['Critical_Path_Flag'].mean():.1%})")
print()
print("=== Priority distribution WITHIN Critical Path tasks ===")
print(raw_tasks_df.loc[raw_tasks_df["Critical_Path_Flag"], "Priority"].value_counts())
print()
cp_low_medium = raw_tasks_df[(raw_tasks_df["Critical_Path_Flag"]) & (raw_tasks_df["Priority"].isin(["Low", "Medium"]))]
print(f"Critical Path tasks with Priority below High (should be 0): {len(cp_low_medium)}")
print()
print("=== Dates sanity ===")
print(f"Min Planned_Start_Date: {raw_tasks_df['Planned_Start_Date'].min()}")
print(f"Max Planned_End_Date: {raw_tasks_df['Planned_End_Date'].max()}  (Opening: {OPENING_DATE.date()})")
print()
print("=== Planned_Cost by department (SAR) ===")
print(raw_tasks_df.groupby("Department_ID")["Planned_Cost"].agg(["mean", "min", "max"]).round(0))
