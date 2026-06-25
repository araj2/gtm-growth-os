from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gtm_growth_os.capacity import quota_capacity_model
from gtm_growth_os.capacity_budget import (
    attainment_distribution_simulation,
    attainment_percentile_table,
    build_capacity_cohorts,
    headcount_budget_recommendations,
    quarterly_cfo_capacity_model,
    time_to_productivity_cohort_analysis,
)
from gtm_growth_os.data import generate_account_universe
from gtm_growth_os.demand_gen import inbound_funnel_requirements
from gtm_growth_os.finance import allocate_new_arr_by_segment, finance_target_plan
from gtm_growth_os.pipeline import pipeline_waterfall
from gtm_growth_os.scenarios import monte_carlo_attainment, scenario_summary
from gtm_growth_os.territories import greedy_balance_territories, territory_summary
from gtm_growth_os.operating_rhythm import build_cco_operating_rhythm, build_operating_calendar, operating_health_score
from gtm_growth_os.forecast_cadence import build_forecast_call_console, build_forecast_pre_read, forecast_call_decision_log
from gtm_growth_os.action_tracker import build_action_risk_tracker, summarize_action_tracker
from gtm_growth_os.standards_library import (
    build_pipeline_stage_standards,
    build_forecast_category_standards,
    build_rules_of_engagement,
    pipeline_hygiene_scorecard,
)
from gtm_growth_os.planning_control_tower import build_annual_planning_control_tower, planning_status_summary
from gtm_growth_os.process_ai import build_operating_assistant_outputs

segments = ["SMB", "Mid-Market", "Enterprise", "Strategic"]
acv = {"SMB": 18000, "Mid-Market": 55000, "Enterprise": 145000, "Strategic": 330000}
mix = {"SMB": 0.18, "Mid-Market": 0.32, "Enterprise": 0.34, "Strategic": 0.16}
win = {"SMB": 0.24, "Mid-Market": 0.22, "Enterprise": 0.19, "Strategic": 0.15}
quota = {"SMB": 650000, "Mid-Market": 950000, "Enterprise": 1450000, "Strategic": 2250000}
aes = {"SMB": 9, "Mid-Market": 8, "Enterprise": 7, "Strategic": 3}
ramp = {"SMB": 0.86, "Mid-Market": 0.82, "Enterprise": 0.76, "Strategic": 0.70}

finance = finance_target_plan(42_000_000, 78_000_000, 0.075, 0.18, [0.18, 0.22, 0.25, 0.35])
targets = allocate_new_arr_by_segment(finance, mix, acv)
pipe = pipeline_waterfall(targets, win)
cap = quota_capacity_model(targets, quota, aes, ramp)
cohorts = build_capacity_cohorts(cap, aes)
cfo_cap = quarterly_cfo_capacity_model(targets, cohorts, quota)
prod = time_to_productivity_cohort_analysis(cohorts, quota)
attainment = attainment_distribution_simulation(cfo_cap, simulations=100)
attainment_pct = attainment_percentile_table(attainment)
budget_recs = headcount_budget_recommendations(cfo_cap, cohorts)
accounts = generate_account_universe(500, seed=3)
territories = greedy_balance_territories(accounts, 6)
terr_summary = territory_summary(territories)
inbound = inbound_funnel_requirements(pipe["pipeline_required"].sum(), 90_000, 0.24, 0.36, 0.56, 0.68, 0.38, 260)
sim = monte_carlo_attainment(targets["new_arr_target"].sum(), pipe["pipeline_required"].sum(), 0.20, 90_000, 0.12, simulations=100)
summary = scenario_summary(sim)

cco_rhythm = build_cco_operating_rhythm()
calendar = build_operating_calendar()
forecast_console = build_forecast_call_console(targets, pipe)
forecast_pre_read = build_forecast_pre_read(forecast_console)
decision_log = forecast_call_decision_log(forecast_console)
actions = build_action_risk_tracker(forecast_console, cfo_cap)
action_summary = summarize_action_tracker(actions)
stages = build_pipeline_stage_standards()
forecast_categories = build_forecast_category_standards()
roe = build_rules_of_engagement()
hygiene = pipeline_hygiene_scorecard(forecast_console)
planning = build_annual_planning_control_tower()
planning_summary = planning_status_summary(planning)
health = operating_health_score(forecast_console, actions, planning)
assistant_outputs = build_operating_assistant_outputs(forecast_console, actions, planning)

assert finance.shape[0] == 4
assert targets["new_arr_target"].sum() > 0
assert pipe["pipeline_required"].sum() > targets["new_arr_target"].sum()
assert cap["productive_capacity"].sum() > 0
assert not cohorts.empty
assert cfo_cap["ramped_quota_capacity"].sum() > 0
assert not prod.empty
assert not attainment_pct.empty
assert not budget_recs.empty
assert len(territories) == 500
assert not terr_summary.empty
assert inbound["required"].sum() > 0
assert 0 <= summary["probability_of_hit"] <= 1
assert len(cco_rhythm) >= 5
assert not calendar.empty
assert not forecast_console.empty
assert not forecast_pre_read.empty
assert not decision_log.empty
assert not actions.empty
assert not action_summary.empty
assert not stages.empty
assert not forecast_categories.empty
assert not roe.empty
assert not hygiene.empty
assert not planning.empty
assert not planning_summary.empty
assert 0 <= health["operating_health_score"] <= 100
assert "forecast_pre_read" in assistant_outputs
assert "Annual Planning Status Update" in assistant_outputs["planning_update"]

print("✅ GTM Growth OS smoke test passed.")
print(f"Finance rows: {len(finance)}")
print(f"Gross new ARR: ${targets['new_arr_target'].sum():,.0f}")
print(f"Pipeline required: ${pipe['pipeline_required'].sum():,.0f}")
print(f"Territories generated: {terr_summary.shape[0]}")
print(f"Probability of hit: {summary['probability_of_hit']:.1%}")
print(f"CFO/CRO capacity rows: {len(cfo_cap)}")
print(f"Capacity cohorts: {len(cohorts)}")
print(f"Operating health: {health['operating_health_score']:.1f}/100")
print(f"Forecast console rows: {len(forecast_console)}")
print(f"Action tracker rows: {len(actions)}")
