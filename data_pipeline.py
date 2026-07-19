"""
SYNTECXHUB PROJECT 1 - BANK LOAN ANALYSIS
Data pipeline: cleans the raw loan book, computes KPIs, classifies loans,
runs trend / regional / factor analysis, and exports a single JSON bundle
consumed by the interactive dashboard (dashboard.html).

Author: Sattwik | Command Center
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime

RAW_PATH = "/mnt/user-data/uploads/dataset.csv"
OUT_PATH = "/home/claude/project1/dashboard_data.json"

# ----------------------------------------------------------------------
# 1. LOAD + CLEAN
# ----------------------------------------------------------------------
df = pd.read_csv(RAW_PATH)

date_cols = ["issue_date", "last_credit_pull_date", "last_payment_date", "next_payment_date"]
for c in date_cols:
    df[c] = pd.to_datetime(df[c], format="%d-%m-%Y", errors="coerce")

df["term_months"] = df["term"].str.extract(r"(\d+)").astype(int)
df["emp_title"] = df["emp_title"].fillna("Not Specified")

# Good Loan  = Fully Paid or Current (performing / performed as agreed)
# Bad Loan   = Charged Off (defaulted)
df["loan_category"] = np.where(df["loan_status"].eq("Charged Off"), "Bad Loan", "Good Loan")

df["issue_month"] = df["issue_date"].dt.to_period("M").astype(str)
df["issue_month_num"] = df["issue_date"].dt.month
df["issue_month_name"] = df["issue_date"].dt.strftime("%b")

# DTI bucket for risk-factor analysis
df["dti_bucket"] = pd.cut(
    df["dti"], bins=[-0.01, 0.1, 0.2, 0.3, 1],
    labels=["0-10%", "10-20%", "20-30%", "30%+"]
)
df["income_bucket"] = pd.cut(
    df["annual_income"],
    bins=[0, 30000, 60000, 90000, 120000, np.inf],
    labels=["<30K", "30-60K", "60-90K", "90-120K", "120K+"]
)

# ----------------------------------------------------------------------
# 2. TOP-LEVEL KPIs
# ----------------------------------------------------------------------
total_applications = len(df)
total_funded_amount = df["loan_amount"].sum()
total_amount_received = df["total_payment"].sum()
avg_int_rate = df["int_rate"].mean() * 100
avg_dti = df["dti"].mean() * 100
mtd_applications = int(df[df["issue_month_num"] == df["issue_month_num"].max()].shape[0])

good_df = df[df["loan_category"] == "Good Loan"]
bad_df = df[df["loan_category"] == "Bad Loan"]

kpis = {
    "total_applications": int(total_applications),
    "total_funded_amount": float(total_funded_amount),
    "total_amount_received": float(total_amount_received),
    "avg_interest_rate": round(float(avg_int_rate), 2),
    "avg_dti": round(float(avg_dti), 2),
    "good_loan": {
        "applications": int(len(good_df)),
        "pct": round(len(good_df) / total_applications * 100, 2),
        "funded_amount": float(good_df["loan_amount"].sum()),
        "amount_received": float(good_df["total_payment"].sum()),
    },
    "bad_loan": {
        "applications": int(len(bad_df)),
        "pct": round(len(bad_df) / total_applications * 100, 2),
        "funded_amount": float(bad_df["loan_amount"].sum()),
        "amount_received": float(bad_df["total_payment"].sum()),
    },
}

# ----------------------------------------------------------------------
# 3. LOAN STATUS BREAKDOWN
# ----------------------------------------------------------------------
status_breakdown = (
    df.groupby("loan_status")
    .agg(applications=("id", "count"), funded_amount=("loan_amount", "sum"), amount_received=("total_payment", "sum"))
    .reset_index()
    .to_dict(orient="records")
)

# ----------------------------------------------------------------------
# 4. TREND ANALYSIS (monthly)
# ----------------------------------------------------------------------
monthly = (
    df.groupby(["issue_month_num", "issue_month_name"])
    .agg(applications=("id", "count"), funded_amount=("loan_amount", "sum"), amount_received=("total_payment", "sum"))
    .reset_index()
    .sort_values("issue_month_num")
)
monthly_trend = monthly.drop(columns="issue_month_num").rename(columns={"issue_month_name": "month"}).to_dict(orient="records")

# ----------------------------------------------------------------------
# 5. REGIONAL ANALYSIS (by state)
# ----------------------------------------------------------------------
state_analysis = (
    df.groupby("address_state")
    .agg(applications=("id", "count"), funded_amount=("loan_amount", "sum"), amount_received=("total_payment", "sum"))
    .reset_index()
    .sort_values("applications", ascending=False)
    .rename(columns={"address_state": "state"})
    .to_dict(orient="records")
)

# ----------------------------------------------------------------------
# 6. CUSTOMER / SEGMENT ANALYSIS
# ----------------------------------------------------------------------
def seg_summary(col):
    grp = df.groupby(col)
    out = grp.agg(applications=("id", "count"), funded_amount=("loan_amount", "sum")).reset_index()
    bad_rate = df.groupby(col)["loan_category"].apply(lambda s: (s == "Bad Loan").mean() * 100).reset_index(name="bad_rate")
    out = out.merge(bad_rate, on=col)
    out = out.rename(columns={col: "segment"})
    out["bad_rate"] = out["bad_rate"].round(2)
    return out.sort_values("applications", ascending=False).to_dict(orient="records")

by_term = seg_summary("term")
by_purpose = seg_summary("purpose")
by_grade = seg_summary("grade")
by_home_ownership = seg_summary("home_ownership")
by_verification = seg_summary("verification_status")
by_emp_length = seg_summary("emp_length")

# fix emp_length ordering
emp_order = ["< 1 year", "1 year", "2 years", "3 years", "4 years", "5 years",
             "6 years", "7 years", "8 years", "9 years", "10+ years"]
by_emp_length = sorted(by_emp_length, key=lambda r: emp_order.index(r["segment"]) if r["segment"] in emp_order else 99)

# ----------------------------------------------------------------------
# 7. RISK FACTOR ANALYSIS (what drives Charged Off / bad loans)
# ----------------------------------------------------------------------
by_dti_bucket = df.groupby("dti_bucket", observed=True)["loan_category"].apply(
    lambda s: (s == "Bad Loan").mean() * 100
).reset_index(name="bad_rate")
by_dti_bucket["bad_rate"] = by_dti_bucket["bad_rate"].round(2)
by_dti_bucket = by_dti_bucket.rename(columns={"dti_bucket": "segment"}).to_dict(orient="records")

by_income_bucket = df.groupby("income_bucket", observed=True)["loan_category"].apply(
    lambda s: (s == "Bad Loan").mean() * 100
).reset_index(name="bad_rate")
by_income_bucket["bad_rate"] = by_income_bucket["bad_rate"].round(2)
by_income_bucket = by_income_bucket.rename(columns={"income_bucket": "segment"}).to_dict(orient="records")

grade_bad_rate = df.groupby("grade")["loan_category"].apply(lambda s: (s == "Bad Loan").mean() * 100).reset_index(name="bad_rate")
grade_bad_rate["bad_rate"] = grade_bad_rate["bad_rate"].round(2)
grade_bad_rate = grade_bad_rate.sort_values("grade").rename(columns={"grade": "segment"}).to_dict(orient="records")

term_bad_rate = df.groupby("term")["loan_category"].apply(lambda s: (s == "Bad Loan").mean() * 100).reset_index(name="bad_rate")
term_bad_rate["bad_rate"] = term_bad_rate["bad_rate"].round(2)
term_bad_rate = term_bad_rate.rename(columns={"term": "segment"}).to_dict(orient="records")

# average interest rate: good vs bad
rate_comparison = {
    "good_loan_avg_rate": round(float(good_df["int_rate"].mean() * 100), 2),
    "bad_loan_avg_rate": round(float(bad_df["int_rate"].mean() * 100), 2),
    "good_loan_avg_dti": round(float(good_df["dti"].mean() * 100), 2),
    "bad_loan_avg_dti": round(float(bad_df["dti"].mean() * 100), 2),
}

# ----------------------------------------------------------------------
# 8. RAW ROW SAMPLE (for data-explorer table in the dashboard)
# ----------------------------------------------------------------------
table_cols = ["id", "address_state", "purpose", "grade", "term", "emp_length",
              "home_ownership", "issue_date", "loan_status", "loan_category",
              "loan_amount", "int_rate", "annual_income", "dti", "total_payment"]
table_df = df[table_cols].copy()
table_df["issue_date"] = table_df["issue_date"].dt.strftime("%Y-%m-%d")
table_df["int_rate"] = (table_df["int_rate"] * 100).round(2)
table_df["dti"] = (table_df["dti"] * 100).round(2)

# Cap the row-level explorer table so the dashboard stays lightweight;
# every aggregate/chart above is still computed on the FULL 38,576-row dataset.
MAX_TABLE_ROWS = 3000
if len(table_df) > MAX_TABLE_ROWS:
    table_sample = table_df.sample(n=MAX_TABLE_ROWS, random_state=42).sort_values("id")
else:
    table_sample = table_df
records = table_sample.to_dict(orient="records")

# ----------------------------------------------------------------------
# 9. BUNDLE + EXPORT
# ----------------------------------------------------------------------
bundle = {
    "meta": {
        "generated_at": datetime.now().isoformat(),
        "source_file": "dataset.csv",
        "row_count": int(total_applications),
        "date_range": [df["issue_date"].min().strftime("%Y-%m-%d"), df["issue_date"].max().strftime("%Y-%m-%d")],
    },
    "kpis": kpis,
    "status_breakdown": status_breakdown,
    "monthly_trend": monthly_trend,
    "state_analysis": state_analysis,
    "by_term": by_term,
    "by_purpose": by_purpose,
    "by_grade": by_grade,
    "by_home_ownership": by_home_ownership,
    "by_verification": by_verification,
    "by_emp_length": by_emp_length,
    "by_dti_bucket": by_dti_bucket,
    "by_income_bucket": by_income_bucket,
    "grade_bad_rate": grade_bad_rate,
    "term_bad_rate": term_bad_rate,
    "rate_comparison": rate_comparison,
    "records": records,
}

with open(OUT_PATH, "w") as f:
    json.dump(bundle, f, default=str)

print("Pipeline complete.")
print(f"Rows processed: {total_applications}")
print(f"Output: {OUT_PATH}")
print(f"JSON size: {len(json.dumps(bundle, default=str)) / 1_000_000:.2f} MB")
