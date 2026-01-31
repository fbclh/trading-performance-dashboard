# 📊 Trading Performance Dashboard  
**Python + SQL + Tableau Analytics Pipeline**

This portfolio project demonstrates a complete analytics workflow that transforms raw trading logs into a structured, repeatable performance reporting system and a Tableau-ready dataset.

Although the example uses trading data, the same pipeline structure applies to financial, operational, and performance analytics in business environments.

---

## 🔄 What This Project Does

**Ingest**  
Processes structured trade reports and prepares them for analysis.

**Transform**  
Pairs entry and exit events into unified trade records (one row per trade).

**Model**  
Builds a clean `trades_fact` dataset designed for BI and dashboard tools.

**Metrics**  
Calculates core performance KPIs using consistent, transparent logic.

**Output**  
Exports structured datasets ready for Tableau dashboarding and reporting.

---

## 📁 Outputs (for Tableau)

| File | Description |
|------|-------------|
`trades_fact.csv` | One row per trade (timestamps, prices, size, net PnL, run-up, drawdown) |
`equity_curve.csv` | Equity progression and drawdown over time |
`kpis_summary.csv` | Summary KPI table (single-row performance snapshot) |

> **Note:** Raw source data is not included in this repository for privacy reasons. The pipeline structure and KPI logic are fully demonstrated.

---

## 📈 Core KPIs Included

- **Win Rate**
- **Average Win vs. Average Loss**
- **Expectancy (per trade)**
- **Profit Factor**
- **Net PnL**
- **Maximum Drawdown** (from equity curve)

These KPIs mirror the type of performance metrics used in business reporting, including revenue performance, marketing efficiency, and operational risk monitoring.

---

## ▶️ How to Run the Pipeline

```bash
pip install -r requirements.txt
python etl_from_excel.py
