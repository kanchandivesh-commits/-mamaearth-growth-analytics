# -mamaearth-growth-analytics

## Project Overview

This project analyzes Mamaearth customer, product, and order data to identify revenue trends, return-rate patterns, customer segments, and data-quality issues.

The workflow uses:

- SQLite for database analysis
- SQL for reporting
- Python and Pandas for cleaning and EDA
- Matplotlib for visualizations
- Gemini for executive narrative generation, with an offline fallback
## Repository Structure

```text
mamaearth-growth-analytics/
├── README.md
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
├── analysis/
│   ├── clean_and_eda.py
│   └── visualize.py
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
└── narrator/
    ├── findings.json
    ├── generate_narrative.py
    └── sample_output.txt
