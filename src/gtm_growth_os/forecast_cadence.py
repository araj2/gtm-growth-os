from __future__ import annotations

import numpy as np
import pandas as pd

REGION_BY_SEGMENT = {
    "SMB": "North America",
    "Mid-Market": "EMEA",
    "Enterprise": "North America",
    "Strategic": "Global Strategic",
}
LEADER_BY_SEGMENT = {
    "SMB": "VP Commercial Sales",
    "Mid-Market": "VP EMEA Sales",
    "Enterprise": "VP Enterprise Sales",
    "Strategic": "SVP Strategic Accounts",
}


def build_forecast_call_console(
    segment_targets: pd.DataFrame,
    pipeline_waterfall: pd.DataFrame,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    base = segment_targets.groupby("segment", as_index=False).agg(
        target_arr=("new_arr_target", "sum"),
        required_deals=("closed_won_deals_required", "sum"),
        target_acv=("target_acv", "mean"),
    )
    pipe = pipeline_waterfall.groupby("segment", as_index=False).agg(required_pipeline=("pipeline_required", "sum"))
    base = base.merge(pipe, on="segment", how="left")
    coverage_profile = {
        "SMB": 1.08,
        "Mid-Market": 0.96,
        "Enterprise": 0.88,
        "Strategic": 0.74,
    }
    hygiene_profile = {
        "SMB": 86,
        "Mid-Market": 79,
        "Enterprise": 71,
        "Strategic": 67,
    }
    for _, r in base.iterrows():
        segment = str(r["segment"])
        target = float(r["target_arr"])
        required_pipeline = float(r["required_pipeline"])
        coverage = coverage_profile.get(segment, 0.95)
        current_pipeline = required_pipeline * coverage
        commit = target * float(rng.uniform(0.58, 0.78))
        best_case = target * float(rng.uniform(0.18, 0.34))
        upside = target * float(rng.uniform(0.08, 0.22))
        pull_in = target * float(rng.uniform(0.02, 0.08))
        slip = target * float(rng.uniform(0.04, 0.16))
        hygiene = hygiene_profile.get(segment, 75)
        submission_status = "Submitted" if segment != "Strategic" else "Late"
        risk = "High" if coverage < 0.85 or hygiene < 70 else ("Medium" if coverage < 1.0 or hygiene < 78 else "Low")
        rows.append({
            "segment": segment,
            "region": REGION_BY_SEGMENT.get(segment, "Global"),
            "forecast_owner": LEADER_BY_SEGMENT.get(segment, "Sales Leader"),
            "submission_status": submission_status,
            "target_arr": target,
            "required_pipeline": required_pipeline,
            "current_pipeline": current_pipeline,
            "pipeline_coverage": current_pipeline / max(required_pipeline, 1),
            "commit_forecast": commit,
            "best_case_forecast": best_case,
            "upside_forecast": upside,
            "forecast_coverage_vs_target": (commit + best_case * 0.55 + upside * 0.25) / max(target, 1),
            "pipeline_created_this_week": current_pipeline * float(rng.uniform(0.025, 0.055)),
            "pipeline_slipped_this_week": slip,
            "pull_in_opportunity": pull_in,
            "stage_regressions": int(rng.integers(2, 12)),
            "close_date_pushes": int(rng.integers(6, 22)),
            "hygiene_score": hygiene,
            "inspection_risk": risk,
            "leader_note_required": "Yes" if risk in ["High", "Medium"] else "No",
        })
    return pd.DataFrame(rows)


def build_forecast_pre_read(forecast_console: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in forecast_console.iterrows():
        coverage = float(r["pipeline_coverage"])
        forecast_cov = float(r["forecast_coverage_vs_target"])
        risk_drivers = []
        if coverage < 0.90:
            risk_drivers.append("pipeline under-covered")
        if forecast_cov < 0.80:
            risk_drivers.append("forecast below target")
        if float(r["hygiene_score"]) < 75:
            risk_drivers.append("hygiene below standard")
        if int(r["close_date_pushes"]) >= 15:
            risk_drivers.append("close-date churn")
        rows.append({
            "segment": r["segment"],
            "leader": r["forecast_owner"],
            "ask_for_forecast_call": "Explain path to coverage and identify exec actions" if risk_drivers else "Confirm commit movement and pull-in candidates",
            "risk_drivers": ", ".join(risk_drivers) if risk_drivers else "No major risk driver",
            "pre_read_status": "Ready" if r["submission_status"] == "Submitted" else "Blocked: leader input late",
        })
    return pd.DataFrame(rows)


def forecast_call_decision_log(forecast_console: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in forecast_console.iterrows():
        if r["inspection_risk"] == "High":
            decision = "CCO inspection required"
            owner = r["forecast_owner"]
            due = "48 hours"
        elif r["inspection_risk"] == "Medium":
            decision = "Manager recovery plan required"
            owner = r["forecast_owner"]
            due = "Next forecast call"
        else:
            decision = "Maintain cadence"
            owner = "Sales Strategy"
            due = "Weekly"
        rows.append({
            "segment": r["segment"],
            "decision": decision,
            "owner": owner,
            "due": due,
            "success_measure": "Coverage restored above 1.0x and hygiene > 80" if r["inspection_risk"] != "Low" else "No regression",
        })
    return pd.DataFrame(rows)
