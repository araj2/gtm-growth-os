from __future__ import annotations

import pandas as pd


def build_annual_planning_control_tower() -> pd.DataFrame:
    rows = [
        {"workstream": "Finance plan", "dri": "Strategic Finance", "input_required": "Company ARR plan, churn/expansion assumptions", "dependency": "Board-approved target range", "due_week": "W1", "status": "Complete", "risk": "None", "executive_decision_needed": "Target scenario selection"},
        {"workstream": "Segment targets", "dri": "Sales Strategy", "input_required": "Segment mix, ACV, win rate, pipeline coverage", "dependency": "Finance plan", "due_week": "W2", "status": "On track", "risk": "Mix sensitivity", "executive_decision_needed": "Segment growth weighting"},
        {"workstream": "Capacity plan", "dri": "RevOps + HRBP", "input_required": "Current HC, open reqs, ramp curves, attrition", "dependency": "Segment targets", "due_week": "W3", "status": "At risk", "risk": "Enterprise ramp coverage gap", "executive_decision_needed": "Approve incremental AE reqs"},
        {"workstream": "Territory design", "dri": "RevOps", "input_required": "Account universe, ICP tiers, whitespace, account ownership exceptions", "dependency": "Capacity plan", "due_week": "W4", "status": "Needs input", "risk": "Strategic account exception list late", "executive_decision_needed": "Territory balancing principle"},
        {"workstream": "Quota deployment", "dri": "Sales Strategy + Finance", "input_required": "Quota model, buffers, ramp assignments", "dependency": "Capacity + territories", "due_week": "W5", "status": "Blocked", "risk": "Cannot deploy quota until territory lock", "executive_decision_needed": "Coverage buffer"},
        {"workstream": "Comp design", "dri": "Total Rewards + Finance", "input_required": "OTE, accelerators, plan mechanics, eligibility rules", "dependency": "Quota deployment", "due_week": "W6", "status": "On track", "risk": "Accelerator budget sensitivity", "executive_decision_needed": "Plan design approval"},
        {"workstream": "Marketing plan", "dri": "Demand Gen", "input_required": "Inbound pipeline target, channel mix, CPL, conversion rates", "dependency": "Pipeline model", "due_week": "W4", "status": "On track", "risk": "Paid channel CAC pressure", "executive_decision_needed": "Budget allocation"},
        {"workstream": "BDR plan", "dri": "BDR Leadership", "input_required": "Outbound pipeline target, activity capacity, conversion assumptions", "dependency": "Pipeline model + territory design", "due_week": "W4", "status": "On track", "risk": "Meeting conversion sensitivity", "executive_decision_needed": "BDR hiring approval"},
        {"workstream": "Systems readiness", "dri": "Sales Systems", "input_required": "Salesforce fields, stage gates, territory rules, dashboard QA", "dependency": "Standards library", "due_week": "W7", "status": "Needs input", "risk": "Field governance not finalized", "executive_decision_needed": "Data governance owner"},
        {"workstream": "Enablement rollout", "dri": "Revenue Enablement", "input_required": "Runbooks, manager training, rep comms, office hours", "dependency": "Quota, territory, standards finalization", "due_week": "W8", "status": "Not started", "risk": "Compressed rollout window", "executive_decision_needed": "Launch date"},
    ]
    return pd.DataFrame(rows)


def planning_status_summary(control_tower: pd.DataFrame) -> pd.DataFrame:
    return control_tower.groupby("status", as_index=False).agg(
        workstreams=("workstream", "count"),
        executive_decisions=("executive_decision_needed", "count"),
    )
