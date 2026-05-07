# Trading Performance Dashboard (Python + SQL + Tableau)

This portfolio project turns raw trade logs into a clean, repeatable analytics pipeline and a Tableau-ready dataset.

## Project layout
```
trading_dashboard_project/
├── app/           # Streamlit dashboard
├── data/          # Generated CSVs (ETL output)
├── etl/           # Excel → CSV pipeline
├── sql/           # Ad hoc SQL (e.g. KPIs)
├── screenshots/
├── README.md
├── requirements.txt
└── pyproject.toml
```

## What it does
1. **Ingest**: reads the Excel trade report (`Replay_Trading_CME_MINI_ES1!_2025-09-27_79f2b.xlsx`, sheet: `List of trades`)
2. **Transform**: pairs Entry/Exit rows into a single trade record (one row per trade)
3. **Model**: produces a `trades_fact` dataset suitable for BI tools
4. **Metrics**: computes core trading KPIs (win rate, expectancy, profit factor, max drawdown)
5. **Output**: exports CSV files for Tableau dashboarding

## Outputs (for Tableau)
Written to `data/` by the ETL:
- `data/trades_fact.csv` — one row per trade (timestamps, prices, size, net PnL, run-up, drawdown)
- `data/equity_curve.csv` — equity and drawdown over time
- `data/kpis_summary.csv` — summary KPI table (single row)

## Core KPIs included
- Win Rate
- Average Win / Average Loss
- Expectancy (per trade)
- Profit Factor
- Net PnL
- Max Drawdown (from equity curve)

## How to run
From the **project root** (`trading_dashboard_project/`):

```bash
pip install -r requirements.txt
python etl/etl_from_excel.py
```

### Run the Streamlit dashboard
```bash
streamlit run app/dashboard_app.py
```

## Linting and formatting
The project uses **Ruff** (modern, fast lint + format). Config is in `pyproject.toml`.

```bash
pip install ruff
ruff check .          # lint
ruff format .         # format
```

**In Cursor / VS Code:** Install the [Ruff extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) to get inline diagnostics and format-on-save. No other extensions are required for Python style.

### SQL (`sql/kpis.sql`)
- **Formatting:** Use the [SQL Formatter](https://marketplace.visualstudio.com/items?itemName=adpyke.vscode-sql-formatter) extension (or Prettier with a SQL plugin) for consistent indentation and line breaks. No project config required for the single file.
- **Linting:** Optional. [SQLFluff](https://marketplace.visualstudio.com/items?itemName=dorzey.vscode-sqlfluff) gives style and dialect checks if you add more SQL later; for one small file it’s optional.

## Tableau dashboard suggestion
**Dashboard 1 — Overview**
- KPI tiles (Net PnL, Win Rate, Profit Factor, Expectancy, Max Drawdown)
- Equity curve line chart

**Dashboard 2 — Trade Quality**
- PnL distribution (histogram)
- Run-up vs Drawdown scatter

**Dashboard 3 — Drilldowns**
- PnL by week/month
- PnL by side (Long/Short)
