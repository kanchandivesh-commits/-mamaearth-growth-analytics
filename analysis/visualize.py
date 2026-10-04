from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "visualizations"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD DATA
# ============================================================

customers = pd.read_csv(
    DATA_DIR / "customers.csv"
)

products = pd.read_csv(
    DATA_DIR / "products.csv"
)

orders = pd.read_csv(
    DATA_DIR / "orders.csv"
)


# ============================================================
# CLEAN DATA
# ============================================================

orders["payment_method"] = (
    orders["payment_method"]
    .astype(str)
    .str.strip()
    .str.upper()
)

natural_key = [
    "customer_id",
    "product_id",
    "order_date",
    "quantity",
    "discount_pct",
    "payment_method",
    "rating",
    "returned"
]

orders = orders.drop_duplicates(
    subset=natural_key,
    keep="first"
).copy()

orders["discount_pct"] = (
    orders["discount_pct"]
    .fillna(0)
)

orders["rating"] = (
    orders["rating"]
    .fillna(orders["rating"].median())
)


# ============================================================
# MERGE DATA
# ============================================================

merged = orders.merge(
    products,
    on="product_id",
    how="left"
)

merged = merged.merge(
    customers,
    on="customer_id",
    how="left"
)

merged["order_value"] = (
    merged["quantity"]
    * merged["price"]
    * (1 - merged["discount_pct"] / 100)
)


# ============================================================
# CHART 1 — RETURN RATE BY PAYMENT METHOD
# ============================================================

return_rates = (
    merged
    .groupby("payment_method")["returned"]
    .mean()
    .mul(100)
    .sort_values(ascending=False)
)

plt.figure(figsize=(8, 5))

bars = plt.bar(
    return_rates.index,
    return_rates.values
)

plt.title(
    "COD Returns at 44.4% — 3x Card"
)

plt.xlabel(
    "Payment Method"
)

plt.ylabel(
    "Return Rate (%)"
)

plt.ylim(
    0,
    max(return_rates.values) + 10
)

for bar, value in zip(
    bars,
    return_rates.values
):

    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1,
        f"{value:.1f}%",
        ha="center"
    )

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "return_rate_by_payment.png",
    dpi=150
)

plt.close()


# ============================================================
# CHART 2 — CORRECTED MONTHLY REVENUE TREND
# ============================================================

merged["order_date"] = pd.to_datetime(
    merged["order_date"]
)

merged["month"] = (
    merged["order_date"]
    .dt.to_period("M")
    .astype(str)
)


# IQR outlier detection
q1 = merged["quantity"].quantile(0.25)
q3 = merged["quantity"].quantile(0.75)

iqr = q3 - q1

upper_bound = q3 + 1.5 * iqr

merged["quantity_outlier"] = (
    merged["quantity"] > upper_bound
)

corrected_monthly_revenue = (
    merged.loc[
        ~merged["quantity_outlier"]
    ]
    .groupby("month")["order_value"]
    .sum()
)


true_peak_month = (
    corrected_monthly_revenue.idxmax()
)

true_peak_revenue = (
    corrected_monthly_revenue.max()
)

plt.figure(figsize=(9, 5))

plt.plot(
    corrected_monthly_revenue.index,
    corrected_monthly_revenue.values,
    marker="o"
)

plt.title(
    f"Corrected Monthly Revenue — Peak: "
    f"{true_peak_month} (₹{true_peak_revenue:,.2f})"
)

plt.xlabel(
    "Month"
)

plt.ylabel(
    "Revenue (INR)"
)

plt.xticks(
    rotation=45
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "monthly_revenue_trend.png",
    dpi=150
)

plt.close()


print(
    "Created:"
)

print(
    OUTPUT_DIR / "return_rate_by_payment.png"
)

print(
    OUTPUT_DIR / "monthly_revenue_trend.png"
)

print(
    "\nVisualization generation completed successfully! 🎉"
)
