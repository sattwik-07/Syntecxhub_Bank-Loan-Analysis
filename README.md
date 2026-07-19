# Bank Loan Analysis — Syntecxhub Internship

An end-to-end analysis of a 38,576-loan lending book: cleaning the raw data, computing portfolio KPIs, classifying loans as Good vs. Bad, and surfacing the risk factors that drive charge-offs — all delivered through a self-contained, interactive dashboard.
Syntecxhub Data Analydid Internship - Task 4

**Live deliverable:** `Syntecxhub_Bank_Loan_Analysis_Dashboard.html` — just open it in any browser. No server, no internet connection, and no dependencies required; every library and every data point is bundled directly into the file.

---

## What this project does

Per the Syntecxhub Task 4 brief, this project:

- Analyzes bank loan data — applications, funded amount, and repayments
- Calculates core KPIs: total applications, total funded amount, total amount received, average interest rate, average DTI
- Classifies loans into **Good Loan** (Fully Paid + Current) vs. **Bad Loan** (Charged Off)
- Performs trend analysis by time (monthly), region (state), and customer segment
- Identifies the factors that most affect approval risk and repayment (grade, term, DTI, income)
- Ships as an interactive dashboard for exploring all of the above

## Dataset

| | |
|---|---|
| Rows | 38,576 loan applications |
| Period | January 2021 – December 2021 |
| Source | `dataset.csv` (bank loan book: applications, funded amount, repayments) |

**Columns:** `id`, `address_state`, `application_type`, `emp_length`, `emp_title`, `grade`, `sub_grade`, `home_ownership`, `issue_date`, `last_credit_pull_date`, `last_payment_date`, `loan_status`, `next_payment_date`, `member_id`, `purpose`, `term`, `verification_status`, `annual_income`, `dti`, `installment`, `int_rate`, `loan_amount`, `total_acc`, `total_payment`

## Repository structure

```
Syntecxhub_Bank_Loan_Analysis/
├── Syntecxhub_Bank_Loan_Analysis_Dashboard.html   # the deliverable — open this
├── data_pipeline.py                               # cleans data, computes all KPIs/aggregates
├── dataset.csv                                    # raw loan book
└── README.md
```

## How to view the dashboard

Just double-click `Syntecxhub_Bank_Loan_Analysis_Dashboard.html`, or open it from a browser's File menu. That's it — the data and the charting library are embedded in the file itself.

## How the pipeline works

`data_pipeline.py` reads `dataset.csv`, cleans and type-casts every field, engineers derived features (loan category, DTI/income buckets, issue month), computes every aggregate the dashboard needs, and writes a single JSON bundle that gets embedded into the HTML.

```bash
pip install pandas numpy
python data_pipeline.py
```

The dashboard also has a **Data Source** tab: drop in a different CSV with the same schema and the entire dashboard — every KPI, chart, and table — recomputes live in the browser using the same logic as the Python pipeline.

## Dashboard sections

| Tab | What's in it |
|---|---|
| **Overview** | Top-line KPIs, Good vs. Bad loan split, loan status breakdown, auto-generated key insights |
| **Trends** | Monthly application volume and funded vs. received amounts |
| **Regional** | Applications and dollars by state, ranked and tabulated |
| **Risk Factors** | Charge-off rate by grade, term, DTI bucket, and income bracket; good-vs-bad rate/DTI comparison |
| **Segments** | Breakdown by purpose, home ownership, verification status, employment length |
| **Data Explorer** | Searchable, sortable, paginated loan-level table |
| **Data Source** | Upload your own CSV to re-run the analysis, or reset to the default book |

## Key findings

- **86.2%** of the book is performing (Good Loan); **13.8%** charged off.
- Charge-off rate climbs monotonically with risk grade: **5.7%** for Grade A vs. **31.3%** for Grade G.
- **60-month** loans default at roughly **double** the rate of **36-month** loans (22.3% vs. 10.7%).
- Bad loans carry a higher average interest rate and DTI at origination than good loans.
- **California** leads the book in both application volume and dollars funded.

## Tech stack

- **Python** (pandas, numpy) — data cleaning and aggregation
- **HTML / CSS / vanilla JavaScript** — dashboard shell and interactivity
- **Chart.js** — charts (bundled locally)
- **PapaParse** — client-side CSV parsing for the upload feature (bundled locally)

---

## 👤 Author

Sattwik Sahu

---

Submitted as part of the **Syntecxhub Internship Program** — Data Analysis Track.

**Connect:** [Syntecxhub](https://www.syntecxhub.com) | `@Syntecxhub`
