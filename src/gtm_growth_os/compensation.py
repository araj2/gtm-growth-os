from __future__ import annotations

import numpy as np
import pandas as pd


def marginal_commission(bookings: float, quota: float, variable_comp: float) -> float:
    """Simple SaaS sales comp payout with accelerators."""
    base_rate = variable_comp / quota
    bands = [
        (0.0, 0.5, 0.50),
        (0.5, 1.0, 1.00),
        (1.0, 1.5, 1.50),
        (1.5, 10.0, 2.00),
    ]
    payout = 0.0
    attainment = bookings / quota if quota else 0
    for low, high, multiplier in bands:
        eligible_attainment = max(0.0, min(attainment, high) - low)
        payout += eligible_attainment * quota * base_rate * multiplier
    return payout


def comp_curve(quota: float, ote: float, base_split: float = 0.5) -> pd.DataFrame:
    base = ote * base_split
    variable = ote - base
    rows: list[dict] = []
    for attainment in np.linspace(0, 2.0, 41):
        bookings = quota * attainment
        variable_payout = marginal_commission(bookings, quota, variable)
        total_pay = base + variable_payout
        rows.append(
            {
                "attainment": attainment,
                "bookings": bookings,
                "base_salary": base,
                "variable_payout": variable_payout,
                "total_pay": total_pay,
                "effective_commission_rate": variable_payout / bookings if bookings else 0,
            }
        )
    return pd.DataFrame(rows)


def segment_comp_summary(quota_by_segment: dict[str, float], ote_by_segment: dict[str, float]) -> pd.DataFrame:
    rows = []
    for segment, quota in quota_by_segment.items():
        ote = ote_by_segment[segment]
        variable = ote * 0.5
        rows.append(
            {
                "segment": segment,
                "quota": quota,
                "ote": ote,
                "base": ote * 0.5,
                "variable": variable,
                "target_commission_rate": variable / quota if quota else 0,
                "payout_at_120pct": marginal_commission(quota * 1.2, quota, variable) + ote * 0.5,
                "payout_at_160pct": marginal_commission(quota * 1.6, quota, variable) + ote * 0.5,
            }
        )
    return pd.DataFrame(rows)
