"""
AI Website QA Agent - Playful, Interactive Web Dashboard & API
Features:
- Dynamic Interactive Particle Canvas & Ambient Glowing Orbs
- Holographic Live Radar / Sonar Scanner when Auditing
- Native Web Audio Sound Effects (bips, sonar pings, victory fanfare, bug squashes)
- "Squash This Bug" interactive remediation simulator with live score recalculation
- "Whack-A-Bug" Arcade mini-game overlay
- Multi-theme switcher (Cyber Dark, Arcade Neon, Synthwave, Clean Studio)
- 1-Click Jira / Slack ticket format copy
"""

import threading
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from ai_website_qa.agent import WebsiteQAAgent
from ai_website_qa.models import QAReport
from ai_website_qa.exporter import QAExporter
from mock_staging.server import app as mock_app

app = FastAPI(title="AI Website QA Agent - Playful Edition")

# In-memory storage for active and last completed scans
current_scan_status: Dict[str, Any] = {
    "status": "idle",
    "message": "Ready to hunt bugs.",
    "progress": 0.0,
    "last_report": None
}


class ScanRequest(BaseModel):
    url: str
    max_pages: int = 5
    max_depth: int = 2
    concurrency: int = 4
    timeout: int = 10


@app.get("/api/mock-status")
def mock_status():
    return {"status": "available", "mock_url": "http://127.0.0.1:8088/"}


@app.post("/api/audit")
def trigger_audit(req: ScanRequest):
    global current_scan_status
    if current_scan_status["status"] == "running":
        return JSONResponse(
            status_code=409,
            content={"error": "Another audit is currently running. Please wait."}
        )

    current_scan_status["status"] = "running"
    current_scan_status["progress"] = 0.05
    current_scan_status["message"] = f"Initializing Bug Radar for {req.url}..."

    def on_progress(msg: str, pct: float):
        current_scan_status["message"] = msg
        current_scan_status["progress"] = pct

    def worker():
        global current_scan_status
        try:
            agent = WebsiteQAAgent(
                max_pages=req.max_pages,
                max_depth=req.max_depth,
                concurrency=req.concurrency,
                timeout=req.timeout
            )
            report = agent.audit(req.url, progress_cb=on_progress)
            current_scan_status["last_report"] = report
            current_scan_status["status"] = "completed"
            current_scan_status["message"] = "Bug hunt completed! Prioritized intelligence ready."
            current_scan_status["progress"] = 1.0
        except Exception as e:
            current_scan_status["status"] = "failed"
            current_scan_status["message"] = f"Audit failed: {str(e)}"
            current_scan_status["progress"] = 0.0

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return {"status": "started", "target_url": req.url}


@app.get("/api/scan-status")
def get_scan_status():
    global current_scan_status
    report_data = None
    if current_scan_status["last_report"]:
        report_data = current_scan_status["last_report"].model_dump()

    return {
        "status": current_scan_status["status"],
        "message": current_scan_status["message"],
        "progress": current_scan_status["progress"],
        "has_report": current_scan_status["last_report"] is not None,
        "report": report_data
    }


@app.get("/api/export/markdown")
def export_md():
    if not current_scan_status["last_report"]:
        raise HTTPException(status_code=404, detail="No scan report available.")
    md_content = QAExporter.to_markdown(current_scan_status["last_report"])
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=qa-report.md"}
    )


@app.get("/api/export/html")
def export_html():
    if not current_scan_status["last_report"]:
        raise HTTPException(status_code=404, detail="No scan report available.")
    html_content = QAExporter.to_standalone_html(current_scan_status["last_report"])
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=qa-report.html"}
    )


@app.get("/api/export/json")
def export_json():
    if not current_scan_status["last_report"]:
        raise HTTPException(status_code=404, detail="No scan report available.")
    return JSONResponse(content=current_scan_status["last_report"].model_dump())


@app.get("/", response_class=HTMLResponse)
def dashboard_ui():
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="en" data-theme="cyber">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🛡️ AI Website QA Agent | Playful Bug Hunter</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
  <style>
    /* Theme Variables */
    :root[data-theme="cyber"] {
      --bg: #070b14;
      --card-bg: rgba(15, 23, 42, 0.78);
      --card-alt: rgba(30, 41, 59, 0.7);
      --border: rgba(51, 65, 85, 0.7);
      --border-glow: rgba(59, 130, 246, 0.5);
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent: #8b5cf6;
      --p0: #ef4444;
      --p1: #f97316;
      --p2: #eab308;
      --p3: #38bdf8;
      --confirmed: #dc2626;
      --suspected: #d97706;
      --success: #10b981;
      --particle-color: rgba(96, 165, 250, 0.35);
      --orb-1: rgba(59, 130, 246, 0.15);
      --orb-2: rgba(139, 92, 246, 0.15);
    }
    :root[data-theme="arcade"] {
      --bg: #0d0221;
      --card-bg: rgba(26, 14, 53, 0.85);
      --card-alt: rgba(45, 24, 92, 0.75);
      --border: rgba(255, 0, 127, 0.4);
      --border-glow: rgba(0, 240, 255, 0.6);
      --text: #ffffff;
      --text-muted: #b8a2db;
      --primary: #ff007f;
      --primary-hover: #e00070;
      --accent: #00f0ff;
      --p0: #ff0055;
      --p1: #ff7700;
      --p2: #ffe600;
      --p3: #00f0ff;
      --confirmed: #ff0055;
      --suspected: #ff7700;
      --success: #00ffaa;
      --particle-color: rgba(255, 0, 127, 0.4);
      --orb-1: rgba(255, 0, 127, 0.2);
      --orb-2: rgba(0, 240, 255, 0.2);
    }
    :root[data-theme="synthwave"] {
      --bg: #130924;
      --card-bg: rgba(27, 16, 54, 0.82);
      --card-alt: rgba(46, 26, 92, 0.7);
      --border: rgba(147, 51, 234, 0.4);
      --border-glow: rgba(236, 72, 153, 0.6);
      --text: #fdf4ff;
      --text-muted: #d8b4fe;
      --primary: #d946ef;
      --primary-hover: #c026d3;
      --accent: #06b6d4;
      --p0: #f43f5e;
      --p1: #fb923c;
      --p2: #facc15;
      --p3: #38bdf8;
      --confirmed: #e11d48;
      --suspected: #ea580c;
      --success: #34d399;
      --particle-color: rgba(217, 70, 239, 0.35);
      --orb-1: rgba(217, 70, 239, 0.2);
      --orb-2: rgba(6, 182, 212, 0.2);
    }
    :root[data-theme="studio"] {
      --bg: #0f172a;
      --card-bg: rgba(30, 41, 59, 0.88);
      --card-alt: rgba(51, 65, 85, 0.7);
      --border: rgba(71, 85, 105, 0.5);
      --border-glow: rgba(148, 163, 184, 0.5);
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --primary-hover: #0284c7;
      --accent: #818cf8;
      --p0: #f87171;
      --p1: #fb923c;
      --p2: #fde047;
      --p3: #7dd3fc;
      --confirmed: #ef4444;
      --suspected: #f59e0b;
      --success: #4ade80;
      --particle-color: rgba(56, 189, 248, 0.3);
      --orb-1: rgba(56, 189, 248, 0.15);
      --orb-2: rgba(129, 140, 248, 0.15);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      min-height: 100vh;
      overflow-x: hidden;
      position: relative;
    }

    /* Ambient Background Components */
    #bg-canvas {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      z-index: 0;
      pointer-events: none;
    }
    .orb {
      position: fixed;
      border-radius: 50%;
      filter: blur(100px);
      z-index: 0;
      pointer-events: none;
      animation: floatOrb 18s ease-in-out infinite alternate;
    }
    .orb-1 {
      top: 5%;
      left: 10%;
      width: 420px;
      height: 420px;
      background: var(--orb-1);
    }
    .orb-2 {
      bottom: 10%;
      right: 8%;
      width: 480px;
      height: 480px;
      background: var(--orb-2);
      animation-duration: 22s;
    }
    @keyframes floatOrb {
      0% { transform: translate(0, 0) scale(1); }
      50% { transform: translate(60px, 40px) scale(1.15); }
      100% { transform: translate(-40px, 80px) scale(0.9); }
    }

    .main-wrap {
      position: relative;
      z-index: 10;
      max-width: 1320px;
      margin: 0 auto;
      padding: 24px 20px 80px;
    }

    /* Top Navigation */
    .top-nav {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .brand-icon {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, var(--primary), var(--accent));
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 26px;
      box-shadow: 0 0 20px var(--border-glow);
      cursor: pointer;
      transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .brand-icon:hover {
      transform: scale(1.15) rotate(8deg);
    }
    .brand-title {
      font-family: 'Space Grotesk', sans-serif;
      font-size: 22px;
      font-weight: 700;
      letter-spacing: -0.5px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .tag-pill {
      font-size: 11px;
      font-weight: 800;
      padding: 3px 8px;
      border-radius: 6px;
      background: rgba(139, 92, 246, 0.2);
      color: #c084fc;
      border: 1px solid rgba(139, 92, 246, 0.4);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .brand-desc {
      font-size: 13px;
      color: var(--text-muted);
    }

    .nav-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .interactive-btn {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 14px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
      backdrop-filter: blur(12px);
    }
    .interactive-btn:hover {
      transform: translateY(-2px);
      border-color: var(--primary);
      box-shadow: 0 4px 14px var(--border-glow);
    }
    .interactive-btn:active {
      transform: scale(0.96);
    }
    .arcade-btn {
      background: linear-gradient(135deg, #ec4899, #8b5cf6);
      color: #fff;
      border: none;
      box-shadow: 0 4px 15px rgba(236, 72, 153, 0.35);
      animation: pulseArcade 2.5s infinite;
    }
    @keyframes pulseArcade {
      0%, 100% { box-shadow: 0 0 15px rgba(236, 72, 153, 0.4); }
      50% { box-shadow: 0 0 25px rgba(139, 92, 246, 0.7); }
    }

    /* Theme Switcher */
    .theme-select {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 12px;
      border-radius: 10px;
      font-size: 13px;
      outline: none;
      cursor: pointer;
      backdrop-filter: blur(12px);
    }

    /* Scanner Hero Card */
    .hero-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 28px;
      margin-bottom: 24px;
      box-shadow: 0 12px 32px rgba(0,0,0,0.3);
      backdrop-filter: blur(16px);
      position: relative;
      overflow: hidden;
    }
    .hero-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, var(--primary), var(--accent), var(--success));
    }
    .scanner-form {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    .url-box-wrap {
      flex: 1;
      min-width: 320px;
      position: relative;
    }
    .url-icon {
      position: absolute;
      left: 16px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 16px;
      opacity: 0.6;
    }
    .url-input {
      width: 100%;
      height: 52px;
      background: rgba(10, 15, 29, 0.75);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 0 16px 0 46px;
      color: #fff;
      font-size: 15px;
      font-family: 'JetBrains Mono', monospace;
      outline: none;
      transition: all 0.25s;
    }
    .url-input:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 4px var(--border-glow);
    }
    .options-group {
      display: flex;
      gap: 10px;
    }
    .select-pill {
      height: 52px;
      background: rgba(10, 15, 29, 0.75);
      border: 1px solid var(--border);
      color: #fff;
      padding: 0 16px;
      border-radius: 12px;
      font-size: 14px;
      outline: none;
      cursor: pointer;
      transition: border-color 0.2s;
    }
    .select-pill:hover { border-color: var(--primary); }

    .btn-hunt {
      height: 52px;
      background: linear-gradient(135deg, var(--primary), var(--accent));
      color: white;
      border: none;
      padding: 0 28px;
      border-radius: 12px;
      font-weight: 800;
      font-size: 16px;
      letter-spacing: -0.2px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 10px;
      transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
      box-shadow: 0 6px 20px var(--border-glow);
    }
    .btn-hunt:hover {
      transform: translateY(-2px) scale(1.02);
      box-shadow: 0 8px 26px var(--border-glow);
    }
    .btn-hunt:active { transform: scale(0.97); }
    .btn-hunt:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

    /* Staging Preset Pills */
    .presets-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 16px;
      flex-wrap: wrap;
      font-size: 13px;
      color: var(--text-muted);
    }
    .preset-chip {
      background: var(--card-alt);
      color: var(--text);
      padding: 5px 12px;
      border-radius: 20px;
      border: 1px solid var(--border);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .preset-chip:hover {
      background: var(--primary);
      color: #fff;
      transform: translateY(-1px);
      border-color: var(--primary);
    }

    /* Live Radar & Scan HUD */
    .radar-banner {
      display: none;
      background: var(--card-bg);
      border: 1px solid var(--border-glow);
      border-radius: 16px;
      padding: 22px 26px;
      margin-bottom: 24px;
      box-shadow: 0 0 30px var(--border-glow);
      animation: fadeIn 0.3s;
      backdrop-filter: blur(16px);
    }
    .radar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    .radar-status {
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 700;
      font-size: 15px;
    }
    .radar-beacon {
      width: 12px;
      height: 12px;
      background: var(--primary);
      border-radius: 50%;
      position: relative;
    }
    .radar-beacon::after {
      content: '';
      position: absolute;
      top: -4px; left: -4px; right: -4px; bottom: -4px;
      border-radius: 50%;
      border: 2px solid var(--primary);
      animation: beaconPing 1.2s cubic-bezier(0, 0, 0.2, 1) infinite;
    }
    @keyframes beaconPing {
      0% { transform: scale(1); opacity: 1; }
      100% { transform: scale(2.8); opacity: 0; }
    }
    .progress-track {
      width: 100%;
      height: 10px;
      background: rgba(15, 23, 42, 0.8);
      border-radius: 6px;
      overflow: hidden;
      border: 1px solid var(--border);
    }
    .progress-fill {
      width: 0%;
      height: 100%;
      background: linear-gradient(90deg, var(--primary), var(--accent), var(--success));
      border-radius: 6px;
      transition: width 0.3s ease;
      position: relative;
    }
    .progress-fill::after {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
      animation: shimmer 1.5s infinite;
    }
    @keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }

    /* Results Dashboard */
    .results-container {
      display: none;
      animation: fadeIn 0.4s ease-out;
    }

    /* KPI Highlights */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .kpi-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 22px;
      backdrop-filter: blur(12px);
      display: flex;
      align-items: center;
      gap: 16px;
      transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
      position: relative;
      overflow: hidden;
    }
    .kpi-card:hover {
      transform: translateY(-3px);
      border-color: var(--border-glow);
    }
    .kpi-avatar {
      width: 54px;
      height: 54px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 26px;
      flex-shrink: 0;
    }
    .kpi-meta h4 {
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.8px;
      font-weight: 700;
    }
    .kpi-meta .kpi-number {
      font-size: 32px;
      font-weight: 900;
      line-height: 1.1;
      font-family: 'Space Grotesk', sans-serif;
    }
    .kpi-badge-hint {
      font-size: 11px;
      font-weight: 700;
      margin-top: 3px;
    }

    /* Dynamic Interactive Health Meter */
    .health-gauge-box {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 24px;
      margin-bottom: 24px;
      backdrop-filter: blur(12px);
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 20px;
    }
    .health-left {
      display: flex;
      align-items: center;
      gap: 20px;
    }
    .gauge-svg-wrap {
      position: relative;
      width: 100px;
      height: 100px;
    }
    .gauge-circle-bg {
      fill: none;
      stroke: rgba(255,255,255,0.08);
      stroke-width: 8;
    }
    .gauge-circle-val {
      fill: none;
      stroke: var(--success);
      stroke-width: 8;
      stroke-linecap: round;
      transform: rotate(-90deg);
      transform-origin: 50% 50%;
      transition: stroke-dashoffset 1s ease, stroke 0.4s;
    }
    .gauge-text {
      position: absolute;
      top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      font-family: 'Space Grotesk', sans-serif;
      font-size: 22px;
      font-weight: 900;
    }
    .health-info h3 {
      font-size: 20px;
      font-weight: 800;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .health-info p {
      font-size: 13.5px;
      color: var(--text-muted);
      max-width: 600px;
    }
    .health-reaction {
      font-size: 28px;
      animation: bounceReaction 2s infinite alternate;
    }
    @keyframes bounceReaction { 0% { transform: scale(1); } 100% { transform: scale(1.2) rotate(6deg); } }

    /* Tab Controls */
    .tab-bar {
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 14px;
      margin-bottom: 20px;
      overflow-x: auto;
    }
    .filter-tab {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 10px 18px;
      border-radius: 12px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
      white-space: nowrap;
    }
    .filter-tab:hover {
      background: var(--card-alt);
      color: #fff;
    }
    .filter-tab.active {
      background: var(--primary);
      color: #fff;
      box-shadow: 0 4px 14px var(--border-glow);
    }
    .pill-counter {
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 11px;
      font-weight: 800;
    }
    .pc-confirmed { background: var(--confirmed); color: #fff; }
    .pc-suspected { background: var(--suspected); color: #fff; }
    .pc-all { background: rgba(255,255,255,0.18); color: #fff; }

    /* Action bar */
    .filter-action-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      flex-wrap: wrap;
      gap: 12px;
    }
    .severity-pills {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .sev-filter-btn {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: 8px;
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s;
    }
    .sev-filter-btn:hover, .sev-filter-btn.active {
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }
    .search-field {
      background: rgba(10, 15, 29, 0.7);
      border: 1px solid var(--border);
      color: #fff;
      padding: 8px 16px;
      border-radius: 10px;
      font-size: 13px;
      min-width: 250px;
      outline: none;
      transition: border-color 0.2s;
    }
    .search-field:focus { border-color: var(--primary); }

    .export-cluster {
      display: flex;
      gap: 8px;
    }
    .btn-dl {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 700;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }
    .btn-dl:hover {
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
      transform: translateY(-1px);
    }

    /* Cards Grid */
    .issues-stack {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .bug-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 22px;
      backdrop-filter: blur(12px);
      transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
      position: relative;
    }
    .bug-card:hover {
      border-color: var(--border-glow);
      transform: translateX(4px);
    }
    .bug-card.is-squashed {
      opacity: 0.45;
      filter: grayscale(0.6);
      transform: scale(0.98);
      border-color: var(--success) !important;
    }
    .squashed-stamp {
      display: none;
      position: absolute;
      top: 18px;
      right: 20px;
      background: rgba(16, 185, 129, 0.2);
      border: 2px dashed #10b981;
      color: #34d399;
      font-weight: 900;
      font-size: 13px;
      padding: 4px 12px;
      border-radius: 8px;
      transform: rotate(8deg);
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    .bug-card.is-squashed .squashed-stamp {
      display: block;
    }

    .bug-card-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }
    .bug-title {
      font-size: 16px;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .tag-cluster {
      display: flex;
      gap: 6px;
      align-items: center;
    }
    .pill-tag {
      font-size: 11px;
      font-weight: 800;
      padding: 3px 9px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .status-confirmed-pill { background: var(--confirmed); color: #fff; }
    .status-suspected-pill { background: var(--suspected); color: #fff; }
    .sev-P0_CRITICAL { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }
    .sev-P1_HIGH { background: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid #f97316; }
    .sev-P2_MEDIUM { background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid #eab308; }
    .sev-P3_LOW { background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; }
    .cat-pill { background: var(--card-alt); color: var(--text-muted); }

    .bug-desc {
      font-size: 14px;
      color: #cbd5e1;
      margin-bottom: 12px;
    }
    .code-snippet {
      background: rgba(7, 11, 20, 0.85);
      border: 1px solid rgba(51, 65, 85, 0.5);
      padding: 10px 14px;
      border-radius: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12.5px;
      color: #93c5fd;
      margin-bottom: 12px;
      word-break: break-all;
    }
    .fix-box {
      background: rgba(16, 185, 129, 0.09);
      border-left: 3px solid #10b981;
      padding: 10px 14px;
      border-radius: 4px;
      font-size: 13.5px;
      color: #a7f3d0;
      margin-bottom: 14px;
    }
    .card-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      border-top: 1px solid rgba(51, 65, 85, 0.35);
      padding-top: 12px;
      font-size: 12px;
      color: var(--text-muted);
    }
    .card-tools {
      display: flex;
      gap: 8px;
    }
    .tool-btn {
      background: var(--card-alt);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 5px 10px;
      border-radius: 6px;
      font-size: 11.5px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s;
    }
    .tool-btn:hover {
      background: var(--primary);
      color: #fff;
    }
    .btn-squash {
      background: rgba(239, 68, 68, 0.2);
      border: 1px solid #ef4444;
      color: #f87171;
    }
    .btn-squash:hover {
      background: #10b981;
      border-color: #10b981;
      color: #fff;
    }

    /* Whack-A-Bug Arcade Modal Overlay */
    #arcade-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0; width: 100vw; height: 100vh;
      background: rgba(0,0,0,0.85);
      backdrop-filter: blur(14px);
      z-index: 1000;
      align-items: center;
      justify-content: center;
      flex-direction: column;
    }
    .arcade-cabinet {
      width: 90%;
      max-width: 700px;
      height: 480px;
      background: var(--card-bg);
      border: 2px solid var(--primary);
      border-radius: 20px;
      box-shadow: 0 0 40px var(--border-glow);
      position: relative;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .arcade-hud {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 24px;
      border-bottom: 2px solid var(--border);
      background: rgba(0,0,0,0.3);
      font-family: 'Space Grotesk', sans-serif;
    }
    .arcade-score { font-size: 20px; font-weight: 900; color: #facc15; }
    .arcade-timer { font-size: 18px; font-weight: 700; color: #38bdf8; }
    .arcade-stage {
      flex: 1;
      position: relative;
      cursor: crosshair;
    }
    .arcade-bug {
      position: absolute;
      font-size: 36px;
      user-select: none;
      cursor: pointer;
      transition: transform 0.1s;
      animation: wiggleBug 0.5s infinite alternate;
    }
    @keyframes wiggleBug { 0% { transform: scale(1) rotate(-8deg); } 100% { transform: scale(1.1) rotate(8deg); } }
    .arcade-bug:active { transform: scale(0.7); }
    .arcade-close {
      position: absolute;
      top: 14px; right: 16px;
      background: transparent;
      border: none;
      color: #fff;
      font-size: 22px;
      cursor: pointer;
    }

    /* Confetti Particle Canvas */
    #confetti-canvas {
      position: fixed;
      top: 0; left: 0; width: 100vw; height: 100vh;
      pointer-events: none;
      z-index: 999;
    }

    /* Toast Notification */
    #toast-msg {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--card-bg);
      border: 1px solid var(--primary);
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
      color: #fff;
      padding: 12px 20px;
      border-radius: 12px;
      font-size: 13.5px;
      font-weight: 600;
      z-index: 9999;
      display: none;
      backdrop-filter: blur(12px);
      animation: slideInToast 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    @keyframes slideInToast { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

    /* Summary & Pages Styling */
    .summary-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      backdrop-filter: blur(12px);
    }
    .summary-text {
      white-space: pre-line;
      line-height: 1.8;
      font-size: 14px;
      color: #e2e8f0;
      margin-bottom: 20px;
    }
    .rec-card {
      padding: 12px 16px;
      background: rgba(255,255,255,0.03);
      border-left: 3px solid var(--primary);
      border-radius: 6px;
      margin-bottom: 10px;
      font-size: 14px;
    }
    .table-pages {
      width: 100%;
      border-collapse: collapse;
      font-size: 13.5px;
    }
    .table-pages th, .table-pages td {
      padding: 12px 16px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }
    .table-pages th { background: rgba(15, 23, 42, 0.6); color: var(--text-muted); }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
  </style>
</head>
<body>
  <!-- Background Components -->
  <canvas id="bg-canvas"></canvas>
  <div class="orb orb-1"></div>
  <div class="orb orb-2"></div>
  <canvas id="confetti-canvas"></canvas>

  <div class="main-wrap">
    <!-- Top Nav -->
    <header class="top-nav">
      <div class="brand">
        <div class="brand-icon" onclick="triggerEasterEgg()" title="Click for a surprise!">👾</div>
        <div>
          <div class="brand-title">
            AI Website QA Agent
            <span class="tag-pill">2026 Pro</span>
          </div>
          <div class="brand-desc">Autonomous deep inspector: links, images, content consistency & SEO</div>
        </div>
      </div>
      <div class="nav-actions">
        <button class="interactive-btn arcade-btn" onclick="openArcade()">
          <span>🎮 Whack-a-Bug Arcade</span>
        </button>
        <button id="sfxToggleBtn" class="interactive-btn" onclick="toggleSFX()">
          <span>🔊 SFX: ON</span>
        </button>
        <select class="theme-select" onchange="changeTheme(this.value)">
          <option value="cyber">🌌 Cyber Dark</option>
          <option value="arcade">👾 Arcade Neon</option>
          <option value="synthwave">🔮 Synthwave</option>
          <option value="studio">💡 Studio Sleek</option>
        </select>
      </div>
    </header>

    <!-- Hero Scanner Card -->
    <section class="hero-card">
      <div class="scanner-form">
        <div class="url-box-wrap">
          <span class="url-icon">🌐</span>
          <input type="url" id="targetUrl" class="url-input" placeholder="https://staging.yourdomain.com or http://127.0.0.1:8088" value="http://127.0.0.1:8088">
        </div>
        <div class="options-group">
          <select id="maxPages" class="select-pill" title="Pages Limit">
            <option value="5" selected>5 Pages</option>
            <option value="10">10 Pages</option>
            <option value="20">20 Pages</option>
            <option value="1">1 Page</option>
          </select>
          <select id="maxDepth" class="select-pill" title="Crawl Depth">
            <option value="1">Depth 1</option>
            <option value="2" selected>Depth 2</option>
            <option value="3">Depth 3</option>
          </select>
          <button id="huntBtn" class="btn-hunt" onclick="startAudit()">
            <span>🚀 Run Autonomous QA</span>
          </button>
        </div>
      </div>

      <!-- Presets -->
      <div class="presets-row">
        <span>⚡ Quick Staging Targets:</span>
        <span class="preset-chip" onclick="setPreset('http://127.0.0.1:8088')">💣 Full Defect Staging (Port 8088)</span>
        <span class="preset-chip" onclick="setPreset('http://127.0.0.1:8088/about')">✍️ Lorem & Mojibake Copy</span>
        <span class="preset-chip" onclick="setPreset('http://127.0.0.1:8088/contact')">📱 Missing Viewport & TODOs</span>
        <span class="preset-chip" onclick="setPreset('http://127.0.0.1:8088/pricing')">🔍 SEO Traps & Canonical Bug</span>
      </div>
    </section>

    <!-- Live Radar / Scan HUD -->
    <section id="radarBanner" class="radar-banner">
      <div class="radar-header">
        <div class="radar-status">
          <div class="radar-beacon"></div>
          <span id="radarMsg">Hunting defects across target DOM and assets...</span>
        </div>
        <span id="radarPct" style="font-family:'Space Grotesk',sans-serif; font-size:18px; font-weight:800; color:var(--primary);">0%</span>
      </div>
      <div class="progress-track">
        <div id="progressFill" class="progress-fill"></div>
      </div>
    </section>

    <!-- Results Section -->
    <main id="resultsWrap" class="results-container">
      <!-- Dynamic Health Score Banner -->
      <div class="health-gauge-box">
        <div class="health-left">
          <div class="gauge-svg-wrap">
            <svg width="100" height="100">
              <circle class="gauge-circle-bg" cx="50" cy="50" r="42"></circle>
              <circle id="gaugeCircle" class="gauge-circle-val" cx="50" cy="50" r="42" stroke-dasharray="264" stroke-dashoffset="264"></circle>
            </svg>
            <div id="gaugeScoreText" class="gauge-text">0</div>
          </div>
          <div class="health-info">
            <h3 id="healthVerdictTitle">QA Health Evaluation</h3>
            <p id="healthVerdictDesc">Autonomous inspection score calculated from weighted defect penalties.</p>
          </div>
        </div>
        <div id="healthEmoji" class="health-reaction">🚀</div>
      </div>

      <!-- KPI Grid -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-avatar" style="background: rgba(220, 38, 38, 0.15); color: #ef4444;">🚨</div>
          <div class="kpi-meta">
            <h4>Confirmed Defects</h4>
            <div class="kpi-number" id="kpiConfirmed" style="color: #ef4444;">0</div>
            <div class="kpi-badge-hint" style="color: #f87171;">Must fix before release</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-avatar" style="background: rgba(217, 119, 6, 0.15); color: #f59e0b;">⚠️</div>
          <div class="kpi-meta">
            <h4>Suspected Issues</h4>
            <div class="kpi-number" id="kpiSuspected" style="color: #f59e0b;">0</div>
            <div class="kpi-badge-hint" style="color: #fbbf24;">Needs human review</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-avatar" style="background: rgba(59, 130, 246, 0.15); color: #3b82f6;">📄</div>
          <div class="kpi-meta">
            <h4>Pages Audited</h4>
            <div class="kpi-number" id="kpiPages">0</div>
            <div class="kpi-badge-hint" id="kpiDuration" style="color: #60a5fa;">0.00s</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-avatar" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">🔍</div>
          <div class="kpi-meta">
            <h4>Assets Checked</h4>
            <div class="kpi-number" id="kpiAssets" style="color: #10b981;">0</div>
            <div class="kpi-badge-hint" id="kpiAssetBreakdown" style="color: #34d399;">Links & Images</div>
          </div>
        </div>
      </div>

      <!-- Tab Bar -->
      <nav class="tab-bar">
        <button class="filter-tab active" onclick="setTab('confirmed', this)">
          🚨 Confirmed Issues <span id="tabCountConfirmed" class="pill-counter pc-confirmed">0</span>
        </button>
        <button class="filter-tab" onclick="setTab('suspected', this)">
          ⚠️ Suspected Issues <span id="tabCountSuspected" class="pill-counter pc-suspected">0</span>
        </button>
        <button class="filter-tab" onclick="setTab('all', this)">
          📑 All Issues <span id="tabCountAll" class="pill-counter pc-all">0</span>
        </button>
        <button class="filter-tab" onclick="setTab('summary', this)">
          🧠 AI Executive Summary
        </button>
        <button class="filter-tab" onclick="setTab('pages', this)">
          🌐 Audited Pages Breakdown
        </button>
      </nav>

      <!-- Action & Filters Bar -->
      <div id="filterCluster" class="filter-action-bar">
        <div class="severity-pills">
          <button class="sev-filter-btn active" onclick="setSeverity('ALL', this)">All Severities</button>
          <button class="sev-filter-btn" onclick="setSeverity('P0_CRITICAL', this)">P0 Critical</button>
          <button class="sev-filter-btn" onclick="setSeverity('P1_HIGH', this)">P1 High</button>
          <button class="sev-filter-btn" onclick="setSeverity('P2_MEDIUM', this)">P2 Medium</button>
          <button class="sev-filter-btn" onclick="setSeverity('P3_LOW', this)">P3 Low</button>
        </div>
        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
          <input type="text" id="searchInput" class="search-field" placeholder="Search issues, selectors..." oninput="onSearch(this.value)">
          <div class="export-cluster">
            <a href="/api/export/html" target="_blank" class="btn-dl">📥 HTML</a>
            <a href="/api/export/markdown" target="_blank" class="btn-dl">📥 Markdown</a>
            <a href="/api/export/json" target="_blank" class="btn-dl">📥 JSON</a>
          </div>
        </div>
      </div>

      <!-- Issues List View -->
      <div id="issuesView">
        <div id="issuesList" class="issues-stack"></div>
      </div>

      <!-- Executive Summary View -->
      <div id="summaryView" style="display: none;">
        <div class="summary-card">
          <h3 style="font-size: 19px; margin-bottom: 12px;">🎯 Prioritized QA Evaluation</h3>
          <div id="summaryContent" class="summary-text"></div>
          <h3 style="font-size: 17px; margin-bottom: 14px;">📋 Actionable Remediation Roadmap</h3>
          <div id="recsList"></div>
        </div>
      </div>

      <!-- Pages View -->
      <div id="pagesView" style="display: none;">
        <div class="summary-card">
          <h3 style="font-size: 19px; margin-bottom: 16px;">🌐 Audited Pages Performance & Diagnostics</h3>
          <table class="table-pages">
            <thead>
              <tr>
                <th>Page URL</th>
                <th>Status</th>
                <th>Load Time</th>
                <th>Links</th>
                <th>Images</th>
                <th>Defects Detected</th>
              </tr>
            </thead>
            <tbody id="pagesTableBody"></tbody>
          </table>
        </div>
      </div>
    </main>
  </div>

  <!-- Whack-a-Bug Arcade Modal -->
  <div id="arcade-overlay">
    <div class="arcade-cabinet">
      <button class="arcade-close" onclick="closeArcade()">✕</button>
      <div class="arcade-hud">
        <div class="arcade-score">BUGS SQUASHED: <span id="arcadeScore">0</span></div>
        <div class="arcade-timer">TIME: <span id="arcadeTimer">20</span>s</div>
      </div>
      <div id="arcadeStage" class="arcade-stage" onclick="onArcadeMiss(event)"></div>
    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast-msg"></div>

  <script>
    /* =========================================================
       1. SYNTHESIZED AUDIO ENGINE (Native Web Audio API)
       ========================================================= */
    let sfxEnabled = true;
    let audioCtx = null;

    function initAudio() {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
    }

    function toggleSFX() {
      sfxEnabled = !sfxEnabled;
      document.getElementById('sfxToggleBtn').innerText = sfxEnabled ? '🔊 SFX: ON' : '🔇 SFX: OFF';
      showToast(sfxEnabled ? 'Sound Effects Enabled! 🎶' : 'Sound Effects Muted 🔇');
    }

    function playTone(freq, type = 'sine', duration = 0.1, gainVal = 0.1) {
      if (!sfxEnabled) return;
      try {
        initAudio();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        gain.gain.setValueAtTime(gainVal, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
      } catch (e) {}
    }

    function sfxClick() { playTone(600, 'sine', 0.05, 0.08); }
    function sfxSonar() { playTone(980, 'triangle', 0.2, 0.12); }
    function sfxSquash() {
      if (!sfxEnabled) return;
      playTone(180, 'sawtooth', 0.12, 0.2);
      setTimeout(() => playTone(320, 'sine', 0.15, 0.15), 60);
    }
    function sfxFanfare() {
      if (!sfxEnabled) return;
      const notes = [523.25, 659.25, 783.99, 1046.50];
      notes.forEach((freq, idx) => {
        setTimeout(() => playTone(freq, 'triangle', 0.2, 0.15), idx * 100);
      });
    }

    /* =========================================================
       2. INTERACTIVE BACKGROUND PARTICLE CANVAS
       ========================================================= */
    const canvas = document.getElementById('bg-canvas');
    const ctx = canvas.getContext('2d');
    let particles = [];
    let mouse = { x: null, y: null, radius: 140 };

    function resizeCanvas() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      initParticles();
    }
    window.addEventListener('resize', resizeCanvas);
    window.addEventListener('mousemove', (e) => {
      mouse.x = e.x;
      mouse.y = e.y;
    });
    window.addEventListener('mouseout', () => {
      mouse.x = null;
      mouse.y = null;
    });

    class Particle {
      constructor(x, y) {
        this.x = x;
        this.y = y;
        this.size = Math.random() * 2 + 1;
        this.baseX = this.x;
        this.baseY = this.y;
        this.density = Math.random() * 20 + 5;
        this.vx = (Math.random() - 0.5) * 0.8;
        this.vy = (Math.random() - 0.5) * 0.8;
      }
      draw() {
        ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--particle-color') || 'rgba(96, 165, 250, 0.4)';
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.closePath();
        ctx.fill();
      }
      update() {
        this.x += this.vx;
        this.y += this.vy;
        if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
        if (this.y < 0 || this.y > canvas.height) this.vy *= -1;

        if (mouse.x != null) {
          const dx = mouse.x - this.x;
          const dy = mouse.y - this.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < mouse.radius) {
            const force = (mouse.radius - dist) / mouse.radius;
            this.x -= (dx / dist) * force * 4;
            this.y -= (dy / dist) * force * 4;
          }
        }
      }
    }

    function initParticles() {
      particles = [];
      const count = Math.min(Math.floor((canvas.width * canvas.height) / 16000), 75);
      for (let i = 0; i < count; i++) {
        particles.push(new Particle(Math.random() * canvas.width, Math.random() * canvas.height));
      }
    }

    function animateParticles() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (let i = 0; i < particles.length; i++) {
        particles[i].draw();
        particles[i].update();
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 110) {
            ctx.strokeStyle = `rgba(147, 197, 253, ${0.15 * (1 - dist / 110)})`;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }
      requestAnimationFrame(animateParticles);
    }
    resizeCanvas();
    animateParticles();

    /* =========================================================
       3. CONFETTI BURST ENGINE
       ========================================================= */
    const confCanvas = document.getElementById('confetti-canvas');
    const confCtx = confCanvas.getContext('2d');
    let confetti = [];

    function popConfetti(originX, originY) {
      confCanvas.width = window.innerWidth;
      confCanvas.height = window.innerHeight;
      const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];
      for (let i = 0; i < 40; i++) {
        confetti.push({
          x: originX || window.innerWidth / 2,
          y: originY || window.innerHeight / 2,
          vx: (Math.random() - 0.5) * 12,
          vy: Math.random() * -10 - 4,
          size: Math.random() * 8 + 4,
          color: colors[Math.floor(Math.random() * colors.length)],
          rotation: Math.random() * 360,
          rotationSpeed: (Math.random() - 0.5) * 10,
          life: 1
        });
      }
    }

    function animateConfetti() {
      confCtx.clearRect(0, 0, confCanvas.width, confCanvas.height);
      confetti.forEach((c, idx) => {
        c.x += c.vx;
        c.y += c.vy;
        c.vy += 0.35; // gravity
        c.rotation += c.rotationSpeed;
        c.life -= 0.015;
        confCtx.save();
        confCtx.translate(c.x, c.y);
        confCtx.rotate((c.rotation * Math.PI) / 180);
        confCtx.fillStyle = c.color;
        confCtx.globalAlpha = Math.max(0, c.life);
        confCtx.fillRect(-c.size / 2, -c.size / 2, c.size, c.size);
        confCtx.restore();
        if (c.life <= 0) confetti.splice(idx, 1);
      });
      requestAnimationFrame(animateConfetti);
    }
    animateConfetti();

    /* =========================================================
       4. WHACK-A-BUG ARCADE MINI-GAME
       ========================================================= */
    let arcadeScore = 0;
    let arcadeTime = 20;
    let arcadeInterval = null;
    let bugSpawnTimeout = null;

    function openArcade() {
      sfxClick();
      arcadeScore = 0;
      arcadeTime = 20;
      document.getElementById('arcadeScore').innerText = '0';
      document.getElementById('arcadeTimer').innerText = '20';
      document.getElementById('arcadeStage').innerHTML = '';
      document.getElementById('arcade-overlay').style.display = 'flex';

      arcadeInterval = setInterval(() => {
        arcadeTime--;
        document.getElementById('arcadeTimer').innerText = arcadeTime;
        if (arcadeTime <= 0) {
          endArcade();
        }
      }, 1000);
      spawnArcadeBug();
    }

    function closeArcade() {
      clearInterval(arcadeInterval);
      clearTimeout(bugSpawnTimeout);
      document.getElementById('arcade-overlay').style.display = 'none';
    }

    function spawnArcadeBug() {
      if (arcadeTime <= 0) return;
      const stage = document.getElementById('arcadeStage');
      const bug = document.createElement('div');
      bug.className = 'arcade-bug';
      const emojis = ['🐛', '🪲', '🐞', '🕷️', '🐜'];
      bug.innerText = emojis[Math.floor(Math.random() * emojis.length)];

      const x = Math.random() * (stage.clientWidth - 60);
      const y = Math.random() * (stage.clientHeight - 60);
      bug.style.left = x + 'px';
      bug.style.top = y + 'px';

      bug.onclick = (e) => {
        e.stopPropagation();
        sfxSquash();
        arcadeScore += 100;
        document.getElementById('arcadeScore').innerText = arcadeScore;
        popConfetti(e.clientX, e.clientY);
        stage.removeChild(bug);
        spawnArcadeBug();
      };

      stage.appendChild(bug);
      bugSpawnTimeout = setTimeout(() => {
        if (stage.contains(bug)) {
          stage.removeChild(bug);
          spawnArcadeBug();
        }
      }, 1300);
    }

    function onArcadeMiss(e) {
      playTone(150, 'square', 0.08, 0.1);
    }

    function endArcade() {
      clearInterval(arcadeInterval);
      clearTimeout(bugSpawnTimeout);
      sfxFanfare();
      alert(`🎉 Arcade Over! You squashed ${arcadeScore / 100} bugs and scored ${arcadeScore} pts!`);
      closeArcade();
    }

    /* =========================================================
       5. CORE QA SCAN LOGIC & REAL-TIME POLL
       ========================================================= */
    let reportData = null;
    let squashedIssueIds = new Set();
    let pollInterval = null;
    let currentTab = 'confirmed';
    let currentSeverity = 'ALL';
    let searchQuery = '';

    function setPreset(url) {
      sfxClick();
      document.getElementById('targetUrl').value = url;
    }

    async function startAudit() {
      sfxClick();
      const url = document.getElementById('targetUrl').value.trim();
      if (!url) return alert('Please enter a target URL.');

      const maxPages = parseInt(document.getElementById('maxPages').value);
      const maxDepth = parseInt(document.getElementById('maxDepth').value);

      document.getElementById('huntBtn').disabled = true;
      document.getElementById('radarBanner').style.display = 'block';
      document.getElementById('resultsWrap').style.display = 'none';
      squashedIssueIds.clear();

      try {
        const resp = await fetch('/api/audit', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ url, max_pages: maxPages, max_depth: maxDepth })
        });
        if (!resp.ok) {
          const err = await resp.json();
          alert('Error: ' + (err.error || 'Failed to start audit'));
          document.getElementById('huntBtn').disabled = false;
          return;
        }
        pollScanStatus();
      } catch (err) {
        alert('Server unreachable: ' + err.message);
        document.getElementById('huntBtn').disabled = false;
      }
    }

    function pollScanStatus() {
      if (pollInterval) clearInterval(pollInterval);
      pollInterval = setInterval(async () => {
        try {
          const resp = await fetch('/api/scan-status');
          const data = await resp.json();

          const pct = Math.round((data.progress || 0) * 100);
          document.getElementById('progressFill').style.width = pct + '%';
          document.getElementById('radarPct').innerText = pct + '%';
          document.getElementById('radarMsg').innerText = data.message || 'Scanning...';
          sfxSonar();

          if (data.status === 'completed') {
            clearInterval(pollInterval);
            document.getElementById('huntBtn').disabled = false;
            document.getElementById('radarBanner').style.display = 'none';
            reportData = data.report;
            sfxFanfare();
            popConfetti();
            renderDashboard();
          } else if (data.status === 'failed') {
            clearInterval(pollInterval);
            document.getElementById('huntBtn').disabled = false;
            alert('Audit failed: ' + data.message);
          }
        } catch (e) {
          console.error(e);
        }
      }, 900);
    }

    /* =========================================================
       6. RENDER DASHBOARD & DYNAMIC HEALTH GAUGE
       ========================================================= */
    function renderDashboard() {
      if (!reportData) return;
      document.getElementById('resultsWrap').style.display = 'block';

      // KPI Numbers
      const effectiveScore = computeDynamicScore();
      updateGauge(effectiveScore);

      document.getElementById('kpiConfirmed').innerText = reportData.confirmed_count;
      document.getElementById('kpiSuspected').innerText = reportData.suspected_count;
      document.getElementById('kpiPages').innerText = reportData.stats.pages_crawled;
      document.getElementById('kpiDuration').innerText = reportData.stats.duration_seconds + 's scan duration';
      document.getElementById('kpiAssets').innerText = reportData.stats.total_links_inspected + reportData.stats.total_images_inspected;
      document.getElementById('kpiAssetBreakdown').innerText = `${reportData.stats.total_links_inspected} links, ${reportData.stats.total_images_inspected} images`;

      document.getElementById('tabCountConfirmed').innerText = reportData.confirmed_count;
      document.getElementById('tabCountSuspected').innerText = reportData.suspected_count;
      document.getElementById('tabCountAll').innerText = reportData.total_issues;

      // Executive Summary Content
      document.getElementById('summaryContent').innerText = reportData.executive_summary;
      const recsList = document.getElementById('recsList');
      recsList.innerHTML = '';
      (reportData.top_recommendations || []).forEach(r => {
        const div = document.createElement('div');
        div.className = 'rec-card';
        div.innerHTML = r;
        recsList.appendChild(div);
      });

      // Pages Breakdown Table
      const pagesBody = document.getElementById('pagesTableBody');
      pagesBody.innerHTML = '';
      (reportData.pages || []).forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><code>${p.url}</code></td>
          <td><span style="color:${p.status_code < 400 ? 'var(--success)' : 'var(--p0)'}">HTTP ${p.status_code}</span></td>
          <td>${p.load_time_ms} ms</td>
          <td>${p.links_checked}</td>
          <td>${p.images_checked}</td>
          <td><strong>${(p.issues || []).length}</strong></td>
        `;
        pagesBody.appendChild(tr);
      });

      renderIssues();
    }

    function computeDynamicScore() {
      if (!reportData || !reportData.issues) return 100;
      let score = 100;
      reportData.issues.forEach(issue => {
        if (squashedIssueIds.has(issue.id)) return; // Ignored if squashed
        if (issue.severity === 'P0_CRITICAL') score -= (issue.status === 'CONFIRMED' ? 20 : 10);
        else if (issue.severity === 'P1_HIGH') score -= (issue.status === 'CONFIRMED' ? 8 : 4);
        else if (issue.severity === 'P2_MEDIUM') score -= (issue.status === 'CONFIRMED' ? 3 : 1.5);
        else if (issue.severity === 'P3_LOW') score -= (issue.status === 'CONFIRMED' ? 1 : 0.5);
      });
      return Math.max(0, Math.min(100, Math.round(score)));
    }

    function updateGauge(score) {
      document.getElementById('gaugeScoreText').innerText = score;
      const circle = document.getElementById('gaugeCircle');
      const circumference = 264; // 2 * PI * 42
      const offset = circumference - (score / 100) * circumference;
      circle.style.strokeDashoffset = offset;

      let color = 'var(--success)';
      let title = 'S-Tier Quality! Ready to Ship 🚀';
      let emoji = '😎';
      if (score < 50) {
        color = 'var(--p0)';
        title = 'Critical Defects Detected! Blocker Risk 🚨';
        emoji = '💀';
      } else if (score < 80) {
        color = 'var(--p1)';
        title = 'Needs Remediation Before Production Launch ⚠️';
        emoji = '🛠️';
      }
      circle.style.stroke = color;
      document.getElementById('healthVerdictTitle').innerText = title;
      document.getElementById('healthEmoji').innerText = emoji;
    }

    /* =========================================================
       7. RENDER ISSUES & INTERACTIVE BUG SQUASHING
       ========================================================= */
    function renderIssues() {
      const list = document.getElementById('issuesList');
      list.innerHTML = '';
      if (!reportData || !reportData.issues) return;

      const filtered = reportData.issues.filter(issue => {
        if (currentTab === 'confirmed' && issue.status !== 'CONFIRMED') return false;
        if (currentTab === 'suspected' && issue.status !== 'SUSPECTED') return false;
        if (currentSeverity !== 'ALL' && issue.severity !== currentSeverity) return false;

        if (searchQuery) {
          const q = searchQuery.toLowerCase();
          const matchTitle = issue.title.toLowerCase().includes(q);
          const matchDesc = issue.description.toLowerCase().includes(q);
          const matchUrl = issue.url.toLowerCase().includes(q);
          if (!matchTitle && !matchDesc && !matchUrl) return false;
        }
        return true;
      });

      if (filtered.length === 0) {
        list.innerHTML = '<div style="text-align:center; padding: 48px; color:var(--text-muted); font-size:16px;">🎉 No issues found under this filter criteria!</div>';
        return;
      }

      filtered.forEach(issue => {
        const isSquashed = squashedIssueIds.has(issue.id);
        const card = document.createElement('div');
        card.id = 'card-' + issue.id;
        card.className = `bug-card ${isSquashed ? 'is-squashed' : ''}`;
        card.innerHTML = `
          <div class="squashed-stamp">SQUASHED! 💥</div>
          <div class="bug-card-top">
            <div class="bug-title">
              <span>${issue.status === 'CONFIRMED' ? '🚨' : '⚠️'}</span>
              <span>${issue.title}</span>
            </div>
            <div class="tag-cluster">
              <span class="pill-tag status-${issue.status.toLowerCase()}-pill">${issue.status === 'CONFIRMED' ? 'Confirmed Defect' : 'Suspected Anomaly'}</span>
              <span class="pill-tag sev-${issue.severity}">${issue.severity.replace('_', ' ')}</span>
              <span class="pill-tag cat-pill">${issue.category.replace('_', ' ')}</span>
            </div>
          </div>
          <div class="bug-desc">${issue.description}</div>
          ${issue.element_selector ? `<div class="code-snippet">Element Context: ${escapeHtml(issue.element_selector)}</div>` : ''}
          <div class="fix-box">💡 <strong>Remediation:</strong> ${issue.remediation}</div>
          <div class="card-footer">
            <span>Found on: <code>${issue.url}</code> &bull; ID: ${issue.id}</span>
            <div class="card-tools">
              <button class="tool-btn btn-squash" onclick="squashBug('${issue.id}', event)">
                ${isSquashed ? '↩️ Unsquash' : '🔨 Squash Bug'}
              </button>
              <button class="tool-btn" onclick="copyJiraTicket('${issue.id}')">📋 Jira</button>
              <button class="tool-btn" onclick="copySlackMsg('${issue.id}')">💬 Slack</button>
            </div>
          </div>
        `;
        list.appendChild(card);
      });
    }

    function squashBug(issueId, event) {
      sfxSquash();
      const card = document.getElementById('card-' + issueId);
      if (squashedIssueIds.has(issueId)) {
        squashedIssueIds.delete(issueId);
        card.classList.remove('is-squashed');
        showToast('Bug restored! ⚠️');
      } else {
        squashedIssueIds.add(issueId);
        card.classList.add('is-squashed');
        popConfetti(event.clientX, event.clientY);
        showToast('💥 Bug squashed! Health score boosted!');
      }
      updateGauge(computeDynamicScore());
    }

    function copyJiraTicket(issueId) {
      sfxClick();
      const issue = reportData.issues.find(i => i.id === issueId);
      if (!issue) return;
      const text = `h2. [${issue.severity}] ${issue.title}
*Status:* ${issue.status}
*Category:* ${issue.category}
*URL:* ${issue.url}

*Description:*
${issue.description}

*Element Context:*
{code:html}
${issue.element_selector || 'N/A'}
{code}

*Remediation Plan:*
${issue.remediation}`;
      navigator.clipboard.writeText(text);
      showToast('📋 Copied Jira Markdown to clipboard!');
    }

    function copySlackMsg(issueId) {
      sfxClick();
      const issue = reportData.issues.find(i => i.id === issueId);
      if (!issue) return;
      const emoji = issue.severity === 'P0_CRITICAL' ? '🚨' : '⚠️';
      const text = `${emoji} *QA Defect Alert: ${issue.title}*
• *Severity:* ${issue.severity} (${issue.status})
• *URL:* ${issue.url}
• *Summary:* ${issue.description}
• *Recommended Fix:* ${issue.remediation}`;
      navigator.clipboard.writeText(text);
      showToast('💬 Copied Slack notification snippet!');
    }

    function showToast(msg) {
      const toast = document.getElementById('toast-msg');
      toast.innerText = msg;
      toast.style.display = 'block';
      setTimeout(() => { toast.style.display = 'none'; }, 2600);
    }

    function escapeHtml(str) {
      return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    /* =========================================================
       8. TAB & THEME NAVIGATION
       ========================================================= */
    function setTab(tab, btn) {
      sfxClick();
      currentTab = tab;
      document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const isIssues = (tab === 'confirmed' || tab === 'suspected' || tab === 'all');
      document.getElementById('issuesView').style.display = isIssues ? 'block' : 'none';
      document.getElementById('filterCluster').style.display = isIssues ? 'flex' : 'none';
      document.getElementById('summaryView').style.display = tab === 'summary' ? 'block' : 'none';
      document.getElementById('pagesView').style.display = tab === 'pages' ? 'block' : 'none';

      if (isIssues) renderIssues();
    }

    function setSeverity(sev, btn) {
      sfxClick();
      currentSeverity = (currentSeverity === sev && sev !== 'ALL') ? 'ALL' : sev;
      document.querySelectorAll('.sev-filter-btn').forEach(b => b.classList.remove('active'));
      if (currentSeverity !== 'ALL') btn.classList.add('active');
      else document.querySelector('.sev-filter-btn').classList.add('active');
      renderIssues();
    }

    function onSearch(val) {
      searchQuery = val.trim();
      renderIssues();
    }

    function changeTheme(theme) {
      sfxClick();
      document.documentElement.setAttribute('data-theme', theme);
      initParticles();
      showToast(`Theme switched to ${theme.toUpperCase()}! 🎨`);
    }

    function triggerEasterEgg() {
      sfxFanfare();
      popConfetti();
      showToast('👾 You found the Secret Bug Mascot! +500 QA Karma!');
    }

    // Auto-load last completed scan if present
    window.addEventListener('DOMContentLoaded', async () => {
      try {
        const resp = await fetch('/api/scan-status');
        const data = await resp.json();
        if (data.has_report) {
          reportData = data.report;
          renderDashboard();
        }
      } catch (e) {}
    });
  </script>
</body>
</html>
""")
