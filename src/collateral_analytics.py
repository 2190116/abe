"""
Abe — Track A: Collateral Analytics
Deterministic tape analysis: pool summary, stratifications, concentrations, DQ checks.
"""
from __future__ import annotations
from datetime import date
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


@dataclass
class CollateralOutput:
    pool_summary: dict = field(default_factory=dict)
    stratifications: dict = field(default_factory=dict)
    concentrations: dict = field(default_factory=dict)
    dq_report: dict = field(default_factory=dict)
    field_mapping: dict = field(default_factory=dict)
    tape_date: str = ""

    def to_dict(self) -> dict:
        return self.__dict__


# ── Field mapping (hardcoded common aliases — LLM version in V1) ───────

DEFAULT_ALIASES = {
    "LN_ID": "asset_id", "loan_id": "asset_id", "account_id": "asset_id",
    "loan_number": "asset_id", "Contract ID": "asset_id",
    "BORROWER_ID": "obligor_id", "borrower_id": "obligor_id", "customer_id": "obligor_id",
    "LN_BAL_CUR": "current_balance", "balance": "current_balance",
    "outstanding_balance": "current_balance", "$ Recv": "current_balance",
    "Orig Prin Amt": "original_balance", "orig_balance": "original_balance",
    "original_amount": "original_balance", "funded_amount": "original_balance",
    "Int Rt": "interest_rate", "rate": "interest_rate", "coupon": "interest_rate",
    "note_rate": "interest_rate",
    "FICO_AT_ORIG": "credit_score", "fico": "credit_score", "fico_score": "credit_score",
    "STAT_CD": "delinquency_status", "status": "delinquency_status",
    "loan_status": "delinquency_status",
    "DPD": "days_past_due", "days_past_due": "days_past_due", "dpd": "days_past_due",
    "St": "geography", "state": "geography", "State": "geography",
    "Product": "product_type", "product": "product_type",
    "Orig_Dt": "origination_date", "orig_date": "origination_date",
    "origination_date": "origination_date",
    "Mat_Dt": "maturity_date", "maturity_date": "maturity_date", "maturity": "maturity_date",
    "Orig_Term": "original_term", "orig_term": "original_term",
    "Rem_Term": "remaining_term", "rem_term": "remaining_term",
    "CO_Flag": "charge_off_status", "chargeoff": "charge_off_status",
    "CO_Date": "charge_off_date",
    "Recovery_Amt": "recovery_amount", "recoveries": "recovery_amount",
}


def auto_map_fields(df: pd.DataFrame) -> dict:
    """Map borrower columns to standard fields using alias lookup."""
    mapping = {}
    for col in df.columns:
        std = DEFAULT_ALIASES.get(col) or DEFAULT_ALIASES.get(col.lower())
        if std:
            mapping[col] = std
    return mapping


# ── Data quality checks ────────────────────────────────────────────────

def run_data_quality_checks(df: pd.DataFrame, tape_date: date) -> list[dict]:
    checks = []
    n = len(df)

    # Duplicate IDs
    if "asset_id" in df.columns:
        dupes = int(df["asset_id"].duplicated().sum())
        checks.append({"check": "Duplicate asset_id", "severity": "blocking" if dupes > 0 else "pass",
                        "rows_affected": dupes, "pct": round(dupes / n * 100, 2)})

    # Missing balances
    if "current_balance" in df.columns:
        nulls = int(df["current_balance"].isna().sum())
        sev = "blocking" if nulls > n * 0.1 else ("material" if nulls > 0 else "pass")
        checks.append({"check": "Missing current_balance", "severity": sev,
                        "rows_affected": nulls, "pct": round(nulls / n * 100, 2)})

    # Negative balances
    if "current_balance" in df.columns:
        negs = int((df["current_balance"] < 0).sum())
        checks.append({"check": "Negative current_balance", "severity": "material" if negs > 0 else "pass",
                        "rows_affected": negs, "pct": round(negs / n * 100, 2)})

    # FICO zeros
    if "credit_score" in df.columns:
        zeros = int((df["credit_score"] == 0).sum())
        pct = zeros / n * 100
        sev = "material" if pct > 10 else ("informational" if pct > 0 else "pass")
        checks.append({"check": "FICO = 0 (likely missing)", "severity": sev,
                        "rows_affected": zeros, "pct": round(pct, 1)})

    # Origination after tape date
    if "origination_date" in df.columns:
        future = int((df["origination_date"] > pd.Timestamp(tape_date)).sum())
        checks.append({"check": "Origination after tape date", "severity": "blocking" if future > 0 else "pass",
                        "rows_affected": future, "pct": round(future / n * 100, 2)})

    # Balance > original
    if "current_balance" in df.columns and "original_balance" in df.columns:
        growth = int((df["current_balance"] > df["original_balance"] * 1.05).sum())
        sev = "material" if growth / n > 0.05 else ("informational" if growth > 0 else "pass")
        checks.append({"check": "Current > 1.05× original balance", "severity": sev,
                        "rows_affected": growth, "pct": round(growth / n * 100, 2)})

    return checks


# ── Pool summary ───────────────────────────────────────────────────────

def calculate_pool_summary(df: pd.DataFrame, tape_date: date) -> dict:
    total_bal = df["current_balance"].sum()
    pool = {
        "loan_count": len(df),
        "total_current_balance": round(total_bal, 2),
        "total_original_balance": round(df["original_balance"].sum(), 2),
        "average_current_balance": round(df["current_balance"].mean(), 2),
        "median_current_balance": round(df["current_balance"].median(), 2),
        "min_balance": round(df["current_balance"].min(), 2),
        "max_balance": round(df["current_balance"].max(), 2),
    }

    # WAC
    if "interest_rate" in df.columns:
        pool["wac"] = round((df["interest_rate"] * df["current_balance"]).sum() / total_bal, 6)

    # WAM
    if "remaining_term" in df.columns:
        pool["wam_months"] = round((df["remaining_term"] * df["current_balance"]).sum() / total_bal, 1)

    # WALA
    if "origination_date" in df.columns:
        mob = ((pd.Timestamp(tape_date) - df["origination_date"]).dt.days / 30.44)
        pool["wala_months"] = round((mob * df["current_balance"]).sum() / total_bal, 1)

    # WA FICO
    if "credit_score" in df.columns:
        valid = df[df["credit_score"] > 0]
        if len(valid) > 0:
            pool["wa_fico"] = round((valid["credit_score"] * valid["current_balance"]).sum() / valid["current_balance"].sum(), 0)
            pool["fico_coverage_pct"] = round(len(valid) / len(df) * 100, 1)
        else:
            pool["wa_fico"] = None
            pool["fico_coverage_pct"] = 0

    # Delinquency
    if "days_past_due" in df.columns:
        pool["dq_30plus_pct"] = round(df[df["days_past_due"] >= 30]["current_balance"].sum() / total_bal, 4)
        pool["dq_60plus_pct"] = round(df[df["days_past_due"] >= 60]["current_balance"].sum() / total_bal, 4)
        pool["dq_90plus_pct"] = round(df[df["days_past_due"] >= 90]["current_balance"].sum() / total_bal, 4)

    # Charge-offs
    if "charge_off_status" in df.columns:
        co = df[df["charge_off_status"] == True]
        pool["charge_off_count"] = len(co)
        pool["gross_charge_off_balance"] = round(co["original_balance"].sum(), 2)
        pool["cumulative_loss_rate"] = round(co["original_balance"].sum() / df["original_balance"].sum(), 4) if df["original_balance"].sum() > 0 else 0
        if "recovery_amount" in df.columns:
            pool["total_recoveries"] = round(co["recovery_amount"].sum(), 2)
            pool["net_loss_rate"] = round((co["original_balance"].sum() - co["recovery_amount"].sum()) / df["original_balance"].sum(), 4)

    return pool


# ── Stratifications ────────────────────────────────────────────────────

def calculate_stratifications(df: pd.DataFrame) -> dict:
    total_bal = df["current_balance"].sum()
    strats = {}

    # Balance distribution
    if "current_balance" in df.columns:
        bins = [0, 5000, 10000, 25000, 50000, 75000, float("inf")]
        labels = ["<$5K", "$5-10K", "$10-25K", "$25-50K", "$50-75K", ">$75K"]
        df["_bal_bucket"] = pd.cut(df["current_balance"], bins=bins, labels=labels)
        s = df.groupby("_bal_bucket", observed=True).agg(
            count=("asset_id", "count"), balance=("current_balance", "sum")).reset_index()
        s["pct_balance"] = (s["balance"] / total_bal * 100).round(1)
        strats["balance_distribution"] = s.rename(columns={"_bal_bucket": "bucket"}).to_dict("records")
        df.drop(columns=["_bal_bucket"], inplace=True)

    # Geography
    if "geography" in df.columns:
        g = df.groupby("geography").agg(count=("asset_id", "count"), balance=("current_balance", "sum"))
        g = g.sort_values("balance", ascending=False).head(10).reset_index()
        g["pct_balance"] = (g["balance"] / total_bal * 100).round(1)
        strats["geography_top10"] = g.to_dict("records")

    # Delinquency
    if "delinquency_status" in df.columns:
        d = df.groupby("delinquency_status").agg(count=("asset_id", "count"), balance=("current_balance", "sum")).reset_index()
        d["pct_balance"] = (d["balance"] / total_bal * 100).round(1)
        strats["delinquency"] = d.to_dict("records")

    # Vintage
    if "origination_date" in df.columns:
        df["_vintage_q"] = df["origination_date"].dt.to_period("Q").astype(str)
        v = df.groupby("_vintage_q").agg(
            count=("asset_id", "count"),
            orig_balance=("original_balance", "sum"),
            cur_balance=("current_balance", "sum")).reset_index()
        v.rename(columns={"_vintage_q": "vintage"}, inplace=True)
        strats["vintage"] = v.to_dict("records")
        df.drop(columns=["_vintage_q"], inplace=True)

    # Product
    if "product_type" in df.columns:
        p = df.groupby("product_type").agg(count=("asset_id", "count"), balance=("current_balance", "sum"))
        p = p.sort_values("balance", ascending=False).reset_index()
        p["pct_balance"] = (p["balance"] / total_bal * 100).round(1)
        strats["product"] = p.to_dict("records")

    return strats


# ── Concentrations ─────────────────────────────────────────────────────

def calculate_concentrations(df: pd.DataFrame) -> dict:
    total_bal = df["current_balance"].sum()
    conc = {}

    if "obligor_id" in df.columns:
        ob = df.groupby("obligor_id")["current_balance"].sum().sort_values(ascending=False)
        conc["unique_obligors"] = len(ob)
        conc["top_obligor_balance"] = round(float(ob.iloc[0]), 2)
        conc["top_obligor_pct"] = round(float(ob.iloc[0]) / total_bal * 100, 2)
        conc["top_10_obligor_pct"] = round(float(ob.head(10).sum()) / total_bal * 100, 2)
        shares = ob / total_bal
        conc["obligor_hhi"] = round(float((shares ** 2).sum() * 10000), 1)

    if "geography" in df.columns:
        geo = df.groupby("geography")["current_balance"].sum().sort_values(ascending=False)
        conc["top_state"] = str(geo.index[0])
        conc["top_state_pct"] = round(float(geo.iloc[0]) / total_bal * 100, 1)
        geo_shares = geo / total_bal
        conc["geo_hhi"] = round(float((geo_shares ** 2).sum() * 10000), 1)

    return conc


# ── Red flags (deterministic) ─────────────────────────────────────────

def generate_collateral_red_flags(pool: dict, concentrations: dict, dq_checks: list[dict]) -> list[dict]:
    flags = []

    # DQ-based flags
    for check in dq_checks:
        if check["severity"] == "blocking":
            flags.append({"severity": "CRITICAL", "title": f"Blocking DQ issue: {check['check']}",
                         "finding": f"{check['rows_affected']} rows affected ({check['pct']}%)"})

    # FICO missing
    fico_check = next((c for c in dq_checks if "FICO" in c["check"]), None)
    if fico_check and fico_check["pct"] > 10:
        flags.append({"severity": "CRITICAL", "title": f"{fico_check['pct']:.0f}% FICO scores missing (coded as 0)",
                      "finding": f"{fico_check['rows_affected']:,} loans have credit_score=0. FICO analytics unreliable."})

    # Delinquency
    dq_30 = pool.get("dq_30plus_pct", 0)
    if dq_30 > 0.10:
        flags.append({"severity": "CRITICAL", "title": f"30+ DPD at {dq_30:.1%}",
                      "finding": "Severely elevated delinquencies."})
    elif dq_30 > 0.05:
        flags.append({"severity": "HIGH", "title": f"30+ DPD at {dq_30:.1%}",
                      "finding": "Elevated delinquencies above 5% threshold."})

    # Concentration
    if concentrations.get("top_state_pct", 0) > 25:
        flags.append({"severity": "MEDIUM",
                      "title": f"{concentrations['top_state']} concentration at {concentrations['top_state_pct']}%",
                      "finding": "Top state exceeds 25% guideline."})

    # Low seasoning
    wala = pool.get("wala_months", 99)
    if wala < 12 and pool.get("cumulative_loss_rate", 0) < 0.02:
        flags.append({"severity": "HIGH", "title": f"Young pool (WALA {wala:.0f}mo) with low losses — may be understated",
                      "finding": "Losses typically emerge at 6-18 MOB. Current loss rate may understate lifetime."})

    return flags


# ── Full pipeline ──────────────────────────────────────────────────────

def run_collateral_pipeline(tape_path: str, tape_date: date) -> CollateralOutput:
    """Run the full Track A pipeline on a loan tape."""
    # Load
    path = str(tape_path)
    if path.endswith(".csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)

    # Map fields
    mapping = auto_map_fields(df)
    df = df.rename(columns=mapping)

    # Parse dates
    for col in ["origination_date", "maturity_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # DQ checks
    dq_checks = run_data_quality_checks(df, tape_date)

    # Pool summary
    pool = calculate_pool_summary(df, tape_date)

    # Stratifications
    strats = calculate_stratifications(df)

    # Concentrations
    conc = calculate_concentrations(df)

    return CollateralOutput(
        pool_summary=pool,
        stratifications=strats,
        concentrations=conc,
        dq_report={"checks": dq_checks},
        field_mapping=mapping,
        tape_date=tape_date.isoformat(),
    )
