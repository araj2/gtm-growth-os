from __future__ import annotations

import numpy as np
import pandas as pd


def monte_carlo_attainment(
    target_arr: float,
    committed_pipeline: float,
    base_win_rate: float,
    base_acv: float,
    base_cycle_slip: float,
    simulations: int = 2000,
    seed: int = 11,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    win_rates = np.clip(rng.normal(base_win_rate, base_win_rate * 0.18, simulations), 0.03, 0.75)
    acv_multipliers = np.clip(rng.normal(1.0, 0.16, simulations), 0.55, 1.65)
    pipeline_multipliers = np.clip(rng.normal(1.0, 0.20, simulations), 0.45, 1.85)
    cycle_slip = np.clip(rng.normal(base_cycle_slip, 0.10, simulations), 0.0, 0.55)
    ramp_factor = np.clip(rng.normal(1.0, 0.12, simulations), 0.60, 1.35)

    realized_arr = committed_pipeline * pipeline_multipliers * win_rates * acv_multipliers * (1 - cycle_slip) * ramp_factor
    return pd.DataFrame(
        {
            "simulation": np.arange(1, simulations + 1),
            "realized_arr": realized_arr,
            "target_arr": target_arr,
            "attainment": realized_arr / max(target_arr, 1),
            "hit_target": realized_arr >= target_arr,
            "win_rate": win_rates,
            "pipeline_multiplier": pipeline_multipliers,
            "cycle_slip": cycle_slip,
            "ramp_factor": ramp_factor,
        }
    )


def scenario_summary(sim_df: pd.DataFrame) -> dict[str, float]:
    return {
        "probability_of_hit": float(sim_df["hit_target"].mean()),
        "p10_arr": float(sim_df["realized_arr"].quantile(0.10)),
        "p50_arr": float(sim_df["realized_arr"].quantile(0.50)),
        "p90_arr": float(sim_df["realized_arr"].quantile(0.90)),
        "median_attainment": float(sim_df["attainment"].median()),
    }


def executive_narrative(metrics: dict[str, float], probability_hit: float, capacity_gap: float, bdr_gap: float) -> str:
    risk_line = "green" if probability_hit >= 0.70 else "yellow" if probability_hit >= 0.50 else "red"
    return f"""
# GTM Operating Plan Narrative

We are planning from **${metrics['starting_arr']/1_000_000:,.1f}M ARR** to **${metrics['exit_arr']/1_000_000:,.1f}M exit ARR**, requiring **${metrics['gross_new_arr']/1_000_000:,.1f}M of gross new ARR** after churn and expansion dynamics.

The current operating model has a **{probability_hit:.0%} probability of hitting plan**, which puts the plan in the **{risk_line.upper()} zone**. The two biggest levers are:

1. **Sales capacity gap:** ${capacity_gap/1_000_000:,.1f}M.
2. **Outbound coverage gap:** {bdr_gap:,.0f} BDRs.

The plan is strongest when finance targets, segment ACV, quota capacity, pipeline coverage, marketing conversion, and BDR outbound math are managed as one system instead of independent spreadsheets.
""".strip()
