"""Create sample test fixtures for the Abe pipeline."""
import pandas as pd
from pathlib import Path

FIXTURE_DIR = Path("fixtures")
FIXTURE_DIR.mkdir(exist_ok=True)

# ── Corporate Financials Template ──────────────────────────────────────

is_data = {
    "Field": [
        "Period End Date", "Statement Type",
        "Total Revenue", "Interest / Fee Income", "Gain on Sale Income", "Other Income",
        "Cost of Revenue / Provision", "Total Operating Expenses",
        "Depreciation & Amortization", "Interest Expense", "Income Tax", "Net Income",
        "Non-Recurring Items", "Stock-Based Compensation",
    ],
    "FY 2022": [
        "2022-12-31", "audited",
        8500000, 7200000, 500000, 800000,
        2800000, 5500000,
        200000, 1200000, 100000, 500000,
        0, 100000,
    ],
    "FY 2023": [
        "2023-12-31", "audited",
        10200000, 8800000, 600000, 800000,
        3400000, 6800000,
        250000, 1500000, 50000, 200000,
        300000, 150000,
    ],
    "LTM 2024": [
        "2024-12-31", "reviewed",
        12500000, 10800000, 700000, 1000000,
        4200000, 8300000,
        300000, 1800000, 0, -350000,
        150000, 200000,
    ],
}

bs_data = {
    "Field": [
        "Period End Date",
        "Cash & Equivalents", "Restricted Cash",
        "Loans Receivable / Portfolio", "Other Current Assets",
        "Total Assets", "Intangible Assets", "Goodwill",
        "Warehouse Lines (Drawn)", "Term Debt", "Subordinated Debt",
        "Other Liabilities", "Total Liabilities", "Total Equity",
    ],
    "FY 2022": [
        "2022-12-31",
        5200000, 500000,
        45000000, 1000000,
        52200000, 1500000, 0,
        38000000, 0, 0,
        3000000, 41500000, 10700000,
    ],
    "FY 2023": [
        "2023-12-31",
        4800000, 600000,
        58000000, 1200000,
        65200000, 2000000, 0,
        48000000, 0, 0,
        3500000, 52000000, 13200000,
    ],
    "LTM 2024": [
        "2024-12-31",
        4200000, 800000,
        72000000, 1500000,
        79000000, 2300000, 0,
        60000000, 0, 0,
        4000000, 64500000, 14500000,
    ],
}

is_df = pd.DataFrame(is_data)
bs_df = pd.DataFrame(bs_data)

with pd.ExcelWriter(FIXTURE_DIR / "corporate_financials.xlsx", engine="openpyxl") as w:
    is_df.to_excel(w, sheet_name="Income_Statement", index=False, header=False)
    bs_df.to_excel(w, sheet_name="Balance_Sheet", index=False, header=False)

print("✓ corporate_financials.xlsx created")

# ── Funding Facilities Template ────────────────────────────────────────

funding_data = {
    "Lender": ["Regional Bank"],
    "Facility Type": ["warehouse"],
    "Committed Amount": [25000000],
    "Drawn Amount": [22000000],
    "Maturity Date": ["2026-06-30"],
    "Pricing Description": ["SOFR + 350bps"],
    "Advance Rate": [0.85],
    "Key Covenants": ["Min TNW $5M; Max D/E 8x; Min IC 1.5x"],
    "Status": ["active"],
    "Notes": ["Renewable annually"],
}

fd_df = pd.DataFrame(funding_data)
fd_df.to_excel(FIXTURE_DIR / "funding_facilities.xlsx", index=False, engine="openpyxl")
print("✓ funding_facilities.xlsx created")

# ── Sample Loan Tape ──────────────────────────────────────────────────

import random
import datetime

random.seed(42)
N = 5000

states = ["CA","CA","CA","CA","CA","CA","TX","TX","TX","FL","FL","NY","NY","IL","OH","PA","GA","NC","MI","AZ","WA","OR","CO","MA","VA","NJ","MD","TN","MN","WI"]
products = ["prime_36mo","prime_48mo","prime_60mo","near_prime_36mo","near_prime_48mo"]
statuses = ["current"]*88 + ["1-29"]*4 + ["30-59"]*3 + ["60-89"]*2 + ["90-119"]*1 + ["120+"]*1 + ["charge_off"]*1

tape_rows = []
for i in range(N):
    orig_date = datetime.date(2022,1,1) + datetime.timedelta(days=random.randint(0, 1000))
    orig_bal = round(random.uniform(3000, 65000), 2)
    # Some amortization
    months_elapsed = (datetime.date(2025,4,30) - orig_date).days / 30.44
    amort_factor = max(0.3, 1 - (months_elapsed / random.uniform(36, 72)))
    cur_bal = round(orig_bal * amort_factor, 2)
    rate = round(random.uniform(0.06, 0.18), 4)
    fico = random.choice([0]*17 + list(range(580, 820)))  # ~17% zeros (missing)
    status = random.choice(statuses)
    dpd = {"current":0,"1-29":random.randint(1,29),"30-59":random.randint(30,59),
           "60-89":random.randint(60,89),"90-119":random.randint(90,119),
           "120+":random.randint(120,180),"charge_off":random.randint(120,365)}.get(status, 0)
    state = random.choice(states)
    product = random.choice(products)
    term = int(product.split("_")[-1].replace("mo",""))
    mat_date = orig_date + datetime.timedelta(days=term*30)
    remaining = max(0, int((mat_date - datetime.date(2025,4,30)).days / 30.44))
    co_flag = status == "charge_off"
    co_date = (datetime.date(2025,4,30) - datetime.timedelta(days=random.randint(10,180))).isoformat() if co_flag else ""
    recovery = round(orig_bal * random.uniform(0.1, 0.4), 2) if co_flag else 0

    tape_rows.append({
        "LN_ID": f"LN-{100000+i}",
        "BORROWER_ID": f"OB-{random.randint(10000, 80000)}",
        "LN_BAL_CUR": cur_bal,
        "Orig Prin Amt": orig_bal,
        "Int Rt": rate,
        "FICO_AT_ORIG": fico,
        "STAT_CD": status,
        "DPD": dpd,
        "St": state,
        "Product": product,
        "Orig_Dt": orig_date.isoformat(),
        "Mat_Dt": mat_date.isoformat(),
        "Orig_Term": term,
        "Rem_Term": remaining,
        "CO_Flag": co_flag,
        "CO_Date": co_date,
        "Recovery_Amt": recovery,
    })

tape_df = pd.DataFrame(tape_rows)
tape_df.to_csv(FIXTURE_DIR / "acme_tape_apr2025.csv", index=False)
print(f"✓ acme_tape_apr2025.csv created ({len(tape_df)} loans)")
