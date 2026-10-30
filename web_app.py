"""
AI Website QA Agent - Interactive Web Dashboard & API
FastAPI backend providing real-time scanning, interactive UI filtering,
and multi-format report exports (HTML, Markdown, JSON).
"""

import asyncio
import threading
from typing import Optional, Dict, Any
from fastapi import FastAPI, BackgroundTasks, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from ai_website_qa.agent import WebsiteQAAgent
from ai_website_qa.models import QAReport
from ai_website_qa.exporter import QAExporter
from mock_staging.server import app as mock_app

app = FastAPI(title="AI Website QA Agent")

# In-memory storage for active and last completed scans
current_scan_status: Dict[str, Any] = {
    "status": "idle",
    "message": "Ready to scan.",
    "progress": 0.0,
    "last_report": None
}


class ScanRequest(BaseModel):
    url: str
    max_pages: int = 5
    max_depth: int = 2
    concurrency: int = 4
    timeout: int = 10


# Mount or route mock staging app internally
@app.get("/api/mock-status")
async def mock_status():
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
    current_scan_status["message"] = f"Initializing scan for {req.url}..."

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
            current_scan_status["message"] = "Scan finished successfully."
            current_scan_status["progress"] = 1.0
        except Exception as e:
            current_scan_status["status"] = "failed"
            current_scan_status["message"] = f"Scan failed: {str(e)}"
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
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Website QA Agent | Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #111827;
      --card-alt: #1a2234;
      --border: #1f293d;
      --border-focus: #3b82f6;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --p0: #ef4444;
      --p1: #f97316;
      --p2: #eab308;
      --p3: #3b82f6;
      --confirmed: #dc2626;
      --suspected: #d97706;
      --success: #10b981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }
    .container { max-width: 1300px; margin: 0 auto; }

    /* Top Nav */
    .top-nav {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .logo-badge {
      width: 42px;
      height: 42px;
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    .brand h1 { font-size: 20px; font-weight: 800; letter-spacing: -0.5px; }
    .brand p { font-size: 13px; color: var(--text-muted); }
    .staging-badge {
      font-size: 12px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid #10b981;
      color: #34d399;
      padding: 6px 14px;
      border-radius: 20px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    /* Scanner Form Card */
    .scan-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }
    .scan-form-row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    .url-input-wrap {
      flex: 1;
      min-width: 300px;
      position: relative;
    }
    .url-input {
      width: 100%;
      height: 48px;
      background: #0d1322;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 0 16px;
      color: #fff;
      font-size: 15px;
      font-family: 'JetBrains Mono', monospace;
      outline: none;
      transition: all 0.2s;
    }
    .url-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2); }
    
    .param-group {
      display: flex;
      gap: 10px;
    }
    .param-select {
      height: 48px;
      background: #0d1322;
      border: 1px solid var(--border);
      color: #fff;
      padding: 0 14px;
      border-radius: 10px;
      font-size: 14px;
      outline: none;
    }
    .btn-start {
      height: 48px;
      background: linear-gradient(135deg, #2563eb, #1d4ed8);
      color: white;
      border: none;
      padding: 0 24px;
      border-radius: 10px;
      font-weight: 700;
      font-size: 15px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
    }
    .btn-start:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4); }
    .btn-start:disabled { opacity: 0.6; cursor: not-allowed; }

    .quick-presets {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: 14px;
      font-size: 13px;
      color: var(--text-muted);
      flex-wrap: wrap;
    }
    .preset-pill {
      background: #1f293d;
      color: #93c5fd;
      padding: 4px 10px;
      border-radius: 6px;
      cursor: pointer;
      border: 1px solid #334155;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      transition: all 0.15s;
    }
    .preset-pill:hover { background: #2563eb; color: #fff; }

    /* Progress Banner */
    .progress-banner {
      display: none;
      background: var(--card-alt);
      border: 1px solid var(--primary);
      border-radius: 12px;
      padding: 16px 20px;
      margin-bottom: 24px;
      animation: fadeIn 0.3s;
    }
    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-size: 14px;
    }
    .progress-bar-track {
      width: 100%;
      height: 8px;
      background: #1f293d;
      border-radius: 4px;
      overflow: hidden;
    }
    .progress-bar-fill {
      width: 0%;
      height: 100%;
      background: linear-gradient(90deg, #3b82f6, #10b981);
      transition: width 0.3s;
    }

    /* KPI Cards */
    .kpi-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .kpi-box {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .kpi-icon {
      width: 48px;
      height: 48px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
    }
    .kpi-val { font-size: 28px; font-weight: 800; line-height: 1.1; }
    .kpi-label { font-size: 12px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }

    /* Report Sections */
    .report-wrap { display: none; }
    .report-nav {
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 12px;
      margin-bottom: 20px;
      overflow-x: auto;
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 8px 16px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      transition: all 0.2s;
      white-space: nowrap;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .tab-btn.active { background: #1e293b; color: #fff; }
    .tab-btn .counter {
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 700;
    }
    .cnt-confirmed { background: #dc2626; color: #fff; }
    .cnt-suspected { background: #d97706; color: #fff; }
    .cnt-all { background: #3b82f6; color: #fff; }

    .action-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      flex-wrap: wrap;
      gap: 12px;
    }
    .filter-pills { display: flex; gap: 8px; flex-wrap: wrap; }
    .pill {
      background: #1e293b;
      border: 1px solid var(--border);
      color: #94a3b8;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      cursor: pointer;
    }
    .pill.active { background: var(--primary); color: #fff; border-color: var(--primary); }
    .search-input {
      background: #0d1322;
      border: 1px solid var(--border);
      color: #fff;
      padding: 7px 14px;
      border-radius: 8px;
      font-size: 13px;
      width: 250px;
      outline: none;
    }

    /* Export button group */
    .export-btns {
      display: flex;
      gap: 8px;
    }
    .btn-export {
      background: #1e293b;
      border: 1px solid var(--border);
      color: #cbd5e1;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s;
    }
    .btn-export:hover { background: #334155; color: #fff; }

    /* Issue Cards */
    .issue-grid {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .qa-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px 20px;
      transition: border-color 0.2s, transform 0.15s;
    }
    .qa-card:hover { border-color: #3b82f6; }
    .qa-card-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 10px;
      gap: 12px;
      flex-wrap: wrap;
    }
    .qa-title { font-size: 15px; font-weight: 700; color: #f9fafb; }
    .badge-wrap { display: flex; gap: 6px; align-items: center; }
    .badge-tag {
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .status-confirmed { background: #dc2626; color: #fff; }
    .status-suspected { background: #d97706; color: #fff; }
    .sev-P0_CRITICAL { background: rgba(239, 68, 68, 0.18); color: #f87171; border: 1px solid #ef4444; }
    .sev-P1_HIGH { background: rgba(249, 115, 22, 0.18); color: #fb923c; border: 1px solid #f97316; }
    .sev-P2_MEDIUM { background: rgba(234, 179, 8, 0.18); color: #facc15; border: 1px solid #eab308; }
    .sev-P3_LOW { background: rgba(59, 130, 246, 0.18); color: #60a5fa; border: 1px solid #3b82f6; }
    .cat-tag { background: #1e293b; color: #cbd5e1; border: 1px solid #334155; }

    .qa-desc { font-size: 13.5px; color: #cbd5e1; margin-bottom: 12px; }
    .qa-code {
      background: #090d16;
      border: 1px solid #1e293b;
      padding: 8px 12px;
      border-radius: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: #93c5fd;
      margin-bottom: 10px;
      white-space: pre-wrap;
      word-break: break-all;
    }
    .qa-fix {
      background: rgba(16, 185, 129, 0.08);
      border-left: 3px solid #10b981;
      padding: 10px 14px;
      border-radius: 4px;
      font-size: 13px;
      color: #a7f3d0;
    }
    .qa-footer {
      font-size: 12px;
      color: #64748b;
      margin-top: 10px;
      display: flex;
      justify-content: space-between;
    }

    /* Summary Tab Styling */
    .summary-box {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 24px;
    }
    .summary-box h3 { font-size: 18px; margin-bottom: 12px; }
    .summary-text { font-size: 14px; color: #d1d5db; white-space: pre-line; line-height: 1.7; margin-bottom: 20px; }
    .rec-item {
      padding: 10px 14px;
      background: rgba(255,255,255,0.03);
      border-left: 3px solid var(--primary);
      margin-bottom: 10px;
      border-radius: 4px;
      font-size: 14px;
    }

    /* Pages Table */
    .pages-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13.5px;
    }
    .pages-table th, .pages-table td {
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }
    .pages-table th { background: #161f31; color: var(--text-muted); font-weight: 600; }
    .pages-table tr:hover { background: rgba(255,255,255,0.02); }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
  </style>
</head>
<body>
  <div class="container">
    <div class="top-nav">
      <div class="brand">
        <div class="logo-badge">🛡️</div>
        <div>
          <h1>AI Website QA Agent</h1>
          <p>Autonomous defect detection, broken links, images, content consistency & SEO inspection</p>
        </div>
      </div>
      <div class="staging-badge">
        <span style="display:inline-block; width:8px; height:8px; background:#10b981; border-radius:50%;"></span>
        Staging Inspector Engine Active
      </div>
    </div>

    <!-- Scanner Control Card -->
    <div class="scan-card">
      <div class="scan-form-row">
        <div class="url-input-wrap">
          <input type="url" id="targetUrl" class="url-input" placeholder="https://staging.example.com or http://127.0.0.1:8088" value="http://127.0.0.1:8088">
        </div>
        <div class="param-group">
          <select id="maxPages" class="param-select" title="Max Pages">
            <option value="5" selected>5 Pages</option>
            <option value="10">10 Pages</option>
            <option value="20">20 Pages</option>
            <option value="1">1 Page Only</option>
          </select>
          <select id="maxDepth" class="param-select" title="Max Crawl Depth">
            <option value="1">Depth: 1</option>
            <option value="2" selected>Depth: 2</option>
            <option value="3">Depth: 3</option>
          </select>
          <button id="startBtn" class="btn-start" onclick="startAudit()">
            <span>⚡ Run QA Audit</span>
          </button>
        </div>
      </div>
      <div class="quick-presets">
        <span>Quick Test Targets:</span>
        <span class="preset-pill" onclick="setPreset('http://127.0.0.1:8088')">⚡ Built-in Defect Staging Site (Port 8088)</span>
        <span class="preset-pill" onclick="setPreset('http://127.0.0.1:8088/about')">📄 Staging /about</span>
        <span class="preset-pill" onclick="setPreset('http://127.0.0.1:8088/contact')">📄 Staging /contact</span>
        <span class="preset-pill" onclick="setPreset('http://127.0.0.1:8088/pricing')">📄 Staging /pricing</span>
      </div>
    </div>

    <!-- Active Scan Progress Banner -->
    <div id="progressBanner" class="progress-banner">
      <div class="progress-header">
        <span id="progressMsg">Auditing target website...</span>
        <span id="progressPct">0%</span>
      </div>
      <div class="progress-bar-track">
        <div id="progressBarFill" class="progress-bar-fill"></div>
      </div>
    </div>

    <!-- Report Dashboard Wrap -->
    <div id="reportWrap" class="report-wrap">
      <!-- KPI Row -->
      <div class="kpi-row">
        <div class="kpi-box">
          <div class="kpi-icon" id="scoreIcon" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">🛡️</div>
          <div>
            <div class="kpi-val" id="kpiScore">--</div>
            <div class="kpi-label">Health Score</div>
          </div>
        </div>
        <div class="kpi-box">
          <div class="kpi-icon" style="background: rgba(220, 38, 38, 0.15); color: #ef4444;">🚨</div>
          <div>
            <div class="kpi-val" id="kpiConfirmed" style="color: #ef4444;">0</div>
            <div class="kpi-label">Confirmed Defects</div>
          </div>
        </div>
        <div class="kpi-box">
          <div class="kpi-icon" style="background: rgba(217, 119, 6, 0.15); color: #f59e0b;">⚠️</div>
          <div>
            <div class="kpi-val" id="kpiSuspected" style="color: #f59e0b;">0</div>
            <div class="kpi-label">Suspected Issues</div>
          </div>
        </div>
        <div class="kpi-box">
          <div class="kpi-icon" style="background: rgba(59, 130, 246, 0.15); color: #3b82f6;">📄</div>
          <div>
            <div class="kpi-val" id="kpiPages">0</div>
            <div class="kpi-label">Pages Crawled</div>
          </div>
        </div>
      </div>

      <!-- Tab Navigation -->
      <div class="report-nav">
        <button class="tab-btn active" onclick="switchTab('confirmed', this)">
          🚨 Confirmed Issues <span id="tabCntConfirmed" class="counter cnt-confirmed">0</span>
        </button>
        <button class="tab-btn" onclick="switchTab('suspected', this)">
          ⚠️ Suspected Issues <span id="tabCntSuspected" class="counter cnt-suspected">0</span>
        </button>
        <button class="tab-btn" onclick="switchTab('all', this)">
          📑 All Issues <span id="tabCntAll" class="counter cnt-all">0</span>
        </button>
        <button class="tab-btn" onclick="switchTab('summary', this)">
          🧠 AI Executive Summary
        </button>
        <button class="tab-btn" onclick="switchTab('pages', this)">
          🌐 Pages Audited
        </button>
      </div>

      <!-- Controls & Exports -->
      <div id="filterBar" class="action-bar">
        <div class="filter-pills">
          <button class="pill active" onclick="setSeverityFilter('ALL', this)">All Severities</button>
          <button class="pill" onclick="setSeverityFilter('P0_CRITICAL', this)">P0 Critical</button>
          <button class="pill" onclick="setSeverityFilter('P1_HIGH', this)">P1 High</button>
          <button class="pill" onclick="setSeverityFilter('P2_MEDIUM', this)">P2 Medium</button>
          <button class="pill" onclick="setSeverityFilter('P3_LOW', this)">P3 Low</button>
        </div>
        <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
          <input type="text" id="searchInput" class="search-input" placeholder="Search issues..." oninput="handleSearch(this.value)">
          <div class="export-btns">
            <a href="/api/export/html" target="_blank" class="btn-export">📥 Export HTML</a>
            <a href="/api/export/markdown" target="_blank" class="btn-export">📥 Export MD</a>
            <a href="/api/export/json" target="_blank" class="btn-export">📥 Export JSON</a>
          </div>
        </div>
      </div>

      <!-- Tab Content: Issues List -->
      <div id="tabIssuesContent">
        <div id="issueList" class="issue-grid"></div>
      </div>

      <!-- Tab Content: Executive Summary -->
      <div id="tabSummaryContent" style="display: none;">
        <div class="summary-box">
          <h3>🎯 Executive QA Evaluation</h3>
          <div id="summaryText" class="summary-text"></div>
          <h3 style="margin-top: 20px;">📋 Actionable Recommendations</h3>
          <div id="recommendationsList"></div>
        </div>
      </div>

      <!-- Tab Content: Pages List -->
      <div id="tabPagesContent" style="display: none;">
        <div class="summary-box">
          <h3>🌐 Crawled Pages Breakdown</h3>
          <table class="pages-table">
            <thead>
              <tr>
                <th>Page URL</th>
                <th>Status</th>
                <th>Load Time</th>
                <th>Links Inspected</th>
                <th>Images Inspected</th>
                <th>Issues Found</th>
              </tr>
            </thead>
            <tbody id="pagesTableBody"></tbody>
          </table>
        </div>
      </div>

    </div>
  </div>

  <script>
    let pollInterval = null;
    let reportData = null;
    let currentTab = 'confirmed'; // 'confirmed', 'suspected', 'all', 'summary', 'pages'
    let currentSeverity = 'ALL';
    let searchQuery = '';

    function setPreset(url) {
      document.getElementById('targetUrl').value = url;
    }

    async function startAudit() {
      const url = document.getElementById('targetUrl').value.trim();
      if (!url) return alert('Please enter a website or staging URL.');

      const maxPages = parseInt(document.getElementById('maxPages').value);
      const maxDepth = parseInt(document.getElementById('maxDepth').value);

      document.getElementById('startBtn').disabled = true;
      document.getElementById('progressBanner').style.display = 'block';
      document.getElementById('reportWrap').style.display = 'none';

      try {
        const resp = await fetch('/api/audit', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ url, max_pages: maxPages, max_depth: maxDepth })
        });
        if (!resp.ok) {
          const err = await resp.json();
          alert('Error: ' + (err.error || 'Failed to start scan'));
          document.getElementById('startBtn').disabled = false;
          return;
        }
        pollScanStatus();
      } catch (err) {
        alert('Failed to connect to agent server: ' + err.message);
        document.getElementById('startBtn').disabled = false;
      }
    }

    function pollScanStatus() {
      if (pollInterval) clearInterval(pollInterval);
      pollInterval = setInterval(async () => {
        try {
          const resp = await fetch('/api/scan-status');
          const data = await resp.json();

          const pct = Math.round((data.progress || 0) * 100);
          document.getElementById('progressBarFill').style.width = pct + '%';
          document.getElementById('progressPct').innerText = pct + '%';
          document.getElementById('progressMsg').innerText = data.message || 'Scanning...';

          if (data.status === 'completed') {
            clearInterval(pollInterval);
            document.getElementById('startBtn').disabled = false;
            document.getElementById('progressBanner').style.display = 'none';
            reportData = data.report;
            renderReport();
          } else if (data.status === 'failed') {
            clearInterval(pollInterval);
            document.getElementById('startBtn').disabled = false;
            alert('Scan failed: ' + data.message);
          }
        } catch (e) {
          console.error(e);
        }
      }, 1000);
    }

    function renderReport() {
      if (!reportData) return;
      document.getElementById('reportWrap').style.display = 'block';

      // KPI values
      const score = reportData.health_score;
      document.getElementById('kpiScore').innerText = score + '/100';
      const scoreColor = score >= 80 ? '#10b981' : (score >= 50 ? '#f59e0b' : '#ef4444');
      document.getElementById('kpiScore').style.color = scoreColor;
      document.getElementById('scoreIcon').style.color = scoreColor;

      document.getElementById('kpiConfirmed').innerText = reportData.confirmed_count;
      document.getElementById('kpiSuspected').innerText = reportData.suspected_count;
      document.getElementById('kpiPages').innerText = reportData.stats.pages_crawled;

      document.getElementById('tabCntConfirmed').innerText = reportData.confirmed_count;
      document.getElementById('tabCntSuspected').innerText = reportData.suspected_count;
      document.getElementById('tabCntAll').innerText = reportData.total_issues;

      // Executive Summary Tab
      document.getElementById('summaryText').innerText = reportData.executive_summary;
      const recContainer = document.getElementById('recommendationsList');
      recContainer.innerHTML = '';
      (reportData.top_recommendations || []).forEach(r => {
        const item = document.createElement('div');
        item.className = 'rec-item';
        item.innerHTML = r;
        recContainer.appendChild(item);
      });

      // Pages Tab
      const pagesBody = document.getElementById('pagesTableBody');
      pagesBody.innerHTML = '';
      (reportData.pages || []).forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><code>${p.url}</code></td>
          <td><span style="color:${p.status_code < 400 ? '#10b981':'#ef4444'}">HTTP ${p.status_code}</span></td>
          <td>${p.load_time_ms} ms</td>
          <td>${p.links_checked}</td>
          <td>${p.images_checked}</td>
          <td><strong>${(p.issues || []).length}</strong></td>
        `;
        pagesBody.appendChild(tr);
      });

      renderIssues();
    }

    function renderIssues() {
      const container = document.getElementById('issueList');
      container.innerHTML = '';

      if (!reportData || !reportData.issues) return;

      const filtered = reportData.issues.filter(issue => {
        // Tab filter
        if (currentTab === 'confirmed' && issue.status !== 'CONFIRMED') return false;
        if (currentTab === 'suspected' && issue.status !== 'SUSPECTED') return false;

        // Severity filter
        if (currentSeverity !== 'ALL' && issue.severity !== currentSeverity) return false;

        // Search
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
        container.innerHTML = '<div style="text-align:center; padding: 48px; color:#64748b;">🎉 No issues found under this filter criteria!</div>';
        return;
      }

      filtered.forEach(issue => {
        const card = document.createElement('div');
        card.className = 'qa-card';
        card.innerHTML = `
          <div class="qa-card-head">
            <div class="qa-title">${issue.title}</div>
            <div class="badge-wrap">
              <span class="badge-tag status-${issue.status.toLowerCase()}">${issue.status === 'CONFIRMED' ? 'Confirmed Defect' : 'Suspected Anomaly'}</span>
              <span class="badge-tag sev-${issue.severity}">${issue.severity.replace('_', ' ')}</span>
              <span class="badge-tag cat-tag">${issue.category.replace('_', ' ')}</span>
            </div>
          </div>
          <div class="qa-desc">${issue.description}</div>
          ${issue.element_selector ? `<div class="qa-code">Element Context: ${escapeHtml(issue.element_selector)}</div>` : ''}
          <div class="qa-fix">💡 <strong>Remediation:</strong> ${issue.remediation}</div>
          <div class="qa-footer">
            <span>Found on: <code>${issue.url}</code></span>
            <span>ID: ${issue.id}</span>
          </div>
        `;
        container.appendChild(card);
      });
    }

    function escapeHtml(str) {
      return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function switchTab(tab, btn) {
      currentTab = tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const isIssues = (tab === 'confirmed' || tab === 'suspected' || tab === 'all');
      document.getElementById('tabIssuesContent').style.display = isIssues ? 'block' : 'none';
      document.getElementById('filterBar').style.display = isIssues ? 'flex' : 'none';
      document.getElementById('tabSummaryContent').style.display = tab === 'summary' ? 'block' : 'none';
      document.getElementById('tabPagesContent').style.display = tab === 'pages' ? 'block' : 'none';

      if (isIssues) renderIssues();
    }

    function setSeverityFilter(sev, btn) {
      currentSeverity = (currentSeverity === sev && sev !== 'ALL') ? 'ALL' : sev;
      document.querySelectorAll('.filter-pills .pill').forEach(p => p.classList.remove('active'));
      if (currentSeverity !== 'ALL') btn.classList.add('active');
      else document.querySelector('.filter-pills .pill').classList.add('active');
      renderIssues();
    }

    function handleSearch(val) {
      searchQuery = val.trim();
      renderIssues();
    }

    // Check if initial status has a report
    window.addEventListener('DOMContentLoaded', async () => {
      try {
        const resp = await fetch('/api/scan-status');
        const data = await resp.json();
        if (data.has_report) {
          reportData = data.report;
          renderReport();
        }
      } catch (e) {}
    });
  </script>
</body>
</html>
""")
