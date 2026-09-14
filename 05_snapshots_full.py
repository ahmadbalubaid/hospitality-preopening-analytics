"""
Phase 4 - Step 4b: task_snapshots.csv (remaining 8 columns)
------------------------------------------------------------------------
Builds on Step 4a (Status + Progress_Percentage) and raw_tasks.csv.

Key corrections from your review:
  1. Delay_Days is FORECAST-aware before completion (early warning),
     and ACTUAL-based after completion.
  2. Delay_Reason is chosen ONCE per task (not re-rolled every week).
  3. Actual_End_Date is a precise simulated day within the completion
     week, not just the snapshot date.
  4. Actual_Cost variance is driven by Delay + Blocker, NOT by Vendor
     presence directly (Vendor stays an exposure factor only).
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(11)

raw_tasks_df = pd.read_csv("raw_tasks.csv", parse_dates=["Planned_Start_Date", "Planned_End_Date"])
snapshots_df = pd.read_csv("task_snapshots_step4a.csv", parse_dates=["Snapshot_Date"])

OPENING_DATE = datetime(2027, 3, 1)
PRE_OPENING_WEEKS = 12
snapshot_dates = [OPENING_DATE - timedelta(weeks=w) for w in range(PRE_OPENING_WEEKS, 0, -1)]

# Re-derive the same per-task pace/skew/stall/archetype info from Step 4a logic
# (regenerated with the same seed logic is risky across files, so instead we
# recompute deterministically from raw_tasks + a fresh, but now TASK-LEVEL,
# set of derived attributes needed for Steps 4b: effective_duration, stall info,
# and whether the task experiences delay at all.)
np.random.seed(7)  # match Step 4a's archetype seed context for consistent story

BASE_WEIGHTS = {"On-Track": 0.60, "Slow-Recovers": 0.15, "Chronically-Delayed": 0.18, "Stalled": 0.07}

def archetype_weights(row):
    w = dict(BASE_WEIGHTS)
    if pd.notna(row["Vendor_ID"]):
        w["On-Track"] *= 0.85; w["Chronically-Delayed"] *= 1.4; w["Stalled"] *= 1.3
    if row["Critical_Path_Flag"]:
        w["On-Track"] *= 1.3; w["Chronically-Delayed"] *= 0.6
    if row["Priority"] == "Low":
        w["Chronically-Delayed"] *= 1.2
    if row["Priority"] in ("High", "Critical"):
        w["On-Track"] *= 1.15
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}

raw_tasks_df["Archetype"] = raw_tasks_df.apply(lambda r: np.random.choice(
    list(archetype_weights(r).keys()), p=list(archetype_weights(r).values())), axis=1)

def sample_pace_skew(archetype):
    if archetype == "On-Track":
        return np.clip(np.random.normal(1.0, 0.08), 0.85, 1.15), 1.0
    elif archetype == "Slow-Recovers":
        return np.clip(np.random.normal(1.0, 0.05), 0.9, 1.1), np.random.uniform(1.5, 2.2)
    elif archetype == "Chronically-Delayed":
        return np.random.uniform(0.45, 0.7), 1.0
    else:
        return np.random.uniform(0.85, 1.0), 1.0

pace_skew = raw_tasks_df["Archetype"].apply(sample_pace_skew)
raw_tasks_df["_pace"] = pace_skew.apply(lambda x: x[0])
raw_tasks_df["_skew"] = pace_skew.apply(lambda x: x[1])

def sample_stall(row):
    if row["Archetype"] != "Stalled":
        return None, None
    dur = max((row["Planned_End_Date"] - row["Planned_Start_Date"]).days, 7)
    stall_start = row["Planned_Start_Date"] + timedelta(days=int(dur * np.random.uniform(0.2, 0.6)))
    stall_length = int(np.random.randint(14, 29))
    return stall_start, stall_length

stall_info = raw_tasks_df.apply(sample_stall, axis=1)
raw_tasks_df["_stall_start"] = stall_info.apply(lambda x: x[0])
raw_tasks_df["_stall_length"] = stall_info.apply(lambda x: x[1])

eligible_for_cancel = raw_tasks_df[~raw_tasks_df["Critical_Path_Flag"]]
n_cancel = max(1, round(len(raw_tasks_df) * 0.01))
cancelled_task_ids = set(np.random.choice(eligible_for_cancel["Task_ID"], size=n_cancel, replace=False))

# ---------------------------------------------------------------
# Task-level derived fields: effective_duration, "Has_Delay", Forecast_End_Date (fixed target)
# ---------------------------------------------------------------
raw_tasks_df["_planned_dur"] = (raw_tasks_df["Planned_End_Date"] - raw_tasks_df["Planned_Start_Date"]).dt.days.clip(lower=1)
raw_tasks_df["_effective_dur"] = raw_tasks_df["_planned_dur"] / raw_tasks_df["_pace"]
if_stall = raw_tasks_df["_stall_length"].fillna(0)
raw_tasks_df["_forecast_end_target"] = raw_tasks_df["Planned_Start_Date"] + pd.to_timedelta(
    raw_tasks_df["_effective_dur"] + if_stall, unit="D")
raw_tasks_df["_has_delay"] = raw_tasks_df["_forecast_end_target"] > raw_tasks_df["Planned_End_Date"]

# ---------------------------------------------------------------
# RULE 2 (Delay_Reason) — assigned ONCE per task, only for delayed/stalled tasks
# ---------------------------------------------------------------
def pick_reason_category(row):
    topic_regulatory = any(k in row["Task_Name"].lower() for k in
        ["fire", "civil defense", "licens", "certif", "haccp", "food safety", "regulatory"])
    if row["Archetype"] == "Stalled":
        options = ["Resource Shortage", "Design/Technical Issue"] + (["Vendor Delay"] if pd.notna(row["Vendor_ID"]) else [])
        return np.random.choice(options)
    if pd.notna(row["Vendor_ID"]) and np.random.random() < 0.55:
        return "Vendor Delay"
    if topic_regulatory and np.random.random() < 0.5:
        return "Permit/Regulatory Delay"
    return np.random.choice(["Scope Change", "Resource Shortage", "Design/Technical Issue"])

def assign_primary_reason(row):
    if not row["_has_delay"] and row["Archetype"] != "Stalled":
        return None
    return pick_reason_category(row)

raw_tasks_df["Primary_Delay_Reason"] = raw_tasks_df.apply(assign_primary_reason, axis=1)

# ---------------------------------------------------------------
# RULE 4 — Actual_Cost variance factor (task-level, Delay/Blocker driven, NOT vendor-driven)
# ---------------------------------------------------------------
def variance_factor(row):
    delay_ratio = max(0.0, row["_effective_dur"] / row["_planned_dur"] - 1)
    delay_component = min(0.4, delay_ratio * 0.5)
    blocker_component = 0.15 if row["Archetype"] == "Stalled" else 0.0
    noise = np.random.uniform(-0.05, 0.10)
    return np.clip(1.0 + delay_component + blocker_component + noise, 0.85, 1.8)

raw_tasks_df["_variance_factor"] = raw_tasks_df.apply(variance_factor, axis=1)

# ---------------------------------------------------------------
# RULE 3 — precise Actual_End_Date (once per task, first time Completed appears)
# ---------------------------------------------------------------
actual_end_dates = {}
snap_sorted = snapshots_df.sort_values(["Task_ID", "Snapshot_Date"])
for tid, g in snap_sorted.groupby("Task_ID"):
    g = g.reset_index(drop=True)
    completed_idx = g.index[g["Status"] == "Completed"]
    if len(completed_idx) == 0:
        continue
    first_idx = completed_idx[0]
    upper_bound = g.loc[first_idx, "Snapshot_Date"]
    lower_bound = g.loc[first_idx - 1, "Snapshot_Date"] if first_idx > 0 else (
        raw_tasks_df.loc[raw_tasks_df["Task_ID"] == tid, "Planned_Start_Date"].iloc[0])
    span_days = max((upper_bound - lower_bound).days, 1)
    offset = int(np.random.randint(1, span_days + 1))
    actual_end_dates[tid] = (lower_bound + timedelta(days=offset)).date()

# ---------------------------------------------------------------
# Merge task-level info into snapshots and compute the remaining columns
# ---------------------------------------------------------------
task_info = raw_tasks_df.set_index("Task_ID")[[
    "Planned_End_Date", "Critical_Path_Flag", "Archetype", "Primary_Delay_Reason",
    "Planned_Cost", "_variance_factor", "_forecast_end_target"
]]

df = snapshots_df.merge(task_info, left_on="Task_ID", right_index=True, how="left")
df["Actual_End_Date"] = df["Task_ID"].map(actual_end_dates)
df["Actual_End_Date"] = pd.to_datetime(df["Actual_End_Date"])

# FIX (Bug #1 — temporal leakage): Actual_End_Date must only be visible from the
# snapshot where the task IS Completed onward. Before that, it is unknown/NULL —
# a snapshot taken in the past cannot show a completion date that hadn't happened yet.
df.loc[df["Status"] != "Completed", "Actual_End_Date"] = pd.NaT

# Blocked_Flag
df["Blocked_Flag"] = df["Status"] == "On Hold"

# Forecast_End_Date (per snapshot rule)
def forecast_end(row):
    if row["Status"] == "Not Started":
        return row["Planned_End_Date"]
    if row["Status"] == "Completed":
        return row["Actual_End_Date"]
    return row["_forecast_end_target"]
df["Forecast_End_Date"] = df.apply(forecast_end, axis=1)

# Delay_Days (forecast-aware pre-completion, actual-based post-completion)
def delay_days(row):
    if row["Status"] == "Cancelled":
        return np.nan  # will forward-fill below
    if row["Status"] == "Completed":
        return max(0, (row["Actual_End_Date"] - row["Planned_End_Date"]).days)
    return max(0, (row["Forecast_End_Date"] - row["Planned_End_Date"]).days)
df["Delay_Days"] = df.apply(delay_days, axis=1)
df["Delay_Days"] = df.groupby("Task_ID")["Delay_Days"].ffill()  # freeze at cancel point

# FIX (Bug #3): the theoretical "_has_delay" forecast flag can miss a task whose
# REALIZED Delay_Days ends up > 0 for other reasons (e.g. the precise simulated
# Actual_End_Date lands a day or two past Planned_End_Date even though the
# forecast target didn't predict it). Do a second, empirical pass: any task that
# actually shows delay/block in the data MUST have a reason, no exceptions.
ever_delayed = df.groupby("Task_ID").apply(
    lambda g: bool((g["Delay_Days"] > 0).any() or g["Blocked_Flag"].any()))
task_lookup = raw_tasks_df.set_index("Task_ID")
missing_reason_tasks = [
    tid for tid in ever_delayed[ever_delayed].index
    if pd.isna(task_lookup.loc[tid, "Primary_Delay_Reason"])
]
for tid in missing_reason_tasks:
    row = task_lookup.loc[tid]
    reason = pick_reason_category(row)
    raw_tasks_df.loc[raw_tasks_df["Task_ID"] == tid, "Primary_Delay_Reason"] = reason
    df.loc[df["Task_ID"] == tid, "Primary_Delay_Reason"] = reason

# Delay_Reason — only shown while there IS a delay or a block
df["Delay_Reason"] = np.where(
    (df["Delay_Days"] > 0) | (df["Blocked_Flag"]), df["Primary_Delay_Reason"], None)

# Risk_Level
def risk_level(row):
    if row["Blocked_Flag"] or (row["Delay_Days"] > 14 and row["Critical_Path_Flag"]):
        return "Critical"
    if row["Delay_Days"] > 7 or row["Blocked_Flag"]:
        base = "High"
    elif row["Delay_Days"] > 0:
        base = "Medium"
    else:
        base = "Low"
    if row["Critical_Path_Flag"] and base in ("Medium", "High"):
        order = ["Low", "Medium", "High", "Critical"]
        base = order[min(order.index(base) + 1, 3)]
    return base
df["Risk_Level"] = df.apply(risk_level, axis=1)

# Open_Issues (Poisson, mean scales with Risk_Level)
RISK_ISSUE_MEAN = {"Low": 0.3, "Medium": 1.0, "High": 2.0, "Critical": 3.5}
df["Open_Issues"] = df["Risk_Level"].map(lambda r: np.random.poisson(RISK_ISSUE_MEAN[r]))

# Actual_Cost (cumulative, monotonic by construction since Progress is monotonic)
df["Actual_Cost"] = (df["Planned_Cost"] * (df["Progress_Percentage"] / 100) * df["_variance_factor"]).round(0)

# ---------------------------------------------------------------
# Final assembly + save
# ---------------------------------------------------------------
final_cols = ["Task_ID", "Snapshot_Date", "Status", "Progress_Percentage", "Blocked_Flag",
              "Delay_Days", "Forecast_End_Date", "Delay_Reason", "Risk_Level", "Open_Issues",
              "Actual_End_Date", "Actual_Cost"]
task_snapshots_df = df[final_cols].copy()
task_snapshots_df["Snapshot_Date"] = task_snapshots_df["Snapshot_Date"].dt.date
task_snapshots_df["Forecast_End_Date"] = task_snapshots_df["Forecast_End_Date"].dt.date
task_snapshots_df["Actual_End_Date"] = task_snapshots_df["Actual_End_Date"].dt.date

# ---------------------------------------------------------------
# HARD ASSERTS requested for this review round — must all be 0
# ---------------------------------------------------------------
leakage = ((task_snapshots_df["Status"] != "Completed") & task_snapshots_df["Actual_End_Date"].notna()).sum()
print(f"[ASSERT 1] Actual_End_Date present before Completed: {leakage}")
assert leakage == 0, "Temporal leakage still present!"

cancel_check = task_snapshots_df[task_snapshots_df["Status"] == "Cancelled"]
bad_cancel_progress = 0
for tid, g in cancel_check.groupby("Task_ID"):
    # All Cancelled rows for a task must share the SAME frozen progress value
    if g["Progress_Percentage"].nunique() > 1:
        bad_cancel_progress += 1
print(f"[ASSERT 2] Cancelled tasks with inconsistent frozen progress: {bad_cancel_progress}")
assert bad_cancel_progress == 0, "Cancelled lifecycle bug still present!"

missing_reason = ((( task_snapshots_df["Delay_Days"] > 0) | (task_snapshots_df["Blocked_Flag"])) &
                   task_snapshots_df["Delay_Reason"].isna()).sum()
print(f"[ASSERT 3] Delay/Blocked rows missing Delay_Reason: {missing_reason}")
assert missing_reason == 0, "Delay_Reason gap still present!"

task_snapshots_df.to_csv("task_snapshots.csv", index=False)
print()
print("All three asserts passed — file saved.")
print()

# ---------------------------------------------------------------
# Verification
# ---------------------------------------------------------------
print(f"Total rows: {len(task_snapshots_df)}")
print()
print("=== Delay_Days sanity: any negative? ===")
print((task_snapshots_df["Delay_Days"] < 0).sum(), "(should be 0)")
print()
print("=== Delay_Days monotonic per task (non-decreasing while not Completed/Cancelled)? spot check ===")
print(f"Max Delay_Days observed: {task_snapshots_df['Delay_Days'].max()}")
print()
print("=== Risk_Level distribution ===")
print(task_snapshots_df["Risk_Level"].value_counts())
print()
print("=== Delay_Reason distribution (non-null only) ===")
print(task_snapshots_df["Delay_Reason"].value_counts())
print()
print("=== Actual_Cost sanity: any exceeding 2x Planned_Cost? ===")
merged_check = task_snapshots_df.merge(raw_tasks_df[["Task_ID","Planned_Cost"]], on="Task_ID")
over2x = merged_check[merged_check["Actual_Cost"] > 2*merged_check["Planned_Cost"]]
print(f"Rows exceeding 2x planned cost: {len(over2x)} (should be 0 or very few)")
print()
print("=== Actual_Cost monotonic check (should be 0 violations) ===")
def cost_mono(g):
    return (g["Actual_Cost"].diff().dropna() < -0.01).sum()
cost_violations = task_snapshots_df.groupby("Task_ID", group_keys=False).apply(cost_mono).sum()
print(f"Violations: {cost_violations}")
print()
print("=== Example: a Chronically-Delayed / Vendor task, full trajectory ===")
example_id = raw_tasks_df[(raw_tasks_df["Archetype"]=="Chronically-Delayed") & (raw_tasks_df["Vendor_ID"].notna())]["Task_ID"].iloc[0]
print(f"Task: {example_id}")
print(task_snapshots_df[task_snapshots_df["Task_ID"]==example_id][
    ["Snapshot_Date","Status","Progress_Percentage","Delay_Days","Risk_Level","Delay_Reason"]
].to_string(index=False))
