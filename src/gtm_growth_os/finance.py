from __future__ import annotations

import numpy as np
import pandas as pd

QUARTERS = ["FY27 Q1", "FY27 Q2", "FY27 Q3", "FY27 Q4"]


def normalize_weights(weights: list[float] | np.ndarray) -> np.ndarray:
    arr = np.array(weights, dtype=float)
    total = arr.sum()
    if total <= 0:
        return np.ones_like(arr) / len(arr)
    return arr / total


def finance_target_plan(
    start_arr: float,
    target_exit_arr: float,
    gross_churn_rate: float,
    expansion_rate: float,
    seasonality: list[float] | np.ndarray,
) -> pd.DataFrame:
    """Create quarterly ARR bridge and gross new ARR requirements.

    gross_churn_rate and expansion_rate are annualized assumptions, entered as decimals.
    """
    q_weights = normalize_weights(seasonality)
    cumulative = np.cumsum(q_weights)
    desired_endings = start_arr + (target_exit_arr - start_arr) * cumulative

    rows: list[dict] = []
    opening = start_arr
    for quarter, desired_ending, q_weight in zip(QUARTERS, desired_endings, q_weights):
        gross_churn = opening * gross_churn_rate / 4
        expansion = opening * expansion_rate / 4
        gross_new_required = desired_ending - opening + gross_churn - expansion
        gross_new_required = max(gross_new_required, 0)
        ending = opening - gross_churn + expansion + gross_new_required
        rows.append(
            {
                "quarter": quarter,
                "opening_arr": opening,
                "gross_churn_arr": gross_churn,
                "expansion_arr": expansion,
                "gross_new_arr_required": gross_new_required,
                "ending_arr": ending,
                "qoq_growth": ending / opening - 1 if opening else np.nan,
                "seasonality_weight": q_weight,
            }
        )
        opening = ending
    return pd.DataFrame(rows)


def allocate_new_arr_by_segment(finance_df: pd.DataFrame, segment_mix: dict[str, float], acv: dict[str, float]) -> pd.DataFrame:
    mix_total = sum(segment_mix.values()) or 1
    rows: list[dict] = []
    for _, q in finance_df.iterrows():
        for segment, mix in segment_mix.items():
            share = mix / mix_total
            target = q["gross_new_arr_required"] * share
            segment_acv = acv[segment]
            rows.append(
                {
                    "quarter": q["quarter"],
                    "segment": segment,
                    "new_arr_target": target,
                    "target_acv": segment_acv,
                    "closed_won_deals_required": target / segment_acv if segment_acv else np.nan,
                }
            )
    return pd.DataFrame(rows)


def board_metrics(finance_df: pd.DataFrame) -> dict[str, float]:
    start = float(finance_df.iloc[0]["opening_arr"])
    end = float(finance_df.iloc[-1]["ending_arr"])
    return {
        "starting_arr": start,
        "exit_arr": end,
        "net_new_arr": end - start,
        "gross_new_arr": float(finance_df["gross_new_arr_required"].sum()),
        "gross_churn_arr": float(finance_df["gross_churn_arr"].sum()),
        "expansion_arr": float(finance_df["expansion_arr"].sum()),
        "growth_rate": end / start - 1 if start else np.nan,
    }
