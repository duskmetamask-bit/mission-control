"""
THE AI WAR ROOM
Shared AI brain + Build Factory. Fully operating machine.
Yuki + Dusk + Mewy all contribute and retrieve.
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
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

AWST_TZ = timezone(timedelta(hours=8))
VAULT_BASE = Path.home() / ".openclaw/vault/dawn-vault/YUKI/projects/mission-control"
WAR_ROOM_JSON = VAULT_BASE / "war-room.json"
PIPELINE_JSON = VAULT_BASE / "pipeline.json"
VAULT_BASE.mkdir(parents=True, exist_ok=True)

# ─── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path):
    try:
        return json.loads(path.read_text())
    except:
        return None

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))

def now_awst():
    return datetime.now(AWST_TZ)

def ts_ago(ts):
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
        delta = now_awst().replace(tzinfo=timezone.utc) - dt
        s = int(delta.total_seconds())
        if s < 60:   return f"{s}s ago"
        if s < 3600: return f"{s//60}m ago"
        if s < 86400: return f"{s//3600}h ago"
        return f"{s//86400}d ago"
    except:
        return str(ts) if ts else "?"

CATEGORIES = {
    "whats_happening": "🔥 What's Happening",
    "problems": "😤 Problems People Face",
    "what_people_want": "🔍 What People Want",
    "model_comparisons": "🧠 Model Comparisons",
    "opportunity_seeds": "💡 Opportunity Seeds",
}

CONTRIBUTORS = ["Yuki", "Dusk", "Mewy"]

def score_opp(demand, feasible, margin, time_build):
    total = demand + feasible + margin + (10 - time_build)
    color = "🟢" if total >= 24 else ("🟡" if total >= 18 else "🔴")
    return total, color

# ─── Theme ─────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    html, body, .stApp { background-color: #0d1117; color: #c9d1d9; }
    h1, h2, h3, h4 { color: #58a6ff !important; font-family: 'Courier New', monospace; }
    .stText, p, span, div, label { color: #c9d1d9 !important; }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div { background: #161b22 !important; color: #c9d1d9 !important; border: 1px solid #30363d !important; }
    .stNumberInput > div > div > input { background: #161b22 !important; color: #c9d1d9 !important; border: 1px solid #30363d !important; }
    .stButton > button { background: #238636; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 600; }
    .stButton > button:hover { background: #2ea043; }
    .stButtonSecondary > button { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; }
    .intel-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; margin: 8px 0; }
    .intel-category { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #8b949e; }
    .intel-content { font-size: 13px; color: #e6edf3; margin: 6px 0; }
    .intel-meta { font-size: 11px; color: #8b949e; }
    .tag { background: #1f3a5f; color: #58a6ff; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin: 2px; display: inline-block; }
    .category-tab { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 10px; margin: 4px 0; cursor: pointer; }
    .opp-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; margin: 8px 0; border-left: 4px solid; }
    .score-high { border-left-color: #3fb950; }
    .score-med { border-left-color: #d29922; }
    .score-low { border-left-color: #f85149; }
    .kanban-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; margin: 6px 0; border-left: 4px solid; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    section[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }
    .metric-box { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 14px; text-align: center; }
    .metric-n { font-size: 28px; font-weight: 700; color: #58a6ff; font-family: 'Courier New', monospace; }
    .metric-l { font-size: 10px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .divider { border-top: 1px solid #30363d; margin: 12px 0; }
</style>
""", unsafe_allow_html=True)

# ─── Load Data ────────────────────────────────────────────────────────────────

data = load_json(WAR_ROOM_JSON) or {
    "intel": {cat: [] for cat in CATEGORIES},
    "opportunities": [],
    "projects": [],
    "activity": []
}

pipeline = load_json(PIPELINE_JSON) or {"projects": [], "opportunities": [], "last_research": None}

# Merge pipeline opportunities into data for display
all_opportunities = data.get("opportunities", []) + pipeline.get("opportunities", [])
intel_categories = data.get("intel", {})
projects = pipeline.get("projects", [])

active_projects = [p for p in projects if p.get("stage") not in ("shipped", "killed")]
shipped = [p for p in projects if p.get("stage") == "shipped"]
building = [p for p in projects if p.get("stage") == "building"]

# ─── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🧠 The AI War Room")
    st.divider()

    # Quick stats
    col1, col2 = st.columns(2)
    with col1:
        total_intel = sum(len(v) for v in intel_categories.values())
        st.markdown(f'<div class="metric-box"><div class="metric-n">{total_intel}</div><div class="metric-l">Intel Entries</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><div class="metric-n">{len(all_opportunities)}</div><div class="metric-l">Opportunities</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="metric-box"><div class="metric-n" style="color:#3fb950">{len(shipped)}</div><div class="metric-l">Shipped</div></div>', unsafe_allow_html=True)

    st.divider()

    # Add intel
    st.markdown("**➕ Dump Intel**")
    with st.expander("New intel entry", expanded=True):
        cat = st.selectbox("Category", list(CATEGORIES.keys()), format_func=lambda x: CATEGORIES[x], key="intel_cat")
        contributor = st.selectbox("From", CONTRIBUTORS, key="intel_contrib")
        content = st.text_area("What do you know?", height=80, key="intel_content")
        source = st.text_input("Source (optional)", placeholder="Reddit / HN / search / observation", key="intel_source")
        tags_raw = st.text_input("Tags (comma-separated)", placeholder="gpt-4, automation, small-business", key="intel_tags")
        if st.button("Dump into Brain", key="dump_intel"):
            if content.strip():
                tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
                entry = {
                    "id": str(uuid.uuid4()),
                    "category": cat,
                    "content": content.strip(),
                    "contributor": contributor,
                    "source": source.strip(),
                    "tags": tags,
                    "created": now_awst().isoformat(),
                    "updated": now_awst().isoformat(),
                    "linked_opportunity_id": None,
                    "used_in_build": None
                }
                data["intel"][cat].append(entry)
                save_json(WAR_ROOM_JSON, data)
                st.success("Dumped! 🧠")
                st.rerun()

    st.divider()

    # Quick add opportunity
    st.markdown("**💡 Add Opportunity**")
    with st.expander("New opportunity", expanded=False):
        opp_name = st.text_input("Opportunity name", key="opp_name")
        opp_signal = st.text_area("Why this matters", height=60, key="opp_signal")
        if st.button("Add Opportunity", key="add_opp_btn"):
            if opp_name:
                opp = {
                    "id": str(uuid.uuid4()),
                    "name": opp_name,
                    "demand_signal": opp_signal,
                    "contributor": "Yuki",
                    "source": "manual",
                    "scored": False,
                    "score": None,
                    "created": now_awst().isoformat()
                }
                data["opportunities"].append(opp)
                save_json(WAR_ROOM_JSON, data)
                st.success("Added!")
                st.rerun()

    st.divider()

    # Refresh
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

    st.caption(f"Last refresh: {now_awst().strftime('%I:%M %p AWST')}")

# ─── Main Tabs ─────────────────────────────────────────────────────────────────

st.markdown("### 🧠 The AI War Room")

tabs = st.tabs([
    "🧠 AI Intel Brain",
    "📊 Opportunity Scanner",
    "🔨 Pipeline Board",
    "🔨 Active Builds",
    "✅ Shipped",
    "📜 Activity"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 0: AI INTEL BRAIN
# ═══════════════════════════════════════════════════════════════════════════════

with tabs[0]:
    st.markdown("#### 🧠 AI Intel Brain")
    st.caption("All intel flows through here — Yuki, Dusk, and Mewy all contribute and retrieve.")

    # Category filter
    filter_cat = st.selectbox("Filter by category", ["ALL"] + list(CATEGORIES.keys()), format_func=lambda x: CATEGORIES[x] if x != "ALL" else "All Categories", key="filter_cat")

    # Search
    search_q = st.text_input("🔍 Search intel", placeholder="Search across all intel...", key="intel_search")

    st.divider()

    # Show intel
    shown = 0
    for cat_key, cat_name in CATEGORIES.items():
        entries = intel_categories.get(cat_key, [])

        # Filter
        if filter_cat != "ALL" and cat_key != filter_cat:
            continue

        # Search
        if search_q:
            entries = [e for e in entries if search_q.lower() in e.get("content","").lower() or search_q.lower() in " ".join(e.get("tags",[])).lower()]

        if not entries:
            continue

        st.markdown(f"**{cat_name}** ({len(entries)} entries)")
        for entry in sorted(entries, key=lambda x: x.get("created",""), reverse=True):
            tags_html = " ".join([f'<span class="tag">{t}</span>' for t in entry.get("tags",[])])
            st.markdown(f"""
            <div class="intel-card">
                <div class="intel-meta">
                    <span style="color:#58a6ff">{entry.get('contributor','?')}</span>
                    · {ts_ago(entry.get('created',''))}
                    · Source: {entry.get('source','unknown')}
                </div>
                <div class="intel-content">{entry.get('content','')}</div>
                <div>{tags_html}</div>
            </div>
            """, unsafe_allow_html=True)
            shown += 1

            # Quick action: turn into opportunity
            col1, col2 = st.columns([1,1])
            with col1:
                if st.button(f"💡 Score as Opportunity", key=f"score_{entry['id']}"):
                    opp = {
                        "id": str(uuid.uuid4()),
                        "name": entry.get("content","")[:80],
                        "demand_signal": entry.get("content",""),
                        "contributor": entry.get("contributor","Yuki"),
                        "source": f"intel: {entry.get('category','unknown')}",
                        "scored": False,
                        "score": None,
                        "created": now_awst().isoformat(),
                        "linked_intel_id": entry["id"]
                    }
                    data["opportunities"].append(opp)
                    save_json(WAR_ROOM_JSON, data)
                    st.success("Added to opportunities!")
                    st.rerun()
            with col2:
                if st.button(f"🗑️", key=f"del_{entry['id']}"):
                    data["intel"][cat_key] = [e for e in data["intel"][cat_key] if e["id"] != entry["id"]]
                    save_json(WAR_ROOM_JSON, data)
                    st.rerun()
            st.divider()

    if shown == 0:
        st.info("No intel yet — dump some via the sidebar!")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: OPPORTUNITY SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

with tabs[1]:
    st.markdown("#### 📊 Opportunity Scanner")
    st.caption("Score each opportunity. ≥18/40 → pipeline. ≥24/40 → auto-build.")

    unscored = [o for o in all_opportunities if not o.get("scored")]
    scored = [o for o in all_opportunities if o.get("scored")]

    st.markdown(f"**Unscored ({len(unscored)})**")
    if unscored:
        for opp in unscored:
            with st.container():
                st.markdown(f"""
                <div class="opp-card score-low">
                <div style="font-weight:700; color:#e6edf3">{opp.get('name','?')}</div>
                <div style="font-size:12px; color:#8b949e; margin: 4px 0">{opp.get('demand_signal','')[:120]}</div>
                <div style="font-size:11px; color:#8b949e">From: {opp.get('contributor','?')} · {ts_ago(opp.get('created',''))} · {opp.get('source','')}</div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    demand = st.number_input("Demand", 1, 10, 5, key=f"d_{opp['id']}")
                with c2:
                    feasible = st.number_input("Feasible", 1, 10, 5, key=f"f_{opp['id']}")
                with c3:
                    margin = st.number_input("Margin", 1, 10, 5, key=f"m_{opp['id']}")
                with c4:
                    time_build = st.number_input("Speed", 1, 10, 5, key=f"t_{opp['id']}")

                total, color = score_opp(demand, feasible, margin, time_build)
                st.markdown(f"**Score: {color} {total}/40**")

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"✅ Save Score", key=f"save_{opp['id']}", use_container_width=True):
                        opp["scored"] = True
                        opp["score"] = {"demand": demand, "feasibility": feasible, "margin": margin, "time_to_build": time_build, "total": total}
                        # Add to pipeline if score >= 18
                        if total >= 18:
                            proj = {
                                "id": str(uuid.uuid4()),
                                "name": opp.get("name",""),
                                "description": opp.get("demand_signal",""),
                                "stage": "scored",
                                "created": opp.get("created", now_awst().isoformat()),
                                "updated": now_awst().isoformat(),
                                "score": opp["score"],
                                "research_notes": f"Source: {opp.get('source','')}",
                                "build_log": [f"[{now_awst().strftime('%I:%M %p')}] Promoted from scanner (score: {total}/40)"],
                                "deployed_url": None,
                                "shipped_at": None,
                                "decision": None
                            }
                            pipeline["projects"].append(proj)
                        save_json(PIPELINE_JSON, pipeline)
                        save_json(WAR_ROOM_JSON, data)
                        st.rerun()
                with col_b:
                    if st.button(f"🗑️ Discard", key=f"kill_{opp['id']}", use_container_width=True):
                        data["opportunities"] = [o for o in data["opportunities"] if o["id"] != opp["id"]]
                        save_json(WAR_ROOM_JSON, data)
                        st.rerun()
                st.divider()
    else:
        st.info("No unscored opportunities")

    st.divider()

    st.markdown(f"**Scored Opportunities ({len(scored)})**")
    scored_sorted = sorted(scored, key=lambda x: x.get("score",{}).get("total",0), reverse=True)
    for opp in scored_sorted:
        s = opp.get("score", {})
        total = s.get("total", 0)
        border_class = "score-high" if total >= 24 else ("score-med" if total >= 18 else "score-low")
        st.markdown(f"""
        <div class="opp-card {border_class}">
        <div style="font-weight:700; font-size:15px; color:#e6edf3">{score_opp(s.get('demand',5), s.get('feasibility',5), s.get('margin',5), s.get('time_to_build',5))[1]} {opp.get('name','?')} — {total}/40</div>
        <div style="font-size:11px; color:#8b949e; margin: 4px 0">
            Demand: {s.get('demand','-')}/10 · Feasible: {s.get('feasibility','-')}/10 · Margin: {s.get('margin','-')}/10 · Speed: {s.get('time_to_build','-')}/10
        </div>
        <div style="font-size:12px; color:#c9d1d9">{opp.get('demand_signal','')[:120]}</div>
        <div style="font-size:11px; color:#8b949e; margin-top:4px">From: {opp.get('contributor','?')} · {opp.get('source','')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Quick action buttons
        c1, c2, c3 = st.columns(3)
        with c1:
            if total >= 24 and st.button(f"🔨 BUILD (≥24)", key=f"build_{opp['id']}", use_container_width=True):
                proj = {
                    "id": str(uuid.uuid4()),
                    "name": opp.get("name",""),
                    "description": opp.get("demand_signal",""),
                    "stage": "building",
                    "created": now_awst().isoformat(),
                    "updated": now_awst().isoformat(),
                    "score": s,
                    "research_notes": f"Source: {opp.get('source','')}",
                    "build_log": [f"[{now_awst().strftime('%I:%M %p')}] HIGH SCORE — AUTO-BUILD TRIGGERED ({total}/40)"],
                    "deployed_url": None,
                    "shipped_at": None,
                    "decision": None
                }
                pipeline["projects"].append(proj)
                save_json(PIPELINE_JSON, pipeline)
                st.info("Added to pipeline as BUILDING — Claude Code will spawn next cycle")
                st.rerun()
        with c2:
            if 18 <= total < 24 and st.button(f"📊 Score → Pipeline", key=f"promote_{opp['id']}", use_container_width=True):
                proj = {
                    "id": str(uuid.uuid4()),
                    "name": opp.get("name",""),
                    "description": opp.get("demand_signal",""),
                    "stage": "scored",
                    "created": now_awst().isoformat(),
                    "updated": now_awst().isoformat(),
                    "score": s,
                    "research_notes": f"Source: {opp.get('source','')}",
                    "build_log": [f"[{now_awst().strftime('%I:%M %p')}] Added to pipeline (score: {total}/40)"],
                    "deployed_url": None,
                    "shipped_at": None,
                    "decision": None
                }
                pipeline["projects"].append(proj)
                save_json(PIPELINE_JSON, pipeline)
                st.rerun()
        with c3:
            if st.button(f"🗑️", key=f"del_opp_{opp['id']}", use_container_width=True):
                data["opportunities"] = [o for o in data["opportunities"] if o["id"] != opp["id"]]
                save_json(WAR_ROOM_JSON, data)
                st.rerun()
        st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: PIPELINE BOARD
# ═══════════════════════════════════════════════════════════════════════════════

with tabs[2]:
    st.markdown("#### 🔨 Pipeline Board")

    cols = ["new", "scored", "building", "deployed", "shipped", "killed"]
    headers = ["🆕 New", "📊 Scored", "🔨 Building", "🚀 Deployed", "✅ Shipped", "🗑️ Killed"]
    colors = ["#6e7681", "#58a6ff", "#d29922", "#a371f7", "#3fb950", "#f85149"]

    cols_display = st.columns(6)
    for col_id, col_name, col_color, col_el in zip(cols, headers, colors, cols_display):
        with col_el:
            col_projs = [p for p in projects if p.get("stage") == col_id]
            st.markdown(f"**{col_name}** ({len(col_projs)})")

            for p in sorted(col_projs, key=lambda x: x.get("updated",""), reverse=True):
                score = p.get("score", {})
                total = score.get("total", 0)
                score_str = f"{total}/40" if total else "unscored"
                age = ts_ago(p.get("updated", p.get("created","")))

                st.markdown(f"""
                <div class="kanban-card" style="border-left-color: {col_color};">
                <div style="font-weight:700; color:#e6edf3">{p.get('name','')[:35]}</div>
                <div style="font-size:11px; color:#8b949e; margin: 3px 0">{p.get('description','')[:60]}</div>
                <div style="font-size:11px; color:#8b949e">Score: {score_str} · {age}</div>
                </div>
                """, unsafe_allow_html=True)

                # Stage transition buttons
                if col_id == "scored" and total >= 18:
                    if st.button(f"🔨 Build", key=f"build_proj_{p['id']}", use_container_width=True):
                        projs = pipeline["projects"]
                        for proj in projs:
                            if proj["id"] == p["id"]:
                                proj["stage"] = "building"
                                proj["updated"] = now_awst().isoformat()
                                proj["build_log"].append(f"[{now_awst().strftime('%I:%M %p')}] Build started")
                        save_json(PIPELINE_JSON, pipeline)
                        st.rerun()
                elif col_id == "building":
                    if st.button(f"🚀 Deployed", key=f"deployed_{p['id']}", use_container_width=True):
                        projs = pipeline["projects"]
                        for proj in projs:
                            if proj["id"] == p["id"]:
                                proj["stage"] = "deployed"
                                proj["updated"] = now_awst().isoformat()
                                proj["build_log"].append(f"[{now_awst().strftime('%I:%M %p')}] Marked deployed")
                        save_json(PIPELINE_JSON, pipeline)
                        st.rerun()
                elif col_id == "deployed":
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"✅ Ship", key=f"ship_proj_{p['id']}", use_container_width=True):
                            projs = pipeline["projects"]
                            for proj in projs:
                                if proj["id"] == p["id"]:
                                    proj["stage"] = "shipped"
                                    proj["shipped_at"] = now_awst().isoformat()
                                    proj["updated"] = now_awst().isoformat()
                                    proj["build_log"].append(f"[{now_awst().strftime('%I:%M %p')}] SHIPPED!")
                            save_json(PIPELINE_JSON, pipeline)
                            st.rerun()
                    with c2:
                        if st.button(f"🔁", key=f"iter_proj_{p['id']}", use_container_width=True):
                            projs = pipeline["projects"]
                            for proj in projs:
                                if proj["id"] == p["id"]:
                                    proj["stage"] = "iterate"
                                    proj["updated"] = now_awst().isoformat()
                            save_json(PIPELINE_JSON, pipeline)
                            st.rerun()

                st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: ACTIVE BUILDS
# ═══════════════════════════════════════════════════════════════════════════════

with tabs[3]:
    st.markdown("#### 🔨 Active Builds")

    if building:
        for p in building:
            st.markdown(f"""
            <div class="kanban-card" style="border-left-color:#d29922;">
            <div style="font-weight:700; font-size:16px; color:#e6edf3">{p.get('name','')}</div>
            <div style="font-size:12px; color:#c9d1d9; margin: 6px 0">{p.get('description','')[:100]}</div>
            <div style="font-size:11px; color:#8b949e">Score: {p.get('score',{}).get('total','?')}/40 · Started: {ts_ago(p.get('updated',''))}</div>
            </div>
            """, unsafe_allow_html=True)

            # Build log
            if p.get("build_log"):
                with st.expander("📋 Build log"):
                    for line in p.get("build_log", []):
                        st.text(line)

            col1, col2 = st.columns(2)
            with col1:
                url = st.text_input("Deployed URL", key=f"url_{p['id']}", placeholder="https://...")
            with col2:
                if st.button(f"🚀 Mark Deployed", key=f"depbtn_{p['id']}", use_container_width=True):
                    projs = pipeline["projects"]
                    for proj in projs:
                        if proj["id"] == p["id"]:
                            if url:
                                proj["deployed_url"] = url
                            proj["stage"] = "deployed"
                            proj["updated"] = now_awst().isoformat()
                            proj["build_log"].append(f"[{now_awst().strftime('%I:%M %p')}] Deployed: {url or 'no URL'}")
                    save_json(PIPELINE_JSON, pipeline)
                    st.rerun()
            st.divider()
    else:
        st.info("No active builds — score opportunities to fill this")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: SHIPPED
# ═══════════════════════════════════════════════════════════════════════════════

with tabs[4]:
    st.markdown(f"#### ✅ Shipped ({len(shipped)})")

    if shipped:
        for p in sorted(shipped, key=lambda x: x.get("shipped_at",""), reverse=True):
            st.markdown(f"""
            <div class="kanban-card" style="border-left-color:#3fb950;">
            <div style="font-weight:700; font-size:16px; color:#e6edf3">{p.get('name','')}</div>
            <div style="font-size:12px; color:#c9d1d9; margin: 4px 0">{p.get('description','')[:100]}</div>
            <div style="font-size:11px; color:#8b949e">
                Score: {p.get('score',{}).get('total','?')}/40 · Shipped: {ts_ago(p.get('shipped_at',''))}
            </div>
            <div style="font-size:12px; margin-top:4px">
                <a href="{p.get('deployed_url','#')}" target="_blank">{p.get('deployed_url','no link yet')}</a>
            </div>
            </div>
            """, unsafe_allow_html=True)
            if p.get("build_log"):
                with st.expander("📋 Build log"):
                    for line in p.get("build_log", []):
                        st.text(line)
    else:
        st.info("Nothing shipped yet — score some opportunities and build!")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: ACTIVITY
# ═══════════════════════════════════════════════════════════════════════════════

with tabs[5]:
    st.markdown("#### 📜 Activity Log")

    all_events = []

    for p in projects:
        all_events.append({"ts": p.get("updated", p.get("created","")), "type": "project", "msg": f"[{p.get('stage','').upper()}] {p.get('name','')}"})
        for log_line in p.get("build_log", []):
            all_events.append({"ts": p.get("updated",""), "type": "log", "msg": log_line, "detail": p.get("name","")})

    for opp in all_opportunities:
        all_events.append({"ts": opp.get("created",""), "type": "opp", "msg": f"💡 NEW: {opp.get('name','')}"})

    for cat_key, cat_name in CATEGORIES.items():
        for entry in intel_categories.get(cat_key, []):
            all_events.append({
                "ts": entry.get("created",""),
                "type": "intel",
                "msg": f"🧠 [{entry.get('contributor','?')}] {entry.get('content','')[:60]}",
                "detail": entry.get("category","")
            })

    all_events.sort(key=lambda x: x.get("ts") or "", reverse=True)

    type_colors = {"project": "#58a6ff", "log": "#8b949e", "opp": "#d29922", "intel": "#a371f7"}
    for ev in all_events[:50]:
        color = type_colors.get(ev.get("type",""), "#8b949e")
        st.markdown(f"""
        <div style="border-left: 3px solid {color}; padding: 4px 12px; margin: 4px 0; background: #0d1117; border-radius: 0 4px 4px 0;">
        {ev.get('msg','')} <span style="color:#8b949e; font-size:11px">— {ts_ago(ev.get('ts',''))}</span>
        </div>
        """, unsafe_allow_html=True)

st.caption(f"The AI War Room · Vault: {VAULT_BASE}")