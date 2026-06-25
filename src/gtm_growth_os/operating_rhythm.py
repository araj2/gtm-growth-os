from __future__ import annotations

import pandas as pd


def build_cco_operating_rhythm() -> pd.DataFrame:
    """Define the operating cadence that keeps GTM leadership aligned.

    This is intentionally process-oriented: it shows the rhythm, owners, required inputs,
    decision rights, and artifacts that make a GTM org scale without every process living
    in tribal knowledge.
    """
    rows = [
        {
            "cadence": "Weekly",
            "meeting": "CCO Forecast Call",
            "primary_owner": "Sales Strategy / Ops DRI",
            "participants": "CCO, regional VPs, RevOps, Finance partner",
            "pre_read_due": "EOD Friday",
            "inputs_required": "Leader forecast submissions, commit/best-case changes, stage movement, close-date pushes, large-deal notes",
            "decision_focus": "Commit integrity, risk triage, pull-in opportunities, executive inspection asks",
            "output_artifact": "Forecast call notes, risk register, action tracker updates",
            "system_path": "Forecast Call Console + Action Tracker",
        },
        {
            "cadence": "Weekly",
            "meeting": "Pipeline Generation Review",
            "primary_owner": "Revenue Strategy + Demand Gen Ops",
            "participants": "Sales, Marketing, BDR leadership, RevOps",
            "pre_read_due": "EOD Monday",
            "inputs_required": "New pipeline, source mix, MQL-SQL-SAO conversion, BDR meetings, territory coverage gaps",
            "decision_focus": "Whether demand gen and outbound are creating enough quality pipeline for future quarters",
            "output_artifact": "Pipeline gap callouts, campaign/BDR actions, territory focus list",
            "system_path": "Demand Gen Engine + BDR Outbound Engine",
        },
        {
            "cadence": "Monthly",
            "meeting": "GTM Operating Review",
            "primary_owner": "CCO Chief of Staff / Sales Strategy",
            "participants": "CCO staff, Finance, Systems, Enablement, People/HR",
            "pre_read_due": "T-3 business days",
            "inputs_required": "Forecast trend, pipeline health, capacity coverage, hiring/ramp status, comp/territory exceptions",
            "decision_focus": "Resource allocation, operating risks, standards adoption, cross-functional blockers",
            "output_artifact": "Decision log, executive readout, systems backlog, escalation list",
            "system_path": "Executive GTM Cockpit + Planning Control Tower",
        },
        {
            "cadence": "Quarterly",
            "meeting": "QBR / Pipeline Council",
            "primary_owner": "Sales Strategy / RevOps",
            "participants": "CCO, sales leaders, strategy, finance, marketing, BDR, systems",
            "pre_read_due": "T-5 business days",
            "inputs_required": "Quarter close bridge, slippage analysis, segment productivity, pipeline source contribution, territory capacity",
            "decision_focus": "Operating model changes required for next quarter",
            "output_artifact": "QBR readout, next-quarter operating plan, revised standards if needed",
            "system_path": "Scenario War Room + Standards Library",
        },
        {
            "cadence": "Annual / In-year replans",
            "meeting": "Annual Planning Control Tower",
            "primary_owner": "Sales Strategy Program DRI",
            "participants": "Sales, Finance, HR, Total Rewards, Systems, Marketing, BDR leadership",
            "pre_read_due": "Published planning calendar",
            "inputs_required": "Company plan, segment targets, hiring budget, quota/comp assumptions, territory rules, systems readiness",
            "decision_focus": "Targets, capacity, territories, quota deployment, compensation readiness, launch calendar",
            "output_artifact": "Signed operating plan, deployment tracker, runbooks, enablement docs",
            "system_path": "Planning Control Tower + GTM Standards Library",
        },
    ]
    return pd.DataFrame(rows)


def build_operating_calendar() -> pd.DataFrame:
    rows = []
    weeks = list(range(1, 14))
    for week in weeks:
        rows.append({
            "quarter_week": f"W{week}",
            "operating_event": "CCO Forecast Call",
            "owner": "Sales Strategy / Ops DRI",
            "input_due": "Friday EOD prior week",
            "decision_due": "Monday forecast call",
            "artifact": "Forecast pre-read + action tracker",
            "status": "On track" if week not in [5, 9] else "Needs input",
            "risk": "VP forecast submission missing" if week == 5 else ("Large-deal slippage requires exec review" if week == 9 else "None"),
        })
        if week in [2, 6, 10, 13]:
            rows.append({
                "quarter_week": f"W{week}",
                "operating_event": "Monthly GTM Operating Review" if week in [6, 10] else "Pipeline Council / QBR prep",
                "owner": "CCO Staff / Revenue Strategy",
                "input_due": "T-3 business days",
                "decision_due": "Review date",
                "artifact": "Operating review pre-read",
                "status": "On track" if week != 10 else "At risk",
                "risk": "Capacity gap in Enterprise requires CFO decision" if week == 10 else "None",
            })
    return pd.DataFrame(rows)


def operating_health_score(
    forecast_console: pd.DataFrame,
    action_tracker: pd.DataFrame,
    planning_control: pd.DataFrame,
) -> dict[str, float]:
    forecast_ready = float((forecast_console["submission_status"] == "Submitted").mean()) if not forecast_console.empty else 0.0
    action_closure = float((action_tracker["status"].isin(["Closed", "On track"])).mean()) if not action_tracker.empty else 0.0
    plan_readiness = float((planning_control["status"].isin(["Complete", "On track"])).mean()) if not planning_control.empty else 0.0
    overdue = int((action_tracker["escalation_flag"] == "Escalate").sum()) if not action_tracker.empty else 0
    score = round((forecast_ready * 0.35 + action_closure * 0.30 + plan_readiness * 0.35) * 100, 1)
    return {
        "operating_health_score": score,
        "forecast_submission_rate": round(forecast_ready, 3),
        "action_closure_rate": round(action_closure, 3),
        "planning_readiness_rate": round(plan_readiness, 3),
        "escalations_open": overdue,
    }
