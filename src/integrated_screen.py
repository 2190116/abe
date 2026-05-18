"""
Integrated Deal Screen Module
ABF Deal Screen MVP — Integration Layer

Combines Track A (collateral) and Track B (corporate) outputs into
a unified deal screen with status determination, contradiction analysis,
and screen narrative generation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Status types
# ---------------------------------------------------------------------------

class TrackStatus(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class OverallAlignment(str, Enum):
    ALIGNED = "aligned"
    MIXED = "mixed"
    CONFLICTING = "conflicting"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ContradictionCheck:
    """Result of a single deterministic contradiction check."""
    check_id: str
    name: str
    triggered: bool
    severity: str
    finding: str
    track_a_value: Any = None
    track_b_value: Any = None


@dataclass
class ContradictionAnalysis:
    """Combined deterministic + LLM contradiction analysis."""
    deterministic_checks: list[ContradictionCheck] = field(default_factory=list)
    llm_contradictions: list[dict] = field(default_factory=list)
    overall_alignment: str = "mixed"
    key_intersection: str = ""

    def to_dict(self) -> dict:
        return {
            "deterministic_checks": [
                {
                    "check_id": c.check_id, "name": c.name,
                    "triggered": c.triggered, "severity": c.severity,
                    "finding": c.finding,
                }
                for c in self.deterministic_checks if c.triggered
            ],
            "llm_contradictions": self.llm_contradictions,
            "overall_alignment": self.overall_alignment,
            "key_intersection": self.key_intersection,
        }


@dataclass
class IntegratedScreen:
    """Full integrated deal screen output."""
    deal_id: str
    screen_date: str
    collateral_status: str
    corporate_status: str
    overall_status: str
    screen_markdown: str
    screen_data: dict = field(default_factory=dict)
    human_decision: str | None = None
    decided_by: str | None = None

    def to_dict(self) -> dict:
        return self.__dict__


# ---------------------------------------------------------------------------
# Track status determination
# ---------------------------------------------------------------------------

def determine_track_status(
    red_flags: list[dict],
    data_completeness: float,
) -> TrackStatus:
    """
    Determine green/yellow/red status for a single track.

    Args:
        red_flags: List of flag dicts, each with "severity" key.
        data_completeness: 0.0 to 1.0 indicating how much required data was available.

    Returns:
        TrackStatus.GREEN, YELLOW, or RED.
    """
    critical_count = sum(1 for f in red_flags if f.get("severity") == "CRITICAL")
    high_count = sum(1 for f in red_flags if f.get("severity") == "HIGH")

    # RED conditions
    if critical_count > 0:
        return TrackStatus.RED
    if high_count >= 3:
        return TrackStatus.RED
    if data_completeness < 0.50:
        return TrackStatus.RED

    # YELLOW conditions
    if high_count >= 1:
        return TrackStatus.YELLOW
    if data_completeness < 0.80:
        return TrackStatus.YELLOW

    return TrackStatus.GREEN


def determine_overall_status(
    collateral_status: TrackStatus,
    corporate_status: TrackStatus,
) -> TrackStatus:
    """Overall status = worst of the two tracks."""
    if collateral_status == TrackStatus.RED or corporate_status == TrackStatus.RED:
        return TrackStatus.RED
    if collateral_status == TrackStatus.YELLOW or corporate_status == TrackStatus.YELLOW:
        return TrackStatus.YELLOW
    return TrackStatus.GREEN


# ---------------------------------------------------------------------------
# Data completeness scoring
# ---------------------------------------------------------------------------

def score_collateral_completeness(collateral_output: dict | None) -> float:
    """Score how complete the collateral analysis is (0.0-1.0)."""
    if collateral_output is None:
        return 0.0

    checks = [
        collateral_output.get("pool_summary") is not None,
        collateral_output.get("stratifications") is not None,
        collateral_output.get("concentrations") is not None,
        collateral_output.get("dq_report") is not None,
        collateral_output.get("field_mapping") is not None,
    ]
    return sum(checks) / len(checks)


def score_corporate_completeness(corporate_output: dict | None) -> float:
    """Score how complete the corporate analysis is (0.0-1.0)."""
    if corporate_output is None:
        return 0.0

    checks = [
        corporate_output.get("financial_metrics") is not None,
        corporate_output.get("funding_analysis") is not None,
        corporate_output.get("platform_scorecard") is not None,
        corporate_output.get("questionnaire") is not None,
    ]
    return sum(checks) / len(checks)


# ---------------------------------------------------------------------------
# Contradiction checks (deterministic)
# ---------------------------------------------------------------------------

def run_deterministic_contradictions(
    collateral: dict,
    corporate: dict,
    deal_intake: dict,
) -> list[ContradictionCheck]:
    """
    Run deterministic contradiction checks between Track A and Track B.

    Each check looks for specific combinations of findings that create
    contradictions, combined risks, or reinforcements.
    """
    results = []

    pool = collateral.get("pool_summary", {})
    metrics = corporate.get("financial_metrics", {})
    scorecard_cats = {}
    sc = corporate.get("platform_scorecard", {})
    if isinstance(sc, dict):
        for cat in sc.get("categories", []):
            if isinstance(cat, dict):
                scorecard_cats[cat.get("category", "")] = cat.get("score", 0)

    funding = corporate.get("funding_analysis", {})
    questionnaire = corporate.get("questionnaire", {})

    # CTR-01: Clean tape but weak underwriting discipline
    dq_30 = pool.get("dq_30plus_pct")
    uw_score = scorecard_cats.get("underwriting_discipline", scorecard_cats.get("Underwriting Discipline", None))
    if dq_30 is not None and uw_score is not None:
        triggered = dq_30 < 0.05 and uw_score <= 2
        results.append(ContradictionCheck(
            check_id="CTR-01",
            name="strong_tape_weak_underwriting",
            triggered=triggered,
            severity="HIGH",
            finding=(
                f"Tape shows low 30+ DPD ({dq_30:.1%}) but underwriting discipline "
                f"scored {uw_score}/5. Current performance may not persist if controls are weak."
            ) if triggered else "",
            track_a_value=dq_30,
            track_b_value=uw_score,
        ))

    # CTR-02: Low losses but young vintages
    cum_loss = pool.get("cumulative_loss_rate")
    wala = pool.get("wala_months")
    if cum_loss is not None and wala is not None:
        triggered = cum_loss < 0.03 and wala < 12
        results.append(ContradictionCheck(
            check_id="CTR-02",
            name="low_losses_young_vintages",
            triggered=triggered,
            severity="HIGH",
            finding=(
                f"Cumulative loss rate of {cum_loss:.1%} appears low, but WALA is only "
                f"{wala:.0f} months. Losses typically emerge at 6-18 MOB."
            ) if triggered else "",
            track_a_value={"loss": cum_loss, "wala": wala},
        ))

    # CTR-03: Adequate BB but weak liquidity
    bb = collateral.get("borrowing_base", {}).get("net_borrowing_base")
    runway = metrics.get("runway_months")
    if bb is not None and runway is not None:
        triggered = bb > 0 and runway < 12
        results.append(ContradictionCheck(
            check_id="CTR-03",
            name="strong_bb_weak_liquidity",
            triggered=triggered,
            severity="HIGH",
            finding=(
                f"Borrowing base of ${bb/1e6:.1f}M is adequate, but borrower has only "
                f"{runway:.0f} months runway. Facility amortization could strand the borrower."
            ) if triggered else "",
            track_a_value=bb,
            track_b_value=runway,
        ))

    # CTR-04: High advance rate but thin equity cushion
    req_ar = deal_intake.get("requested_advance_rate")
    ec = metrics.get("equity_cushion")
    if req_ar is not None and ec is not None:
        triggered = req_ar > 0.80 and ec < 0.10
        results.append(ContradictionCheck(
            check_id="CTR-04",
            name="high_advance_thin_equity",
            triggered=triggered,
            severity="MEDIUM",
            finding=(
                f"Requested advance rate of {req_ar:.0%} with only {ec:.1%} equity cushion. "
                f"Combined lender exposure is high relative to borrower skin-in-the-game."
            ) if triggered else "",
            track_a_value=req_ar,
            track_b_value=ec,
        ))

    # CTR-05: Good collateral but single funding source
    if dq_30 is not None:
        funding_count = funding.get("facility_count", 0)
        triggered = dq_30 < 0.05 and funding_count <= 1
        results.append(ContradictionCheck(
            check_id="CTR-05",
            name="good_collateral_single_funding",
            triggered=triggered,
            severity="HIGH",
            finding=(
                f"Collateral quality is acceptable (30+ DPD {dq_30:.1%}), but borrower "
                f"has only {funding_count} funding source(s). Platform failure risk "
                f"becomes lender concentration risk."
            ) if triggered else "",
            track_a_value=dq_30,
            track_b_value=funding_count,
        ))

    # CTR-06: Fast growth but limited servicing capacity
    orig_section = questionnaire.get("origination", {})
    orig_growth = orig_section.get("origination_growth_yoy_pct", 0)
    svc_score = scorecard_cats.get("servicing_capability", scorecard_cats.get("Servicing Capability", None))
    if svc_score is not None:
        triggered = orig_growth > 30 and svc_score <= 3
        results.append(ContradictionCheck(
            check_id="CTR-06",
            name="fast_growth_limited_servicing",
            triggered=triggered,
            severity="MEDIUM",
            finding=(
                f"Origination growing {orig_growth:.0f}% YoY but servicing scored {svc_score}/5. "
                f"Growth without servicing investment may degrade future pool performance."
            ) if triggered else "",
            track_a_value=orig_growth,
            track_b_value=svc_score,
        ))

    # CTR-07: Strong collateral but borrower interest coverage is weak
    if dq_30 is not None:
        ic = metrics.get("interest_coverage")
        if ic is not None:
            triggered = dq_30 < 0.05 and ic < 1.5
            results.append(ContradictionCheck(
                check_id="CTR-07",
                name="good_collateral_weak_coverage",
                triggered=triggered,
                severity="HIGH",
                finding=(
                    f"Collateral quality is acceptable (30+ DPD {dq_30:.1%}), but borrower "
                    f"interest coverage is only {ic:.2f}×. Borrower may not survive stress "
                    f"even if collateral performs."
                ) if triggered else "",
                track_a_value=dq_30,
                track_b_value=ic,
            ))

    # CTR-08: Borrower requests large facility relative to equity
    req_size = deal_intake.get("requested_facility_size", 0)
    total_equity = metrics.get("total_equity")
    if req_size and total_equity and total_equity > 0:
        ratio = req_size / total_equity
        triggered = ratio > 5
        results.append(ContradictionCheck(
            check_id="CTR-08",
            name="facility_size_vs_equity",
            triggered=triggered,
            severity="MEDIUM",
            finding=(
                f"Requested facility (${req_size/1e6:.0f}M) is {ratio:.1f}× borrower equity "
                f"(${total_equity/1e6:.1f}M). Facility is large relative to borrower's capitalization."
            ) if triggered else "",
            track_a_value=req_size,
            track_b_value=total_equity,
        ))

    return results


# ---------------------------------------------------------------------------
# Combine outputs for screen generation
# ---------------------------------------------------------------------------

def combine_track_outputs(
    deal_intake: dict,
    collateral_output: dict | None,
    corporate_output: dict | None,
    collateral_red_flags: list[dict] | None,
    corporate_red_flags: list[dict] | None,
) -> dict:
    """
    Combine all track outputs into a single dict for screen generation.
    Handles cases where one or both tracks may not be available.
    """
    return {
        "deal_intake": deal_intake,
        "collateral": collateral_output or {},
        "corporate": corporate_output or {},
        "collateral_red_flags": collateral_red_flags or [],
        "corporate_red_flags": corporate_red_flags or [],
        "collateral_available": collateral_output is not None,
        "corporate_available": corporate_output is not None,
    }


# ---------------------------------------------------------------------------
# Human review checklist
# ---------------------------------------------------------------------------

def generate_human_review_checklist(
    combined: dict,
    contradiction_analysis: ContradictionAnalysis | None = None,
) -> list[dict]:
    """
    Generate the human review checklist based on what outputs are available
    and what issues were flagged.
    """
    checklist = []
    item_id = 1

    # Always required
    checklist.append({
        "id": item_id, "category": "intake",
        "item": "Confirm deal intake data is accurate",
        "required": True, "status": "pending",
    })
    item_id += 1

    # Track A items
    if combined.get("collateral_available"):
        checklist.append({
            "id": item_id, "category": "field_mapping",
            "item": "Review and approve loan tape field mapping",
            "required": True, "status": "pending",
        })
        item_id += 1

        # DQ issues
        dq = combined.get("collateral", {}).get("dq_report", {})
        blocking_issues = [c for c in dq.get("checks", []) if c.get("severity") == "blocking" and not c.get("passed")]
        if blocking_issues:
            checklist.append({
                "id": item_id, "category": "data_quality",
                "item": f"Review {len(blocking_issues)} blocking data quality issues",
                "required": True, "status": "pending",
            })
            item_id += 1

        checklist.append({
            "id": item_id, "category": "collateral",
            "item": "Review collateral analytics output and spot-check key metrics",
            "required": True, "status": "pending",
        })
        item_id += 1

        # Eligibility
        if combined.get("collateral", {}).get("eligibility"):
            checklist.append({
                "id": item_id, "category": "eligibility",
                "item": "Review eligibility criteria application and borrowing base",
                "required": True, "status": "pending",
            })
            item_id += 1

    # Track B items
    if combined.get("corporate_available"):
        checklist.append({
            "id": item_id, "category": "financials",
            "item": "Confirm financial template data matches source statements",
            "required": True, "status": "pending",
        })
        item_id += 1

        checklist.append({
            "id": item_id, "category": "scorecard",
            "item": "Review platform scorecard and override scores where appropriate",
            "required": True, "status": "pending",
        })
        item_id += 1

    # Red flags (always, if any exist)
    a_flags = combined.get("collateral_red_flags", [])
    b_flags = combined.get("corporate_red_flags", [])
    total_flags = len(a_flags) + len(b_flags)
    if total_flags > 0:
        checklist.append({
            "id": item_id, "category": "red_flags",
            "item": f"Acknowledge all {total_flags} red flags (collateral: {len(a_flags)}, corporate: {len(b_flags)})",
            "required": True, "status": "pending",
        })
        item_id += 1

    # Contradictions
    if contradiction_analysis:
        triggered = [c for c in contradiction_analysis.deterministic_checks if c.triggered]
        llm_count = len(contradiction_analysis.llm_contradictions)
        if triggered or llm_count:
            checklist.append({
                "id": item_id, "category": "contradictions",
                "item": f"Review Track A/B contradiction analysis ({len(triggered)} deterministic, {llm_count} LLM-identified)",
                "required": True, "status": "pending",
            })
            item_id += 1

    # Final approval
    checklist.append({
        "id": item_id, "category": "approval",
        "item": "Deal lead: approve integrated screen and record decision (pass / continue / request info)",
        "required": True, "status": "pending",
    })

    return checklist


# ---------------------------------------------------------------------------
# Screen narrative assembly (prepares LLM input)
# ---------------------------------------------------------------------------

def prepare_screen_llm_input(
    deal_intake: dict,
    collateral_output: dict | None,
    corporate_output: dict | None,
    collateral_red_flags: list[dict],
    corporate_red_flags: list[dict],
    contradiction_analysis: ContradictionAnalysis,
    collateral_status: TrackStatus,
    corporate_status: TrackStatus,
    overall_status: TrackStatus,
) -> dict:
    """
    Prepare the structured input for the screen writer LLM prompt.
    This is everything the LLM needs to generate the markdown screen.
    """
    # Extract key collateral metrics
    pool = {}
    if collateral_output:
        ps = collateral_output.get("pool_summary", {})
        pool = {
            "loan_count": ps.get("loan_count"),
            "total_balance": ps.get("total_current_balance"),
            "wac": ps.get("wac"),
            "wam_months": ps.get("wam_months"),
            "wala_months": ps.get("wala_months"),
            "dq_30plus_pct": ps.get("dq_30plus_pct"),
            "cumulative_loss_rate": ps.get("cumulative_loss_rate"),
            "average_balance": ps.get("average_current_balance"),
        }
        conc = collateral_output.get("concentrations", {})
        pool["top_obligor_pct"] = conc.get("top_obligor_pct")
        pool["top_state"] = conc.get("top_state")
        pool["top_state_pct"] = conc.get("top_state_pct")
        pool["obligor_hhi"] = conc.get("obligor_hhi")

        bb = collateral_output.get("borrowing_base", {})
        pool["borrowing_base"] = bb.get("net_borrowing_base")
        pool["eligible_balance"] = bb.get("eligible_balance")
        pool["advance_rate_applied"] = bb.get("advance_rate")

    # Extract key corporate metrics
    corp = {}
    if corporate_output:
        fm = corporate_output.get("financial_metrics", {})
        corp = {
            "revenue": fm.get("revenue_current"),
            "revenue_growth": fm.get("revenue_growth_yoy"),
            "ebitda": fm.get("ebitda_gaap"),
            "ebitda_margin": fm.get("ebitda_margin"),
            "net_income": fm.get("net_income"),
            "cash": fm.get("cash_unrestricted"),
            "total_debt": fm.get("total_debt"),
            "tnw": fm.get("tnw"),
            "debt_equity": fm.get("debt_equity"),
            "interest_coverage": fm.get("interest_coverage"),
            "equity_cushion": fm.get("equity_cushion"),
            "runway_months": fm.get("runway_months"),
            "profitable": fm.get("profitable"),
        }

        fa = corporate_output.get("funding_analysis", {})
        corp["funding_count"] = fa.get("facility_count")
        corp["utilization"] = fa.get("utilization")
        corp["nearest_maturity"] = fa.get("nearest_maturity")
        corp["diversification_score"] = fa.get("diversification_score")

        sc = corporate_output.get("platform_scorecard", {})
        corp["scorecard_overall"] = sc.get("overall_score")
        corp["scorecard_categories"] = sc.get("categories", [])

    # Top red flags per track
    def top_flags(flags: list[dict], n: int = 3) -> list[dict]:
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_flags = sorted(flags, key=lambda f: severity_order.get(f.get("severity", "LOW"), 99))
        return sorted_flags[:n]

    return {
        "deal_intake": deal_intake,
        "collateral_summary": pool,
        "corporate_summary": corp,
        "collateral_red_flags": top_flags(collateral_red_flags),
        "corporate_red_flags": top_flags(corporate_red_flags),
        "all_collateral_flags_count": len(collateral_red_flags),
        "all_corporate_flags_count": len(corporate_red_flags),
        "contradiction_analysis": contradiction_analysis.to_dict(),
        "collateral_status": collateral_status.value,
        "corporate_status": corporate_status.value,
        "overall_status": overall_status.value,
        "collateral_available": collateral_output is not None,
        "corporate_available": corporate_output is not None,
    }


# ---------------------------------------------------------------------------
# Screen writer prompt
# ---------------------------------------------------------------------------

SCREEN_WRITER_PROMPT = """ROLE: You are the Integrated Deal Screen Writer for an asset-based finance firm.

OBJECTIVE: Produce a 2-4 page deal screen in markdown. A deal lead should read this in 5 minutes and know: what the deal is, whether collateral is acceptable, whether the platform is sound, where the risks are, and what questions to answer next.

INPUTS: You will receive a JSON object with deal_intake, collateral_summary, corporate_summary, red flags, contradiction analysis, and track statuses.

STRUCTURE (follow exactly):

# Integrated Deal Screen
## {deal_name} — {date}

### Transaction Overview
[2-3 sentences: who, what, how much, why]

### Track A — Collateral Assessment [{STATUS}]
Pool stats in one line. Key quality metrics. BB if available.
**Strengths:** 2-3 bullets
**Concerns:** 2-3 bullets

### Track B — Corporate/Platform Assessment [{STATUS}]
Key financial metrics in one line. Scorecard summary. Funding overview.
**Strengths:** 2-3 bullets
**Concerns:** 2-3 bullets

### Track A / Track B Intersections
The single most important cross-track observation, then 1-2 additional.

### Red Flags
Top 3 collateral flags. Top 3 corporate flags. Cite severity.

### Missing Information
What data was not available and what it would have enabled.

### Gating Diligence Questions
3-5 numbered questions that must be answered before committing full diligence.

### Recommended Next Step
**[ ] Pass** — {reason}
**[ ] Continue to Full Diligence** — Focus on: {areas}
**[ ] Request More Information** — Need: {items}

*This is a workflow recommendation, not an investment decision.*

RULES:
- 600-900 words total
- Every number must come from the input data
- Do NOT make investment decisions
- Do NOT exceed 1000 words
- Do NOT bury bad news
- Status labels must match the input status values exactly
- If a track is not available, note it prominently
"""


# ---------------------------------------------------------------------------
# Full screen generation pipeline
# ---------------------------------------------------------------------------

def generate_integrated_screen(
    deal_id: str,
    deal_intake: dict,
    collateral_output: dict | None,
    corporate_output: dict | None,
    collateral_red_flags: list[dict],
    corporate_red_flags: list[dict],
    call_llm_fn=None,
) -> IntegratedScreen:
    """
    Generate the full integrated deal screen.

    Args:
        deal_id: Deal identifier.
        deal_intake: Deal intake form data.
        collateral_output: Track A outputs (or None if not yet available).
        corporate_output: Track B outputs (or None if not yet available).
        collateral_red_flags: Track A red flags.
        corporate_red_flags: Track B red flags.
        call_llm_fn: Callable(system_prompt, user_message) -> str.
                     If None, returns screen with data but no narrative.

    Returns:
        IntegratedScreen with markdown narrative and structured data.
    """
    # 1. Determine completeness
    collateral_completeness = score_collateral_completeness(collateral_output)
    corporate_completeness = score_corporate_completeness(corporate_output)

    # 2. Determine status
    collateral_status = determine_track_status(collateral_red_flags, collateral_completeness)
    corporate_status = determine_track_status(corporate_red_flags, corporate_completeness)
    overall_status = determine_overall_status(collateral_status, corporate_status)

    # 3. Run contradiction analysis
    contradiction_checks = run_deterministic_contradictions(
        collateral=collateral_output or {},
        corporate=corporate_output or {},
        deal_intake=deal_intake,
    )
    triggered = [c for c in contradiction_checks if c.triggered]

    contradiction_analysis = ContradictionAnalysis(
        deterministic_checks=contradiction_checks,
        overall_alignment=(
            "conflicting" if any(c.severity == "HIGH" for c in triggered)
            else "mixed" if triggered
            else "aligned"
        ),
    )

    # 4. If LLM available, run contradiction LLM review and screen writer
    screen_markdown = ""
    if call_llm_fn is not None:
        # Prepare input for LLM
        llm_input = prepare_screen_llm_input(
            deal_intake=deal_intake,
            collateral_output=collateral_output,
            corporate_output=corporate_output,
            collateral_red_flags=collateral_red_flags,
            corporate_red_flags=corporate_red_flags,
            contradiction_analysis=contradiction_analysis,
            collateral_status=collateral_status,
            corporate_status=corporate_status,
            overall_status=overall_status,
        )

        # Generate screen narrative
        screen_markdown = call_llm_fn(
            system_prompt=SCREEN_WRITER_PROMPT,
            user_message=json.dumps(llm_input, indent=2, default=str),
        )
    else:
        screen_markdown = _generate_fallback_screen(
            deal_intake, collateral_output, corporate_output,
            collateral_red_flags, corporate_red_flags,
            contradiction_analysis, collateral_status, corporate_status,
        )

    # 5. Build checklist
    combined = combine_track_outputs(
        deal_intake, collateral_output, corporate_output,
        collateral_red_flags, corporate_red_flags,
    )
    checklist = generate_human_review_checklist(combined, contradiction_analysis)

    # 6. Build screen data
    screen_data = {
        "collateral_completeness": collateral_completeness,
        "corporate_completeness": corporate_completeness,
        "collateral_status": collateral_status.value,
        "corporate_status": corporate_status.value,
        "overall_status": overall_status.value,
        "contradiction_analysis": contradiction_analysis.to_dict(),
        "review_checklist": checklist,
        "collateral_flag_count": len(collateral_red_flags),
        "corporate_flag_count": len(corporate_red_flags),
        "triggered_contradiction_count": len(triggered),
    }

    return IntegratedScreen(
        deal_id=deal_id,
        screen_date=datetime.now().strftime("%Y-%m-%d"),
        collateral_status=collateral_status.value,
        corporate_status=corporate_status.value,
        overall_status=overall_status.value,
        screen_markdown=screen_markdown,
        screen_data=screen_data,
    )


def _generate_fallback_screen(
    deal_intake: dict,
    collateral_output: dict | None,
    corporate_output: dict | None,
    collateral_flags: list[dict],
    corporate_flags: list[dict],
    contradictions: ContradictionAnalysis,
    collateral_status: TrackStatus,
    corporate_status: TrackStatus,
) -> str:
    """
    Generate a basic screen without LLM when LLM is not available.
    Useful for testing and offline operation.
    """
    lines = []
    dn = deal_intake.get("deal_name", "Unknown Deal")
    bn = deal_intake.get("borrower_name", "Unknown Borrower")
    today = datetime.now().strftime("%Y-%m-%d")

    lines.append(f"# Integrated Deal Screen")
    lines.append(f"## {dn} — {today}")
    lines.append("")
    lines.append("### Transaction Overview")
    lines.append(
        f"**Borrower:** {bn} | "
        f"**Facility:** ${deal_intake.get('requested_facility_size', 0)/1e6:.0f}M "
        f"{deal_intake.get('facility_type', '')} | "
        f"**Collateral:** {deal_intake.get('collateral_type', '')}"
    )
    lines.append(f"**Use of Proceeds:** {deal_intake.get('use_of_proceeds', 'Not specified')}")
    lines.append("")

    # Track A
    lines.append(f"### Track A — Collateral Assessment [{collateral_status.value.upper()}]")
    if collateral_output:
        ps = collateral_output.get("pool_summary", {})
        lines.append(
            f"**Pool:** {ps.get('loan_count', 'N/A')} loans | "
            f"${ps.get('total_current_balance', 0)/1e6:.1f}M | "
            f"WAC {ps.get('wac', 0):.2%} | "
            f"30+ DPD {ps.get('dq_30plus_pct', 0):.1%}"
        )
    else:
        lines.append("*Track A not yet available — loan tape not processed.*")
    lines.append("")

    # Track B
    lines.append(f"### Track B — Corporate/Platform Assessment [{corporate_status.value.upper()}]")
    if corporate_output:
        fm = corporate_output.get("financial_metrics", {})
        lines.append(
            f"**Financial:** Revenue ${fm.get('revenue_current', 0)/1e6:.1f}M | "
            f"EBITDA ${fm.get('ebitda_gaap', 0)/1e6:.1f}M | "
            f"TNW ${fm.get('tnw', 0)/1e6:.1f}M | "
            f"IC {fm.get('interest_coverage', 0):.2f}×"
        )
        sc = corporate_output.get("platform_scorecard", {})
        lines.append(f"**Scorecard:** {sc.get('overall_score', 'N/A')}/5.0")
    else:
        lines.append("*Track B not yet available — corporate materials not processed.*")
    lines.append("")

    # Contradictions
    triggered = [c for c in contradictions.deterministic_checks if c.triggered]
    if triggered:
        lines.append("### Track A / Track B Intersections")
        for c in triggered:
            lines.append(f"- **[{c.severity}]** {c.finding}")
        lines.append("")

    # Red flags
    if collateral_flags or corporate_flags:
        lines.append("### Red Flags")
        if collateral_flags:
            lines.append(f"**Collateral ({len(collateral_flags)} flags):**")
            for f in collateral_flags[:3]:
                lines.append(f"- [{f.get('severity', '')}] {f.get('title', '')}")
        if corporate_flags:
            lines.append(f"**Corporate ({len(corporate_flags)} flags):**")
            for f in corporate_flags[:3]:
                lines.append(f"- [{f.get('severity', '')}] {f.get('title', '')}")
        lines.append("")

    lines.append("### Recommended Next Step")
    lines.append("**[ ] Pass** | **[ ] Continue to Full Diligence** | **[ ] Request More Information**")
    lines.append("")
    lines.append("*This is a workflow recommendation, not an investment decision.*")
    lines.append("")
    lines.append(f"---")
    lines.append(f"Generated: {today} | Analyst review: pending | Deal lead review: pending")

    return "\n".join(lines)
