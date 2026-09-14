"""
Phase 4 - Step 4a: task_snapshots.csv (Status + Progress_Percentage)
------------------------------------------------------------------------
Builds the weekly fact table skeleton: one row per (Task, Snapshot_Date).
Only Status and Progress_Percentage are generated here — Blocked_Flag,
Delay_Days, Forecast_End_Date, Delay_Reason, Risk_Level, Open_Issues and
Actual_Cost are deliberately deferred to Step 4b/4c per our agreed plan.

Guardrails enforced (per your review):
  1. Progress is monotonic non-decreasing per task across snapshots
     (Cancelled tasks freeze at their last value).
  2. The progress curve is computed from each task's OWN
     Planned_Start_Date / Planned_End_Date, not from a fixed week index.
  3. Cancelled is only ever assigned to non-Critical-Path tasks.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(7)

# ---------------------------------------------------------------
# Load Step 3 output + rebuild the 12 weekly snapshot dates
# ---------------------------------------------------------------
raw_tasks_df = pd.read_csv("raw_tasks.csv", parse_dates=["Planned_Start_Date", "Planned_End_Date"])

OPENING_DATE = datetime(2027, 3, 1)
PRE_OPENING_WEEKS = 12
PROJECT_START = OPENING_DATE - timedelta(weeks=PRE_OPENING_WEEKS)
snapshot_dates = [OPENING_DATE - timedelta(weeks=w) for w in range(PRE_OPENING_WEEKS, 0, -1)]

# ---------------------------------------------------------------
# 1. Assign each task an execution Archetype
#    (weighted by Vendor / Critical Path / Priority — combination, not a single trigger)
# ---------------------------------------------------------------
BASE_WEIGHTS = {"On-Track": 0.60, "Slow-Recovers": 0.15, "Chronically-Delayed": 0.18, "Stalled": 0.07}

def archetype_weights(row):
    w = dict(BASE_WEIGHTS)
    if pd.notna(row["Vendor_ID"]):
        w["On-Track"] *= 0.85
        w["Chronically-Delayed"] *= 1.4
        w["Stalled"] *= 1.3
    if row["Critical_Path_Flag"]:
        w["On-Track"] *= 1.3
        w["Chronically-Delayed"] *= 0.6
    if row["Priority"] == "Low":
        w["Chronically-Delayed"] *= 1.2
    if row["Priority"] in ("High", "Critical"):
        w["On-Track"] *= 1.15
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}

def pick_archetype(row):
    w = archetype_weights(row)
    return np.random.choice(list(w.keys()), p=list(w.values()))

raw_tasks_df["Archetype"] = raw_tasks_df.apply(pick_archetype, axis=1)

# ---------------------------------------------------------------
# 2. Archetype -> pace_factor (stretches/compresses effective duration)
#    and skew (curve shape: >1 = slow start that catches up)
# ---------------------------------------------------------------
def sample_pace_skew(archetype):
    if archetype == "On-Track":
        pace = np.clip(np.random.normal(1.0, 0.08), 0.85, 1.15)
        skew = 1.0
    elif archetype == "Slow-Recovers":
        pace = np.clip(np.random.normal(1.0, 0.05), 0.9, 1.1)
        skew = np.random.uniform(1.5, 2.2)
    elif archetype == "Chronically-Delayed":
        pace = np.random.uniform(0.45, 0.7)
        skew = 1.0
    else:  # Stalled
        pace = np.random.uniform(0.85, 1.0)
        skew = 1.0
    return pace, skew

pace_skew = raw_tasks_df["Archetype"].apply(sample_pace_skew)
raw_tasks_df["_pace"] = pace_skew.apply(lambda x: x[0])
raw_tasks_df["_skew"] = pace_skew.apply(lambda x: x[1])

# Stall window (only meaningful for Stalled archetype)
def sample_stall(row):
    if row["Archetype"] != "Stalled":
        return None, None
    dur = (row["Planned_End_Date"] - row["Planned_Start_Date"]).days
    dur = max(dur, 7)
    stall_start_offset = int(dur * np.random.uniform(0.2, 0.6))
    stall_start = row["Planned_Start_Date"] + timedelta(days=stall_start_offset)
    stall_length = int(np.random.randint(14, 29))  # 2-4 weeks
    return stall_start, stall_length

stall_info = raw_tasks_df.apply(sample_stall, axis=1)
raw_tasks_df["_stall_start"] = stall_info.apply(lambda x: x[0])
raw_tasks_df["_stall_length"] = stall_info.apply(lambda x: x[1])

# ---------------------------------------------------------------
# 3. Cancelled tasks — ONLY from non-Critical-Path tasks, ~1%
# ---------------------------------------------------------------
eligible_for_cancel = raw_tasks_df[~raw_tasks_df["Critical_Path_Flag"]]
n_cancel = max(1, round(len(raw_tasks_df) * 0.01))
cancelled_task_ids = np.random.choice(eligible_for_cancel["Task_ID"], size=n_cancel, replace=False)
cancel_info = {}
for tid in cancelled_task_ids:
    cancel_info[tid] = np.random.randint(3, 10)  # cancel between snapshot index 3-9 (0-based)

# ---------------------------------------------------------------
# 4. Core curve function — smoothstep, driven by REAL dates
# ---------------------------------------------------------------
def smoothstep(t):
    t = np.clip(t, 0, 1)
    return 3 * t**2 - 2 * t**3

def compute_progress(row, snap_date):
    start, end = row["Planned_Start_Date"], row["Planned_End_Date"]
    planned_dur = max((end - start).days, 1)
    effective_dur = planned_dur / row["_pace"]

    # --- Stalled archetype: freeze-then-resume, shifted time ---
    if row["Archetype"] == "Stalled" and row["_stall_start"] is not None:
        stall_start = row["_stall_start"]
        stall_end = stall_start + timedelta(days=row["_stall_length"])
        if snap_date < start:
            return 0.0
        if start <= snap_date < stall_start:
            t_norm = (snap_date - start).days / effective_dur
            return round(smoothstep(t_norm ** row["_skew"]) * 100, 1)
        if stall_start <= snap_date < stall_end:
            t_norm = (stall_start - start).days / effective_dur
            return round(smoothstep(t_norm ** row["_skew"]) * 100, 1)
        # resumed: shift time back by the stall length
        shifted_date = snap_date - timedelta(days=row["_stall_length"])
        t_norm = (shifted_date - start).days / effective_dur
        return round(smoothstep(t_norm ** row["_skew"]) * 100, 1)

    # --- Normal curve (On-Track / Slow-Recovers / Chronically-Delayed) ---
    if snap_date < start:
        return 0.0
    t_norm = (snap_date - start).days / effective_dur
    return round(smoothstep(t_norm ** row["_skew"]) * 100, 1)

def derive_status(row, snap_date, progress):
    if snap_date < row["Planned_Start_Date"]:
        return "Not Started"
    if row["Archetype"] == "Stalled" and row["_stall_start"] is not None:
        stall_end = row["_stall_start"] + timedelta(days=row["_stall_length"])
        if row["_stall_start"] <= snap_date < stall_end:
            return "On Hold"
    if progress >= 100:
        return "Completed"
    return "In Progress"

# ---------------------------------------------------------------
# 5. Build the fact table: cross join tasks x snapshot_dates,
#    then simulate CHRONOLOGICALLY per task so Cancelled freezing works
# ---------------------------------------------------------------
records = []
for _, row in raw_tasks_df.iterrows():
    last_progress = 0.0
    cancelled_from_idx = cancel_info.get(row["Task_ID"])
    for i, snap_date in enumerate(snapshot_dates):
        if cancelled_from_idx is not None and i >= cancelled_from_idx:
            progress = last_progress  # frozen
            status = "Cancelled"
        else:
            progress = compute_progress(row, snap_date)
            progress = max(progress, last_progress)  # hard monotonic guarantee
            status = derive_status(row, snap_date, progress)
            if status == "Completed":
                progress = 100.0
        last_progress = progress
        records.append({
            "Task_ID": row["Task_ID"],
            "Snapshot_Date": snap_date.date(),
            "Status": status,
            "Progress_Percentage": progress,
        })

snapshots_df = pd.DataFrame(records)
snapshots_df.to_csv("task_snapshots_step4a.csv", index=False)

# ---------------------------------------------------------------
# Verification
# ---------------------------------------------------------------
print(f"Total fact rows: {len(snapshots_df)} (expected {len(raw_tasks_df)} x {len(snapshot_dates)} = {len(raw_tasks_df)*len(snapshot_dates)})")
print()
print("=== Archetype distribution ===")
print(raw_tasks_df["Archetype"].value_counts())
print()
print("=== Status distribution at LAST snapshot (week before opening) ===")
last_snap = snapshots_df[snapshots_df["Snapshot_Date"] == snapshot_dates[-1].date()]
print(last_snap["Status"].value_counts())
print(f"% Completed by last snapshot: {(last_snap['Status']=='Completed').mean():.1%}")
print()
print("=== Monotonicity check (should be 0 violations) ===")
def check_monotonic(g):
    non_cancel = g[g["Status"] != "Cancelled"]
    return (non_cancel["Progress_Percentage"].diff().dropna() < -0.01).sum()
violations = snapshots_df.groupby("Task_ID", group_keys=False).apply(check_monotonic).sum()
print(f"Progress decreases across snapshots: {violations}")
print()
print("=== Cancelled tasks check ===")
cancelled_ids = list(cancel_info.keys())
print(f"Cancelled task count: {len(cancelled_ids)}")
cp_check = raw_tasks_df[raw_tasks_df["Task_ID"].isin(cancelled_ids)]["Critical_Path_Flag"]
print(f"Any of them Critical Path? {cp_check.any()} (must be False)")
print(raw_tasks_df[raw_tasks_df["Task_ID"].isin(cancelled_ids)][["Task_ID","Task_Name","Priority"]].to_string(index=False))
