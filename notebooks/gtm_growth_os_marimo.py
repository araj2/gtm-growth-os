import marimo

__generated_with = "0.23.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[1]
    SRC = ROOT / "src"
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    from gtm_growth_os.finance import finance_target_plan, allocate_new_arr_by_segment
    from gtm_growth_os.pipeline import pipeline_waterfall
    from gtm_growth_os.data import generate_account_universe
    return mo, finance_target_plan, allocate_new_arr_by_segment, pipeline_waterfall, generate_account_universe


@app.cell
def _(mo):
    mo.md("""
    # GTM Growth OS — marimo notebook

    A reactive notebook version of the GTM planning engine. Change assumptions, then watch finance targets, segment ARR, and pipeline requirements recompute.
    """)
    return


@app.cell
def _(mo):
    start_arr = mo.ui.number(value=42_000_000, label="Starting ARR")
    exit_arr = mo.ui.number(value=78_000_000, label="Exit ARR target")
    gross_churn = mo.ui.slider(0, 0.25, value=0.075, step=0.005, label="Annual gross churn")
    expansion = mo.ui.slider(0, 0.60, value=0.18, step=0.01, label="Annual expansion")
    mo.vstack([start_arr, exit_arr, gross_churn, expansion])
    return start_arr, exit_arr, gross_churn, expansion


@app.cell
def _(finance_target_plan, start_arr, exit_arr, gross_churn, expansion):
    finance = finance_target_plan(start_arr.value, exit_arr.value, gross_churn.value, expansion.value, [0.18, 0.22, 0.25, 0.35])
    finance
    return finance


@app.cell
def _(allocate_new_arr_by_segment, finance):
    acv = {"SMB": 18_000, "Mid-Market": 55_000, "Enterprise": 145_000, "Strategic": 330_000}
    mix = {"SMB": 0.18, "Mid-Market": 0.32, "Enterprise": 0.34, "Strategic": 0.16}
    targets = allocate_new_arr_by_segment(finance, mix, acv)
    targets
    return targets, acv


@app.cell
def _(pipeline_waterfall, targets):
    win = {"SMB": 0.24, "Mid-Market": 0.22, "Enterprise": 0.19, "Strategic": 0.15}
    pipe = pipeline_waterfall(targets, win)
    pipe.groupby("segment", as_index=False)[["new_arr_target", "pipeline_required"]].sum()
    return pipe


@app.cell
def _(generate_account_universe):
    accounts = generate_account_universe(1000, seed=5)
    accounts.head(20)
    return accounts


if __name__ == "__main__":
    app.run()
