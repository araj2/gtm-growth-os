from __future__ import annotations

import pandas as pd


def build_pipeline_stage_standards() -> pd.DataFrame:
    rows = [
        {"stage": "Stage 1 Prospecting", "entry_criteria": "Target account identified with ICP fit and named persona", "exit_criteria": "Meeting booked or disqualified", "required_fields": "ICP tier, persona, source, next step", "aging_sla_days": 14, "inspection_rule": "No next step = hygiene fail"},
        {"stage": "Stage 2 Qualified", "entry_criteria": "Pain, use case, authority path, and timing validated", "exit_criteria": "Sales accepted opportunity created", "required_fields": "Use case, buying committee, close quarter, source", "aging_sla_days": 21, "inspection_rule": "No quantified pain = push back"},
        {"stage": "Stage 3 Technical Validation", "entry_criteria": "Technical sponsor and success criteria identified", "exit_criteria": "Technical win or mutual action plan", "required_fields": "Technical owner, evaluation plan, success criteria", "aging_sla_days": 35, "inspection_rule": "No mutual action plan = manager review"},
        {"stage": "Stage 4 Proposal", "entry_criteria": "Business case, commercial scope, and stakeholders aligned", "exit_criteria": "Legal/procurement or closed lost", "required_fields": "Proposal amount, close date, EB, competitor, next step", "aging_sla_days": 28, "inspection_rule": "Amount/close date movement requires note"},
        {"stage": "Stage 5 Procurement", "entry_criteria": "Commercial agreement in review", "exit_criteria": "Closed won/lost", "required_fields": "Procurement owner, legal status, signature path", "aging_sla_days": 21, "inspection_rule": "Push > 2 times = CCO inspection"},
        {"stage": "Closed Won", "entry_criteria": "Signed order form / contract", "exit_criteria": "Booked and handed to post-sales", "required_fields": "ARR, term, products, start date, handoff owner", "aging_sla_days": 0, "inspection_rule": "Bookings reconciliation required"},
    ]
    return pd.DataFrame(rows)


def build_forecast_category_standards() -> pd.DataFrame:
    rows = [
        {"forecast_category": "Pipeline", "definition": "Open opportunity with plausible path but not yet manager-validated", "minimum_evidence": "Qualified use case and active next step", "allowed_close_window": "Current or future quarter", "inspection_standard": "Do not count as coverage without hygiene compliance"},
        {"forecast_category": "Upside", "definition": "Real opportunity with timing or stakeholder risk", "minimum_evidence": "Champion, use case, active evaluation, quantified value", "allowed_close_window": "Current quarter possible", "inspection_standard": "Leader must name risk and next action"},
        {"forecast_category": "Best Case", "definition": "Strong path to close if identified risks are removed", "minimum_evidence": "Mutual plan, business case, executive buyer identified", "allowed_close_window": "Current quarter", "inspection_standard": "Risk removal action required"},
        {"forecast_category": "Commit", "definition": "Sales leader accountable for closing in-quarter", "minimum_evidence": "Economic buyer, signature path, confirmed commercial terms", "allowed_close_window": "Current quarter", "inspection_standard": "Any push requires leader note and CCO visibility"},
    ]
    return pd.DataFrame(rows)


def build_rules_of_engagement() -> pd.DataFrame:
    rows = [
        {"standard": "Territory ownership", "rule": "Named account ownership wins over geography unless strategic overlay is documented", "owner": "RevOps", "reinforcement_mechanism": "Weekly exception review"},
        {"standard": "Pipeline source attribution", "rule": "First-touch source and opportunity-source must be locked at SAO creation", "owner": "Marketing Ops", "reinforcement_mechanism": "Monthly source audit"},
        {"standard": "Forecast submissions", "rule": "Regional forecast inputs are due Friday EOD before Monday CCO call", "owner": "Sales Strategy", "reinforcement_mechanism": "Forecast console submission tracker"},
        {"standard": "Close-date movement", "rule": "More than two close-date pushes triggers manager inspection", "owner": "Sales Leadership", "reinforcement_mechanism": "Pipeline hygiene scorecard"},
        {"standard": "Quota deployment", "rule": "Final quotas must reconcile to buffered plan before comp letters go out", "owner": "Finance + Total Rewards", "reinforcement_mechanism": "Planning control tower checkpoint"},
    ]
    return pd.DataFrame(rows)


def pipeline_hygiene_scorecard(forecast_console: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in forecast_console.iterrows():
        hygiene = float(r["hygiene_score"])
        close_pushes = int(r["close_date_pushes"])
        regressions = int(r["stage_regressions"])
        rows.append({
            "segment": r["segment"],
            "hygiene_score": hygiene,
            "missing_next_steps_est": max(0, int((100 - hygiene) * 1.5)),
            "close_date_pushes": close_pushes,
            "stage_regressions": regressions,
            "standard_status": "Pass" if hygiene >= 80 and close_pushes < 15 else ("Watch" if hygiene >= 72 else "Fail"),
            "reinforcement_action": "Manager coaching and pipeline cleanup sprint" if hygiene < 80 else "Maintain weekly inspection",
        })
    return pd.DataFrame(rows)
