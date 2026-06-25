from __future__ import annotations

import os
import pandas as pd


def build_operating_assistant_outputs(
    forecast_console: pd.DataFrame,
    action_tracker: pd.DataFrame,
    planning_control_tower: pd.DataFrame,
) -> dict[str, str]:
    """Create Claude-style operating artifacts.

    The function is deterministic by default so the portfolio runs without API keys.
    If an ANTHROPIC_API_KEY is present, this module can be extended to call Claude,
    but the offline artifacts are intentionally useful on their own.
    """
    high_risk = forecast_console[forecast_console["inspection_risk"] == "High"]
    late = forecast_console[forecast_console["submission_status"] != "Submitted"]
    escalations = action_tracker[action_tracker["escalation_flag"] == "Escalate"]
    blocked = planning_control_tower[planning_control_tower["status"].isin(["Blocked", "At risk", "Needs input"])]

    forecast_bullets = []
    for _, r in forecast_console.iterrows():
        forecast_bullets.append(
            f"- {r['segment']}: {r['pipeline_coverage']:.1f}x pipeline coverage, "
            f"{r['forecast_coverage_vs_target']:.0%} weighted forecast coverage, "
            f"risk={r['inspection_risk']}."
        )
    action_bullets = []
    for _, r in escalations.head(6).iterrows():
        action_bullets.append(f"- {r['priority']} | {r['owner']}: {r['action_item']} due {r['due_date']}.")
    planning_bullets = []
    for _, r in blocked.iterrows():
        planning_bullets.append(f"- {r['workstream']} ({r['status']}): {r['risk']}; decision needed: {r['executive_decision_needed']}.")

    forecast_pre_read = "\n".join([
        "### CCO Forecast Call Pre-read",
        "",
        "**Purpose:** Make the Monday call decision-oriented instead of status-oriented.",
        "",
        "**Submission status:** " + ("All leaders submitted." if late.empty else f"Late inputs from: {', '.join(late['forecast_owner'].astype(str).tolist())}."),
        "",
        "**Segment readout:**",
        *forecast_bullets,
        "",
        "**Primary asks:**",
        "- Confirm commit movement by segment.",
        "- Inspect high-risk segments with under-covered pipeline or weak hygiene.",
        "- Assign executive actions for slipped strategic deals and pipeline creation gaps.",
    ])

    risk_memo = "\n".join([
        "### GTM Operating Risk Memo",
        "",
        f"Open escalations: {len(escalations)}",
        f"High-risk forecast segments: {len(high_risk)}",
        f"Planning workstreams needing attention: {len(blocked)}",
        "",
        "**Escalated actions:**",
        *(action_bullets or ["- No P0 escalations currently open."]),
        "",
        "**Planning blockers:**",
        *(planning_bullets or ["- No critical planning blockers."]),
        "",
        "**Recommendation:** Keep the weekly forecast call focused on decision rights, not metric narration. Any segment with <1.0x coverage or <80 hygiene should enter a recovery loop with named owners and due dates.",
    ])

    planning_update = "\n".join([
        "### Annual Planning Status Update",
        "",
        "**Operating principle:** Quota deployment should not occur until targets, capacity, territories, and comp mechanics reconcile to the buffered plan.",
        "",
        "**Workstreams requiring leadership attention:**",
        *(planning_bullets or ["- All workstreams are on track."]),
        "",
        "**Next cross-functional checkpoint agenda:**",
        "1. Confirm target scenario and segment mix.",
        "2. Resolve capacity gaps and hiring decisions.",
        "3. Lock territory design principles and exception process.",
        "4. Validate quota-to-plan reconciliation before comp letters.",
        "5. Confirm systems readiness for stage standards and forecast categories.",
    ])

    api_mode = "Claude API key detected" if os.getenv("ANTHROPIC_API_KEY") else "Offline deterministic mode"
    return {
        "mode": api_mode,
        "forecast_pre_read": forecast_pre_read,
        "risk_memo": risk_memo,
        "planning_update": planning_update,
    }
