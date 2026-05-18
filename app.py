"""
Honest Abe — ABF Deal Screen Platform
by i80 Group

Run with: streamlit run app.py
"""

import streamlit as st
from pathlib import Path

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Honest Abe — Deal Screen",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# i80 Group color system + Abe branding
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ── i80 Design Tokens ─────────────────────────────────── */
    :root {
        --c-dark-green:   #1B3A2F;
        --c-accent-green: #1A8C6A;
        --c-near-black:   #EDF5F0;
        --c-body:         #49524F;
        --c-border-mid:   #A7A7A7;
        --c-border-light: #D1D1D1;
        --c-off-white:    #F2F2F2;
        --c-white:        #FFFFFF;
    }

    /* ── Global ────────────────────────────────────────────── */
    .block-container { padding-top: 1.5rem; max-width: 1100px; }
    .stApp { background: var(--c-white); }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] { background: var(--c-white); }

    /* ── Typography ────────────────────────────────────────── */
    h1, h2, h3 { color: var(--c-dark-green) !important; }
    h1 { font-weight: 700 !important; letter-spacing: -0.5px; }
    p, li, span, label, .stMarkdown { color: var(--c-body); }

    /* ── Sidebar ───────────────────────────────────────────── */
    [data-testid="stSidebar"] { background: var(--c-near-black) !important; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #2D3A34 !important; }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown { color: #2D3A34 !important; }
    [data-testid="stSidebar"] hr { border-color: var(--c-body) !important; }
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: transparent !important; border: none !important;
        color: #2D3A34 !important; text-align: left !important;
        font-size: 0.9rem !important; padding: 6px 12px !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: rgba(26,140,106,0.15) !important; color: #2D3A34 !important;
    }

    /* ── Buttons ───────────────────────────────────────────── */
    .stButton > button[kind="primary"] {
        background-color: var(--c-dark-green) !important;
        color: #2D3A34 !important; border: none !important;
        font-weight: 600 !important; border-radius: 6px !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: var(--c-accent-green) !important;
    }
    .stButton > button[kind="secondary"] {
        border-color: var(--c-border-light) !important; background: #EDF5F0 !important;
        color: var(--c-body) !important; border-radius: 6px !important;
    }

    /* ── Inputs ────────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        border-color: var(--c-border-light) !important; background: #EDF5F0 !important;
        color: #111827 !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--c-accent-green) !important;
        box-shadow: 0 0 0 1px var(--c-accent-green) !important;
    }

    /* ── Tabs ──────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: var(--c-dark-green) !important;
        border-bottom-color: var(--c-accent-green) !important;
    }

    /* ── Badges ────────────────────────────────────────────── */
    .abe-badge { padding:5px 14px; border-radius:4px; font-weight:600; font-size:0.85rem; display:inline-block; letter-spacing:0.3px; }
    .abe-badge-green  { background:var(--c-accent-green); color:var(--c-white); }
    .abe-badge-yellow { background:#D97706; color:var(--c-white); }
    .abe-badge-red    { background:#B91C1C; color:var(--c-white); }
    .abe-badge-pending{ background:var(--c-border-mid); color:var(--c-white); }

    /* ── Metric cards ──────────────────────────────────────── */
    .abe-metric { text-align:center; padding:12px 0; }
    .abe-metric-value { font-size:1.8rem; font-weight:700; color:var(--c-dark-green); line-height:1.1; }
    .abe-metric-label { font-size:0.78rem; color:var(--c-border-mid); text-transform:uppercase; letter-spacing:0.5px; margin-top:4px; }

    /* ── Cards ─────────────────────────────────────────────── */
    .abe-card { border:1px solid var(--c-border-light); border-radius:8px; padding:20px; background:var(--c-white); margin-bottom:12px; }
    .abe-card-accent { border-left:4px solid var(--c-accent-green); }
    .abe-card-warn   { border-left:4px solid #D97706; background:#FFFBEB; }
    .abe-card-crit   { border-left:4px solid #B91C1C; background:#FEF2F2; }

    /* ── Misc ──────────────────────────────────────────────── */
    hr { border-top:1px solid var(--c-border-light) !important; }
    .stDataFrame { border:1px solid var(--c-border-light); border-radius:6px; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def init_state():
    for k, v in {
        "current_step":1, "intake_complete":False, "tape_uploaded":False,
        "mapping_approved":False, "financials_validated":False,
        "funding_uploaded":False, "questionnaire_complete":False,
        "track_a_complete":False, "track_b_complete":False,
        "red_flags_complete":False, "screen_complete":False,
        "review_complete":False, "intake_data":{},
        "questionnaire_data":{},
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_state()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def badge(status):
    cls = {"green":"abe-badge-green","yellow":"abe-badge-yellow","red":"abe-badge-red"}.get(status,"abe-badge-pending")
    return f'<span class="abe-badge {cls}">{status.upper()}</span>'

def metric_card(val, lab):
    return f'<div class="abe-metric"><div class="abe-metric-value">{val}</div><div class="abe-metric-label">{lab}</div></div>'


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
STEPS = [
    (1,"Deal Intake","intake_complete"),(2,"Upload Tape","tape_uploaded"),
    (3,"Field Mapping","mapping_approved"),(4,"Financials","financials_validated"),
    (5,"Funding","funding_uploaded"),(6,"Questionnaire","questionnaire_complete"),
    (7,"Run Analysis","track_a_complete"),(8,"Red Flags","red_flags_complete"),
    (9,"Deal Screen","screen_complete"),(10,"Decision","review_complete"),
]

with st.sidebar:
    st.markdown(
        '<h1 style="color:#FFF;margin-bottom:0;font-size:2.2rem;letter-spacing:-1px;">◆ Honest Abe</h1>'
        '<p style="color:#A7A7A7;font-size:0.75rem;margin-top:2px;letter-spacing:1.5px;text-transform:uppercase;">ABF Deal Screen</p>',
        unsafe_allow_html=True)
    st.markdown("---")
    for n, name, key in STEPS:
        done = st.session_state.get(key, False)
        cur = st.session_state.current_step == n
        icon = "✓" if done else ("▸" if cur else " ")
        if st.sidebar.button(f"{icon}  {n}. {name}", key=f"nav_{n}", use_container_width=True,
                             disabled=not done and not cur and n > st.session_state.current_step+1):
            st.session_state.current_step = n; st.rerun()
    st.markdown("---")
    if st.session_state.intake_complete:
        d = st.session_state.intake_data
        st.markdown(f'<p style="color:#FFF;font-weight:600;margin-bottom:2px">{d.get("deal_name","")}</p>'
                    f'<p style="color:#A7A7A7;font-size:0.82rem;margin:0">{d.get("borrower_name","")}<br>'
                    f'${d.get("requested_facility_size",0)/1e6:.0f}M {d.get("facility_type","")}</p>',
                    unsafe_allow_html=True)
    st.markdown('<p style="color:#49524F;font-size:0.7rem;position:fixed;bottom:12px">Honest Abe v0.1 · i80 Group</p>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# STEPS
# ═══════════════════════════════════════════════════════════════════════════

# -- Step 1: Intake --------------------------------------------------------
def step_1():
    st.header("Deal Intake")
    st.markdown("Enter basic deal information to get started.")
    with st.form("intake"):
        c1,c2 = st.columns(2)
        with c1:
            dn = st.text_input("Deal Name *", placeholder="Acme Consumer Warehouse")
            bn = st.text_input("Borrower *", placeholder="Acme Lending Inc.")
            ct = st.selectbox("Collateral Type *", ["consumer_receivables","smb_loans","mca","equipment_finance","invoice_finance","saas_receivables","trade_finance","auto_receivables","other"])
            ft = st.selectbox("Facility Type *", ["warehouse","delayed_draw_term","forward_flow","rediscount","revolving","other"])
        with c2:
            fs = st.number_input("Requested Size ($) *", 0, value=0, step=1_000_000)
            ar = st.number_input("Advance Rate", 0.0, 1.0, 0.85, 0.01)
            pr = st.number_input("Pricing (bps/SOFR)", 0, value=500, step=25)
            uop = st.text_area("Use of Proceeds *", placeholder="Fund originations…")
        c3,c4 = st.columns(2)
        with c3: dl = st.text_input("Deal Lead *"); an = st.text_input("Analyst *")
        with c4: notes = st.text_area("Notes", height=104)
        if st.form_submit_button("Save & Continue →", type="primary", use_container_width=True):
            errs = []
            if not dn: errs.append("Deal Name required")
            if not bn: errs.append("Borrower required")
            if fs<=0: errs.append("Size must be positive")
            if not uop: errs.append("Use of Proceeds required")
            if not dl: errs.append("Deal Lead required")
            if not an: errs.append("Analyst required")
            if errs:
                for e in errs: st.error(e)
            else:
                st.session_state.intake_data = dict(deal_name=dn,borrower_name=bn,collateral_type=ct,facility_type=ft,
                    requested_facility_size=fs,requested_advance_rate=ar,requested_pricing_bps=pr,
                    use_of_proceeds=uop,assigned_deal_lead=dl,assigned_analyst=an,notes=notes)
                st.session_state.intake_complete = True; st.session_state.current_step = 2; st.rerun()

# -- Step 2: Tape ----------------------------------------------------------
def step_2():
    st.header("Upload Loan Tape")
    f = st.file_uploader("Drag & drop loan tape", type=["xlsx","xls","csv"], key="tape_up")
    if f:
        st.success(f"**{f.name}** ({f.size/1024:.0f} KB)")
        st.session_state.tape_uploaded = True
        try:
            import pandas as pd
            df = pd.read_csv(f, nrows=10) if f.name.endswith(".csv") else pd.read_excel(f, nrows=10)
            st.dataframe(df, use_container_width=True); st.caption(f"{df.shape[1]} columns")
        except: pass
        if st.button("Process Tape →", type="primary"):
            with st.spinner("Detecting tabs · Profiling · Mapping…"):
                import time; time.sleep(2)
            st.session_state.current_step = 3; st.rerun()

# -- Step 3: Mapping -------------------------------------------------------
def step_3():
    st.header("Review Field Mapping")
    import pandas as pd
    df = pd.DataFrame([
        {"Borrower Column":"LN_BAL_CUR","→ Standard Field":"current_balance","Confidence":0.95},
        {"Borrower Column":"Orig Prin Amt","→ Standard Field":"original_balance","Confidence":0.92},
        {"Borrower Column":"FICO_AT_ORIG","→ Standard Field":"credit_score","Confidence":0.97},
        {"Borrower Column":"Int Rt","→ Standard Field":"interest_rate","Confidence":0.88},
        {"Borrower Column":"STAT_CD","→ Standard Field":"delinquency_status","Confidence":0.72},
        {"Borrower Column":"St","→ Standard Field":"geography","Confidence":0.65},
        {"Borrower Column":"Internal Score","→ Standard Field":"— unmapped —","Confidence":0.00},
    ])
    st.dataframe(df, column_config={"Confidence":st.column_config.ProgressColumn(min_value=0,max_value=1,format="%.0f%%")},
                 use_container_width=True, hide_index=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("✓ Approve", type="primary", use_container_width=True):
            st.session_state.mapping_approved=True; st.session_state.current_step=4; st.rerun()
    with c2: st.button("Edit", use_container_width=True)
    with c3:
        if st.button("Reject", use_container_width=True):
            st.session_state.tape_uploaded=False; st.session_state.current_step=2; st.rerun()

# -- Step 4: Financials ----------------------------------------------------
def step_4():
    st.header("Upload Corporate Financials")
    st.download_button("↓ Download template", b"placeholder", "corporate_financials.xlsx")
    f = st.file_uploader("Upload completed template", type=["xlsx","xls"], key="fin_up")
    if f:
        with st.spinner("Validating…"): import time; time.sleep(1)
        st.success("Balance sheet balances"); st.success("Required fields present")
        st.session_state.financials_validated = True
        if st.button("Continue →", type="primary"):
            st.session_state.current_step=5; st.rerun()

# -- Step 5: Funding -------------------------------------------------------
def step_5():
    st.header("Funding Facilities")
    st.download_button("↓ Download template", b"placeholder", "funding_facilities.xlsx")
    f = st.file_uploader("Upload", type=["xlsx","xls"], key="fund_up")
    if f:
        st.session_state.funding_uploaded = True
        if st.button("Continue →", type="primary"): st.session_state.current_step=6; st.rerun()
    if st.button("Skip"): st.session_state.funding_uploaded=True; st.session_state.current_step=6; st.rerun()

# -- Step 6: Questionnaire -------------------------------------------------
def step_6():
    st.header("Platform Questionnaire")
    with st.form("q"):
        st.markdown("#### Management")
        c1,c2=st.columns(2)
        with c1: ceo=st.text_input("CEO"); ceo_t=st.number_input("CEO tenure (yr)",0,value=0)
        with c2: cfo=st.text_input("CFO"); cro=st.text_input("CRO")
        emp=st.number_input("Total employees",0,value=0)
        st.markdown("---"); st.markdown("#### Origination")
        ch=st.multiselect("Channels",["direct","digital","broker","partnerships","other"])
        wp=st.checkbox("Written credit policy?",True); er=st.number_input("Exception rate %",0.0,100.0,0.0)
        st.markdown("---"); st.markdown("#### Servicing")
        sm=st.selectbox("Model",["In-house","Outsourced","Hybrid"]); ss=st.number_input("Staff",0,value=0)
        bu=st.text_input("Backup servicer",placeholder="None identified")
        st.markdown("---"); st.markdown("#### Sponsor")
        sp=st.text_input("Primary sponsor"); eq=st.number_input("Equity raised ($)",0,value=0,step=1_000_000)
        if st.form_submit_button("Save & Continue →", type="primary", use_container_width=True):
            st.session_state.questionnaire_data = dict(ceo=ceo,cfo=cfo,cro=cro,emp=emp,channels=ch,policy=wp,exc=er,svc=sm,staff=ss,backup=bu,sponsor=sp,equity=eq)
            st.session_state.questionnaire_complete=True; st.session_state.current_step=7; st.rerun()

# -- Step 7: Run -----------------------------------------------------------
def step_7():
    st.header("Run Analysis")
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div class="abe-card abe-card-accent"><h4 style="color:#1B3A2F;margin:0">Track A — Collateral</h4></div>',unsafe_allow_html=True)
        if st.session_state.mapping_approved:
            if st.button("▶ Run Track A",type="primary",key="ra",use_container_width=True):
                p=st.progress(0); import time
                for i,(v,t) in enumerate([(20,"DQ checks…"),(50,"Pool summary…"),(80,"Strats…"),(100,"Done")]):
                    p.progress(v,t); time.sleep(0.4)
                st.session_state.track_a_complete=True; st.rerun()
        else: st.warning("Complete steps 2-3 first")
    with c2:
        st.markdown('<div class="abe-card abe-card-accent"><h4 style="color:#1B3A2F;margin:0">Track B — Corporate</h4></div>',unsafe_allow_html=True)
        if st.session_state.financials_validated or st.session_state.questionnaire_complete:
            if st.button("▶ Run Track B",type="primary",key="rb",use_container_width=True):
                p=st.progress(0); import time
                for v,t in [(25,"Metrics…"),(50,"Funding…"),(75,"Scorecard…"),(100,"Done")]:
                    p.progress(v,t); time.sleep(0.4)
                st.session_state.track_b_complete=True; st.rerun()
        else: st.warning("Complete steps 4-6 first")
    if st.session_state.track_a_complete and st.session_state.track_b_complete:
        st.markdown("---"); st.success("Both tracks complete.")
        if st.button("Continue →",type="primary"): st.session_state.current_step=8; st.rerun()

# -- Step 8: Red Flags -----------------------------------------------------
def step_8():
    st.header("Review Red Flags")
    sev={"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡"}
    tab1,tab2,tab3=st.tabs(["Collateral","Corporate","Contradictions"])
    with tab1:
        for s,t,d in [("CRITICAL","34% FICO missing","11K of 33K loans show FICO=0"),("HIGH","Q3-24 vintage elevated","4.2% loss at MOB 9 vs 2.1% avg"),("MEDIUM","CA concentration 31%","$48M of $155M")]:
            with st.expander(f'{sev[s]} **[{s}]** {t}',expanded=s=="CRITICAL"):
                st.markdown(d); st.radio("",["Acknowledge","Escalate","Dismiss"],key=f"a{t[:5]}",horizontal=True)
    with tab2:
        for s,t,d in [("HIGH","IC 1.17× below 1.5×","Cannot service debt from operations"),("HIGH","No backup servicer","32K loans, no transition plan"),("MEDIUM","Single funding source","Would be sole capital line")]:
            with st.expander(f'{sev[s]} **[{s}]** {t}'):
                st.markdown(d); st.radio("",["Acknowledge","Escalate","Dismiss"],key=f"b{t[:5]}",horizontal=True)
    with tab3:
        st.markdown('<div class="abe-card abe-card-warn"><strong>Good collateral, weak coverage</strong><br>30+ DPD 3.2% but IC only 1.17×. Platform risk dominates.</div>',unsafe_allow_html=True)
        st.markdown('<div class="abe-card abe-card-warn"><strong>Single funding source</strong><br>Clean tape but this facility would be sole line.</div>',unsafe_allow_html=True)
    st.markdown("---")
    if st.button("All reviewed → Continue",type="primary"):
        st.session_state.red_flags_complete=True; st.session_state.current_step=9; st.rerun()

# -- Step 9: Screen --------------------------------------------------------
def step_9():
    st.header("Integrated Deal Screen")
    d=st.session_state.intake_data
    c1,c2,c3=st.columns(3)
    with c1: st.markdown(f"Track A {badge('yellow')}",unsafe_allow_html=True)
    with c2: st.markdown(f"Track B {badge('yellow')}",unsafe_allow_html=True)
    with c3: st.markdown(f"Overall {badge('yellow')}",unsafe_allow_html=True)
    st.markdown("---")
    mc=st.columns(6)
    for col,(v,l) in zip(mc,[("$155M","Pool"),("3.2%","30+ DPD"),("$12.5M","Revenue"),("1.17×","IC"),("20.1%","Eq. Cushion"),("3.4","Score")]):
        with col: st.markdown(metric_card(v,l),unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"""
### Transaction Overview
**{d.get('borrower_name','')}** seeks **${d.get('requested_facility_size',0)/1e6:.0f}M {d.get('facility_type','')}** secured by **{d.get('collateral_type','').replace('_',' ')}** at {d.get('requested_advance_rate',0):.0%}.

---
### Track A — Collateral [YELLOW]
**Pool:** 32,951 loans · $155.3M · WAC 8.25% · 30+ DPD 3.2%
**Strengths:** Granular, adequate spread, DPD within range.
**Concerns:** 34% FICO missing. Q3-24 vintage elevated. CA 31%.

### Track B — Corporate [YELLOW]
**Financial:** Revenue $12.5M · EBITDA $2.1M · TNW $12.2M · IC 1.17×
**Strengths:** Revenue +22.5%. Equity cushion 20.1%. Experienced CRO.
**Concerns:** IC below 1.5×. Single funding source. No backup servicer.

### Key Intersection
Collateral performs today but borrower's thin coverage and single funding source create platform risk that could overwhelm structural protections.

### Gating Questions
1. Provide actual FICO scores for 11,204 loans showing zero
2. Explain Q3-24 vintage loss trajectory
3. Funding diversification plan?
4. Identify backup servicer
5. Provide 12 months management accounts
""")
    st.markdown("---")
    if st.button("Continue to Decision →",type="primary"):
        st.session_state.screen_complete=True; st.session_state.current_step=10; st.rerun()

# -- Step 10: Decision -----------------------------------------------------
def step_10():
    st.header("Decision")
    items=["Intake confirmed","Mapping approved","Collateral spot-checked","Financials verified","Scorecard reviewed","Red flags acknowledged","Contradictions reviewed","Screen reviewed"]
    ok=all(st.checkbox(i,key=f"ck{j}") for j,i in enumerate(items))
    st.markdown("---")
    dec=st.radio("Next step:",["**Pass** — Decline","**Continue to Full Diligence**","**Request More Information**"],index=None)
    cond=st.text_area("Notes / Conditions",height=80)
    by=st.text_input("Decision by",st.session_state.intake_data.get("assigned_deal_lead",""))
    st.markdown("---")
    if st.button("✓ Record Decision & Export",type="primary",use_container_width=True,disabled=not ok or not dec):
        st.session_state.review_complete=True; st.balloons()
        st.success("Decision recorded. Outputs exported.")

# ═══════════════════════════════════════════════════════════════════════════
# Router
# ═══════════════════════════════════════════════════════════════════════════
{1:step_1,2:step_2,3:step_3,4:step_4,5:step_5,6:step_6,7:step_7,8:step_8,9:step_9,10:step_10}.get(st.session_state.current_step,step_1)()
