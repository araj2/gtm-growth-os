from __future__ import annotations

import math
import pandas as pd


def inbound_funnel_requirements(
    pipeline_required: float,
    avg_acv: float,
    lead_to_mql: float,
    mql_to_sql: float,
    sql_to_sao: float,
    sao_to_pipeline: float,
    inbound_share: float,
    cpl: float,
) -> pd.DataFrame:
    inbound_pipeline = pipeline_required * inbound_share
    opps = inbound_pipeline / max(avg_acv, 1)
    sao = opps / max(sao_to_pipeline, 0.0001)
    sql = sao / max(sql_to_sao, 0.0001)
    mql = sql / max(mql_to_sql, 0.0001)
    leads = mql / max(lead_to_mql, 0.0001)
    budget = leads * cpl
    return pd.DataFrame(
        [
            {"stage": "Inbound Pipeline $", "required": inbound_pipeline, "unit": "$"},
            {"stage": "Pipeline Opportunities", "required": opps, "unit": "opps"},
            {"stage": "SAOs", "required": sao, "unit": "SAOs"},
            {"stage": "SQLs", "required": sql, "unit": "SQLs"},
            {"stage": "MQLs", "required": mql, "unit": "MQLs"},
            {"stage": "Raw Leads", "required": leads, "unit": "leads"},
            {"stage": "Marketing Budget", "required": budget, "unit": "$"},
        ]
    )


def channel_mix_model(total_leads: float, cpl_by_channel: dict[str, float], mix: dict[str, float]) -> pd.DataFrame:
    total_mix = sum(mix.values()) or 1
    rows = []
    for channel, share in mix.items():
        normalized_share = share / total_mix
        leads = total_leads * normalized_share
        cpl = cpl_by_channel[channel]
        rows.append(
            {
                "channel": channel,
                "lead_share": normalized_share,
                "leads_required": leads,
                "cpl": cpl,
                "budget_required": leads * cpl,
            }
        )
    return pd.DataFrame(rows)


def bdr_outbound_requirements(
    pipeline_required: float,
    outbound_share: float,
    avg_acv: float,
    bdrs_current: int,
    monthly_activities_per_bdr: int,
    connect_rate: float,
    meeting_rate: float,
    meeting_to_opp: float,
    opp_accept_rate: float,
    months: int = 3,
) -> pd.DataFrame:
    outbound_pipeline = pipeline_required * outbound_share
    activities_per_bdr_q = monthly_activities_per_bdr * months
    meetings_per_bdr_q = activities_per_bdr_q * connect_rate * meeting_rate
    opps_per_bdr_q = meetings_per_bdr_q * meeting_to_opp * opp_accept_rate
    pipeline_per_bdr_q = opps_per_bdr_q * avg_acv
    bdrs_required = math.ceil(outbound_pipeline / max(pipeline_per_bdr_q, 1))
    return pd.DataFrame(
        [
            {
                "outbound_pipeline_required": outbound_pipeline,
                "activities_per_bdr_per_quarter": activities_per_bdr_q,
                "meetings_per_bdr_per_quarter": meetings_per_bdr_q,
                "accepted_opps_per_bdr_per_quarter": opps_per_bdr_q,
                "pipeline_per_bdr_per_quarter": pipeline_per_bdr_q,
                "current_bdrs": bdrs_current,
                "bdrs_required": bdrs_required,
                "incremental_bdrs_needed": max(0, bdrs_required - bdrs_current),
            }
        ]
    )
