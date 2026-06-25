# GTM Growth OS 🚀

A portfolio-grade, end-to-end GTM planning command center designed to look like something a serious RevOps / GTM Strategy / Strategic Finance team would actually use.

This project connects the entire GTM chain:

```text
Board / Finance ARR targets
        ↓
Quarterly gross-new ARR requirements
        ↓
Segment mix + ACV targets
        ↓
Pipeline coverage and stage requirements
        ↓
AE capacity, quota, ramp, and hiring model
        ↓
CFO/CRO quarterly headcount budget model
        ↓
Sales compensation design
        ↓
Account universe and territory optimization
        ↓
Marketing demand generation requirements
        ↓
BDR outbound pipeline requirements
        ↓
Monte Carlo scenario war room
        ↓
Executive narrative + Excel export pack
```

## Why this project is impressive

Most GTM dashboards show historical metrics. This one is different: it is a **forward-looking operating model**.

It demonstrates that you understand:

- Strategic finance targets
- ARR bridge logic
- Gross churn and expansion dynamics
- ACV and segment mix strategy
- Pipeline coverage math
- Reverse funnel conversion math
- AE capacity and quota modeling
- CFO/CRO headcount budget planning
- Productive vs. ramping vs. open headcount coverage
- Attainment distribution curves
- Time-to-productivity cohort analysis
- Sales ramp / productivity assumptions
- Compensation accelerators
- Territory balancing
- Marketing lead and budget requirements
- BDR outbound capacity
- Scenario risk and probability of hitting plan
- Exportable executive planning artifacts


## CFO/CRO capacity planning module

The upgraded model now includes a dedicated **CFO/CRO HC budget** tab that does the annual-planning work usually trapped across several spreadsheets:

- Maps quarterly finance targets to buffered quota-capacity requirements.
- Separates **productive**, **ramping**, and **open** AE headcount by quarter and segment.
- Converts ramp cohorts into ramp-adjusted quota capacity.
- Shows quota coverage against plan by quarter.
- Creates P10 / P50 / P90 attainment distribution curves.
- Calculates time-to-80%-productivity by hiring cohort.
- Produces segment-level headcount budget recommendations for CFO/CRO planning.
- Exports the capacity budget, cohorts, productivity analysis, and attainment percentiles in the Excel pack.

## Tech stack

Built with your installed AI/data stack:

- Python
- Streamlit
- pandas
- NumPy
- Plotly
- DuckDB
- scikit-learn
- scipy-compatible modeling style
- openpyxl
- marimo notebook
- uv project management

## Run the project

From the unzipped folder:

```bash
cd ~/Developer/gtm_growth_os
uv python pin 3.12
uv sync
uv run python scripts/smoke_test.py
uv run streamlit run app/streamlit_app.py
```

Or use the convenience script:

```bash
cd ~/Developer/gtm_growth_os
./scripts/run_app.sh
```

The app should open at:

```text
http://localhost:8501
```

## Run the marimo notebook

```bash
cd ~/Developer/gtm_growth_os
./scripts/run_marimo.sh
```

## Optional “wow” packages

The project works without these. If you want to extend it into an even more advanced optimization engine, install:

```bash
uv add "gtm-growth-os[wow]"
```

Or manually:

```bash
uv add ortools networkx great-tables
```

Ideas for extension:

- Use OR-Tools for territory optimization with hard constraints.
- Use NetworkX to model account hierarchies and buying committees.
- Use Great Tables to create board-ready GTM tables.
- Add OpenAI/Anthropic to auto-generate CFO/ CRO narrative memos.
- Add real CRM exports and replace the synthetic account universe.

## Suggested demo flow for interviews

1. Start with finance targets: “Here is how the board plan turns into quarterly gross-new ARR.”
2. Move to segment strategy: “Here is the ACV and deal-count implication.”
3. Show pipeline coverage: “Here is how much pipeline must exist by stage and quarter.”
4. Show capacity: “Here is whether the sales team can actually carry the plan.”
5. Open CFO/CRO HC budget: “Here is how productive, ramping, and open headcount converts into quota coverage and hiring-budget decisions.”
6. Show comp: “Here is whether incentives support the strategy.”
6. Show territories: “Here is how I would turn account intelligence into balanced books.”
7. Show demand gen and BDR math: “Here is how much demand and outbound activity the plan requires.”
8. End with the scenario war room: “Here is the probability of hitting plan under realistic volatility.”
9. Export the Excel pack: “Here is the operating plan output.”

## Project structure

```text
gtm_growth_os/
  app/
    streamlit_app.py
  src/gtm_growth_os/
    finance.py
    pipeline.py
    capacity.py
    capacity_budget.py
    compensation.py
    data.py
    territories.py
    demand_gen.py
    scenarios.py
    sql.py
    exports.py
  notebooks/
    gtm_growth_os_marimo.py
  scripts/
    smoke_test.py
    run_app.sh
    run_marimo.sh
  pyproject.toml
  README.md
```

## What to say this project is

> GTM Growth OS is an end-to-end operating model that connects board-level ARR targets to the day-to-day execution math of GTM: ACV, pipeline, capacity, quota, productive/ramping/open headcount, compensation, territory design, marketing demand, and BDR outbound requirements. It is designed to expose whether a GTM plan is actually executable before the quarter starts and whether the CFO/CRO should fund the headcount required to hit plan.

