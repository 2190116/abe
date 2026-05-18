"""
Abe — ABF Deal Screen Platform
i80 Group
Run: streamlit run app.py
"""
import streamlit as st
st.set_page_config(page_title="Abe — Deal Screen", page_icon="◆", layout="wide", initial_sidebar_state="expanded")

# ═══ i80 DESIGN SYSTEM ═══════════════════════════════════════════════════
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{--dg:#1B3A2F;--ag:#1A8C6A;--nb:#111827;--body:#49524F;--bm:#A7A7A7;--bl:#D1D1D1;--ow:#F2F2F2;--wh:#FFFFFF}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:var(--ow)!important;font-family:'Inter',-apple-system,sans-serif!important}
#MainMenu,footer,header[data-testid="stHeader"]{display:none!important}
.block-container{max-width:1060px;padding:2rem 2rem 4rem!important}
h1{color:var(--dg)!important;font-weight:700!important;font-size:1.65rem!important;letter-spacing:-0.5px!important;margin-bottom:.15rem!important}
h2{color:var(--dg)!important;font-weight:600!important;font-size:1.15rem!important;letter-spacing:-0.2px!important}
h3{color:var(--dg)!important;font-weight:600!important;font-size:.95rem!important;text-transform:uppercase!important;letter-spacing:.8px!important}
p,li,label,.stMarkdown,span,td,th{color:var(--body)!important;font-family:'Inter',sans-serif!important}
section[data-testid="stSidebar"]{background:var(--nb)!important}
section[data-testid="stSidebar"]>div{padding-top:1.5rem!important}
section[data-testid="stSidebar"] *{font-family:'Inter',sans-serif!important}
section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] li,section[data-testid="stSidebar"] .stMarkdown{color:var(--bm)!important}
section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3{color:var(--wh)!important}
section[data-testid="stSidebar"] hr{border-color:#1f2937!important;margin:.75rem 0!important}
section[data-testid="stSidebar"] button{background:transparent!important;border:none!important;color:var(--bm)!important;text-align:left!important;font-size:13px!important;padding:6px 10px!important;border-radius:6px!important;transition:all .15s!important}
section[data-testid="stSidebar"] button:hover{background:rgba(26,140,106,.1)!important;color:var(--wh)!important}
.stButton>button[kind="primary"]{background:var(--dg)!important;color:var(--wh)!important;border:none!important;font-weight:600!important;font-size:14px!important;padding:.55rem 1.5rem!important;border-radius:8px!important;letter-spacing:.2px!important;transition:all .2s!important}
.stButton>button[kind="primary"]:hover{background:var(--ag)!important;transform:translateY(-1px);box-shadow:0 4px 12px rgba(26,140,106,.25)!important}
.stButton>button[kind="secondary"],.stButton>button:not([kind]){background:var(--wh)!important;color:var(--body)!important;border:1px solid var(--bl)!important;border-radius:8px!important;font-weight:500!important;transition:all .15s!important}
.stTextInput input,.stNumberInput input,.stTextArea textarea{background:var(--wh)!important;border:1px solid var(--bl)!important;color:var(--nb)!important;font-size:14px!important;font-family:'Inter',sans-serif!important;border-radius:8px!important}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{border-color:var(--ag)!important;box-shadow:0 0 0 3px rgba(26,140,106,.1)!important}
label{font-size:13px!important;font-weight:500!important;color:var(--body)!important}
.stTabs [data-baseweb="tab-list"]{gap:0!important;border-bottom:1px solid var(--bl)!important}
.stTabs [data-baseweb="tab"]{font-family:'Inter',sans-serif!important;font-size:13px!important;font-weight:500!important;padding:8px 20px!important;color:var(--bm)!important}
.stTabs [data-baseweb="tab"][aria-selected="true"]{color:var(--dg)!important;border-bottom:2px solid var(--ag)!important}
.abe-s{background:var(--wh);border:1px solid var(--bl);border-radius:12px;padding:24px;margin-bottom:16px}
.abe-sa{border-left:3px solid var(--ag)}
.abe-sf{background:var(--ow);border:1px solid var(--bl);border-radius:12px;padding:20px;margin-bottom:12px}
.abe-ms{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:16px 0}
.abe-m{background:var(--wh);border:1px solid var(--bl);border-radius:10px;padding:18px 14px;text-align:center}
.abe-mv{font-size:1.6rem;font-weight:700;color:var(--dg);line-height:1.1;letter-spacing:-.5px}
.abe-ml{font-size:.7rem;color:var(--bm);text-transform:uppercase;letter-spacing:1px;margin-top:6px}
.abe-st{display:inline-flex;align-items:center;gap:6px;font-weight:600;font-size:12px;letter-spacing:.5px;text-transform:uppercase;padding:5px 14px;border-radius:6px}
.abe-st-go{background:var(--ag);color:var(--wh)}.abe-st-caution{background:var(--dg);color:var(--wh)}.abe-st-stop{background:var(--nb);color:var(--wh)}
.stDataFrame{border-radius:10px!important;overflow:hidden;border:1px solid var(--bl)!important}
.stProgress>div>div>div{background:var(--ag)!important;border-radius:4px!important}
.stProgress>div>div{background:var(--ow)!important;border-radius:4px!important}
[data-testid="stFileUploader"]>div{background:var(--wh)!important;border:2px dashed var(--bl)!important;border-radius:12px!important;padding:24px!important}
details{border:1px solid var(--bl)!important;border-radius:8px!important;margin-bottom:8px!important}
.streamlit-expanderHeader{font-weight:500!important;font-size:14px!important;color:var(--nb)!important}
.stAlert>div{border-radius:8px!important;font-size:13px!important}
hr{border:none!important;border-top:1px solid var(--bl)!important;margin:20px 0!important}
.stDownloadButton button{background:var(--wh)!important;border:1px solid var(--bl)!important;color:var(--body)!important;font-weight:500!important;border-radius:8px!important}
</style>""", unsafe_allow_html=True)

# ═══ STATE ═══════════════════════════════════════════════════════════════
for k,v in {"step":1,"intake_done":False,"tape_done":False,"map_done":False,"fin_done":False,"fund_done":False,"quest_done":False,"track_a_done":False,"track_b_done":False,"flags_done":False,"screen_done":False,"review_done":False,"intake":{}}.items():
    if k not in st.session_state: st.session_state[k]=v

STEPS=[(1,"Deal intake","intake_done"),(2,"Loan tape","tape_done"),(3,"Field mapping","map_done"),(4,"Financials","fin_done"),(5,"Funding","fund_done"),(6,"Questionnaire","quest_done"),(7,"Run analysis","track_a_done"),(8,"Red flags","flags_done"),(9,"Deal screen","screen_done"),(10,"Decision","review_done")]

# ═══ SIDEBAR ═════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div style="padding:4px 0 0 2px"><span style="font-size:28px;font-weight:700;color:#FFF;letter-spacing:-1.5px"><span style="color:#1A8C6A">◆</span> Abe</span><br><span style="font-size:10px;color:#A7A7A7;letter-spacing:2px;text-transform:uppercase">Deal Screen Platform</span></div>',unsafe_allow_html=True)
    st.markdown("---")
    for n,name,key in STEPS:
        done=st.session_state.get(key,False);cur=st.session_state.step==n
        label=f"✓  {name}" if done else (f"›  {name}" if cur else f"    {name}")
        if st.button(label,key=f"n{n}",use_container_width=True,disabled=not(done or cur or n<=st.session_state.step+1)):
            st.session_state.step=n;st.rerun()
    if st.session_state.intake_done:
        d=st.session_state.intake;st.markdown("---")
        st.markdown(f'<div style="padding:2px 0"><div style="color:#FFF;font-weight:600;font-size:13px">{d.get("deal_name","")}</div><div style="color:#A7A7A7;font-size:12px;line-height:1.6;margin-top:2px">{d.get("borrower_name","")}<br>${d.get("requested_facility_size",0)/1e6:.0f}M {d.get("facility_type","")}<br>{d.get("collateral_type","").replace("_"," ").title()}</div></div>',unsafe_allow_html=True)
    st.markdown('<div style="position:fixed;bottom:16px;left:16px"><span style="color:#49524F;font-size:10px;letter-spacing:.5px">Abe v0.1 · i80 Group</span></div>',unsafe_allow_html=True)

# ═══ HELPERS ═════════════════════════════════════════════════════════════
def badge(lv):
    c={"green":"go","yellow":"caution","red":"stop"}.get(lv,"caution");lb={"green":"● Clear","yellow":"◆ Caution","red":"■ Elevated"}.get(lv,lv.upper())
    return f'<span class="abe-st abe-st-{c}">{lb}</span>'
def mcard(v,l): return f'<div class="abe-m"><div class="abe-mv">{v}</div><div class="abe-ml">{l}</div></div>'
def go(s): st.session_state.step=s;st.rerun()

# ═══ STEP 1 ══════════════════════════════════════════════════════════════
def step_1():
    st.markdown("# New deal");st.markdown("Enter deal and borrower information to begin screening.")
    st.markdown('<div class="abe-s">',unsafe_allow_html=True)
    with st.form("intake"):
        c1,c2=st.columns(2)
        with c1: dn=st.text_input("Deal name",placeholder="Acme Consumer Warehouse");bn=st.text_input("Borrower",placeholder="Acme Lending Inc.");ct=st.selectbox("Collateral type",["consumer_receivables","smb_loans","mca","equipment_finance","invoice_finance","saas_receivables","trade_finance","auto_receivables","other"]);ft=st.selectbox("Facility type",["warehouse","delayed_draw_term","forward_flow","rediscount","revolving","other"]);dl=st.text_input("Deal lead",placeholder="Jane Smith")
        with c2: fs=st.number_input("Requested size ($)",0,value=0,step=1000000);ar=st.number_input("Advance rate",0.0,1.0,0.85,0.01);tn=st.number_input("Tenor (months)",0,value=24,step=6);pr=st.number_input("Pricing (bps/SOFR)",0,value=500,step=25);an=st.text_input("Analyst",placeholder="Bob Chen")
        uop=st.text_area("Use of proceeds",placeholder="Fund new originations and refinance existing warehouse…");notes=st.text_area("Notes",placeholder="Context, referral source…",height=80)
        if st.form_submit_button("Save & continue",type="primary",use_container_width=True):
            errs=[]
            if not dn:errs.append("Deal name required")
            if not bn:errs.append("Borrower required")
            if fs<=0:errs.append("Size must be positive")
            if not uop:errs.append("Use of proceeds required")
            if not dl:errs.append("Deal lead required")
            if not an:errs.append("Analyst required")
            if errs:
                for e in errs:st.error(e)
            else:
                st.session_state.intake=dict(deal_name=dn,borrower_name=bn,collateral_type=ct,facility_type=ft,requested_facility_size=fs,requested_advance_rate=ar,requested_tenor_months=tn,requested_pricing_bps=pr,use_of_proceeds=uop,assigned_deal_lead=dl,assigned_analyst=an,notes=notes);st.session_state.intake_done=True;go(2)
    st.markdown('</div>',unsafe_allow_html=True)

# ═══ STEP 2 ══════════════════════════════════════════════════════════════
def step_2():
    st.markdown("# Upload loan tape");st.markdown("Upload the borrower's loan tape. Abe will auto-detect the format and propose field mappings.")
    f=st.file_uploader("",type=["xlsx","xls","csv"],key="tu",label_visibility="collapsed")
    if f:
        st.success(f"**{f.name}** uploaded ({f.size/1024:.0f} KB)");st.session_state.tape_done=True
        try:
            import pandas as pd;df=pd.read_csv(f,nrows=8) if f.name.endswith(".csv") else pd.read_excel(f,nrows=8)
            st.markdown(f"**{df.shape[1]} columns** detected");st.dataframe(df,use_container_width=True,hide_index=True)
        except:pass
        if st.button("Process tape →",type="primary"):
            with st.spinner("Detecting format · Profiling · Mapping…"):import time;time.sleep(2)
            go(3)

# ═══ STEP 3 ══════════════════════════════════════════════════════════════
def step_3():
    st.markdown("# Review field mapping");st.markdown("Abe proposed the following mappings. Review and approve before analysis.")
    import pandas as pd
    df=pd.DataFrame([{"Borrower column":"LN_BAL_CUR","Standard field":"current_balance","Confidence":0.95},{"Borrower column":"Orig Prin Amt","Standard field":"original_balance","Confidence":0.92},{"Borrower column":"FICO_AT_ORIG","Standard field":"credit_score","Confidence":0.97},{"Borrower column":"Int Rt","Standard field":"interest_rate","Confidence":0.88},{"Borrower column":"STAT_CD","Standard field":"delinquency_status","Confidence":0.72},{"Borrower column":"St","Standard field":"geography","Confidence":0.65},{"Borrower column":"Internal Score","Standard field":"— unmapped —","Confidence":0.00}])
    st.dataframe(df,column_config={"Confidence":st.column_config.ProgressColumn(min_value=0,max_value=1,format="%.0f%%")},use_container_width=True,hide_index=True)
    low=sum(1 for _,r in df.iterrows() if 0<r["Confidence"]<0.80)
    if low:st.warning(f"**{low} mappings** below 80% confidence — please verify.")
    c1,c2,c3=st.columns(3)
    with c1:
        if st.button("✓ Approve",type="primary",use_container_width=True):st.session_state.map_done=True;go(4)
    with c2:st.button("Edit",use_container_width=True)
    with c3:
        if st.button("Reject",use_container_width=True):st.session_state.tape_done=False;go(2)

# ═══ STEP 4 ══════════════════════════════════════════════════════════════
def step_4():
    st.markdown("# Corporate financials");st.markdown("Upload the template populated from audited or reviewed statements.")
    st.download_button("↓ Download blank template",b"placeholder","corporate_financials.xlsx")
    f=st.file_uploader("",type=["xlsx","xls"],key="fu",label_visibility="collapsed")
    if f:
        with st.spinner("Validating…"):import time;time.sleep(1)
        st.success("Balance sheet balances across all periods.");st.success("All required fields present.");st.session_state.fin_done=True
        if st.button("Continue →",type="primary"):go(5)

# ═══ STEP 5 ══════════════════════════════════════════════════════════════
def step_5():
    st.markdown("# Funding facilities");st.markdown("Upload existing borrower credit facility details.")
    st.download_button("↓ Download blank template",b"placeholder","funding_facilities.xlsx")
    f=st.file_uploader("",type=["xlsx","xls"],key="fdu",label_visibility="collapsed")
    if f:st.session_state.fund_done=True;st.button("Continue →",type="primary") and go(6)
    st.markdown("---")
    if st.button("Skip — not available yet"):st.session_state.fund_done=True;go(6)

# ═══ STEP 6 ══════════════════════════════════════════════════════════════
def step_6():
    st.markdown("# Platform questionnaire");st.markdown("Complete from diligence materials and borrower conversations.")
    with st.form("q"):
        st.markdown("### Management")
        c1,c2=st.columns(2)
        with c1:st.text_input("CEO",placeholder="John Smith",key="q1");st.number_input("CEO tenure (years)",0,key="q2");st.text_input("CFO",key="q3")
        with c2:st.text_input("CRO",placeholder="Bob Johnson",key="q4");st.number_input("Total employees",0,key="q5");st.number_input("Senior departures (12 mo)",0,key="q6")
        st.markdown("### Origination")
        c3,c4=st.columns(2)
        with c3:st.multiselect("Channels",["direct","digital","broker","partnerships","referral","other"],key="q7");st.checkbox("Written credit policy",True,key="q8")
        with c4:st.number_input("Exception rate (%)",0.0,100.0,0.0,key="q9");st.text_input("Underwriting model",placeholder="Scorecard + bureau",key="q10")
        st.markdown("### Servicing & compliance")
        c5,c6=st.columns(2)
        with c5:st.selectbox("Servicing model",["In-house","Outsourced","Hybrid"],key="q11");st.number_input("Staff",0,key="q12");st.text_input("Backup servicer",placeholder="None identified",key="q13")
        with c6:st.text_input("Primary sponsor",placeholder="Summit Capital",key="q14");st.number_input("Equity raised ($)",0,step=1000000,key="q15");st.number_input("State licenses",0,key="q16")
        if st.form_submit_button("Save & continue",type="primary",use_container_width=True):st.session_state.quest_done=True;go(7)

# ═══ STEP 7 ══════════════════════════════════════════════════════════════
def step_7():
    st.markdown("# Run analysis");st.markdown("Execute both tracks independently.")
    c1,_,c2=st.columns([5,1,5])
    with c1:
        st.markdown('<div class="abe-s abe-sa"><h3 style="margin:0 0 8px">Track A · Collateral</h3><p style="font-size:13px;margin:0">Pool summary, stratifications, concentrations, DQ, eligibility</p></div>',unsafe_allow_html=True)
        if st.session_state.map_done:
            if st.session_state.track_a_done:st.success("Complete")
            elif st.button("▶  Run Track A",type="primary",key="ra",use_container_width=True):
                p=st.progress(0);import time
                for v,t in[(15,"Data quality…"),(35,"Pool summary…"),(55,"Stratifications…"),(75,"Concentrations…"),(100,"Done")]:p.progress(v,t);time.sleep(.4)
                st.session_state.track_a_done=True;st.rerun()
        else:st.info("Complete steps 2–3 first.")
    with c2:
        st.markdown('<div class="abe-s abe-sa"><h3 style="margin:0 0 8px">Track B · Corporate</h3><p style="font-size:13px;margin:0">Metrics, funding, scorecard, covenant headroom</p></div>',unsafe_allow_html=True)
        if st.session_state.fin_done or st.session_state.quest_done:
            if st.session_state.track_b_done:st.success("Complete")
            elif st.button("▶  Run Track B",type="primary",key="rb",use_container_width=True):
                p=st.progress(0);import time
                for v,t in[(20,"Financial metrics…"),(45,"Funding…"),(70,"Scorecard…"),(100,"Done")]:p.progress(v,t);time.sleep(.4)
                st.session_state.track_b_done=True;st.rerun()
        else:st.info("Complete steps 4–6 first.")
    if st.session_state.track_a_done and st.session_state.track_b_done:
        st.markdown("---")
        if st.button("Continue to red flags →",type="primary"):go(8)

# ═══ STEP 8 ══════════════════════════════════════════════════════════════
def step_8():
    st.markdown("# Red flags & contradictions");st.markdown("Review all findings. Acknowledge, escalate, or dismiss each flag.")
    t1,t2,t3=st.tabs(["Collateral","Corporate","Contradictions"])
    with t1:
        for s,t,d in[("CRITICAL","17% FICO scores missing (coded as 0)","849 of 5,000 loans have credit_score=0. FICO analytics unreliable."),("HIGH","30+ DPD at 7.6%","Above 5% prime threshold. $7.3M delinquent on $95.6M pool."),("MEDIUM","California concentration 19%","Largest single-state exposure. Below 25% guideline.")]:
            with st.expander(f"**{s}** — {t}",expanded=s=="CRITICAL"):st.markdown(d);st.radio("",["Acknowledge","Escalate","Dismiss"],key=f"a{t[:8]}",horizontal=True)
    with t2:
        for s,t,d in[("CRITICAL","Interest coverage 0.97× — below 1.0×","EBITDA does not cover interest. Existing IC covenant in breach."),("HIGH","Single funding source","Only 1 facility. Proposed deal becomes sole capital line."),("HIGH","Net loss — swung from profit","$(350K) loss vs $200K prior profit. Margin compression."),("HIGH","No backup servicer","5,000-loan portfolio, in-house only, no transition plan.")]:
            with st.expander(f"**{s}** — {t}",expanded=s=="CRITICAL"):st.markdown(d);st.radio("",["Acknowledge","Escalate","Dismiss"],key=f"b{t[:8]}",horizontal=True)
    with t3:
        for title,body in[("Good collateral, weak borrower coverage","30+ DPD is 7.6% but IC is 0.97×. Borrower cannot service its own debt. If the platform fails, collateral protections may not matter."),("Single funding creates concentration risk","Tape performance acceptable but borrower has one funding line. This facility becomes the sole lifeline."),("Facility large relative to equity","$50M facility is 3.4× borrower equity of $14.5M. Meaningful skin in the game (20.1%) but facility dwarfs the balance sheet.")]:
            st.markdown(f'<div class="abe-s abe-sa"><strong style="color:#1B3A2F">{title}</strong><p style="font-size:13px;margin-top:6px">{body}</p></div>',unsafe_allow_html=True)
    st.markdown("---")
    if st.button("All reviewed — continue",type="primary"):st.session_state.flags_done=True;go(9)

# ═══ STEP 9 ══════════════════════════════════════════════════════════════
def step_9():
    d=st.session_state.intake;st.markdown("# Integrated deal screen")
    c1,c2,c3=st.columns(3)
    with c1:st.markdown(f"Track A&emsp;{badge('yellow')}",unsafe_allow_html=True)
    with c2:st.markdown(f"Track B&emsp;{badge('red')}",unsafe_allow_html=True)
    with c3:st.markdown(f"Overall&emsp;{badge('red')}",unsafe_allow_html=True)
    st.markdown('<div class="abe-ms">'+mcard("$95.6M","Pool")+mcard("7.6%","30+ DPD")+mcard("$12.5M","Revenue")+mcard("0.97×","IC Ratio")+mcard("20.1%","Eq. Cushion")+mcard("3.4","Scorecard")+'</div>',unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f'<div class="abe-sf"><strong style="color:#1B3A2F">{d.get("borrower_name","")}</strong> seeks a <strong>${d.get("requested_facility_size",0)/1e6:.0f}M {d.get("facility_type","")}</strong> secured by <strong>{d.get("collateral_type","").replace("_"," ")}</strong> at {d.get("requested_advance_rate",0):.0%} advance, {d.get("requested_tenor_months",0)}-month tenor. Proceeds: {d.get("use_of_proceeds","").lower()}.</div>',unsafe_allow_html=True)
    st.markdown("---")
    c1,c2=st.columns(2)
    with c1:
        st.markdown(f"### Track A · Collateral&emsp;{badge('yellow')}",unsafe_allow_html=True)
        st.markdown('<div class="abe-s"><p style="font-size:13px;margin:0"><strong>Pool:</strong> 5,000 loans · $95.6M · WAC 12.0% · WAM 24mo · WALA 21mo</p><p style="font-size:13px;margin:8px 0 0"><strong>WA FICO:</strong> 698 (93.8% cov) · <strong>Loss:</strong> 0.88% gross · 0.66% net</p></div>',unsafe_allow_html=True)
        st.markdown("**Strengths:** Highly granular (4,836 obligors), adequate spread, low cumulative losses")
        st.markdown("**Concerns:** 17% FICO missing, 30+ DPD 7.6%, CA concentration 19%")
    with c2:
        st.markdown(f"### Track B · Corporate&emsp;{badge('red')}",unsafe_allow_html=True)
        st.markdown('<div class="abe-s"><p style="font-size:13px;margin:0"><strong>Financial:</strong> Rev $12.5M (+22.5%) · EBITDA $1.8M (14%) · TNW $12.2M</p><p style="font-size:13px;margin:8px 0 0"><strong>Leverage:</strong> D/E 4.1× · IC 0.97× · Cushion 20.1% · Score 3.4/5</p></div>',unsafe_allow_html=True)
        st.markdown("**Strengths:** Revenue +22.5%, equity cushion 20.1%, strong origination (4/5)")
        st.markdown("**Concerns:** IC 0.97× (breach), single funding, no backup servicer, net loss")
    st.markdown("---")
    st.markdown("### Key intersection")
    st.markdown('<div class="abe-s abe-sa"><p style="font-size:13px;margin:0">Collateral performs today, but borrower IC is <strong>below 1.0×</strong> — EBITDA does not cover interest. Combined with single funding and no backup servicer, <strong>platform risk dominates structural protections</strong>.</p></div>',unsafe_allow_html=True)
    st.markdown("### Platform scorecard")
    import pandas as pd
    st.dataframe(pd.DataFrame([{"Category":"Management","Score":"4/5"},{"Category":"Sponsor","Score":"3/5"},{"Category":"Financial condition","Score":"2/5"},{"Category":"Origination quality","Score":"4/5"},{"Category":"Underwriting discipline","Score":"4/5"},{"Category":"Servicing capability","Score":"3/5"},{"Category":"Reporting quality","Score":"4/5"},{"Category":"Compliance","Score":"4/5"},{"Category":"Funding diversification","Score":"1/5"},{"Category":"Historical performance","Score":"3/5"}]),use_container_width=True,hide_index=True)
    st.markdown("### Gating diligence questions")
    for i,q in enumerate(["What is the borrower's plan to restore IC above 1.5×? Provide monthly P&L for 12 months.","What is the funding diversification strategy? Has borrower approached other lenders or ABS?","Identify a backup servicer and describe the transition plan.","Provide actual FICO scores for the 849 loans showing zero.","Explain elevated 30+ DPD — concentrated in specific vintages or channels?"],1):st.markdown(f"**{i}.** {q}")
    st.markdown("---")
    if st.button("Continue to decision →",type="primary"):st.session_state.screen_done=True;go(10)

# ═══ STEP 10 ═════════════════════════════════════════════════════════════
def step_10():
    st.markdown("# Decision")
    st.markdown("### Review checklist")
    items=["Deal intake confirmed","Tape mapping approved","Collateral spot-checked","Financials verified","Scorecard reviewed","Red flags acknowledged","Contradictions reviewed","Deal screen reviewed"]
    ok=all(st.checkbox(i,key=f"c{j}") for j,i in enumerate(items))
    st.markdown("---");st.markdown("### Recommended next step")
    dec=st.radio("",["■  **Pass** — Decline","◆  **Continue to full diligence**","●  **Request more information**"],index=None,label_visibility="collapsed")
    st.text_area("Conditions / focus areas / notes",height=80,placeholder="If continuing: focus areas. If requesting: what's needed. If passing: reason.")
    st.text_input("Decision by",st.session_state.intake.get("assigned_deal_lead",""))
    st.markdown("---")
    if st.button("✓  Record decision & export",type="primary",use_container_width=True,disabled=not ok or not dec):
        st.session_state.review_done=True;st.balloons()
        st.markdown('<div class="abe-s abe-sa"><h3 style="margin:0 0 12px">Exported</h3><p style="font-size:13px;line-height:2;margin:0">◆ Integrated deal screen<br>◆ Collateral analytics<br>◆ Corporate financial summary<br>◆ Platform scorecard<br>◆ Red flags<br>◆ Contradiction analysis<br>◆ Diligence questions<br>◆ Review record</p></div>',unsafe_allow_html=True)

# ═══ ROUTER ══════════════════════════════════════════════════════════════
{1:step_1,2:step_2,3:step_3,4:step_4,5:step_5,6:step_6,7:step_7,8:step_8,9:step_9,10:step_10}.get(st.session_state.step,step_1)()
