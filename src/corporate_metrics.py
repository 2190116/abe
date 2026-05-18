"""
Corporate Financial Metrics Module
ABF Deal Screen MVP — Track B

Calculates 15 financial metrics from structured corporate financials template.
All calculations are deterministic. No LLM calls.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


@dataclass
class MetricFlag:
    metric: str
    severity: Severity
    message: str
    value: Any = None
    threshold: Any = None


@dataclass
class FinancialMetrics:
    """All 15 corporate financial metrics for the deal screen."""

    as_of_date: str | None = None
    statement_type: str | None = None

    # 1. Revenue growth
    revenue_current: float | None = None
    revenue_prior: float | None = None
    revenue_growth_yoy: float | None = None

    # 2. EBITDA
    ebitda_gaap: float | None = None
    ebitda_adjusted: float | None = None
    ebitda_margin: float | None = None
    ebitda_addbacks: list[dict] = field(default_factory=list)

    # 3. Net income
    net_income: float | None = None
    net_margin: float | None = None

    # 4. Cash
    cash_unrestricted: float | None = None
    cash_restricted: float | None = None
    cash_total: float | None = None

    # 5. Debt
    total_debt: float | None = None
    warehouse_drawn: float | None = None
    term_debt: float | None = None
    sub_debt: float | None = None

    # 6. TNW
    tnw: float | None = None
    total_equity: float | None = None
    intangibles: float | None = None
    goodwill: float | None = None

    # 7. Burn rate
    monthly_burn: float | None = None
    annualized_burn: float | None = None
    profitable: bool = False

    # 8. Runway
    runway_months: float | None = None

    # 9-10. Leverage
    debt_equity: float | None = None
    debt_ebitda: float | None = None
    debt_ebitda_note: str | None = None

    # 11. Coverage
    interest_coverage: float | None = None
    interest_expense: float | None = None

    # 12. Funding utilization (from funding template, calculated externally)
    funding_utilization: float | None = None

    # 13. Maturity wall (from funding template, calculated externally)
    nearest_maturity: str | None = None
    months_to_nearest: int | None = None
    facilities_maturing_12mo: int | None = None
    amount_maturing_12mo: float | None = None

    # 14. Covenant headroom (from funding template, calculated externally)
    covenant_headroom: list[dict] = field(default_factory=list)

    # 15. Equity cushion
    equity_cushion: float | None = None
    portfolio_balance: float | None = None

    # Flags
    flags: list[MetricFlag] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dict."""
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, list) and v and isinstance(v[0], MetricFlag):
                result[k] = [
                    {"metric": f.metric, "severity": f.severity.value,
                     "message": f.message, "value": f.value, "threshold": f.threshold}
                    for f in v
                ]
            elif isinstance(v, Severity):
                result[k] = v.value
            else:
                result[k] = v
        return result


# ---------------------------------------------------------------------------
# Template loader
# ---------------------------------------------------------------------------

def load_financials_template(file_path: str | Path) -> dict:
    """
    Load the corporate_financials.xlsx template.

    Returns:
        {
            "income_statement": {period_label: {field: value, ...}, ...},
            "balance_sheet": {period_label: {field: value, ...}, ...},
            "periods": [period_labels in chronological order]
        }
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Financials template not found: {path}")
    if path.suffix not in (".xlsx", ".xls"):
        raise ValueError(f"Expected .xlsx or .xls, got {path.suffix}")

    # Read both sheets
    try:
        is_df = pd.read_excel(path, sheet_name="Income_Statement", header=None)
    except Exception as e:
        raise ValueError(f"Cannot read Income_Statement sheet: {e}") from e

    try:
        bs_df = pd.read_excel(path, sheet_name="Balance_Sheet", header=None)
    except Exception as e:
        raise ValueError(f"Cannot read Balance_Sheet sheet: {e}") from e

    income_statement = _parse_financial_sheet(is_df)
    balance_sheet = _parse_financial_sheet(bs_df)

    # Determine chronological period order from income statement
    periods = list(income_statement.keys())

    return {
        "income_statement": income_statement,
        "balance_sheet": balance_sheet,
        "periods": periods,
    }


def _parse_financial_sheet(df: pd.DataFrame) -> dict:
    """
    Parse a financial sheet where column 0 is field names and
    columns 1..N are period values. Row 0 is expected to contain
    the period end dates or period labels.
    """
    # First column = field names, remaining columns = periods
    # Row 0 should contain period identifiers (dates or labels)
    period_headers = []
    for col_idx in range(1, len(df.columns)):
        raw = df.iloc[0, col_idx]
        if pd.isna(raw):
            continue
        if isinstance(raw, datetime):
            period_headers.append((col_idx, raw.strftime("%Y-%m-%d")))
        else:
            period_headers.append((col_idx, str(raw).strip()))

    if not period_headers:
        raise ValueError("No period headers found in row 0")

    result = {}
    for col_idx, period_label in period_headers:
        period_data = {}
        for row_idx in range(1, len(df)):
            field_name = df.iloc[row_idx, 0]
            if pd.isna(field_name):
                continue
            field_name = str(field_name).strip()
            value = df.iloc[row_idx, col_idx]
            if pd.isna(value):
                period_data[field_name] = None
            elif isinstance(value, (int, float)):
                period_data[field_name] = float(value)
            else:
                # Try to parse as number
                try:
                    cleaned = str(value).replace(",", "").replace("$", "").replace("(", "-").replace(")", "").strip()
                    period_data[field_name] = float(cleaned)
                except (ValueError, TypeError):
                    period_data[field_name] = str(value).strip()
        result[period_label] = period_data

    return result


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# Fields expected in each sheet (required marked True)
IS_REQUIRED_FIELDS = {
    "Total Revenue": True,
    "Total Operating Expenses": True,
    "Depreciation & Amortization": True,
    "Interest Expense": True,
    "Income Tax": True,
    "Net Income": True,
}

BS_REQUIRED_FIELDS = {
    "Cash & Equivalents": True,
    "Loans Receivable / Portfolio": True,
    "Total Assets": True,
    "Warehouse Lines (Drawn)": True,
    "Term Debt": True,
    "Total Liabilities": True,
    "Total Equity": True,
}


def validate_financials(data: dict) -> ValidationResult:
    """Validate loaded financial data for completeness and consistency."""
    errors = []
    warnings = []

    periods = data.get("periods", [])
    if len(periods) < 2:
        errors.append(f"At least 2 periods required, found {len(periods)}")

    # Check required fields in income statement
    for period in periods:
        is_data = data["income_statement"].get(period, {})
        for field_name, required in IS_REQUIRED_FIELDS.items():
            if required and (field_name not in is_data or is_data[field_name] is None):
                errors.append(f"Missing required field '{field_name}' in Income Statement period {period}")

    # Check required fields in balance sheet
    for period in periods:
        bs_data = data["balance_sheet"].get(period, {})
        for field_name, required in BS_REQUIRED_FIELDS.items():
            if required and (field_name not in bs_data or bs_data[field_name] is None):
                errors.append(f"Missing required field '{field_name}' in Balance Sheet period {period}")

    # Balance sheet must balance: Total Assets ≈ Total Liabilities + Total Equity
    for period in periods:
        bs = data["balance_sheet"].get(period, {})
        total_assets = bs.get("Total Assets")
        total_liabilities = bs.get("Total Liabilities")
        total_equity = bs.get("Total Equity")
        if all(v is not None for v in [total_assets, total_liabilities, total_equity]):
            diff = abs(total_assets - (total_liabilities + total_equity))
            if diff > 1000:
                errors.append(
                    f"Balance sheet does not balance in period {period}: "
                    f"Assets ({total_assets:,.0f}) ≠ Liabilities ({total_liabilities:,.0f}) + "
                    f"Equity ({total_equity:,.0f}). Difference: {diff:,.0f}"
                )
            elif diff > 0:
                warnings.append(
                    f"Minor balance sheet rounding difference in period {period}: ${diff:,.0f}"
                )

    # Check for negative total assets
    for period in periods:
        bs = data["balance_sheet"].get(period, {})
        if bs.get("Total Assets") is not None and bs["Total Assets"] < 0:
            errors.append(f"Negative Total Assets in period {period}")
        if bs.get("Total Equity") is not None and bs["Total Equity"] < 0:
            warnings.append(f"Negative Total Equity in period {period} — this is a significant red flag")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Metric calculations
# ---------------------------------------------------------------------------

def _safe_div(numerator: float | None, denominator: float | None, cap: float = 99.9) -> float | None:
    """Safe division. Returns None if inputs are None, caps at ±cap."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    result = numerator / denominator
    return max(min(result, cap), -cap)


def _get(data: dict, field_name: str, default: float | None = None) -> float | None:
    """Get a numeric field from a period dict, returning default if missing."""
    val = data.get(field_name)
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    return default


def calculate_financial_metrics(financials: dict) -> FinancialMetrics:
    """
    Calculate all 15 financial metrics from validated financials data.

    Args:
        financials: Output of load_financials_template(), validated.

    Returns:
        FinancialMetrics with all calculated values and flags.
    """
    metrics = FinancialMetrics()
    flags: list[MetricFlag] = []

    periods = financials["periods"]
    latest_period = periods[-1]
    prior_period = periods[-2] if len(periods) >= 2 else None

    is_latest = financials["income_statement"].get(latest_period, {})
    is_prior = financials["income_statement"].get(prior_period, {}) if prior_period else {}
    bs_latest = financials["balance_sheet"].get(latest_period, {})

    metrics.as_of_date = latest_period
    metrics.statement_type = _get_string(bs_latest, "Statement Type")

    # -----------------------------------------------------------------------
    # 1. Revenue Growth
    # -----------------------------------------------------------------------
    revenue_current = _get(is_latest, "Total Revenue")
    revenue_prior = _get(is_prior, "Total Revenue")
    metrics.revenue_current = revenue_current
    metrics.revenue_prior = revenue_prior

    if revenue_current is not None and revenue_prior is not None and revenue_prior != 0:
        metrics.revenue_growth_yoy = (revenue_current - revenue_prior) / abs(revenue_prior)
    else:
        metrics.revenue_growth_yoy = None

    if metrics.revenue_growth_yoy is not None:
        if metrics.revenue_growth_yoy < 0:
            flags.append(MetricFlag("revenue_growth", Severity.HIGH,
                f"Revenue declined {metrics.revenue_growth_yoy:.1%} YoY",
                metrics.revenue_growth_yoy, 0.0))
        elif metrics.revenue_growth_yoy > 0.50:
            flags.append(MetricFlag("revenue_growth", Severity.MEDIUM,
                f"Hyper-growth ({metrics.revenue_growth_yoy:.1%} YoY) — assess sustainability",
                metrics.revenue_growth_yoy, 0.50))

    # -----------------------------------------------------------------------
    # 2. EBITDA
    # -----------------------------------------------------------------------
    net_income = _get(is_latest, "Net Income")
    interest_expense = _get(is_latest, "Interest Expense", 0)
    income_tax = _get(is_latest, "Income Tax", 0)
    da = _get(is_latest, "Depreciation & Amortization", 0)

    if net_income is not None:
        ebitda_gaap = net_income + interest_expense + income_tax + da
        metrics.ebitda_gaap = ebitda_gaap

        # Adjusted EBITDA
        non_recurring = _get(is_latest, "Non-Recurring Items", 0)
        sbc = _get(is_latest, "Stock-Based Compensation", 0)
        ebitda_adjusted = ebitda_gaap + non_recurring + sbc
        metrics.ebitda_adjusted = ebitda_adjusted

        addbacks = []
        if non_recurring:
            addbacks.append({"item": "Non-Recurring Items", "amount": non_recurring})
        if sbc:
            addbacks.append({"item": "Stock-Based Compensation", "amount": sbc})
        metrics.ebitda_addbacks = addbacks

        if revenue_current and revenue_current > 0:
            metrics.ebitda_margin = ebitda_gaap / revenue_current

        if ebitda_gaap < 0:
            flags.append(MetricFlag("ebitda", Severity.HIGH,
                f"Negative EBITDA (${ebitda_gaap:,.0f})", ebitda_gaap, 0))
        if ebitda_adjusted > 0 and ebitda_gaap > 0 and ebitda_adjusted > ebitda_gaap * 1.5:
            flags.append(MetricFlag("ebitda", Severity.MEDIUM,
                "Adjusted EBITDA is >1.5× GAAP EBITDA — large addbacks",
                ebitda_adjusted, ebitda_gaap * 1.5))

    # -----------------------------------------------------------------------
    # 3. Net Income
    # -----------------------------------------------------------------------
    metrics.net_income = net_income
    if revenue_current and revenue_current > 0 and net_income is not None:
        metrics.net_margin = net_income / revenue_current

    if net_income is not None and net_income < 0:
        # Check if prior was also negative (widening losses)
        ni_prior = _get(is_prior, "Net Income")
        if ni_prior is not None and ni_prior < 0 and net_income < ni_prior:
            flags.append(MetricFlag("net_income", Severity.HIGH,
                f"Net losses widening: ${net_income:,.0f} vs. prior ${ni_prior:,.0f}",
                net_income))
        elif ni_prior is not None and ni_prior >= 0:
            flags.append(MetricFlag("net_income", Severity.HIGH,
                f"Borrower swung to net loss (${net_income:,.0f}) from prior profit (${ni_prior:,.0f})",
                net_income))

    # -----------------------------------------------------------------------
    # 4. Cash Position
    # -----------------------------------------------------------------------
    cash = _get(bs_latest, "Cash & Equivalents", 0)
    restricted = _get(bs_latest, "Restricted Cash", 0)
    metrics.cash_unrestricted = cash
    metrics.cash_restricted = restricted
    metrics.cash_total = cash + restricted

    opex = _get(is_latest, "Total Operating Expenses")
    if opex and opex > 0 and cash < (opex / 12) * 3:
        flags.append(MetricFlag("cash", Severity.HIGH,
            f"Unrestricted cash (${cash:,.0f}) < 3 months operating expenses (${opex/4:,.0f})",
            cash, opex / 4))

    # -----------------------------------------------------------------------
    # 5. Total Debt
    # -----------------------------------------------------------------------
    warehouse = _get(bs_latest, "Warehouse Lines (Drawn)", 0)
    term = _get(bs_latest, "Term Debt", 0)
    sub = _get(bs_latest, "Subordinated Debt", 0)
    total_debt = warehouse + term + sub
    metrics.total_debt = total_debt
    metrics.warehouse_drawn = warehouse
    metrics.term_debt = term
    metrics.sub_debt = sub

    # -----------------------------------------------------------------------
    # 6. TNW
    # -----------------------------------------------------------------------
    equity = _get(bs_latest, "Total Equity", 0)
    intangibles = _get(bs_latest, "Intangible Assets", 0)
    goodwill_val = _get(bs_latest, "Goodwill", 0)
    tnw = equity - intangibles - goodwill_val
    metrics.tnw = tnw
    metrics.total_equity = equity
    metrics.intangibles = intangibles
    metrics.goodwill = goodwill_val

    total_assets = _get(bs_latest, "Total Assets", 0)
    if tnw < 0:
        flags.append(MetricFlag("tnw", Severity.CRITICAL,
            f"Negative tangible net worth (${tnw:,.0f})", tnw, 0))
    elif total_assets > 0 and tnw / total_assets < 0.05:
        flags.append(MetricFlag("tnw", Severity.HIGH,
            f"TNW is only {tnw/total_assets:.1%} of total assets",
            tnw / total_assets, 0.05))

    # -----------------------------------------------------------------------
    # 7. Burn Rate
    # -----------------------------------------------------------------------
    if net_income is not None and net_income < 0:
        metrics.monthly_burn = abs(net_income) / 12
        metrics.annualized_burn = abs(net_income)
        metrics.profitable = False
    else:
        metrics.monthly_burn = 0
        metrics.annualized_burn = 0
        metrics.profitable = True

    # -----------------------------------------------------------------------
    # 8. Runway
    # -----------------------------------------------------------------------
    if metrics.profitable:
        metrics.runway_months = None  # N/A — profitable
    elif metrics.monthly_burn and metrics.monthly_burn > 0:
        metrics.runway_months = cash / metrics.monthly_burn
        if metrics.runway_months < 12:
            flags.append(MetricFlag("runway", Severity.HIGH,
                f"Liquidity runway of {metrics.runway_months:.0f} months (< 12 month threshold)",
                metrics.runway_months, 12))
        if metrics.runway_months < 6:
            flags.get  # already flagged above, but upgrade severity
            flags.append(MetricFlag("runway", Severity.CRITICAL,
                f"Critical: only {metrics.runway_months:.0f} months runway",
                metrics.runway_months, 6))
    else:
        metrics.runway_months = None

    # -----------------------------------------------------------------------
    # 9. Debt / Equity
    # -----------------------------------------------------------------------
    if equity and equity > 0:
        metrics.debt_equity = total_debt / equity
    elif equity and equity <= 0:
        metrics.debt_equity = None
        flags.append(MetricFlag("debt_equity", Severity.CRITICAL,
            "Cannot calculate D/E — equity is zero or negative", equity, 0))
    else:
        metrics.debt_equity = None

    if metrics.debt_equity is not None and metrics.debt_equity > 8.0:
        flags.append(MetricFlag("debt_equity", Severity.MEDIUM,
            f"D/E of {metrics.debt_equity:.1f}× exceeds 8× threshold for specialty finance",
            metrics.debt_equity, 8.0))

    # -----------------------------------------------------------------------
    # 10. Debt / EBITDA
    # -----------------------------------------------------------------------
    if metrics.ebitda_gaap and metrics.ebitda_gaap > 0:
        metrics.debt_ebitda = total_debt / metrics.ebitda_gaap
        metrics.debt_ebitda_note = None
    else:
        metrics.debt_ebitda = None
        metrics.debt_ebitda_note = "NM — EBITDA is zero or negative"

    # -----------------------------------------------------------------------
    # 11. Interest Coverage
    # -----------------------------------------------------------------------
    metrics.interest_expense = interest_expense
    if metrics.ebitda_gaap is not None and interest_expense and interest_expense > 0:
        metrics.interest_coverage = metrics.ebitda_gaap / interest_expense
    elif interest_expense == 0:
        metrics.interest_coverage = None  # No interest expense
    else:
        metrics.interest_coverage = None

    if metrics.interest_coverage is not None:
        if metrics.interest_coverage < 1.0:
            flags.append(MetricFlag("interest_coverage", Severity.CRITICAL,
                f"Interest coverage of {metrics.interest_coverage:.2f}× — cannot service debt from operations",
                metrics.interest_coverage, 1.0))
        elif metrics.interest_coverage < 1.5:
            flags.append(MetricFlag("interest_coverage", Severity.HIGH,
                f"Interest coverage of {metrics.interest_coverage:.2f}× below 1.5× threshold",
                metrics.interest_coverage, 1.5))

    # -----------------------------------------------------------------------
    # 15. Equity Cushion
    # -----------------------------------------------------------------------
    portfolio = _get(bs_latest, "Loans Receivable / Portfolio", 0)
    metrics.portfolio_balance = portfolio
    if portfolio and portfolio > 0 and equity is not None:
        metrics.equity_cushion = equity / portfolio
    else:
        metrics.equity_cushion = None

    if metrics.equity_cushion is not None:
        if metrics.equity_cushion < 0.05:
            flags.append(MetricFlag("equity_cushion", Severity.CRITICAL,
                f"Equity cushion of {metrics.equity_cushion:.1%} — critically thin",
                metrics.equity_cushion, 0.05))
        elif metrics.equity_cushion < 0.10:
            flags.append(MetricFlag("equity_cushion", Severity.HIGH,
                f"Equity cushion of {metrics.equity_cushion:.1%} below 10% threshold",
                metrics.equity_cushion, 0.10))

    metrics.flags = flags
    return metrics


def _get_string(data: dict, field_name: str, default: str | None = None) -> str | None:
    """Get a string field."""
    val = data.get(field_name)
    if val is None:
        return default
    return str(val).strip()


# ---------------------------------------------------------------------------
# Funding analysis (from funding_facilities.xlsx)
# ---------------------------------------------------------------------------

@dataclass
class FundingAnalysis:
    total_committed: float = 0
    total_drawn: float = 0
    utilization: float = 0
    facility_count: int = 0
    nearest_maturity: str | None = None
    months_to_nearest: int | None = None
    facilities_maturing_12mo: int = 0
    amount_maturing_12mo: float = 0
    diversification_score: int = 1
    facilities: list[dict] = field(default_factory=list)
    flags: list[MetricFlag] = field(default_factory=list)

    def to_dict(self) -> dict:
        result = self.__dict__.copy()
        result["flags"] = [
            {"metric": f.metric, "severity": f.severity.value,
             "message": f.message, "value": f.value}
            for f in self.flags
        ]
        return result


def load_funding_template(file_path: str | Path) -> pd.DataFrame:
    """Load the funding_facilities.xlsx template."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Funding template not found: {path}")
    df = pd.read_excel(path)
    required_cols = {"Lender", "Facility Type", "Committed Amount", "Drawn Amount", "Maturity Date", "Status"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in funding template: {missing}")
    return df


def analyze_funding_facilities(
    df: pd.DataFrame,
    as_of_date: date | None = None,
) -> FundingAnalysis:
    """Analyze borrower's existing funding facilities."""
    if as_of_date is None:
        as_of_date = date.today()

    analysis = FundingAnalysis()
    flags: list[MetricFlag] = []

    active = df[df["Status"].str.lower().isin(["active", "current"])]
    if active.empty:
        analysis.facility_count = 0
        flags.append(MetricFlag("funding", Severity.HIGH,
            "No active funding facilities found", 0))
        analysis.flags = flags
        return analysis

    analysis.facility_count = len(active)
    analysis.total_committed = float(active["Committed Amount"].sum())
    analysis.total_drawn = float(active["Drawn Amount"].sum())

    if analysis.total_committed > 0:
        analysis.utilization = analysis.total_drawn / analysis.total_committed
    else:
        analysis.utilization = 0

    # Maturity analysis
    maturities = pd.to_datetime(active["Maturity Date"], errors="coerce")
    valid_maturities = maturities.dropna()
    if not valid_maturities.empty:
        nearest = valid_maturities.min()
        analysis.nearest_maturity = nearest.strftime("%Y-%m-%d")
        delta = (nearest.date() - as_of_date).days
        analysis.months_to_nearest = max(0, delta // 30)

        twelve_mo_cutoff = pd.Timestamp(as_of_date) + pd.DateOffset(months=12)
        maturing_12mo = active[maturities <= twelve_mo_cutoff]
        analysis.facilities_maturing_12mo = len(maturing_12mo)
        analysis.amount_maturing_12mo = float(maturing_12mo["Committed Amount"].sum())

    # Diversification score
    n = analysis.facility_count
    if n >= 3:
        analysis.diversification_score = 4
    elif n == 2:
        analysis.diversification_score = 3
    elif n == 1:
        analysis.diversification_score = 1
    else:
        analysis.diversification_score = 1

    # Flags
    if analysis.utilization > 0.90:
        flags.append(MetricFlag("funding_utilization", Severity.HIGH,
            f"Funding utilization at {analysis.utilization:.0%} — limited available capacity",
            analysis.utilization, 0.90))

    if analysis.facility_count == 1:
        flags.append(MetricFlag("funding_diversification", Severity.HIGH,
            "Single funding source — no diversification", 1))

    if analysis.facilities_maturing_12mo > 0:
        pct_maturing = analysis.amount_maturing_12mo / analysis.total_committed if analysis.total_committed > 0 else 0
        if pct_maturing > 0.50:
            flags.append(MetricFlag("maturity_wall", Severity.HIGH,
                f"{pct_maturing:.0%} of committed funding matures within 12 months",
                pct_maturing, 0.50))

    # Build facility list
    facilities = []
    for _, row in active.iterrows():
        facilities.append({
            "lender": str(row.get("Lender", "")),
            "type": str(row.get("Facility Type", "")),
            "committed": float(row.get("Committed Amount", 0)),
            "drawn": float(row.get("Drawn Amount", 0)),
            "maturity": str(row.get("Maturity Date", "")),
            "advance_rate": float(row["Advance Rate"]) if pd.notna(row.get("Advance Rate")) else None,
            "key_covenants": str(row.get("Key Covenants", "")) if pd.notna(row.get("Key Covenants")) else None,
        })
    analysis.facilities = facilities
    analysis.flags = flags

    return analysis


# ---------------------------------------------------------------------------
# Covenant headroom (basic parsing from funding template)
# ---------------------------------------------------------------------------

def calc_covenant_headroom(
    facilities: list[dict],
    metrics: FinancialMetrics,
) -> list[dict]:
    """
    Parse covenant strings from funding facilities and calculate headroom.
    Expects covenant strings like: "Min TNW $5M; Max D/E 8x; Min IC 1.5x"
    """
    headroom_results = []

    for facility in facilities:
        cov_str = facility.get("key_covenants")
        if not cov_str:
            continue

        # Parse individual covenants
        parts = [p.strip() for p in cov_str.split(";")]
        for part in parts:
            part_lower = part.lower()

            # Try to match common covenant patterns
            if "tnw" in part_lower or "tangible net worth" in part_lower:
                required = _extract_number(part)
                if required is not None and metrics.tnw is not None:
                    headroom = (metrics.tnw - required) / required if required > 0 else None
                    headroom_results.append({
                        "lender": facility.get("lender", ""),
                        "covenant": "Min TNW",
                        "required": required,
                        "actual": metrics.tnw,
                        "headroom_pct": headroom,
                        "compliant": metrics.tnw >= required,
                    })

            elif "d/e" in part_lower or "debt" in part_lower and "equity" in part_lower:
                required = _extract_number(part)
                if required is not None and metrics.debt_equity is not None:
                    headroom = (required - metrics.debt_equity) / required if required > 0 else None
                    headroom_results.append({
                        "lender": facility.get("lender", ""),
                        "covenant": "Max D/E",
                        "required": required,
                        "actual": metrics.debt_equity,
                        "headroom_pct": headroom,
                        "compliant": metrics.debt_equity <= required,
                    })

            elif "ic" in part_lower or "interest coverage" in part_lower:
                required = _extract_number(part)
                if required is not None and metrics.interest_coverage is not None:
                    headroom = (metrics.interest_coverage - required) / required if required > 0 else None
                    headroom_results.append({
                        "lender": facility.get("lender", ""),
                        "covenant": "Min Interest Coverage",
                        "required": required,
                        "actual": metrics.interest_coverage,
                        "headroom_pct": headroom,
                        "compliant": metrics.interest_coverage >= required,
                    })

    return headroom_results


def _extract_number(text: str) -> float | None:
    """Extract a number from a covenant string like 'Min TNW $5M' or 'Max D/E 8x'."""
    import re
    # Remove common suffixes
    cleaned = text.replace(",", "").strip()
    # Find numbers with optional $ and M/K/x suffixes
    matches = re.findall(r"\$?([\d.]+)\s*([MmKkXx])?", cleaned)
    if not matches:
        return None
    num_str, suffix = matches[-1]  # Take last match (likely the threshold)
    try:
        num = float(num_str)
    except ValueError:
        return None
    if suffix.upper() == "M":
        num *= 1_000_000
    elif suffix.upper() == "K":
        num *= 1_000
    # 'x' suffix means it's a ratio, keep as-is
    return num


# ---------------------------------------------------------------------------
# Generate screen language
# ---------------------------------------------------------------------------

def format_metric_for_screen(metrics: FinancialMetrics) -> dict[str, str]:
    """Generate human-readable screen language for each metric."""
    lines = {}

    if metrics.revenue_current is not None:
        growth_str = f" ({metrics.revenue_growth_yoy:+.1%} YoY)" if metrics.revenue_growth_yoy is not None else ""
        lines["revenue"] = f"Revenue of ${metrics.revenue_current/1e6:.1f}M (LTM){growth_str}"

    if metrics.ebitda_gaap is not None:
        margin_str = f" ({metrics.ebitda_margin:.1%} margin)" if metrics.ebitda_margin is not None else ""
        lines["ebitda"] = f"EBITDA of ${metrics.ebitda_gaap/1e6:.1f}M{margin_str}"

    if metrics.net_income is not None:
        if metrics.net_income >= 0:
            lines["net_income"] = f"Net income of ${metrics.net_income/1e6:.1f}M"
        else:
            lines["net_income"] = f"Net loss of $(${abs(metrics.net_income)/1e6:.1f}M)"

    if metrics.cash_unrestricted is not None:
        restricted_str = f" (${metrics.cash_restricted/1e6:.1f}M restricted)" if metrics.cash_restricted else ""
        lines["cash"] = f"Cash of ${metrics.cash_unrestricted/1e6:.1f}M unrestricted{restricted_str}"

    if metrics.total_debt is not None:
        lines["debt"] = f"Total debt of ${metrics.total_debt/1e6:.1f}M"

    if metrics.tnw is not None:
        lines["tnw"] = f"TNW of ${metrics.tnw/1e6:.1f}M"

    if metrics.debt_equity is not None:
        lines["leverage"] = f"D/E of {metrics.debt_equity:.1f}×"

    if metrics.interest_coverage is not None:
        lines["coverage"] = f"Interest coverage of {metrics.interest_coverage:.2f}×"

    if metrics.equity_cushion is not None:
        lines["equity_cushion"] = f"Equity cushion of {metrics.equity_cushion:.1%}"

    if metrics.runway_months is not None:
        lines["runway"] = f"Runway of {metrics.runway_months:.0f} months"
    elif metrics.profitable:
        lines["runway"] = "Profitable — no burn"

    return lines
