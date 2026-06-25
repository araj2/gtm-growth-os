from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

QUARTERS = ["Q1", "Q2", "Q3", "Q4"]


DEFAULT_RAMP_CURVES: dict[str, list[float]] = {
    "SMB": [0.45, 0.75, 1.00, 1.00, 1.00],
    "Mid-Market": [0.35, 0.65, 0.90, 1.00, 1.00],
    "Enterprise": [0.30, 0.55, 0.80, 1.00, 1.00],
    "Strategic": [0.25, 0.45, 0.70, 0.90, 1.00],
}


@dataclass(frozen=True)
class CohortSpec:
    segment: str
    cohort: str
    hire_quarter: str
    start_quarter_index: int
    headcount: int
    source: str


def _quota_lookup(quota_by_segment: dict[str, float], segment: str) -> float:
    try:
        return float(quota_by_segment[segment])
    except KeyError as exc:
        raise KeyError(f"Missing quota assumption for segment: {segment}") from exc


def _ote_lookup(ote_by_segment: dict[str, float] | None, segment: str) -> float:
    if ote_by_segment is None:
        return 180_000.0
    return float(ote_by_segment.get(segment, 180_000.0))


def _ramp_curve(segment: str, custom_curves: dict[str, list[float]] | None = None) -> list[float]:
    curves = custom_curves or DEFAULT_RAMP_CURVES
    return curves.get(segment, [0.30, 0.60, 0.85, 1.00, 1.00])


def ramp_factor(segment: str, tenure_quarters: int, custom_curves: dict[str, list[float]] | None = None) -> float:
    if tenure_quarters < 0:
        return 0.0
    curve = _ramp_curve(segment, custom_curves)
    if tenure_quarters >= len(curve):
        return float(curve[-1])
    return float(curve[tenure_quarters])


def _allocate_integer_hires(total_hires: int, weights: list[float]) -> list[int]:
    if total_hires <= 0:
        return [0 for _ in weights]
    raw = np.array(weights, dtype=float) / max(sum(weights), 1e-9) * total_hires
    base = np.floor(raw).astype(int)
    remainder = int(total_hires - base.sum())
    if remainder > 0:
        order = np.argsort(raw - base)[::-1]
        for i in order[:remainder]:
            base[i] += 1
    return base.tolist()


def build_capacity_cohorts(
    capacity_df: pd.DataFrame,
    current_aes: dict[str, int],
    productive_share_of_current: float = 0.72,
    hiring_distribution: list[float] | None = None,
) -> pd.DataFrame:
    """Create the headcount cohorts used by CFO/CRO capacity planning.

    The model separates current productive reps, current ramping reps, and planned/open reqs.
    Planned reqs are allocated across quarters so the budget model can show timing risk.
    """
    hiring_distribution = hiring_distribution or [0.40, 0.30, 0.20, 0.10]
    specs: list[CohortSpec] = []
    for _, row in capacity_df.iterrows():
        segment = str(row["segment"])
        current = int(current_aes.get(segment, int(row.get("current_aes", 0))))
        current_productive = int(math.floor(current * productive_share_of_current))
        current_ramping = max(0, current - current_productive)
        incremental_hires = int(max(0, math.ceil(float(row.get("incremental_hires_needed", 0)))))

        if current_productive > 0:
            specs.append(CohortSpec(segment, "Incumbent productive", "Pre-plan", -4, current_productive, "current_productive"))
        if current_ramping > 0:
            specs.append(CohortSpec(segment, "Incumbent ramping", "Pre-plan", -1, current_ramping, "current_ramping"))

        hires_by_quarter = _allocate_integer_hires(incremental_hires, hiring_distribution)
        for q_idx, hires in enumerate(hires_by_quarter):
            if hires > 0:
                specs.append(CohortSpec(segment, f"FY plan hires {QUARTERS[q_idx]}", QUARTERS[q_idx], q_idx, hires, "planned_hire"))

    return pd.DataFrame([s.__dict__ for s in specs])


def expand_cohort_productivity(
    cohorts: pd.DataFrame,
    quota_by_segment: dict[str, float],
    ote_by_segment: dict[str, float] | None = None,
    custom_ramp_curves: dict[str, list[float]] | None = None,
    quarter_labels: list[str] | None = None,
) -> pd.DataFrame:
    rows: list[dict] = []
    labels = quarter_labels or QUARTERS
    for _, c in cohorts.iterrows():
        segment = str(c["segment"])
        start_idx = int(c["start_quarter_index"])
        headcount = int(c["headcount"])
        quota = _quota_lookup(quota_by_segment, segment)
        ote = _ote_lookup(ote_by_segment, segment)
        for q_idx, quarter in enumerate(labels):
            tenure = q_idx - start_idx
            is_active = tenure >= 0
            factor = ramp_factor(segment, tenure, custom_ramp_curves) if is_active else 0.0
            if not is_active:
                status = "Open"
            elif factor >= 0.95:
                status = "Productive"
            else:
                status = "Ramping"
            rows.append(
                {
                    "quarter": quarter,
                    "quarter_index": q_idx,
                    "segment": segment,
                    "cohort": str(c["cohort"]),
                    "hire_quarter": str(c["hire_quarter"]),
                    "source": str(c["source"]),
                    "status": status,
                    "tenure_quarters": tenure if is_active else np.nan,
                    "headcount": headcount,
                    "productivity_factor": factor,
                    "quota_per_rep": quota,
                    "full_quota_capacity": headcount * quota if is_active else 0.0,
                    "ramped_quota_capacity": headcount * quota * factor,
                    "ote_cost": headcount * ote if is_active else 0.0,
                    "ramped_cost_efficiency": (headcount * quota * factor) / max(headcount * ote, 1) if is_active else 0.0,
                }
            )
    return pd.DataFrame(rows)


def quarterly_cfo_capacity_model(
    segment_targets: pd.DataFrame,
    cohorts: pd.DataFrame,
    quota_by_segment: dict[str, float],
    ote_by_segment: dict[str, float] | None = None,
    plan_buffer: float = 0.10,
    custom_ramp_curves: dict[str, list[float]] | None = None,
) -> pd.DataFrame:
    quarter_labels = list(pd.Series(segment_targets["quarter"]).drop_duplicates())
    expanded = expand_cohort_productivity(cohorts, quota_by_segment, ote_by_segment, custom_ramp_curves, quarter_labels=quarter_labels)
    targets = (
        segment_targets.groupby(["quarter", "segment"], as_index=False)["new_arr_target"]
        .sum()
        .rename(columns={"new_arr_target": "plan_target_arr"})
    )

    active = expanded[expanded["status"].isin(["Productive", "Ramping"])]
    status_hc = (
        expanded.pivot_table(index=["quarter", "segment"], columns="status", values="headcount", aggfunc="sum", fill_value=0)
        .reset_index()
        .rename_axis(None, axis=1)
    )
    for col in ["Productive", "Ramping", "Open"]:
        if col not in status_hc.columns:
            status_hc[col] = 0

    agg = (
        active.groupby(["quarter", "segment"], as_index=False)
        .agg(
            active_headcount=("headcount", "sum"),
            full_quota_capacity=("full_quota_capacity", "sum"),
            ramped_quota_capacity=("ramped_quota_capacity", "sum"),
            headcount_cost=("ote_cost", "sum"),
            avg_productivity_factor=("productivity_factor", "mean"),
        )
    )

    out = targets.merge(agg, on=["quarter", "segment"], how="left").merge(status_hc, on=["quarter", "segment"], how="left")
    numeric_cols = ["active_headcount", "full_quota_capacity", "ramped_quota_capacity", "headcount_cost", "Productive", "Ramping", "Open"]
    out[numeric_cols] = out[numeric_cols].fillna(0)
    out["avg_productivity_factor"] = out["avg_productivity_factor"].fillna(0)
    out = out.rename(columns={"Productive": "productive_headcount", "Ramping": "ramping_headcount", "Open": "open_headcount"})
    out["plan_target_with_buffer"] = out["plan_target_arr"] * (1 + plan_buffer)
    out["quota_coverage_ratio"] = out["ramped_quota_capacity"] / out["plan_target_with_buffer"].replace(0, np.nan)
    out["quota_capacity_surplus_gap"] = out["ramped_quota_capacity"] - out["plan_target_with_buffer"]
    out["required_hc_to_close_gap"] = np.maximum(
        0,
        out["plan_target_with_buffer"] - out["ramped_quota_capacity"],
    ) / out["segment"].map(lambda s: _quota_lookup(quota_by_segment, s)).replace(0, np.nan)
    out["budget_decision_signal"] = np.select(
        [out["quota_coverage_ratio"] >= 1.15, out["quota_coverage_ratio"] >= 1.00, out["quota_coverage_ratio"] >= 0.85],
        ["Over-covered", "Funded", "Watchlist"],
        default="Budget risk",
    )
    return out.sort_values(["quarter", "segment"]).reset_index(drop=True)


def attainment_distribution_simulation(
    cfo_capacity_df: pd.DataFrame,
    simulations: int = 2500,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for _, r in cfo_capacity_df.iterrows():
        expected_arr = float(r["ramped_quota_capacity"])
        target_arr = float(r["plan_target_with_buffer"])
        # Wider variance when the segment relies heavily on ramping reps.
        ramping_mix = float(r["ramping_headcount"] / max(r["active_headcount"], 1))
        sigma = 0.22 + 0.22 * ramping_mix
        random_factor = rng.lognormal(mean=-0.5 * sigma * sigma, sigma=sigma, size=simulations)
        realized_arr = expected_arr * random_factor
        attainment = realized_arr / max(target_arr, 1)
        for i, value in enumerate(attainment):
            rows.append(
                {
                    "quarter": r["quarter"],
                    "segment": r["segment"],
                    "simulation": i + 1,
                    "plan_attainment": float(value),
                    "realized_arr": float(realized_arr[i]),
                    "target_arr": target_arr,
                    "ramping_mix": ramping_mix,
                }
            )
    return pd.DataFrame(rows)


def attainment_percentile_table(attainment_df: pd.DataFrame) -> pd.DataFrame:
    return (
        attainment_df.groupby(["quarter", "segment"], as_index=False)
        .agg(
            p10_attainment=("plan_attainment", lambda x: float(np.quantile(x, 0.10))),
            p50_attainment=("plan_attainment", lambda x: float(np.quantile(x, 0.50))),
            p90_attainment=("plan_attainment", lambda x: float(np.quantile(x, 0.90))),
            probability_of_full_coverage=("plan_attainment", lambda x: float((x >= 1.0).mean())),
        )
        .sort_values(["quarter", "segment"])
        .reset_index(drop=True)
    )


def time_to_productivity_cohort_analysis(
    cohorts: pd.DataFrame,
    quota_by_segment: dict[str, float],
    productivity_threshold: float = 0.80,
    custom_ramp_curves: dict[str, list[float]] | None = None,
    quarter_labels: list[str] | None = None,
) -> pd.DataFrame:
    rows: list[dict] = []
    labels = quarter_labels or QUARTERS
    for _, c in cohorts.iterrows():
        segment = str(c["segment"])
        curve = _ramp_curve(segment, custom_ramp_curves)
        threshold_idx = next((i for i, factor in enumerate(curve) if factor >= productivity_threshold), len(curve) - 1)
        first_threshold_quarter_idx = int(c["start_quarter_index"]) + threshold_idx
        first_threshold_quarter = labels[first_threshold_quarter_idx] if 0 <= first_threshold_quarter_idx < len(labels) else "Post-plan"
        quota = _quota_lookup(quota_by_segment, segment)
        rows.append(
            {
                "segment": segment,
                "cohort": c["cohort"],
                "hire_quarter": c["hire_quarter"],
                "source": c["source"],
                "headcount": int(c["headcount"]),
                "quarters_to_80pct_productivity": threshold_idx,
                "first_80pct_productive_quarter": first_threshold_quarter,
                "q1_productivity": ramp_factor(segment, 0 - int(c["start_quarter_index"]), custom_ramp_curves),
                "q2_productivity": ramp_factor(segment, 1 - int(c["start_quarter_index"]), custom_ramp_curves),
                "q3_productivity": ramp_factor(segment, 2 - int(c["start_quarter_index"]), custom_ramp_curves),
                "q4_productivity": ramp_factor(segment, 3 - int(c["start_quarter_index"]), custom_ramp_curves),
                "steady_state_quota_capacity": int(c["headcount"]) * quota,
            }
        )
    return pd.DataFrame(rows)


def headcount_budget_recommendations(
    cfo_capacity_df: pd.DataFrame,
    cohorts: pd.DataFrame,
    ote_by_segment: dict[str, float] | None = None,
) -> pd.DataFrame:
    planned_hires = cohorts[cohorts["source"] == "planned_hire"].groupby("segment", as_index=False)["headcount"].sum()
    if planned_hires.empty:
        planned_hires = pd.DataFrame({"segment": cfo_capacity_df["segment"].unique(), "headcount": 0})
    annual = (
        cfo_capacity_df.groupby("segment", as_index=False)
        .agg(
            annual_target_with_buffer=("plan_target_with_buffer", "sum"),
            annual_ramped_capacity=("ramped_quota_capacity", "sum"),
            max_open_headcount=("open_headcount", "max"),
            avg_quota_coverage=("quota_coverage_ratio", "mean"),
            annual_headcount_cost=("headcount_cost", "sum"),
        )
    ).merge(planned_hires.rename(columns={"headcount": "planned_new_hires"}), on="segment", how="left")
    annual["planned_new_hires"] = annual["planned_new_hires"].fillna(0).astype(int)
    annual["annual_capacity_gap"] = annual["annual_ramped_capacity"] - annual["annual_target_with_buffer"]
    annual["budget_recommendation"] = np.select(
        [annual["avg_quota_coverage"] < 0.90, annual["avg_quota_coverage"] < 1.05, annual["avg_quota_coverage"] > 1.30],
        ["Approve additional headcount or reduce target", "Approve plan but watch ramp timing", "Potential overcapacity: inspect productivity and territories"],
        default="Budget structurally supportable",
    )
    annual["cfo_cro_question"] = np.select(
        [annual["avg_quota_coverage"] < 0.90, annual["planned_new_hires"] > annual["max_open_headcount"]],
        ["Can we hire earlier or re-phase ARR?", "Are these reqs funded and recruiting-ready?"],
        default="Is attainment distribution acceptable?",
    )
    return annual.sort_values("avg_quota_coverage").reset_index(drop=True)
