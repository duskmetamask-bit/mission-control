"""
OPENCLAW MISSION CONTROL DASHBOARD
Single-pane-of-glass visibility and control over OpenClaw agent operations.
"""

import streamlit as st
import subprocess
import json
import time
from datetime import datetime, timezone, timedelta
import re

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mission Control",
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

AWST_TZ = timezone(timedelta(hours=8))
CLI_TIMEOUT = 8  # seconds

# ─── Helpers ──────────────────────────────────────────────────────────────────

def run_cli(args: list, timeout=CLI_TIMEOUT) -> str:
    """Run openclaw CLI command, return stdout or error message."""
    try:
        result = subprocess.run(
            ["openclaw"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/home/dusk"
        )
        return result.stdout.strip() if result.returncode == 0 else f"ERROR {result.returncode}: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"EXCEPTION: {e}"


def parse_table(raw: str) -> list[dict]:
    """Parse CLI table output (separated by │) into list of dicts."""
    lines = raw.strip().split("\n")
    if len(lines) < 2:
        return []
    headers = [h.strip() for h in lines[0].split("│")[1:-1]]
    rows = []
    for line in lines[2:]:
        cells = [c.strip() for c in line.split("│")[1:-1]]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


def parse_json(raw: str) -> list[dict]:
    """Try parse CLI JSON output."""
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "sessions" in data:
            return data["sessions"]
        return [data]
    except:
        return []


def to_awst(ts_str: str) -> str:
    """Convert ISO timestamp to AWST human string."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        dt_awst = dt.astimezone(AWST_TZ)
        return dt_awst.strftime("%I:%M %p AWST")
    except:
        return ts_str


def time_ago(ts_str: str) -> str:
    """Return human-readable time since ISO timestamp."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - dt
        s = int(delta.total_seconds())
        if s < 60:   return f"{s}s ago"
        if s < 3600: return f"{s//60}m ago"
        if s < 86400: return f"{s//3600}h ago"
        return f"{s//86400}d ago"
    except:
        return ts_str


def status_color(status: str) -> str:
    status = status.lower()
    if "ok" in status or "running" in status or "idle" in status:
        return "green"
    if "error" in status or "fail" in status or "stopped" in status:
        return "red"
    return "gray"


# ─── Dark Theme ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    html, body, .stApp { background-color: #0d1117; color: #c9d1d9; }
    .stApp { border: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff !important; font-family: 'Courier New', monospace; }
    .element-container { color: #c9d1d9; }
    label, .stText, p, span, div { color: #c9d1d9 !important; }
    .StatusBox { padding: 6px 12px; border-radius: 4px; font-size: 13px; font-weight: 700; display: inline-block; }
    .ok     { background: #1a4d2e; color: #3fb950; border: 1px solid #3fb95044; }
    .error  { background: #4d1a1a; color: #f85149; border: 1px solid #f8514944; }
    .idle   { background: #1a2d4d; color: #58a6ff; border: 1px solid #58a6ff44; }
    .running { background: #1a4d2e; color: #3fb950; border: 1px solid #3fb95044; }
    .metric-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; text-align: center; }
    .metric-num { font-size: 28px; font-weight: 700; color: #58a6ff; font-family: 'Courier New', monospace; }
    .metric-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    table { border-collapse: collapse; width: 100%; }
    th { background: #161b22; color: #8b949e; padding: 8px 12px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #30363d; }
    td { padding: 8px 12px; border-bottom: 1px solid #21262d; font-size: 13px; }
    tr:hover { background: #161b22; }
    .log-entry { padding: 6px 12px; border-left: 3px solid; font-size: 12px; margin: 4px 0; background: #0d1117; }
    .log-spawn   { border-color: #3fb950; }
    .log-kill    { border-color: #f85149; }
    .log-cron    { border-color: #58a6ff; }
    .log-session { border-color: #d29922; }
    .log-info    { border-color: #8b949e; }
    .sidebar-sidebar { background: #161b22; }
    .stButton > button { background: #238636; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; }
    .stButton > button:hover { background: #2ea043; }
    .stSelectbox > div { background: #0d1117; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    .block-container { padding: 1rem 2rem; }
</style>
""", unsafe_allow_html=True)


# ─── HEADER ───────────────────────────────────────────────────────────────────

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.markdown("### 🎛️ MISSION CONTROL")
    st.caption("OpenClaw Operations Dashboard")
with col2:
    st.markdown(f"**Now:** `{datetime.now(AWST_TZ).strftime('%I:%M %p AWST')}`")
with col3:
    auto = st.toggle("Auto-refresh (30s)", value=True, key="auto_refresh")

st.divider()

# ─── SIDEBAR: QUICK ACTIONS ───────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚡ Quick Actions")
    st.divider()

    st.markdown("**🚀 Spawn Subagent**")
    with st.expander("Spawn new subagent", expanded=False):
        agent_type = st.selectbox("Type", ["content", "research", "build", "outreach", "custom"], key="spawn_type")
        agent_task = st.text_area("Task description", key="spawn_task", height=80)
        if st.button("Spawn", key="spawn_btn"):
            st.info("Spawning not yet wired — coming in v2")

    st.divider()
    st.markdown("**⏰ Trigger Cron**")
    with st.expander("Run cron now", expanded=False):
        cron_select = st.selectbox("Select cron", ["vault-sync", "research", "content"], key="cron_select")
        if st.button("Run Now", key="cron_run_btn"):
            st.info("Cron trigger not yet wired — coming in v2")

    st.divider()
    st.markdown("**📨 Send to Session**")
    with st.expander("Send message", expanded=False):
        sess_id = st.text_input("Session ID", key="sess_id")
        sess_msg = st.text_area("Message", key="sess_msg", height=60)
        if st.button("Send", key="sess_send_btn"):
            st.info("Session messaging not yet wired — coming in v2")

    st.divider()
    if st.button("🔄 Refresh All", use_container_width=True):
        st.rerun()

# ─── DATA FETCH ────────────────────────────────────────────────────────────────

now = datetime.now(AWST_TZ).strftime("%I:%M %p AWST")

with st.spinner("Fetching OpenClaw state..."):
    cron_raw   = run_cli(["cron", "list"])
    sub_raw    = run_cli(["subagents", "list"])
    sess_raw   = run_cli(["sessions", "list"])
    status_raw = run_cli(["status"])

# Parse cron
cron_jobs = parse_table(cron_raw)

# Parse subagents
subagents = parse_table(sub_raw)

# Parse sessions (may be JSON or table)
sessions = []
if sess_raw.startswith("[") or sess_raw.startswith("{"):
    sessions = parse_json(sess_raw)
else:
    sessions = parse_table(sess_raw)

# Parse status
status_lines = status_raw.split("\n") if status_raw else []

# ─── METRIC CARDS ─────────────────────────────────────────────────────────────

st.markdown("#### System Overview")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

ok_crons  = len([c for c in cron_jobs   if "ok"   in c.get("Status","").lower()])
err_crons = len([c for c in cron_jobs   if "error" in c.get("Status","").lower() or "fail" in c.get("Status","").lower()])
run_subs  = len([s for s in subagents   if "running" in s.get("Status","").lower()])
act_sess  = len(sessions)

with m_col1:
    st.markdown(f'<div class="metric-card"><div class="metric-num">{len(cron_jobs)}</div><div class="metric-label">Cron Jobs</div></div>', unsafe_allow_html=True)
with m_col2:
    st.markdown(f'<div class="metric-card"><div class="metric-num" style="color:#3fb950">{ok_crons} ✅</div><div class="metric-label">OK Crons</div></div>', unsafe_allow_html=True)
with m_col3:
    st.markdown(f'<div class="metric-card"><div class="metric-num">{len(subagents)}</div><div class="metric-label">Subagents</div></div>', unsafe_allow_html=True)
with m_col4:
    st.markdown(f'<div class="metric-card"><div class="metric-num" style="color:#3fb950">{act_sess}</div><div class="metric-label">Sessions</div></div>', unsafe_allow_html=True)

st.divider()

# ─── CRON JOBS ────────────────────────────────────────────────────────────────

st.markdown("#### ⏰ Cron Jobs")
if cron_jobs:
    # Build display table
    cron_display = []
    for c in cron_jobs:
        status = c.get("Status", "unknown")
        badge_class = "ok" if "ok" in status.lower() else ("error" if "error" in status.lower() or "fail" in status.lower() else "idle")
        cron_display.append({
            "Name": c.get("Name", ""),
            "Schedule": c.get("Schedule", ""),
            "Next Run": c.get("Next", ""),
            "Last Run": c.get("Last", ""),
            "Status": f'<span class="StatusBox {badge_class}">{status.upper()}</span>',
            "ID": c.get("ID", "")[:8]
        })
    st.write("⚠️ Some actions require cron ID — copy from `ID` column")
    st.dataframe(cron_display, use_container_width=True, hide_index=True, column_config={
        "Status": st.column_config.Column(width="small"),
        "ID": st.column_config.Column(width="small"),
    }, html=True)
else:
    st.info("No cron jobs found")

st.divider()

# ─── SUBAGENTS ────────────────────────────────────────────────────────────────

st.markdown("#### 🤖 Active Subagents")
if subagents:
    sub_display = []
    for s in subagents:
        status = s.get("Status", "unknown")
        badge_class = "running" if "running" in status.lower() else ("error" if "error" in status.lower() else "idle")
        sub_display.append({
            "Name": s.get("Name", "")[:40],
            "Status": f'<span class="StatusBox {badge_class}">{status.upper()}</span>',
            "Started": s.get("Started", ""),
            "Model": s.get("Model", "-"),
            "ID": s.get("ID", "")[:8]
        })
    st.dataframe(sub_display, use_container_width=True, hide_index=True, column_config={
        "Status": st.column_config.Column(width="small"),
        "ID": st.column_config.Column(width="small"),
    }, html=True)
else:
    st.info("No active subagents")

st.divider()

# ─── SESSIONS ────────────────────────────────────────────────────────────────

st.markdown("#### 💾 Sessions")
if sessions:
    sess_display = []
    for s in sessions:
        kind = s.get("kind", s.get("type", "unknown"))
        last = s.get("last", s.get("lastActive", s.get("updated", "")))
        sess_display.append({
            "Session": s.get("id", s.get("sessionId", ""))[:12] + "...",
            "Full ID": s.get("id", s.get("sessionId", "")),
            "Kind": kind,
            "Last Active": last,
            "Messages": s.get("messages", s.get("messageCount", "-")),
        })
    st.dataframe(sess_display, use_container_width=True, hide_index=True, column_config={
        "Full ID": st.column_config.Column(width="medium"),
    }, html=True)
else:
    st.info("No active sessions — or CLI timed out")

st.divider()

# ─── RAW STATUS OUTPUT ────────────────────────────────────────────────────────

with st.expander("📋 Raw openclaw status output"):
    st.code(status_raw if status_raw else "(empty)")

# ─── ACTIVITY LOG ─────────────────────────────────────────────────────────────

st.markdown("#### 📜 Activity Log")
log_entries = []

for c in cron_jobs:
    if "ok" in c.get("Status","").lower():
        log_entries.append({"time": c.get("Last",""), "type": "cron", "msg": f'Cron fired: {c.get("Name","")} [{c.get("Status","")}]'})
    elif c.get("Last") == "-":
        log_entries.append({"time": "never", "type": "info", "msg": f'Cron never fired: {c.get("Name","")} [{c.get("Status","")}]'})

for s in subagents:
    log_entries.append({"time": s.get("Started",""), "type": "spawn", "msg": f'Subagent: {s.get("Name","")} [{s.get("Status","")}]'})

log_entries.sort(key=lambda x: x["time"] or "", reverse=True)

for entry in log_entries[:20]:
    etype = entry["type"]
    icon = {"spawn":"🚀","cron":"⏰","session":"💾","kill":"🛑","info":"ℹ️"}.get(etype,"•")
    css_class = etype
    st.markdown(f'<div class="log-entry log-{css_class}">{icon} {entry["msg"]} <span style="color:#8b949e">— {entry["time"] or "?"}</span></div>', unsafe_allow_html=True)

# ─── AUTO REFRESH ─────────────────────────────────────────────────────────────

if auto:
    time.sleep(0.1)
    st.rerun()

st.caption(f"Last refreshed: {now}")