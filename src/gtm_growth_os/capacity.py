from __future__ import annotations

import numpy as np
import pandas as pd


def quota_capacity_model(
    segment_targets: pd.DataFrame,
    quota_by_segment: dict[str, float],
    current_aes: dict[str, int],
    ramp_productivity: dict[str, float],
    safety_buffer: float = 0.10,
) -> pd.DataFrame:
    grouped = segment_targets.groupby("segment", as_index=False)["new_arr_target"].sum()
    rows: list[dict] = []
    for _, r in grouped.iterrows():
        segment = r["segment"]
        annual_target = r["new_arr_target"]
        quota = quota_by_segment[segment]
        current = current_aes[segment]
        ramp = ramp_productivity[segment]
        productive_capacity = current * quota * ramp
        required_capacity = annual_target * (1 + safety_buffer)
        aes_needed = required_capacity / max(quota * ramp, 1)
        hires_needed = max(0, np.ceil(aes_needed - current))
        attainment_needed = annual_target / max(productive_capacity, 1)
        rows.append(
            {
                "segment": segment,
                "annual_new_arr_target": annual_target,
                "quota_per_ae": quota,
                "current_aes": current,
                "avg_ramp_productivity": ramp,
                "productive_capacity": productive_capacity,
                "attainment_required": attainment_needed,
                "aes_needed_with_buffer": aes_needed,
                "incremental_hires_needed": hires_needed,
                "capacity_gap": required_capacity - productive_capacity,
            }
        )
    return pd.DataFrame(rows)


def quarterly_capacity_phasing(capacity_df: pd.DataFrame, segment_targets: pd.DataFrame) -> pd.DataFrame:
    merged = segment_targets.merge(capacity_df[["segment", "productive_capacity"]], on="segment", how="left")
    annual_by_seg = merged.groupby("segment")["new_arr_target"].transform("sum")
    merged["quarterly_capacity_allocated"] = merged["productive_capacity"] * merged["new_arr_target"] / annual_by_seg.replace(0, np.nan)
    merged["capacity_surplus_deficit"] = merged["quarterly_capacity_allocated"] - merged["new_arr_target"]
    return merged
