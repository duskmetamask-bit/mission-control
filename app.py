"""
THE AI WAR ROOM
Autonomous SaaS/project prototype factory.
Yuki runs: research → evaluate → build → deploy → review → loop
"""

import streamlit as st
import json
import uuid
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The AI War Room",
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

AWST_TZ = timezone(timedelta(hours=8))
VAULT_PIPELINE = Path.home() / ".openclaw/vault/dawn-vault/YUKI/projects/mission-control/pipeline.json"
CLI_TIMEOUT = 8

# ─── Helpers ───────────────────────────────────────────────────────────────────

def load_pipeline() -> dict:
    try:
        return json.loads(VAULT_PIPELINE.read_text())
    except:
        return {"projects": [], "opportunities": [], "last_research": None, "build_queue": []}


def save_pipeline(data: dict):
    VAULT_PIPELINE.write_text(json.dumps(data, indent=2))


def now_awst():
    return datetime.now(AWST_TZ)


def ts_ago(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
        delta = now_awst().replace(tzinfo=timezone.utc) - dt
        s = int(delta.total_seconds())
        if s < 60:   return f"{s}s ago"
        if s < 3600: return f"{s//60}m ago"
        if s < 86400: return f"{s//3600}h ago"
        return f"{s//86400}d ago"
    except:
        return ts


def score_color(total: int) -> str:
    if total >= 24: return "🟢"
    if total >= 18: return "🟡"
    return "🔴"


STAGE_EMOJI = {
    "new": "🆕",
    "scored": "📊",
    "building": "🔨",
    "deployed": "🚀",
    "shipped": "✅",
    "killed": "🗑️",
    "iterate": "🔁",
}

STAGE_COLORS = {
    "new": "#6e7681",
    "scored": "#58a6ff",
    "building": "#d29922",
    "deployed": "#a371f7",
    "shipped": "#3fb950",
    "killed": "#f85149",
    "iterate": "#d29922",
}


# ─── Dark Theme ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    html, body, .stApp { background-color: #0d1117; color: #c9d1d9; }
    h1, h2, h3, h4 { color: #58a6ff !important; font-family: 'Courier New', monospace; }
    .stApp { }
    label, .stText, p, span, div { color: #c9d1d9 !important; }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div { background: #161b22 !important; color: #c9d1d9 !important; border: 1px solid #30363d !important; }
    .stNumberInput > div > div > input { background: #161b22 !important; color: #c9d1d9 !important; border: 1px solid #30363d !important; }
    .stButton > button { background: #238636; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 600; width: 100%; }
    .stButton > button:hover { background: #2ea043; }
    .stButton-secondary > button { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; }
    .stButton-secondary > button:hover { background: #30363d; }
    .stSelectbox label, .stTextArea label, .stTextInput label { color: #8b949e !important; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
    table { border-collapse: collapse; width: 100%; }
    th { background: #161b22; color: #8b949e; padding: 8px 12px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #30363d; }
    td { padding: 8px 12px; border-bottom: 1px solid #21262d; font-size: 13px; }
    tr:hover { background: #161b22; }
    .metric-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; text-align: center; }
    .metric-num { font-size: 28px; font-weight: 700; color: #58a6ff; font-family: 'Courier New', monospace; }
    .metric-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .stage-badge { padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 700; display: inline-block; }
    .kanban-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; margin: 6px 0; border-left: 4px solid; }
    .opp-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; margin: 6px 0; }
    .pipeline-col { background: #0d1117; border-radius: 8px; padding: 10px; min-height: 400px; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    .block-container { padding: 1rem 1.5rem; }
    .stDivider > div > hr { border-color: #30363d; }
    section[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }
    .sidebar-section { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 12px; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)


# ─── Load Data ────────────────────────────────────────────────────────────────

data = load_pipeline()
projects = data.get("projects", [])
opportunities = data.get("opportunities", [])
build_queue = data.get("build_queue", [])

active_projects = [p for p in projects if p["stage"] not in ("shipped", "killed")]
scored_opps = [o for o in opportunities if o.get("scored")]
unscored_opps = [o for o in opportunities if not o.get("scored")]
shipped = [p for p in projects if p["stage"] == "shipped"]
building = [p for p in projects if p["stage"] == "building"]
deployed = [p for p in projects if p["stage"] == "deployed"]

# ─── Sidebar: Quick Actions ───────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚡ Mission Control")
    st.divider()

    # Quick stats
    st.markdown(f"""
    <div class="metric-card">
    <div class="metric-num" style="font-size:20px">{len(active_projects)}</div>
    <div class="metric-label">Active Projects</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="metric-card">
    <div class="metric-num" style="font-size:20px">{len(scored_opps)}</div>
    <div class="metric-label">Scored Opps</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="metric-card">
    <div class="metric-num" style="font-size:20px">{len(shipped)}</div>
    <div class="metric-label">Shipped</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # Add opportunity
    st.markdown("**📝 Add Opportunity**")
    with st.expander("New research lead", expanded=False):
        opp_name = st.text_input("What is it?", placeholder="AI tool / SaaS gap", key="opp_name")
        opp_source = st.text_input("Source", placeholder="Reddit / search / observation", key="opp_source")
        opp_signal = st.text_area("Demand signal", placeholder="Why do people want this?", key="opp_signal", height=80)
        if st.button("Add to Pipeline", key="add_opp_btn"):
            if opp_name:
                opps = load_pipeline()["opportunities"]
                opps.append({
                    "id": str(uuid.uuid4()),
                    "name": opp_name,
                    "source": opp_source,
                    "demand_signal": opp_signal,
                    "scored": False,
                    "score": None,
                    "created": datetime.now(AWST_TZ).isoformat()
                })
                save_pipeline({**load_pipeline(), "opportunities": opps})
                st.success("Added!")
                st.rerun()
            else:
                st.warning("Name required")

    st.divider()

    # Add project
    st.markdown("**🆕 Quick Add Project**")
    with st.expander("New project", expanded=False):
        proj_name = st.text_input("Project name", key="proj_quick_name")
        proj_desc = st.text_area("Description", key="proj_quick_desc", height=60)
        if st.button("Create Project", key="add_proj_btn"):
            if proj_name:
                projs = load_pipeline()["projects"]
                projs.append({
                    "id": str(uuid.uuid4()),
                    "name": proj_name,
                    "description": proj_desc,
                    "stage": "new",
                    "created": datetime.now(AWST_TZ).isoformat(),
                    "updated": datetime.now(AWST_TZ).isoformat(),
                    "score": None,
                    "research_notes": "",
                    "build_log": [],
                    "deployed_url": None,
                    "shipped_at": None,
                    "decision": None
                })
                save_pipeline({**load_pipeline(), "projects": projs})
                st.success("Project created!")
                st.rerun()

    st.divider()

    # Actions
    st.markdown("**🔄 Refresh**")
    if st.button("Refresh All", use_container_width=True):
        st.rerun()

    st.divider()
    if st.button("📋 Open Vault Pipeline", use_container_width=True):
        st.markdown(f"`{VAULT_PIPELINE}`")

    st.caption(f"Last refresh: {now_awst().strftime('%I:%M %p AWST')}")


# ─── Main Dashboard ───────────────────────────────────────────────────────────

st.markdown("### 🎛️ Mission Control — Build Factory")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Pipeline Board",
    "🔍 Opportunities",
    "🔨 Active Builds",
    "✅ Shipped",
    "📜 Activity"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: PIPELINE BOARD
# ═══════════════════════════════════════════════════════════════════════════════

with tab1:
    st.markdown("#### Project Pipeline")

    cols = ["new", "scored", "building", "deployed", "shipped", "killed"]
    headers = ["🆕 New", "📊 Scored", "🔨 Building", "🚀 Deployed", "✅ Shipped", "🗑️ Killed"]

    cols_display = st.columns(6)

    for i, (col_id, col_name, col_el) in enumerate(zip(cols, headers, cols_display)):
        with col_el:
            col_projs = [p for p in projects if p["stage"] == col_id]
            border_color = STAGE_COLORS.get(col_id, "#30363d")
            st.markdown(f"**{col_name}** ({len(col_projs)})")

            for p in sorted(col_projs, key=lambda x: x.get("updated", ""), reverse=True):
                score_str = f"**{p['score']['total']}/40**" if p.get("score") else "unscored"
                score_emoji = score_color(p["score"]["total"]) if p.get("score") else "⚪"
                age = ts_ago(p.get("updated", p.get("created", "")))

                with st.container():
                    st.markdown(f"""
                    <div class="kanban-card" style="border-left-color: {border_color};">
                    <div style="font-weight:700; color:#e6edf3">{p['name']}</div>
                    <div style="font-size:11px; color:#8b949e; margin: 4px 0">{p.get('description','')[:60]}</div>
                    <div style="font-size:11px; color:#8b949e">{score_emoji} {score_str} · {age}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Stage transition buttons
                    if col_id == "new":
                        if st.button(f"📊 Score", key=f"score_{p['id']}", use_container_width=True):
                            projs = load_pipeline()["projects"]
                            for proj in projs:
                                if proj["id"] == p["id"]:
                                    proj["stage"] = "scored"
                                    proj["updated"] = datetime.now(AWST_TZ).isoformat()
                            save_pipeline({**load_pipeline(), "projects": projs})
                            st.rerun()
                    elif col_id == "scored":
                        if p.get("score") and p["score"]["total"] >= 18:
                            if st.button(f"🔨 Build", key=f"build_{p['id']}", use_container_width=True):
                                projs = load_pipeline()["projects"]
                                for proj in projs:
                                    if proj["id"] == p["id"]:
                                        proj["stage"] = "building"
                                        proj["updated"] = datetime.now(AWST_TZ).isoformat()
                                        proj["build_log"].append(f"[{now_awst().strftime('%I:%M %p')}] Build started")
                                save_pipeline({**load_pipeline(), "projects": projs})
                                st.rerun()
                        if st.button(f"🗑️ Kill", key=f"kill_{p['id']}", use_container_width=True):
                            projs = load_pipeline()["projects"]
                            for proj in projs:
                                if proj["id"] == p["id"]:
                                    proj["stage"] = "killed"
                                    proj["updated"] = datetime.now(AWST_TZ).isoformat()
                            save_pipeline({**load_pipeline(), "projects": projs})
                            st.rerun()
                    elif col_id == "building":
                        if st.button(f"🚀 Deploy", key=f"deploy_{p['id']}", use_container_width=True):
                            projs = load_pipeline()["projects"]
                            for proj in projs:
                                if proj["id"] == p["id"]:
                                    proj["stage"] = "deployed"
                                    proj["updated"] = datetime.now(AWST_TZ).isoformat()
                                    proj["build_log"].append(f"[{now_awst().strftime('%I:%M %p')}] Deployed")
                            save_pipeline({**load_pipeline(), "projects": projs})
                            st.rerun()
                    elif col_id == "deployed":
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button(f"✅ Ship", key=f"ship_{p['id']}", use_container_width=True):
                                projs = load_pipeline()["projects"]
                                for proj in projs:
                                    if proj["id"] == p["id"]:
                                        proj["stage"] = "shipped"
                                        proj["shipped_at"] = datetime.now(AWST_TZ).isoformat()
                                        proj["updated"] = datetime.now(AWST_TZ).isoformat()
                                        proj["build_log"].append(f"[{now_awst().strftime('%I:%M %p')}] Shipped!")
                                save_pipeline({**load_pipeline(), "projects": projs})
                                st.rerun()
                        with c2:
                            if st.button(f"🔁 Iterate", key=f"iter_{p['id']}", use_container_width=True):
                                projs = load_pipeline()["projects"]
                                for proj in projs:
                                    if proj["id"] == p["id"]:
                                        proj["stage"] = "iterate"
                                        proj["updated"] = datetime.now(AWST_TZ).isoformat()
                                save_pipeline({**load_pipeline(), "projects": projs})
                                st.rerun()
                    elif col_id == "iterate":
                        if st.button(f"🔨 Back to Build", key=f"backbuild_{p['id']}", use_container_width=True):
                            projs = load_pipeline()["projects"]
                            for proj in projs:
                                if proj["id"] == p["id"]:
                                    proj["stage"] = "building"
                                    proj["updated"] = datetime.now(AWST_TZ).isoformat()
                            save_pipeline({**load_pipeline(), "projects": projs})
                            st.rerun()

                    st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: OPPORTUNITIES
# ═══════════════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown("#### 🔍 Opportunity Scanner")

    # Unscored opportunities
    st.markdown(f"**Unscored ({len(unscored_opps)})**")
    if unscored_opps:
        for opp in sorted(unscored_opps, key=lambda x: x.get("created", ""), reverse=True):
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    <div class="opp-card">
                    <div style="font-weight:700; color:#e6edf3">{opp['name']}</div>
                    <div style="font-size:11px; color:#8b949e; margin: 4px 0">Source: {opp.get('source','unknown')} · {ts_ago(opp.get('created',''))}</div>
                    <div style="font-size:12px; color:#c9d1d9">{opp.get('demand_signal','')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown("Score it:")
                    demand = st.number_input("Demand", 1, 10, 5, key=f"d_{opp['id']}")
                    feasible = st.number_input("Feasible", 1, 10, 5, key=f"f_{opp['id']}")
                    margin = st.number_input("Margin", 1, 10, 5, key=f"m_{opp['id']}")
                    time_build = st.number_input("Time (1=慢, 10=快)", 1, 10, 5, key=f"t_{opp['id']}")

                    total = demand + feasible + margin + (10 - time_build)
                    st.markdown(f"**Total: {score_color(total)} {total}/40**")

                    if st.button(f"Save Score → Project", key=f"score_opp_{opp['id']}", use_container_width=True):
                        opps = load_pipeline()["opportunities"]
                        projs = load_pipeline()["projects"]
                        for o in opps:
                            if o["id"] == opp["id"]:
                                o["scored"] = True
                                o["score"] = {"demand": demand, "feasibility": feasible, "margin": margin, "time_to_build": time_build, "total": total}
                        projs.append({
                            "id": str(uuid.uuid4()),
                            "name": opp["name"],
                            "description": opp.get("demand_signal", ""),
                            "stage": "scored",
                            "created": opp.get("created", datetime.now(AWST_TZ).isoformat()),
                            "updated": datetime.now(AWST_TZ).isoformat(),
                            "score": {"demand": demand, "feasibility": feasible, "margin": margin, "time_to_build": time_build, "total": total},
                            "research_notes": f"Source: {opp.get('source','')}\nDemand signal: {opp.get('demand_signal','')}",
                            "build_log": [],
                            "deployed_url": None,
                            "shipped_at": None,
                            "decision": None
                        })
                        save_pipeline({**load_pipeline(), "opportunities": opps, "projects": projs})
                        st.rerun()
    else:
        st.info("No unscored opportunities — add one via the sidebar")

    st.divider()

    # Scored opportunities
    st.markdown(f"**Scored Opportunities ({len(scored_opps)})**")
    if scored_opps:
        scored_sorted = sorted(scored_opps, key=lambda x: x.get("score", {}).get("total", 0), reverse=True)
        for opp in scored_sorted:
            s = opp.get("score", {})
            total = s.get("total", 0)
            st.markdown(f"""
            <div class="opp-card" style="border-left: 4px solid {STAGE_COLORS.get('scored','#58a6ff') if total >= 18 else '#f85149' if total < 14 else '#d29922'}">
            <div style="font-weight:700; color:#e6edf3">{score_color(total)} {opp['name']} — {total}/40</div>
            <div style="font-size:11px; color:#8b949e; margin: 4px 0">
                Demand: {s.get('demand','-')}/10 · Feasible: {s.get('feasibility','-')}/10 · Margin: {s.get('margin','-')}/10 · Time: {s.get('time_to_build','-')}/10
            </div>
            <div style="font-size:12px; color:#c9d1d9">{opp.get('demand_signal','')}</div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if total >= 18 and st.button(f"🔨 Start Build →", key=f"build_opp_{opp['id']}", use_container_width=True):
                    projs = load_pipeline()["projects"]
                    projs.append({
                        "id": str(uuid.uuid4()),
                        "name": opp["name"],
                        "description": opp.get("demand_signal", ""),
                        "stage": "building",
                        "created": datetime.now(AWST_TZ).isoformat(),
                        "updated": datetime.now(AWST_TZ).isoformat(),
                        "score": s,
                        "research_notes": f"Source: {opp.get('source','')}\nDemand signal: {opp.get('demand_signal','')}",
                        "build_log": [f"[{now_awst().strftime('%I:%M %p')}] Build queued from scored opp"],
                        "deployed_url": None,
                        "shipped_at": None,
                        "decision": None
                    })
                    # Remove from opportunities
                    opps = [o for o in load_pipeline()["opportunities"] if o["id"] != opp["id"]]
                    save_pipeline({**load_pipeline(), "projects": projs, "opportunities": opps})
                    st.rerun()
            with col2:
                if st.button(f"🗑️ Discard", key=f"kill_opp_{opp['id']}", use_container_width=True):
                    opps = [o for o in load_pipeline()["opportunities"] if o["id"] != opp["id"]]
                    save_pipeline({**load_pipeline(), "opportunities": opps})
                    st.rerun()
    else:
        st.info("No scored opportunities yet")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: ACTIVE BUILDS
# ═══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.markdown("#### 🔨 Active Builds")

    if building:
        for p in building:
            border_color = STAGE_COLORS.get("building", "#d29922")
            st.markdown(f"""
            <div class="kanban-card" style="border-left-color: {border_color};">
            <div style="font-weight:700; font-size:16px; color:#e6edf3">{p['name']}</div>
            <div style="font-size:12px; color:#c9d1d9; margin: 6px 0">{p.get('description','')}</div>
            <div style="font-size:11px; color:#8b949e">Score: {p['score']['total']}/40 · Started: {ts_ago(p.get('updated',''))}</div>
            </div>
            """, unsafe_allow_html=True)

            # Build log
            if p.get("build_log"):
                with st.expander("📋 Build log"):
                    for log_line in p.get("build_log", []):
                        st.text(log_line)

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"🚀 Mark Deployed", key=f"deployed_btn_{p['id']}", use_container_width=True):
                    projs = load_pipeline()["projects"]
                    for proj in projs:
                        if proj["id"] == p["id"]:
                            proj["stage"] = "deployed"
                            proj["updated"] = datetime.now(AWST_TZ).isoformat()
                            proj["build_log"].append(f"[{now_awst().strftime('%I:%M %p')}] Marked deployed")
                    save_pipeline({**load_pipeline(), "projects": projs})
                    st.rerun()
            with col2:
                url = st.text_input("Deployed URL", key=f"url_{p['id']}", placeholder="https://...")
                if st.button("Save URL", key=f"save_url_{p['id']}", use_container_width=True):
                    if url:
                        projs = load_pipeline()["projects"]
                        for proj in projs:
                            if proj["id"] == p["id"]:
                                proj["deployed_url"] = url
                                proj["updated"] = datetime.now(AWST_TZ).isoformat()
                        save_pipeline({**load_pipeline(), "projects": projs})
                        st.rerun()
            with col3:
                if st.button(f"🗑️ Kill Build", key=f"killbuild_{p['id']}", use_container_width=True):
                    projs = load_pipeline()["projects"]
                    for proj in projs:
                        if proj["id"] == p["id"]:
                            proj["stage"] = "killed"
                            proj["updated"] = datetime.now(AWST_TZ).isoformat()
                    save_pipeline({**load_pipeline(), "projects": projs})
                    st.rerun()
            st.divider()
    else:
        st.info("No active builds")

    # Deployed (needs action)
    if deployed:
        st.markdown("#### 🚀 Deployed — Awaiting Review")
        for p in deployed:
            border_color = STAGE_COLORS.get("deployed", "#a371f7")
            st.markdown(f"""
            <div class="kanban-card" style="border-left-color: {border_color};">
            <div style="font-weight:700; font-size:16px; color:#e6edf3">{p['name']}</div>
            <div style="font-size:12px; margin: 4px 0">
                <a href="{p.get('deployed_url','#')}" target="_blank">{p.get('deployed_url','no URL')}</a>
            </div>
            <div style="font-size:11px; color:#8b949e">Deployed: {ts_ago(p.get('updated',''))}</div>
            </div>
            """, unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button(f"✅ APPROVE SHIP", key=f"ship_btn_{p['id']}", use_container_width=True):
                    projs = load_pipeline()["projects"]
                    for proj in projs:
                        if proj["id"] == p["id"]:
                            proj["stage"] = "shipped"
                            proj["shipped_at"] = datetime.now(AWST_TZ).isoformat()
                            proj["updated"] = datetime.now(AWST_TZ).isoformat()
                            proj["build_log"].append(f"[{now_awst().strftime('%I:%M %p')}] APPROVED SHIPPED")
                    save_pipeline({**load_pipeline(), "projects": projs})
                    st.rerun()
            with c2:
                if st.button(f"🔁 ITERATE", key=f"iter_btn_{p['id']}", use_container_width=True):
                    projs = load_pipeline()["projects"]
                    for proj in projs:
                        if proj["id"] == p["id"]:
                            proj["stage"] = "iterate"
                            proj["updated"] = datetime.now(AWST_TZ).isoformat()
                    save_pipeline({**load_pipeline(), "projects": projs})
                    st.rerun()
            with c3:
                if st.button(f"🗑️ KILL", key=f"kill_btn_{p['id']}", use_container_width=True):
                    projs = load_pipeline()["projects"]
                    for proj in projs:
                        if proj["id"] == p["id"]:
                            proj["stage"] = "killed"
                            proj["updated"] = datetime.now(AWST_TZ).isoformat()
                    save_pipeline({**load_pipeline(), "projects": projs})
                    st.rerun()
            st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: SHIPPED
# ═══════════════════════════════════════════════════════════════════════════════

with tab4:
    st.markdown(f"#### ✅ Shipped ({len(shipped)})")
    if shipped:
        for p in sorted(shipped, key=lambda x: x.get("shipped_at", ""), reverse=True):
            border_color = STAGE_COLORS.get("shipped", "#3fb950")
            st.markdown(f"""
            <div class="kanban-card" style="border-left-color: {border_color};">
            <div style="font-weight:700; font-size:16px; color:#e6edf3">{p['name']}</div>
            <div style="font-size:12px; color:#c9d1d9; margin: 4px 0">{p.get('description','')}</div>
            <div style="font-size:11px; color:#8b949e">
                Score: {p.get('score',{}).get('total','?')}/40 · Shipped: {ts_ago(p.get('shipped_at',''))}
            </div>
            <div style="font-size:12px; margin-top: 4px">
                <a href="{p.get('deployed_url','#')}" target="_blank">{p.get('deployed_url','no link')}</a>
            </div>
            </div>
            """, unsafe_allow_html=True)
            if p.get("build_log"):
                with st.expander("📋 Build log"):
                    for log_line in p.get("build_log", []):
                        st.text(log_line)
    else:
        st.info("Nothing shipped yet — build something!")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: ACTIVITY LOG
# ═══════════════════════════════════════════════════════════════════════════════

with tab5:
    st.markdown("#### 📜 Recent Activity")

    # Build combined log
    all_events = []

    for p in projects:
        all_events.append({
            "ts": p.get("updated", p.get("created", "")),
            "type": "project",
            "msg": f"[{p['stage'].upper()}] {p['name']}",
            "detail": p.get("description", "")[:80]
        })
        for log_line in p.get("build_log", []):
            all_events.append({
                "ts": "",
                "type": "log",
                "msg": log_line,
                "detail": p["name"]
            })

    for opp in opportunities:
        all_events.append({
            "ts": opp.get("created", ""),
            "type": "opp",
            "msg": f"🆕 NEW OPP: {opp['name']}",
            "detail": opp.get("demand_signal", "")[:80]
        })

    all_events.sort(key=lambda x: x.get("ts") or "", reverse=True)

    type_colors = {"project": "#58a6ff", "log": "#8b949e", "opp": "#d29922"}
    type_icons = {"project": "📋", "log": "📝", "opp": "🔍"}

    for ev in all_events[:50]:
        color = type_colors.get(ev["type"], "#8b949e")
        icon = type_icons.get(ev["type"], "•")
        st.markdown(f"""
        <div style="border-left: 3px solid {color}; padding: 4px 12px; margin: 4px 0; background: #0d1117; border-radius: 0 4px 4px 0;">
        {icon} {ev['msg']} <span style="color:#8b949e; font-size:11px">— {ts_ago(ev.get('ts','')) if ev.get('ts') else 'no time'}</span>
        <div style="font-size:11px; color:#8b949e">{ev.get('detail','')}</div>
        </div>
        """, unsafe_allow_html=True)

st.caption(f"The AI War Room v1.0 · Pipeline: ~/.openclaw/vault/dawn-vault/YUKI/projects/mission-control/pipeline.json