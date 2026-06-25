from __future__ import annotations

import pandas as pd


def build_action_risk_tracker(forecast_console: pd.DataFrame, cfo_capacity_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for _, r in forecast_console.iterrows():
        segment = str(r["segment"])
        if r["inspection_risk"] in ["High", "Medium"]:
            rows.append({
                "source_meeting": "CCO Forecast Call",
                "action_item": f"Submit {segment} recovery plan with commit path and deal-level exec asks",
                "owner": r["forecast_owner"],
                "function": "Sales",
                "due_date": "This Friday",
                "priority": "P0" if r["inspection_risk"] == "High" else "P1",
                "risk_category": "Forecast risk",
                "status": "At risk" if r["inspection_risk"] == "High" else "On track",
                "days_open": 9 if r["inspection_risk"] == "High" else 3,
                "linked_metric": "forecast_coverage_vs_target",
                "escalation_flag": "Escalate" if r["inspection_risk"] == "High" else "Monitor",
            })
        if float(r["hygiene_score"]) < 78:
            rows.append({
                "source_meeting": "Pipeline Review",
                "action_item": f"Clean {segment} pipeline hygiene: next steps, close dates, stage criteria, economic buyer fields",
                "owner": "RevOps + " + str(r["forecast_owner"]),
                "function": "RevOps",
                "due_date": "Next Wednesday",
                "priority": "P1",
                "risk_category": "Pipeline hygiene",
                "status": "Needs input",
                "days_open": 5,
                "linked_metric": "hygiene_score",
                "escalation_flag": "Monitor",
            })

    capacity_risk = cfo_capacity_df.groupby("segment", as_index=False).agg(
        avg_coverage=("quota_coverage_ratio", "mean"),
        max_gap=("quota_capacity_surplus_gap", "min"),
        req_hc=("required_hc_to_close_gap", "max"),
    )
    for _, r in capacity_risk.iterrows():
        if float(r["avg_coverage"]) < 0.95:
            rows.append({
                "source_meeting": "Monthly GTM Operating Review",
                "action_item": f"Resolve {r['segment']} capacity coverage gap before quota deployment lock",
                "owner": "Finance + Sales Strategy + HRBP",
                "function": "Cross-functional",
                "due_date": "Planning checkpoint",
                "priority": "P0",
                "risk_category": "Capacity / budget risk",
                "status": "At risk",
                "days_open": 12,
                "linked_metric": "quota_coverage_ratio",
                "escalation_flag": "Escalate",
            })
    if not rows:
        rows.append({
            "source_meeting": "CCO Forecast Call",
            "action_item": "Maintain weekly forecast and pipeline hygiene cadence",
            "owner": "Sales Strategy",
            "function": "Sales Strategy",
            "due_date": "Weekly",
            "priority": "P2",
            "risk_category": "Operating discipline",
            "status": "On track",
            "days_open": 1,
            "linked_metric": "operating_health_score",
            "escalation_flag": "None",
        })
    return pd.DataFrame(rows)


def summarize_action_tracker(action_tracker: pd.DataFrame) -> pd.DataFrame:
    if action_tracker.empty:
        return pd.DataFrame()
    return action_tracker.groupby(["function", "status", "priority"], as_index=False).agg(
        actions=("action_item", "count"),
        avg_days_open=("days_open", "mean"),
        escalations=("escalation_flag", lambda x: int((x == "Escalate").sum())),
    )
