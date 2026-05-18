"""
Abe — CLI Pipeline Runner
Run: python run_pipeline.py

Processes sample deal data through Track A + Track B + Integration.
Outputs markdown deal screen + JSON analytics to ./outputs/
"""
import json
import sys
from pathlib import Path
from datetime import date, datetime

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent))

from src.collateral_analytics import run_collateral_pipeline, generate_collateral_red_flags
from src.corporate_metrics import (
    load_financials_template, validate_financials, calculate_financial_metrics,
    load_funding_template, analyze_funding_facilities, calc_covenant_headroom,
    format_metric_for_screen,
)
from src.integrated_screen import (
    run_deterministic_contradictions, determine_track_status, determine_overall_status,
    generate_integrated_screen, TrackStatus,
)

FIXTURE_DIR = Path("fixtures")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
TAPE_DATE = date(2025, 4, 30)

INTAKE = {
    "deal_name": "Acme Consumer Warehouse",
    "borrower_name": "Acme Lending Inc.",
    "collateral_type": "consumer_receivables",
    "facility_type": "warehouse",
    "requested_facility_size": 50_000_000,
    "requested_advance_rate": 0.85,
    "requested_tenor_months": 24,
    "requested_pricing_bps": 500,
    "use_of_proceeds": "Fund new consumer loan originations and refinance existing Regional Bank warehouse",
    "assigned_deal_lead": "Jane Smith",
    "assigned_analyst": "Bob Chen",
}

print("=" * 70)
print("  ◆ Abe — ABF Deal Screen Pipeline")
print("=" * 70)
print(f"  Deal: {INTAKE['deal_name']}")
print(f"  Borrower: {INTAKE['borrower_name']}")
print(f"  Facility: ${INTAKE['requested_facility_size']/1e6:.0f}M {INTAKE['facility_type']}")
print()

# ── TRACK A ────────────────────────────────────────────────────────────
print("─" * 70)
print("  TRACK A — Collateral Analytics")
print("─" * 70)

tape_path = FIXTURE_DIR / "acme_tape_apr2025.csv"
if not tape_path.exists():
    print("  ✗ Tape not found. Run: python create_fixtures.py")
    sys.exit(1)

coll = run_collateral_pipeline(str(tape_path), TAPE_DATE)
ps = coll.pool_summary
cn = coll.concentrations

print(f"  ✓ {ps['loan_count']:,} loans | ${ps['total_current_balance']/1e6:.1f}M")
print(f"    WAC {ps.get('wac',0):.2%} | WAM {ps.get('wam_months',0):.0f}mo | WALA {ps.get('wala_months',0):.0f}mo")
print(f"    30+ DPD {ps.get('dq_30plus_pct',0):.2%} | Loss {ps.get('cumulative_loss_rate',0):.2%}")
print(f"    Top obligor {cn.get('top_obligor_pct',0):.2f}% | Top state {cn.get('top_state','')} ({cn.get('top_state_pct',0)}%)")

coll_flags = generate_collateral_red_flags(ps, cn, coll.dq_report.get("checks", []))
for f in coll_flags:
    print(f"    [{f['severity']}] {f['title']}")

# ── TRACK B ────────────────────────────────────────────────────────────
print("\n" + "─" * 70)
print("  TRACK B — Corporate Analytics")
print("─" * 70)

fin_path = FIXTURE_DIR / "corporate_financials.xlsx"
fund_path = FIXTURE_DIR / "funding_facilities.xlsx"

if not fin_path.exists():
    print("  ✗ Financials not found. Run: python create_fixtures.py")
    sys.exit(1)

financials = load_financials_template(str(fin_path))
validation = validate_financials(financials)
if not validation.valid:
    for e in validation.errors:
        print(f"  ✗ {e}")
else:
    print(f"  ✓ Financials validated ({len(financials['periods'])} periods)")

metrics = calculate_financial_metrics(financials)
screen_lang = format_metric_for_screen(metrics)
for key, line in screen_lang.items():
    print(f"    {line}")

# Flags
for f in metrics.flags:
    print(f"    [{f.severity.value}] {f.message}")

# Funding
fund_df = load_funding_template(str(fund_path))
funding = analyze_funding_facilities(fund_df)
print(f"  ✓ {funding.facility_count} facility | ${funding.total_committed/1e6:.0f}M | {funding.utilization:.0%} util")
for f in funding.flags:
    print(f"    [{f.severity.value}] {f.message}")

# Covenant headroom
headroom = calc_covenant_headroom(funding.facilities, metrics)
for h in headroom:
    status = "✓" if h["compliant"] else "✗ BREACH"
    print(f"    {status} {h['covenant']}: actual {h['actual']:.2f} vs required {h['required']} ({h['headroom_pct']:.0f}%)")

# Assemble corporate flags
corp_flags = []
for f in metrics.flags:
    corp_flags.append({"severity": f.severity.value, "title": f.message, "finding": f.message})
for f in funding.flags:
    corp_flags.append({"severity": f.severity.value, "title": f.message, "finding": f.message})
corp_flags.append({"severity": "HIGH", "title": "No backup servicer identified",
                   "finding": "In-house servicing with no backup servicer."})

# Corporate output
corporate_output = {
    "financial_metrics": metrics.to_dict(),
    "funding_analysis": funding.to_dict(),
    "platform_scorecard": {
        "overall_score": 3.4,
        "categories": [
            {"category": "Management", "score": 4},
            {"category": "Sponsor / Equity Backing", "score": 3},
            {"category": "Financial Condition", "score": 2},
            {"category": "Origination Quality", "score": 4},
            {"category": "Underwriting Discipline", "score": 4},
            {"category": "Servicing Capability", "score": 3},
            {"category": "Reporting Quality", "score": 4},
            {"category": "Compliance", "score": 4},
            {"category": "Funding Diversification", "score": 1},
            {"category": "Historical Performance", "score": 3},
        ],
    },
}

# ── INTEGRATION ────────────────────────────────────────────────────────
print("\n" + "─" * 70)
print("  INTEGRATION — Contradictions & Screen")
print("─" * 70)

screen = generate_integrated_screen(
    deal_id="acme-001",
    deal_intake=INTAKE,
    collateral_output=coll.to_dict(),
    corporate_output=corporate_output,
    collateral_red_flags=coll_flags,
    corporate_red_flags=corp_flags,
    call_llm_fn=None,  # Uses fallback screen generator (no API key needed)
)

print(f"  Track A: {screen.collateral_status.upper()}")
print(f"  Track B: {screen.corporate_status.upper()}")
print(f"  Overall: {screen.overall_status.upper()}")

# ── WRITE OUTPUTS ──────────────────────────────────────────────────────
(OUTPUT_DIR / "deal_screen.md").write_text(screen.screen_markdown)
(OUTPUT_DIR / "collateral_analytics.json").write_text(json.dumps(coll.to_dict(), indent=2, default=str))
(OUTPUT_DIR / "corporate_analytics.json").write_text(json.dumps(corporate_output, indent=2, default=str))
(OUTPUT_DIR / "collateral_red_flags.json").write_text(json.dumps(coll_flags, indent=2))
(OUTPUT_DIR / "corporate_red_flags.json").write_text(json.dumps(corp_flags, indent=2))
(OUTPUT_DIR / "screen_data.json").write_text(json.dumps(screen.screen_data, indent=2, default=str))

print(f"\n{'=' * 70}")
print(f"  ✓ Pipeline complete — outputs in ./{OUTPUT_DIR}/")
print(f"{'=' * 70}")
for f in sorted(OUTPUT_DIR.glob("*")):
    print(f"    {f.name} ({f.stat().st_size/1024:.1f} KB)")
print()
print("  Open outputs/deal_screen.md to see the integrated deal screen.")
