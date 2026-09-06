Telecom Corporate Financial Risk Anaysis

Project Question

How can corporate credit risk and financial distress be quantitatively monitored across South African telecommunications
operators using standardized  financial metrics and SQL analytical window funtions?

Methodology

This project implements an automated quantitative credit-scoring egine using a multi-layered SQL Common Table Expression architecture integrated into a ptyhon data pipeline.

DATA INGESTION: Cleaned historical financial statements from telecom operators, including Telkom and Cell C, were structured and ingested into a relational database.

SIGNAL ENGINEERING: SQL window funtions were used to track year-over-tear trends and operational indicators, focusing on identifying top-line contradictions, evaluating operational efficiency changes, monitioring raw profitability or capital losses, and evaluating structural pricing power alongside high-value subscribers churn.

RISK SCORING MATRIX: A deterministic condtional logic matrix automatically flags deteriorating metrics, calculating raw risk point to tier operations into low risk, medium risk, or hihg risk categories.

INTERFACE DEPLOYMENT: Impleemented an interacive executive dashboard using streamlit foe dynamics sector filtering, visualization, and portfolio surveillance.

KEY FINDINGS

CELL C BACKTEST VAKIDATION: The quantative matrix successfull backtested against historical market reality.The model triggers a critical high risk classification during the recent financial periods, matching the operator's public capital restructuring phase and insolvency threats.

TELKOM MARGIN COMPRESSION: Analysis verifies a steady contraction in telkom's core margins over time, driven by intensifying competition and heavy infastructure fixed costs, placing them into a persistent medium risk takeover-target profile.

MACRO-SIGNAL CORRELATION: Top-line revenue stability often makes severe under-the-surface capital erosion. profitability drops and structural revenue-per-user degradation serve as leading indicators of financial distress before absolute insolvency occurs.

ANALYTICAL MODEL LIMITATIONS

ASYMMETRICAL SAMPLE SIZE: The dataset monitors a highly specialized, small pool of reginal corporate entities. statistical inferences or machine learning modeling cannot be applied robustly without a broader global telecom sample.

ABSENCE OF BALANCE SHEET LIQUIDITY INDICATORS: The model relies excusively on income statement items. true corporate solvency assessments require key balance sheet health ratios, specifically debt-to-profitability levarage metrics to assess exact default probabilities.

SUBJECTIVE OPERATIONAL WEIGHTS: The scoring algorithm assumes equal weight distribution across all monitored signals. in real-world credit syndicates, macro revenue contractions and customer revenue erosion are often weighted differently depending on market maturity and capital expenditures.

