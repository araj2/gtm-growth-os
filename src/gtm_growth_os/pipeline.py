from __future__ import annotations

import pandas as pd

DEFAULT_STAGE_CONVERSIONS = {
    "Closed Won": 1.00,
    "Commit": 0.72,
    "Proposal": 0.48,
    "SAO": 0.30,
    "SQL": 0.18,
    "MQL": 0.08,
    "Lead": 0.025,
}


def pipeline_requirements(
    segment_targets: pd.DataFrame,
    win_rates: dict[str, float],
    coverage_ratios: dict[str, float],
    stage_conversions: dict[str, float] | None = None,
) -> pd.DataFrame:
    stage_conversions = stage_conversions or DEFAULT_STAGE_CONVERSIONS
    rows: list[dict] = []
    for _, r in segment_targets.iterrows():
        segment = r["segment"]
        win_rate = win_rates[segment]
        coverage = coverage_ratios[segment]
        closed_won_arr = r["new_arr_target"]
        total_pipeline = closed_won_arr * coverage
        for stage, probability in stage_conversions.items():
            # Pipeline value required at each stage if the stage has a given probability of closing.
            stage_pipe = closed_won_arr / max(probability, 0.0001)
            rows.append(
                {
                    "quarter": r["quarter"],
                    "segment": segment,
                    "stage": stage,
                    "stage_probability": probability,
                    "pipeline_required": stage_pipe,
                    "coverage_pipeline_required": total_pipeline,
                    "win_rate": win_rate,
                    "coverage_ratio": coverage,
                }
            )
    return pd.DataFrame(rows)


def pipeline_waterfall(segment_targets: pd.DataFrame, win_rates: dict[str, float]) -> pd.DataFrame:
    rows: list[dict] = []
    for _, r in segment_targets.iterrows():
        segment = r["segment"]
        win_rate = win_rates[segment]
        arr = r["new_arr_target"]
        acv = r["target_acv"]
        won_deals = arr / acv
        opportunities = won_deals / max(win_rate, 0.0001)
        pipeline = opportunities * acv
        rows.append(
            {
                "quarter": r["quarter"],
                "segment": segment,
                "new_arr_target": arr,
                "target_acv": acv,
                "won_deals_required": won_deals,
                "opportunities_required": opportunities,
                "pipeline_required": pipeline,
                "win_rate": win_rate,
            }
        )
    return pd.DataFrame(rows)
