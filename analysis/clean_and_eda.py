import json
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
NARRATOR_DIR = ROOT / "narrator"

CUSTOMERS_FILE = DATA_DIR / "customers.csv"
PRODUCTS_FILE = DATA_DIR / "products.csv"
ORDERS_FILE = DATA_DIR / "orders.csv"

FINDINGS_FILE = NARRATOR_DIR / "findings.json"


# ============================================================
# TASK 1 — LOAD RAW CSV FILES
# ============================================================

customers = pd.read_csv(CUSTOMERS_FILE)
products = pd.read_csv(PRODUCTS_FILE)
orders = pd.read_csv(ORDERS_FILE)

print("\n" + "=" * 60)
print("TASK 1 — RAW DATA")
print("=" * 60)

print("Customers shape:", customers.shape)
print("Products shape:", products.shape)
print("Orders shape before cleaning:", orders.shape)

assert orders.shape == (180, 9)


# ============================================================
# TASK 2 — STANDARDIZE PAYMENT METHOD
# ============================================================

print("\n" + "=" * 60)
print("TASK 2 — PAYMENT METHOD CLEANING")
print("=" * 60)

print("Raw payment methods:")
print(orders["payment_method"].value_counts())

orders["payment_method"] = (
    orders["payment_method"]
    .astype(str)
    .str.strip()
    .str.upper()
)

print("\nCleaned payment methods:")
print(orders["payment_method"].value_counts())

assert set(orders["payment_method"].unique()) == {
    "CARD",
    "COD",
    "UPI"
}

payment_counts = orders["payment_method"].value_counts().to_dict()

assert payment_counts["CARD"] == 70
assert payment_counts["UPI"] == 55
assert payment_counts["COD"] == 55


# ============================================================
# TASK 3 — DUPLICATE DETECTION AND REMOVAL
# ============================================================

print("\n" + "=" * 60)
print("TASK 3 — DUPLICATES")
print("=" * 60)

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

duplicate_mask = orders.duplicated(
    subset=natural_key,
    keep="first"
)

duplicates = orders.loc[duplicate_mask].copy()

print("Duplicate rows flagged:", len(duplicates))
print("Duplicate order IDs:")
print(duplicates["order_id"].tolist())

assert len(duplicates) == 5

assert duplicates["order_id"].tolist() == [
    "O0176",
    "O0177",
    "O0178",
    "O0179",
    "O0180"
]

orders = orders.loc[~duplicate_mask].copy()

print("Clean shape after duplicate removal:", orders.shape)

assert orders.shape == (175, 9)


# ============================================================
# TASK 4 — MISSING VALUE IMPUTATION
# ============================================================

print("\n" + "=" * 60)
print("TASK 4 — MISSING VALUES")
print("=" * 60)

missing_discount = orders["discount_pct"].isna().sum()
missing_rating = orders["rating"].isna().sum()

print("Missing discount_pct before fill:", missing_discount)
print("Missing rating before fill:", missing_rating)

assert missing_discount == 12
assert missing_rating == 15

# Missing discounts are treated as 0%
orders["discount_pct"] = orders["discount_pct"].fillna(0)

# Missing ratings are filled using the median
rating_median = orders["rating"].median()

print("Rating median:", rating_median)

assert rating_median == 3.0

orders["rating"] = orders["rating"].fillna(rating_median)

print(
    "Missing discount_pct after fill:",
    orders["discount_pct"].isna().sum()
)

print(
    "Missing rating after fill:",
    orders["rating"].isna().sum()
)

assert orders["discount_pct"].isna().sum() == 0
assert orders["rating"].isna().sum() == 0


# ============================================================
# TASK 5 — MERGE DATA AND CALCULATE REVENUE
# ============================================================

print("\n" + "=" * 60)
print("TASK 5 — REVENUE")
print("=" * 60)

merged = orders.merge(
    products,
    on="product_id",
    how="left",
    validate="many_to_one"
)

merged = merged.merge(
    customers,
    on="customer_id",
    how="left",
    validate="many_to_one"
)

merged["order_value"] = (
    merged["quantity"]
    * merged["price"]
    * (1 - merged["discount_pct"] / 100)
)

cleaned_total_revenue = merged["order_value"].sum()


# Calculate raw revenue separately
raw_orders = pd.read_csv(ORDERS_FILE)

raw_orders["discount_pct"] = raw_orders["discount_pct"].fillna(0)

raw_merged = raw_orders.merge(
    products,
    on="product_id",
    how="left"
)

raw_merged["order_value"] = (
    raw_merged["quantity"]
    * raw_merged["price"]
    * (1 - raw_merged["discount_pct"] / 100)
)

raw_total_revenue = raw_merged["order_value"].sum()

reconciliation_delta = (
    raw_total_revenue - cleaned_total_revenue
)

print(
    f"Cleaned total revenue: "
    f"₹{cleaned_total_revenue:,.2f}"
)

print(
    f"Raw total revenue: "
    f"₹{raw_total_revenue:,.2f}"
)

print(
    f"Reconciliation delta: "
    f"₹{reconciliation_delta:,.2f}"
)

assert round(cleaned_total_revenue, 2) == 97358.30
assert round(raw_total_revenue, 2) == 99860.20
assert round(reconciliation_delta, 2) == 2501.90

print(
    "\nReconciliation: the ₹2,501.90 difference is caused "
    "by the five duplicated order rows removed during cleaning. "
    "Discount and rating imputation do not create this delta."
)


# ============================================================
# TASK 6 — QUANTITY OUTLIERS USING IQR
# ============================================================

print("\n" + "=" * 60)
print("TASK 6 — QUANTITY OUTLIERS")
print("=" * 60)

q1 = merged["quantity"].quantile(0.25)
q3 = merged["quantity"].quantile(0.75)

iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

merged["quantity_outlier"] = (
    (merged["quantity"] < lower_bound)
    | (merged["quantity"] > upper_bound)
)

outliers = merged.loc[
    merged["quantity_outlier"]
].copy()

print("Q1:", q1)
print("Q3:", q3)
print("IQR:", iqr)
print("Lower bound:", lower_bound)
print("Upper bound:", upper_bound)

print("\nOutlier orders:")

print(
    outliers[
        ["order_id", "quantity"]
    ].to_string(index=False)
)

assert q1 == 1.0
assert q3 == 2.0
assert iqr == 1.0
assert lower_bound == -0.5
assert upper_bound == 3.5

assert outliers["order_id"].tolist() == [
    "O0011",
    "O0098"
]

print(
    "\nOutliers are flagged, NOT removed."
)


# ============================================================
# TASK 7 — RETURN RATE BY PAYMENT METHOD
# ============================================================

print("\n" + "=" * 60)
print("TASK 7 — RETURN RATE BY PAYMENT METHOD")
print("=" * 60)

payment_returns = (
    merged
    .groupby("payment_method")["returned"]
    .agg(["count", "mean"])
)

payment_returns["return_rate_pct"] = (
    payment_returns["mean"] * 100
)

payment_returns = payment_returns.drop(
    columns="mean"
)

print(payment_returns)

expected_rates = {
    "CARD": 14.7,
    "COD": 44.4,
    "UPI": 18.9
}

for method, expected in expected_rates.items():

    actual = round(
        payment_returns.loc[
            method,
            "return_rate_pct"
        ],
        1
    )

    assert actual == expected

print(
    "\nHypothesis: COD has a higher return rate."
)

print("Result: CONFIRMED")


# ============================================================
# TASK 8 — PAYMENT METHOD + CITY TIER SEGMENTATION
# ============================================================

print("\n" + "=" * 60)
print("TASK 8 — RISK SEGMENTATION")
print("=" * 60)

segment = (
    merged
    .groupby(
        ["payment_method", "city_tier"]
    )["returned"]
    .agg(["count", "mean"])
)

segment["return_rate_pct"] = (
    segment["mean"] * 100
)

segment = segment.drop(columns="mean")

print(segment)

highest_segment = (
    segment["return_rate_pct"]
    .idxmax()
)

highest_rate = round(
    segment.loc[
        highest_segment,
        "return_rate_pct"
    ],
    1
)

print(
    f"\nHighest-risk segment: "
    f"{highest_segment[0]} + Tier {highest_segment[1]}"
)

print(
    f"Return rate: {highest_rate}%"
)

assert highest_segment == ("COD", 2)
assert highest_rate == 54.5

print(
    "\nRisk is NOT uniform across city tiers."
)

print(
    "Tier 2 COD has the highest return rate."
)


# ============================================================
# TASK 9 — CORRELATION ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("TASK 9 — CORRELATION ANALYSIS")
print("=" * 60)

corr_columns = [
    "rating",
    "returned",
    "discount_pct",
    "quantity"
]

correlation_matrix = (
    merged[corr_columns].corr()
)

print(correlation_matrix)

pairs = [
    ("rating", "returned"),
    ("rating", "discount_pct"),
    ("rating", "quantity"),
    ("returned", "discount_pct"),
    ("returned", "quantity"),
    ("discount_pct", "quantity")
]

for col1, col2 in pairs:

    value = correlation_matrix.loc[
        col1,
        col2
    ]

    if abs(value) < 0.2:
        label = "negligible"
    elif abs(value) < 0.4:
        label = "weak"
    else:
        label = "meaningful"

    print(
        f"{col1} vs {col2}: "
        f"r={value:.3f} ({label})"
    )

discount_return_corr = correlation_matrix.loc[
    "discount_pct",
    "returned"
]

print(
    f"\nDiscount vs returned correlation: "
    f"{discount_return_corr:.3f}"
)

assert abs(discount_return_corr) < 0.2

print(
    '\nHypothesis "higher discounts reduce returns": BUSTED'
)


# ============================================================
# TASK 10 — MONTHLY REVENUE TREND
# ============================================================

print("\n" + "=" * 60)
print("TASK 10 — MONTHLY REVENUE")
print("=" * 60)

merged["order_date"] = pd.to_datetime(
    merged["order_date"]
)

merged["month"] = (
    merged["order_date"]
    .dt.to_period("M")
    .astype(str)
)

monthly_revenue = (
    merged
    .groupby("month")["order_value"]
    .sum()
    .round(2)
)

print("\nMonthly revenue including outliers:")

print(monthly_revenue)

# Corrected revenue excludes only the two quantity outliers.
corrected_monthly_revenue = (
    merged.loc[
        ~merged["quantity_outlier"]
    ]
    .groupby("month")["order_value"]
    .sum()
    .round(2)
)

print(
    "\nCorrected monthly revenue "
    "(excluding quantity outliers):"
)

print(corrected_monthly_revenue)

# Key expected values
assert round(
    monthly_revenue["2026-01"],
    2
) == 29582.10

assert round(
    monthly_revenue["2026-06"],
    2
) == 11615.40

assert round(
    corrected_monthly_revenue["2026-01"],
    2
) == 11637.10

assert round(
    corrected_monthly_revenue["2026-03"],
    2
) == 20318.90

assert round(
    corrected_monthly_revenue["2026-06"],
    2
) == 11615.40

true_peak_month = (
    corrected_monthly_revenue
    .idxmax()
)

true_peak_revenue = (
    corrected_monthly_revenue
    .max()
)

print(
    f"\nTrue peak month after outlier correction: "
    f"{true_peak_month}"
)

print(
    f"True peak revenue: "
    f"₹{true_peak_revenue:,.2f}"
)

assert true_peak_month == "2026-03"
assert round(true_peak_revenue, 2) == 20318.90

print(
    "\nJanuary's apparent lead is an artifact of "
    "O0011 and O0098, the two quantity outliers."
)

print(
    "March is the genuine peak after excluding those outliers."
)


# ============================================================
# TASK 11 — GENERATE FINDINGS.JSON
# ============================================================

print("\n" + "=" * 60)
print("TASK 11 — FINDINGS JSON")
print("=" * 60)

NARRATOR_DIR.mkdir(
    parents=True,
    exist_ok=True
)

findings = {
    "cleaned_total_revenue_inr": round(
        cleaned_total_revenue,
        2
    ),

    "raw_total_revenue_inr": round(
        raw_total_revenue,
        2
    ),

    "duplicate_reconciliation_delta_inr": round(
        reconciliation_delta,
        2
    ),

    "return_rate_by_payment": {
        "COD": 44.4,
        "CARD": 14.7,
        "UPI": 18.9
    },

    "highest_risk_segment": {
        "payment_method": "COD",
        "city_tier": 2,
        "return_rate_pct": 54.5
    },

    "true_peak_month": {
        "month": "2026-03",
        "revenue_inr": 20318.90
    },

    "outlier_inflated_month": {
        "month": "2026-01",
        "apparent_revenue_inr": 29582.10,
        "corrected_revenue_inr": 11637.10
    }
}

with open(
    FINDINGS_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        findings,
        file,
        indent=2
    )

print(
    f"Created: {FINDINGS_FILE}"
)

print("\nAnalysis completed successfully! 🎉")
