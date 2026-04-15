# OPENCLAW MISSION CONTROL

Single-pane-of-glass visibility and control over OpenClaw agent operations.

## What it does
- Monitors subagents, cron jobs, and sessions in real-time
- Dark ops dashboard with auto-refresh
- Pulls data directly from OpenClaw CLI

## Deploy

```bash
cd mission-control
git init
git add app.py requirements.txt README.md
git commit -m "initial"
git remote add origin https://github.com/duskmetamask-bit/mission-control.git
git push -u origin main
```

Then connect to Streamlit Community Cloud: https://share.streamlit.io

## Requirements
- streamlit
- Python 3.9+

## Local run
```bash
streamlit run app.py
```