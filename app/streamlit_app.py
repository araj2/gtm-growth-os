from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from gtm_growth_os.capacity import quarterly_capacity_phasing, quota_capacity_model
from gtm_growth_os.capacity_budget import (
    attainment_distribution_simulation,
    attainment_percentile_table,
    build_capacity_cohorts,
    headcount_budget_recommendations,
    quarterly_cfo_capacity_model,
    time_to_productivity_cohort_analysis,
)
from gtm_growth_os.compensation import comp_curve, segment_comp_summary
from gtm_growth_os.data import generate_account_universe
from gtm_growth_os.demand_gen import bdr_outbound_requirements, channel_mix_model, inbound_funnel_requirements
from gtm_growth_os.exports import make_excel_workbook
from gtm_growth_os.finance import allocate_new_arr_by_segment, board_metrics, finance_target_plan
from gtm_growth_os.pipeline import pipeline_requirements, pipeline_waterfall
from gtm_growth_os.scenarios import executive_narrative, monte_carlo_attainment, scenario_summary
from gtm_growth_os.sql import duckdb_market_query
from gtm_growth_os.territories import greedy_balance_territories, territory_summary
from gtm_growth_os.operating_rhythm import build_cco_operating_rhythm, build_operating_calendar, operating_health_score
from gtm_growth_os.forecast_cadence import build_forecast_call_console, build_forecast_pre_read, forecast_call_decision_log
from gtm_growth_os.action_tracker import build_action_risk_tracker, summarize_action_tracker
from gtm_growth_os.standards_library import build_pipeline_stage_standards, build_forecast_category_standards, build_rules_of_engagement, pipeline_hygiene_scorecard
from gtm_growth_os.planning_control_tower import build_annual_planning_control_tower, planning_status_summary
from gtm_growth_os.process_ai import build_operating_assistant_outputs

st.set_page_config(page_title="GTM Growth OS", page_icon="🚀", layout="wide")

SEGMENTS = ["SMB", "Mid-Market", "Enterprise", "Strategic"]
DEFAULT_ACV = {"SMB": 18_000, "Mid-Market": 55_000, "Enterprise": 145_000, "Strategic": 330_000}
DEFAULT_MIX = {"SMB": 0.18, "Mid-Market": 0.32, "Enterprise": 0.34, "Strategic": 0.16}
DEFAULT_WIN = {"SMB": 0.24, "Mid-Market": 0.22, "Enterprise": 0.19, "Strategic": 0.15}
DEFAULT_COVERAGE = {"SMB": 3.0, "Mid-Market": 3.4, "Enterprise": 4.0, "Strategic": 4.8}
DEFAULT_QUOTA = {"SMB": 650_000, "Mid-Market": 950_000, "Enterprise": 1_450_000, "Strategic": 2_250_000}
DEFAULT_AES = {"SMB": 9, "Mid-Market": 8, "Enterprise": 7, "Strategic": 3}
DEFAULT_RAMP = {"SMB": 0.86, "Mid-Market": 0.82, "Enterprise": 0.76, "Strategic": 0.70}
DEFAULT_OTE = {"SMB": 120_000, "Mid-Market": 160_000, "Enterprise": 220_000, "Strategic": 300_000}


def money(x: float) -> str:
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:,.1f}M"
    if abs(x) >= 1_000:
        return f"${x/1_000:,.0f}K"
    return f"${x:,.0f}"


def pct(x: float) -> str:
    return f"{x:.1%}"


def format_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy()


st.title("🚀 GTM Growth OS")
st.caption("A board-to-rep GTM operating system: annual planning model + CCO operating rhythm + forecast cadence + execution accountability.")

with st.sidebar:
    st.header("Operating Plan")
    start_arr = st.number_input("Starting ARR", min_value=1_000_000, max_value=500_000_000, value=42_000_000, step=1_000_000, format="%d")
    target_exit_arr = st.number_input("Exit ARR target", min_value=2_000_000, max_value=900_000_000, value=78_000_000, step=1_000_000, format="%d")
    gross_churn = st.slider("Annual gross churn", 0.00, 0.25, 0.075, 0.005)
    expansion = st.slider("Annual expansion / upsell", 0.00, 0.60, 0.18, 0.01)
    st.divider()
    st.subheader("Quarter seasonality")
    q1 = st.slider("Q1", 0.05, 0.50, 0.18, 0.01)
    q2 = st.slider("Q2", 0.05, 0.50, 0.22, 0.01)
    q3 = st.slider("Q3", 0.05, 0.50, 0.25, 0.01)
    q4 = st.slider("Q4", 0.05, 0.60, 0.35, 0.01)
    st.divider()
    st.subheader("Risk simulator")
    committed_pipeline_multiplier = st.slider("Committed pipeline vs required", 0.50, 1.80, 1.00, 0.05)
    avg_cycle_slip = st.slider("Avg cycle slip", 0.00, 0.45, 0.12, 0.01)

segment_input = pd.DataFrame(
    {
        "segment": SEGMENTS,
        "arr_mix": [DEFAULT_MIX[s] for s in SEGMENTS],
        "acv": [DEFAULT_ACV[s] for s in SEGMENTS],
        "win_rate": [DEFAULT_WIN[s] for s in SEGMENTS],
        "coverage_ratio": [DEFAULT_COVERAGE[s] for s in SEGMENTS],
        "quota_per_ae": [DEFAULT_QUOTA[s] for s in SEGMENTS],
        "current_aes": [DEFAULT_AES[s] for s in SEGMENTS],
        "ramp_productivity": [DEFAULT_RAMP[s] for s in SEGMENTS],
        "ote": [DEFAULT_OTE[s] for s in SEGMENTS],
    }
)

st.markdown("### Segment strategy assumptions")
segment_editor = st.data_editor(
    segment_input,
    use_container_width=True,
    hide_index=True,
    column_config={
        "segment": st.column_config.TextColumn(disabled=True),
        "arr_mix": st.column_config.NumberColumn(format="%.2f", min_value=0.0, max_value=1.0, step=0.01),
        "acv": st.column_config.NumberColumn(format="$%d", step=5_000),
        "win_rate": st.column_config.NumberColumn(format="%.2f", min_value=0.01, max_value=0.80, step=0.01),
        "coverage_ratio": st.column_config.NumberColumn(format="%.1f", min_value=1.0, max_value=8.0, step=0.1),
        "quota_per_ae": st.column_config.NumberColumn(format="$%d", step=25_000),
        "current_aes": st.column_config.NumberColumn(format="%d", min_value=0, step=1),
        "ramp_productivity": st.column_config.NumberColumn(format="%.2f", min_value=0.1, max_value=1.2, step=0.01),
        "ote": st.column_config.NumberColumn(format="$%d", step=10_000),
    },
)

segment_mix = dict(zip(segment_editor["segment"], segment_editor["arr_mix"]))
acv = dict(zip(segment_editor["segment"], segment_editor["acv"]))
win_rates = dict(zip(segment_editor["segment"], segment_editor["win_rate"]))
coverage = dict(zip(segment_editor["segment"], segment_editor["coverage_ratio"]))
quota = dict(zip(segment_editor["segment"], segment_editor["quota_per_ae"]))
current_aes = dict(zip(segment_editor["segment"], segment_editor["current_aes"].astype(int)))
ramp = dict(zip(segment_editor["segment"], segment_editor["ramp_productivity"]))
ote = dict(zip(segment_editor["segment"], segment_editor["ote"]))

finance_df = finance_target_plan(start_arr, target_exit_arr, gross_churn, expansion, [q1, q2, q3, q4])
segment_targets = allocate_new_arr_by_segment(finance_df, segment_mix, acv)
waterfall = pipeline_waterfall(segment_targets, win_rates)
stage_pipe = pipeline_requirements(segment_targets, win_rates, coverage)
capacity_df = quota_capacity_model(segment_targets, quota, current_aes, ramp)
capacity_phasing = quarterly_capacity_phasing(capacity_df, segment_targets)
capacity_cohorts = build_capacity_cohorts(capacity_df, current_aes)
cfo_capacity_df = quarterly_cfo_capacity_model(segment_targets, capacity_cohorts, quota, ote, plan_buffer=0.10)
cohort_productivity_df = time_to_productivity_cohort_analysis(capacity_cohorts, quota)
attainment_dist_df = attainment_distribution_simulation(cfo_capacity_df, simulations=1200)
attainment_pct_df = attainment_percentile_table(attainment_dist_df)
hc_budget_recs = headcount_budget_recommendations(cfo_capacity_df, capacity_cohorts, ote)
comp_df = segment_comp_summary(quota, ote)
accounts = generate_account_universe(n=2600, seed=7)
market_query = duckdb_market_query(accounts)

# Operating rhythm layer: connects annual planning to weekly execution discipline.
cco_rhythm_df = build_cco_operating_rhythm()
operating_calendar_df = build_operating_calendar()
forecast_console_df = build_forecast_call_console(segment_targets, waterfall)
forecast_pre_read_df = build_forecast_pre_read(forecast_console_df)
forecast_decision_log_df = forecast_call_decision_log(forecast_console_df)
action_tracker_df = build_action_risk_tracker(forecast_console_df, cfo_capacity_df)
action_summary_df = summarize_action_tracker(action_tracker_df)
stage_standards_df = build_pipeline_stage_standards()
forecast_standards_df = build_forecast_category_standards()
roe_df = build_rules_of_engagement()
pipeline_hygiene_df = pipeline_hygiene_scorecard(forecast_console_df)
planning_control_df = build_annual_planning_control_tower()
planning_summary_df = planning_status_summary(planning_control_df)
operating_health = operating_health_score(forecast_console_df, action_tracker_df, planning_control_df)
assistant_outputs = build_operating_assistant_outputs(forecast_console_df, action_tracker_df, planning_control_df)

metrics = board_metrics(finance_df)
total_pipeline_required = float(waterfall["pipeline_required"].sum())
weighted_acv = float(segment_targets["new_arr_target"].sum() / segment_targets["closed_won_deals_required"].sum())
weighted_win = float((segment_targets["new_arr_target"] * segment_targets["segment"].map(win_rates)).sum() / segment_targets["new_arr_target"].sum())
sim = monte_carlo_attainment(
    target_arr=float(segment_targets["new_arr_target"].sum()),
    committed_pipeline=total_pipeline_required * committed_pipeline_multiplier,
    base_win_rate=weighted_win,
    base_acv=weighted_acv,
    base_cycle_slip=avg_cycle_slip,
)
sim_summary = scenario_summary(sim)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Starting ARR", money(metrics["starting_arr"]))
k2.metric("Exit ARR", money(metrics["exit_arr"]), pct(metrics["growth_rate"]))
k3.metric("Gross New ARR Needed", money(metrics["gross_new_arr"]))
k4.metric("Pipeline Required", money(total_pipeline_required))
k5.metric("Plan Hit Probability", pct(sim_summary["probability_of_hit"]))

if sim_summary["probability_of_hit"] < 0.50:
    st.error("This plan is under-covered. You need more pipeline, better conversion, faster ramp, or a lower ARR target.")
elif sim_summary["probability_of_hit"] < 0.70:
    st.warning("This plan is plausible but fragile. Inspect capacity gaps, BDR coverage, and Q4 dependency.")
else:
    st.success("This plan is structurally credible. The model still exposes where execution risk can break it.")

st.info(f"Operating rhythm health: {operating_health['operating_health_score']:.1f}/100 | Forecast submission rate: {operating_health['forecast_submission_rate']:.0%} | Open escalations: {int(operating_health['escalations_open'])}")

tabs = st.tabs([
    "1 Board targets",
    "2 ACV + pipeline",
    "3 Capacity + quota",
    "4 CFO/CRO HC budget",
    "5 Compensation",
    "6 Territories",
    "7 Demand gen + BDR",
    "8 Scenario war room",
    "9 Export + narrative",
    "10 CCO rhythm",
    "11 Forecast console",
    "12 Standards library",
    "13 Action + risk",
    "14 Planning tower",
    "15 Claude assistant",
])

with tabs[0]:
    st.subheader("Finance target bridge")
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.dataframe(
            finance_df.style.format({
                "opening_arr": "${:,.0f}",
                "gross_churn_arr": "${:,.0f}",
                "expansion_arr": "${:,.0f}",
                "gross_new_arr_required": "${:,.0f}",
                "ending_arr": "${:,.0f}",
                "qoq_growth": "{:.1%}",
                "seasonality_weight": "{:.1%}",
            }),
            use_container_width=True,
        )
    with c2:
        fig = go.Figure()
        fig.add_bar(x=finance_df["quarter"], y=finance_df["gross_new_arr_required"], name="Gross new ARR")
        fig.add_bar(x=finance_df["quarter"], y=finance_df["expansion_arr"], name="Expansion")
        fig.add_bar(x=finance_df["quarter"], y=-finance_df["gross_churn_arr"], name="Gross churn")
        fig.update_layout(title="Quarterly ARR bridge components", barmode="relative", yaxis_tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)

    fig2 = px.line(finance_df, x="quarter", y="ending_arr", markers=True, title="Exit ARR trajectory")
    fig2.update_layout(yaxis_tickprefix="$")
    st.plotly_chart(fig2, use_container_width=True)

with tabs[1]:
    st.subheader("ACV model and pipeline math")
    c1, c2 = st.columns(2)
    with c1:
        seg_pivot = segment_targets.groupby("segment", as_index=False).agg(
            new_arr_target=("new_arr_target", "sum"),
            target_acv=("target_acv", "mean"),
            closed_won_deals_required=("closed_won_deals_required", "sum"),
        )
        st.dataframe(seg_pivot.style.format({"new_arr_target": "${:,.0f}", "target_acv": "${:,.0f}", "closed_won_deals_required": "{:,.1f}"}), use_container_width=True)
    with c2:
        fig = px.bar(seg_pivot, x="segment", y="new_arr_target", text_auto=".2s", title="Annual new ARR by segment")
        fig.update_layout(yaxis_tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Pipeline waterfall")
    st.dataframe(waterfall.style.format({
        "new_arr_target": "${:,.0f}", "target_acv": "${:,.0f}", "won_deals_required": "{:,.1f}",
        "opportunities_required": "{:,.1f}", "pipeline_required": "${:,.0f}", "win_rate": "{:.1%}",
    }), use_container_width=True)
    pipe_by_q = waterfall.groupby("quarter", as_index=False)["pipeline_required"].sum()
    fig = px.bar(pipe_by_q, x="quarter", y="pipeline_required", title="Pipeline creation required by quarter", text_auto=".2s")
    fig.update_layout(yaxis_tickprefix="$")
    st.plotly_chart(fig, use_container_width=True)

    stage_view = stage_pipe.groupby(["stage"], as_index=False)["pipeline_required"].sum()
    stage_order = ["Lead", "MQL", "SQL", "SAO", "Proposal", "Commit", "Closed Won"]
    stage_view["stage"] = pd.Categorical(stage_view["stage"], categories=stage_order, ordered=True)
    stage_view = stage_view.sort_values("stage")
    fig = px.funnel(stage_view, x="pipeline_required", y="stage", title="Reverse pipeline requirement by funnel stage")
    st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.subheader("AE capacity, quota coverage, and hiring plan")
    st.dataframe(capacity_df.style.format({
        "annual_new_arr_target": "${:,.0f}", "quota_per_ae": "${:,.0f}", "avg_ramp_productivity": "{:.0%}",
        "productive_capacity": "${:,.0f}", "attainment_required": "{:.0%}", "aes_needed_with_buffer": "{:,.1f}",
        "incremental_hires_needed": "{:,.0f}", "capacity_gap": "${:,.0f}",
    }), use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(capacity_df, x="segment", y=["annual_new_arr_target", "productive_capacity"], barmode="group", title="Target vs productive AE capacity")
        fig.update_layout(yaxis_tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(capacity_df, x="segment", y="incremental_hires_needed", text_auto=True, title="Incremental AE hires needed")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Quarterly capacity pressure")
    fig = px.bar(capacity_phasing, x="quarter", y="capacity_surplus_deficit", color="segment", title="Quarterly capacity surplus / deficit")
    fig.update_layout(yaxis_tickprefix="$")
    st.plotly_chart(fig, use_container_width=True)


with tabs[3]:
    st.subheader("CFO/CRO quarterly capacity planning model")
    st.caption("Maps productive vs. ramping vs. open headcount to quota coverage against the annual plan, then shows attainment curves, time-to-productivity cohorts, and budget decision signals.")

    agg_capacity = cfo_capacity_df.groupby("quarter", as_index=False).agg(
        plan_target_with_buffer=("plan_target_with_buffer", "sum"),
        ramped_quota_capacity=("ramped_quota_capacity", "sum"),
        productive_headcount=("productive_headcount", "sum"),
        ramping_headcount=("ramping_headcount", "sum"),
        open_headcount=("open_headcount", "sum"),
        headcount_cost=("headcount_cost", "sum"),
    )
    agg_capacity["quota_coverage_ratio"] = agg_capacity["ramped_quota_capacity"] / agg_capacity["plan_target_with_buffer"].replace(0, np.nan)

    annual_coverage = float(cfo_capacity_df["ramped_quota_capacity"].sum() / cfo_capacity_df["plan_target_with_buffer"].sum())
    q4_open_hc = float(agg_capacity.loc[agg_capacity["quarter"] == "Q4", "open_headcount"].sum())
    total_planned_hires = int(capacity_cohorts.loc[capacity_cohorts["source"] == "planned_hire", "headcount"].sum())
    annual_hc_budget = float(cfo_capacity_df["headcount_cost"].sum())
    attainment_p50 = float(attainment_dist_df.groupby("simulation", as_index=False)["realized_arr"].sum()["realized_arr"].median() / cfo_capacity_df["plan_target_with_buffer"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Annual quota coverage", pct(annual_coverage))
    c2.metric("Planned new AE hires", f"{total_planned_hires:,}")
    c3.metric("Q4 open req exposure", f"{q4_open_hc:,.0f}")
    c4.metric("P50 attainment vs buffered plan", pct(attainment_p50))

    st.markdown("#### Productive vs ramping vs open headcount")
    hc_long = agg_capacity.melt(
        id_vars="quarter",
        value_vars=["productive_headcount", "ramping_headcount", "open_headcount"],
        var_name="headcount_type",
        value_name="headcount",
    )
    fig = px.bar(hc_long, x="quarter", y="headcount", color="headcount_type", title="Quarterly headcount state: productive, ramping, and open")
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Quota coverage vs plan")
        cover_plot = agg_capacity.melt(
            id_vars="quarter",
            value_vars=["plan_target_with_buffer", "ramped_quota_capacity"],
            var_name="metric",
            value_name="arr",
        )
        fig = px.bar(cover_plot, x="quarter", y="arr", color="metric", barmode="group", title="Buffered target vs ramp-adjusted quota capacity")
        fig.update_layout(yaxis_tickprefix="$", legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Attainment distribution curves")
        attainment_by_q = (
            attainment_dist_df.groupby(["quarter", "simulation"], as_index=False)
            .agg(realized_arr=("realized_arr", "sum"), target_arr=("target_arr", "sum"))
        )
        attainment_by_q["plan_attainment"] = attainment_by_q["realized_arr"] / attainment_by_q["target_arr"].replace(0, np.nan)
        attainment_lines = (
            attainment_by_q.groupby("quarter", as_index=False)
            .agg(
                p10_attainment=("plan_attainment", lambda x: float(np.quantile(x, 0.10))),
                p50_attainment=("plan_attainment", lambda x: float(np.quantile(x, 0.50))),
                p90_attainment=("plan_attainment", lambda x: float(np.quantile(x, 0.90))),
            )
        )
        attainment_long = attainment_lines.melt("quarter", var_name="curve", value_name="attainment")
        fig = px.line(attainment_long, x="quarter", y="attainment", color="curve", markers=True, title="P10 / P50 / P90 quota attainment curve")
        fig.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Segment-level CFO/CRO capacity table")
    st.dataframe(
        cfo_capacity_df.style.format({
            "plan_target_arr": "${:,.0f}",
            "plan_target_with_buffer": "${:,.0f}",
            "active_headcount": "{:,.0f}",
            "productive_headcount": "{:,.0f}",
            "ramping_headcount": "{:,.0f}",
            "open_headcount": "{:,.0f}",
            "full_quota_capacity": "${:,.0f}",
            "ramped_quota_capacity": "${:,.0f}",
            "headcount_cost": "${:,.0f}",
            "avg_productivity_factor": "{:.0%}",
            "quota_coverage_ratio": "{:.0%}",
            "quota_capacity_surplus_gap": "${:,.0f}",
            "required_hc_to_close_gap": "{:,.1f}",
        }),
        use_container_width=True,
    )

    c1, c2 = st.columns([1.15, 1])
    with c1:
        st.markdown("#### Time-to-productivity cohort analysis")
        st.dataframe(
            cohort_productivity_df.style.format({
                "headcount": "{:,.0f}",
                "quarters_to_80pct_productivity": "{:,.0f}",
                "q1_productivity": "{:.0%}",
                "q2_productivity": "{:.0%}",
                "q3_productivity": "{:.0%}",
                "q4_productivity": "{:.0%}",
                "steady_state_quota_capacity": "${:,.0f}",
            }),
            use_container_width=True,
        )
    with c2:
        st.markdown("#### Headcount budget decision memo")
        st.dataframe(
            hc_budget_recs.style.format({
                "annual_target_with_buffer": "${:,.0f}",
                "annual_ramped_capacity": "${:,.0f}",
                "max_open_headcount": "{:,.0f}",
                "avg_quota_coverage": "{:.0%}",
                "annual_headcount_cost": "${:,.0f}",
                "planned_new_hires": "{:,.0f}",
                "annual_capacity_gap": "${:,.0f}",
            }),
            use_container_width=True,
        )

    with st.expander("Show raw cohort ramp math"):
        st.dataframe(capacity_cohorts, use_container_width=True)


with tabs[4]:
    st.subheader("Sales compensation designer")
    selected_segment = st.selectbox("Select segment for payout curve", SEGMENTS, index=2)
    curve = comp_curve(quota[selected_segment], ote[selected_segment])
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.dataframe(comp_df.style.format({
            "quota": "${:,.0f}", "ote": "${:,.0f}", "base": "${:,.0f}", "variable": "${:,.0f}",
            "target_commission_rate": "{:.2%}", "payout_at_120pct": "${:,.0f}", "payout_at_160pct": "${:,.0f}",
        }), use_container_width=True)
    with c2:
        fig = px.line(curve, x="attainment", y="total_pay", markers=True, title=f"{selected_segment} payout curve")
        fig.update_layout(xaxis_tickformat=".0%", yaxis_tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)
    st.caption("This is a marginal accelerator design: reps get paid more aggressively after crossing quota, which motivates overperformance without overpaying low attainment.")

with tabs[5]:
    st.subheader("Sales territory optimizer")
    c1, c2, c3 = st.columns(3)
    region_filter = c1.selectbox("Region", ["All", "North America", "EMEA", "APAC", "LATAM"])
    segment_filter = c2.selectbox("Segment", ["All"] + SEGMENTS)
    rep_count = c3.slider("Reps to assign", 2, 24, 8)
    territories = greedy_balance_territories(accounts, rep_count=rep_count, region=region_filter, segment=segment_filter)
    summary = territory_summary(territories)
    st.dataframe(summary.style.format({
        "whitespace_arr": "${:,.0f}", "weighted_book_value": "${:,.0f}", "avg_fit": "{:.1f}", "avg_intent": "{:.1f}", "balance_index": "{:.2f}x",
    }), use_container_width=True)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        fig = px.bar(summary, x="territory_owner", y="weighted_book_value", title="Balanced book value by rep")
        fig.update_layout(yaxis_tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.scatter(
            territories.sample(min(len(territories), 900), random_state=1),
            x="fit_score",
            y="intent_score",
            size="whitespace_arr",
            color="territory_owner",
            hover_name="account_name",
            title="Account universe: fit vs intent",
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Show top target accounts"):
        st.dataframe(
            territories[["account_name", "region", "country", "segment", "industry", "fit_score", "intent_score", "whitespace_arr", "territory_owner"]]
            .head(100)
            .style.format({"whitespace_arr": "${:,.0f}"}),
            use_container_width=True,
        )

    st.markdown("#### DuckDB market cut")
    st.dataframe(market_query.style.format({"whitespace_arr": "${:,.0f}", "avg_fit": "{:.1f}", "avg_intent": "{:.1f}", "customer_expansion_pool": "${:,.0f}"}), use_container_width=True)

with tabs[6]:
    st.subheader("Marketing demand generation and BDR outbound math")
    c1, c2, c3, c4 = st.columns(4)
    inbound_share = c1.slider("Inbound pipeline share", 0.05, 0.80, 0.38, 0.01)
    outbound_share = c2.slider("BDR outbound pipeline share", 0.05, 0.80, 0.32, 0.01)
    partner_share = max(0.0, 1.0 - inbound_share - outbound_share)
    c3.metric("Partner / AE-sourced remainder", pct(partner_share))
    cpl = c4.number_input("Blended CPL", min_value=10, max_value=5000, value=260, step=10)

    c1, c2, c3, c4 = st.columns(4)
    lead_to_mql = c1.slider("Lead → MQL", 0.01, 0.80, 0.24, 0.01)
    mql_to_sql = c2.slider("MQL → SQL", 0.01, 0.80, 0.36, 0.01)
    sql_to_sao = c3.slider("SQL → SAO", 0.01, 0.90, 0.56, 0.01)
    sao_to_pipeline = c4.slider("SAO → Pipeline opp", 0.01, 0.95, 0.68, 0.01)

    inbound_df = inbound_funnel_requirements(total_pipeline_required, weighted_acv, lead_to_mql, mql_to_sql, sql_to_sao, sao_to_pipeline, inbound_share, cpl)
    st.dataframe(inbound_df.style.format({"required": "{:,.0f}"}), use_container_width=True)

    raw_leads = float(inbound_df.loc[inbound_df["stage"] == "Raw Leads", "required"].iloc[0])
    channel_mix = channel_mix_model(
        raw_leads,
        cpl_by_channel={"Paid Search": 420, "LinkedIn": 720, "Webinars": 180, "Content Syndication": 240, "Events": 1250, "Partners": 360},
        mix={"Paid Search": 0.18, "LinkedIn": 0.20, "Webinars": 0.16, "Content Syndication": 0.18, "Events": 0.14, "Partners": 0.14},
    )
    fig = px.bar(channel_mix, x="channel", y="budget_required", text_auto=".2s", title="Demand gen budget by channel")
    fig.update_layout(yaxis_tickprefix="$")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### BDR outbound engine")
    c1, c2, c3, c4, c5 = st.columns(5)
    bdrs_current = c1.number_input("Current BDRs", 0, 200, 12)
    monthly_activities = c2.number_input("Monthly activities / BDR", 100, 5000, 1100, step=50)
    connect_rate = c3.slider("Connect rate", 0.01, 0.35, 0.11, 0.01)
    meeting_rate = c4.slider("Connect → meeting", 0.01, 0.35, 0.16, 0.01)
    meeting_to_opp = c5.slider("Meeting → opp", 0.01, 0.80, 0.38, 0.01)
    opp_accept = st.slider("AE accepted opp rate", 0.10, 1.00, 0.72, 0.01)
    bdr_df = bdr_outbound_requirements(total_pipeline_required, outbound_share, weighted_acv, bdrs_current, monthly_activities, connect_rate, meeting_rate, meeting_to_opp, opp_accept)
    st.dataframe(bdr_df.style.format({
        "outbound_pipeline_required": "${:,.0f}", "activities_per_bdr_per_quarter": "{:,.0f}", "meetings_per_bdr_per_quarter": "{:,.1f}",
        "accepted_opps_per_bdr_per_quarter": "{:,.1f}", "pipeline_per_bdr_per_quarter": "${:,.0f}", "bdrs_required": "{:,.0f}",
        "incremental_bdrs_needed": "{:,.0f}",
    }), use_container_width=True)

with tabs[7]:
    st.subheader("Scenario war room")
    st.markdown("Run a Monte Carlo simulation across pipeline coverage, ACV variance, win-rate volatility, cycle slip, and sales ramp risk.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Probability of hit", pct(sim_summary["probability_of_hit"]))
    c2.metric("P10 ARR", money(sim_summary["p10_arr"]))
    c3.metric("P50 ARR", money(sim_summary["p50_arr"]))
    c4.metric("P90 ARR", money(sim_summary["p90_arr"]))
    fig = px.histogram(sim, x="realized_arr", nbins=60, title="Distribution of realized gross new ARR")
    fig.add_vline(x=float(segment_targets["new_arr_target"].sum()), line_dash="dash", annotation_text="Target")
    fig.update_layout(xaxis_tickprefix="$")
    st.plotly_chart(fig, use_container_width=True)

    fig = px.scatter(sim.sample(700, random_state=2), x="win_rate", y="realized_arr", color="hit_target", title="Sensitivity: win rate vs realized ARR")
    fig.update_layout(xaxis_tickformat=".0%", yaxis_tickprefix="$")
    st.plotly_chart(fig, use_container_width=True)

with tabs[8]:
    st.subheader("Executive narrative and export pack")
    bdr_gap = 0
    try:
        bdr_gap = float(bdr_df["incremental_bdrs_needed"].iloc[0])
    except Exception:
        pass
    capacity_gap = float(capacity_df["capacity_gap"].clip(lower=0).sum())
    narrative = executive_narrative(metrics, sim_summary["probability_of_hit"], capacity_gap, bdr_gap)
    st.markdown(narrative)

    export_sheets = {
        "finance_targets": finance_df,
        "segment_targets": segment_targets,
        "pipeline_waterfall": waterfall,
        "capacity_model": capacity_df,
        "cfo_cro_capacity_budget": cfo_capacity_df,
        "capacity_cohorts": capacity_cohorts,
        "time_to_productivity": cohort_productivity_df,
        "attainment_percentiles": attainment_pct_df,
        "hc_budget_recommendations": hc_budget_recs,
        "compensation": comp_df,
        "territory_summary": summary if "summary" in locals() else pd.DataFrame(),
        "demand_gen_channels": channel_mix if "channel_mix" in locals() else pd.DataFrame(),
        "scenario_simulation": sim.head(500),
        "cco_operating_rhythm": cco_rhythm_df,
        "operating_calendar": operating_calendar_df,
        "forecast_console": forecast_console_df,
        "forecast_pre_read": forecast_pre_read_df,
        "forecast_decision_log": forecast_decision_log_df,
        "action_tracker": action_tracker_df,
        "pipeline_hygiene": pipeline_hygiene_df,
        "stage_standards": stage_standards_df,
        "forecast_standards": forecast_standards_df,
        "rules_of_engagement": roe_df,
        "planning_control_tower": planning_control_df,
    }
    st.download_button(
        label="Download GTM operating plan Excel pack",
        data=make_excel_workbook(export_sheets),
        file_name="gtm_growth_os_operating_plan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.download_button(
        label="Download executive narrative Markdown",
        data=narrative.encode("utf-8"),
        file_name="gtm_growth_os_executive_narrative.md",
        mime="text/markdown",
    )



with tabs[9]:
    st.subheader("CCO operating rhythm")
    st.markdown("This layer turns the planning model into a weekly/monthly/quarterly operating cadence: who owes what, when inputs are due, what decisions leaders make, and which artifacts come out of each review.")
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Operating health", f"{operating_health['operating_health_score']:.1f}/100")
    h2.metric("Forecast submission", pct(operating_health["forecast_submission_rate"]))
    h3.metric("Planning readiness", pct(operating_health["planning_readiness_rate"]))
    h4.metric("Open escalations", int(operating_health["escalations_open"]))

    st.markdown("#### Cadence map")
    st.dataframe(cco_rhythm_df, use_container_width=True, hide_index=True)

    st.markdown("#### Quarter operating calendar")
    st.dataframe(operating_calendar_df, use_container_width=True, hide_index=True)

    fig = px.bar(
        operating_calendar_df.groupby(["quarter_week", "status"], as_index=False).size(),
        x="quarter_week",
        y="size",
        color="status",
        title="Operating calendar load and status by week",
    )
    st.plotly_chart(fig, use_container_width=True)

with tabs[10]:
    st.subheader("Forecast call console")
    st.markdown("A Monday-morning console for the CCO: forecast submissions, commit/best-case coverage, pipeline movement, hygiene, close-date churn, and the inspection asks leaders should focus on.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Submitted leaders", f"{int((forecast_console_df['submission_status'] == 'Submitted').sum())}/{len(forecast_console_df)}")
    c2.metric("Avg pipeline coverage", f"{forecast_console_df['pipeline_coverage'].mean():.2f}x")
    c3.metric("Avg forecast coverage", pct(forecast_console_df["forecast_coverage_vs_target"].mean()))
    c4.metric("High-risk segments", int((forecast_console_df["inspection_risk"] == "High").sum()))

    st.dataframe(
        forecast_console_df.style.format({
            "target_arr": "${:,.0f}",
            "required_pipeline": "${:,.0f}",
            "current_pipeline": "${:,.0f}",
            "pipeline_coverage": "{:.2f}x",
            "commit_forecast": "${:,.0f}",
            "best_case_forecast": "${:,.0f}",
            "upside_forecast": "${:,.0f}",
            "forecast_coverage_vs_target": "{:.0%}",
            "pipeline_created_this_week": "${:,.0f}",
            "pipeline_slipped_this_week": "${:,.0f}",
            "pull_in_opportunity": "${:,.0f}",
            "hygiene_score": "{:.0f}",
        }),
        use_container_width=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(forecast_console_df, x="segment", y="pipeline_coverage", color="inspection_risk", title="Pipeline coverage by segment")
        fig.add_hline(y=1.0, line_dash="dash", annotation_text="Required coverage")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(forecast_console_df, x="segment", y="forecast_coverage_vs_target", color="inspection_risk", title="Weighted forecast coverage vs target")
        fig.update_layout(yaxis_tickformat=".0%")
        fig.add_hline(y=0.90, line_dash="dash", annotation_text="Exec inspection threshold")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Forecast pre-read asks")
    st.dataframe(forecast_pre_read_df, use_container_width=True, hide_index=True)

    st.markdown("#### Decision log")
    st.dataframe(forecast_decision_log_df, use_container_width=True, hide_index=True)

with tabs[11]:
    st.subheader("GTM standards library")
    st.markdown("This is the tribal-knowledge-to-operating-system layer: common stage criteria, forecast category definitions, hygiene rules, and rules of engagement across Sales and Strategy.")

    st.markdown("#### Pipeline hygiene scorecard")
    st.dataframe(pipeline_hygiene_df, use_container_width=True, hide_index=True)
    fig = px.bar(pipeline_hygiene_df, x="segment", y="hygiene_score", color="standard_status", title="Pipeline hygiene by segment")
    fig.add_hline(y=80, line_dash="dash", annotation_text="Standard")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Stage standards")
    st.dataframe(stage_standards_df, use_container_width=True, hide_index=True)

    st.markdown("#### Forecast category standards")
    st.dataframe(forecast_standards_df, use_container_width=True, hide_index=True)

    st.markdown("#### Rules of engagement")
    st.dataframe(roe_df, use_container_width=True, hide_index=True)

with tabs[12]:
    st.subheader("Action + risk tracker")
    st.markdown("A cross-functional accountability layer for commitments coming out of forecast calls, pipeline reviews, and operating reviews.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open actions", len(action_tracker_df))
    c2.metric("P0 actions", int((action_tracker_df["priority"] == "P0").sum()))
    c3.metric("Escalations", int((action_tracker_df["escalation_flag"] == "Escalate").sum()))
    c4.metric("Avg days open", f"{action_tracker_df['days_open'].mean():.1f}")

    st.dataframe(action_tracker_df, use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(action_summary_df, x="function", y="actions", color="status", title="Actions by function and status")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(action_tracker_df, x="risk_category", y="days_open", color="priority", title="Risk aging by category")
        st.plotly_chart(fig, use_container_width=True)

with tabs[13]:
    st.subheader("Annual planning control tower")
    st.markdown("The program-management backbone for in-year and annual planning: timelines, DRIs, inputs, dependencies, blockers, and executive decisions required before quota/territory/comp deployment.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Workstreams", len(planning_control_df))
    c2.metric("Blocked / at risk", int(planning_control_df["status"].isin(["Blocked", "At risk"]).sum()))
    c3.metric("Needs input", int((planning_control_df["status"] == "Needs input").sum()))
    c4.metric("Executive decisions", len(planning_control_df))

    st.dataframe(planning_control_df, use_container_width=True, hide_index=True)
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.dataframe(planning_summary_df, use_container_width=True, hide_index=True)
    with c2:
        fig = px.bar(planning_control_df, x="due_week", color="status", title="Planning workstream status by due week")
        st.plotly_chart(fig, use_container_width=True)

with tabs[14]:
    st.subheader("Claude operating assistant")
    st.markdown("Offline deterministic mode produces Claude-style operating artifacts without API keys. If you later wire in the Anthropic API, this becomes a live operating assistant for pre-reads, risk memos, and planning updates.")
    st.info(f"Assistant mode: {assistant_outputs['mode']}")

    doc_type = st.radio(
        "Artifact to generate",
        ["Forecast call pre-read", "GTM operating risk memo", "Annual planning status update"],
        horizontal=True,
    )
    if doc_type == "Forecast call pre-read":
        st.markdown(assistant_outputs["forecast_pre_read"])
        download_name = "forecast_call_pre_read.md"
        download_payload = assistant_outputs["forecast_pre_read"]
    elif doc_type == "GTM operating risk memo":
        st.markdown(assistant_outputs["risk_memo"])
        download_name = "gtm_operating_risk_memo.md"
        download_payload = assistant_outputs["risk_memo"]
    else:
        st.markdown(assistant_outputs["planning_update"])
        download_name = "annual_planning_status_update.md"
        download_payload = assistant_outputs["planning_update"]

    st.download_button(
        label="Download generated operating artifact",
        data=download_payload.encode("utf-8"),
        file_name=download_name,
        mime="text/markdown",
    )

st.caption("Built as a portfolio project to demonstrate strategic finance, GTM operations, RevOps analytics, territory design, demand generation modeling, and sales planning, and CCO operating cadence in one system.")
