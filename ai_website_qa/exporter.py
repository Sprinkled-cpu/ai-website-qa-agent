import json
from datetime import datetime
from ai_website_qa.models import QAReport, Severity, IssueStatus, Category


class QAExporter:
    @staticmethod
    def to_json(report: QAReport, indent: int = 2) -> str:
        return report.model_dump_json(indent=indent)

    @staticmethod
    def to_markdown(report: QAReport) -> str:
        confirmed_issues = [i for i in report.issues if i.status == IssueStatus.CONFIRMED]
        suspected_issues = [i for i in report.issues if i.status == IssueStatus.SUSPECTED]

        md = []
        md.append(f"# 🛡️ AI Website QA Audit Report")
        md.append(f"**Target URL:** `{report.target_url}`  ")
        md.append(f"**Generated At:** {report.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}  ")
        md.append(f"**Overall Health Score:** **{report.health_score}/100**  ")
        md.append(f"**Pages Audited:** {report.stats.pages_crawled} | **Links Checked:** {report.stats.total_links_inspected} | **Images Checked:** {report.stats.total_images_inspected}  ")
        md.append(f"**Total Issues:** {report.total_issues} (**{report.confirmed_count} Confirmed**, **{report.suspected_count} Suspected**)")
        md.append("")
        md.append("---")
        md.append("")

        # Executive Summary
        md.append(report.executive_summary)
        md.append("")

        # Top Recommendations
        md.append("## 🎯 Prioritized Action Items")
        for rec in report.top_recommendations:
            md.append(f"- {rec}")
        md.append("")

        # Issue Summary Table
        md.append("## 📊 Defect Distribution")
        md.append("| Severity | Total | Confirmed (Verified) | Suspected (Review) |")
        md.append("| :--- | :--- | :--- | :--- |")
        for sev in [Severity.P0_CRITICAL, Severity.P1_HIGH, Severity.P2_MEDIUM, Severity.P3_LOW]:
            c_cnt = sum(1 for i in confirmed_issues if i.severity == sev)
            s_cnt = sum(1 for i in suspected_issues if i.severity == sev)
            md.append(f"| **{sev.value}** | {c_cnt + s_cnt} | {c_cnt} | {s_cnt} |")
        md.append("")

        # Confirmed Issues Section
        md.append(f"## 🚨 1. Confirmed Issues ({len(confirmed_issues)})")
        md.append("> *These are definite, reproducible defects verified by automated HTTP responses or explicit DOM violations.*")
        md.append("")
        if not confirmed_issues:
            md.append("✅ *No confirmed defects detected.*")
            md.append("")
        else:
            for i, issue in enumerate(confirmed_issues, 1):
                md.append(f"### #{i} [{issue.severity.value}] {issue.title}")
                md.append(f"- **Category:** `{issue.category.value}`")
                md.append(f"- **URL:** `{issue.url}`")
                md.append(f"- **Status:** `CONFIRMED DEFECT`")
                md.append(f"- **Description:** {issue.description}")
                if issue.element_selector:
                    md.append(f"- **Element / Context:** `{issue.element_selector}`")
                if issue.evidence:
                    md.append(f"- **Diagnostics:** `{issue.evidence}`")
                md.append(f"- **Remediation:** 💡 {issue.remediation}")
                md.append("")

        # Suspected Issues Section
        md.append(f"## ⚠️ 2. Suspected Issues ({len(suspected_issues)})")
        md.append("> *These are potential anomalies, SEO/editorial best practice warnings, or heuristic matches requiring human or contextual review.*")
        md.append("")
        if not suspected_issues:
            md.append("✅ *No suspected anomalies flagged.*")
            md.append("")
        else:
            for i, issue in enumerate(suspected_issues, 1):
                md.append(f"### #{i} [{issue.severity.value}] {issue.title}")
                md.append(f"- **Category:** `{issue.category.value}`")
                md.append(f"- **URL:** `{issue.url}`")
                md.append(f"- **Status:** `SUSPECTED (NEEDS REVIEW)`")
                md.append(f"- **Description:** {issue.description}")
                if issue.element_selector:
                    md.append(f"- **Element / Context:** `{issue.element_selector}`")
                if issue.evidence:
                    md.append(f"- **Diagnostics:** `{issue.evidence}`")
                md.append(f"- **Remediation:** 💡 {issue.remediation}")
                md.append("")

        # Page Audit Details
        md.append("## 📄 Audited Pages Summary")
        md.append("| Page URL | Status | Response Time | Issues Found |")
        md.append("| :--- | :--- | :--- | :--- |")
        for p in report.pages:
            md.append(f"| `{p.url}` | HTTP {p.status_code} | {p.load_time_ms}ms | {len(p.issues)} |")
        md.append("")

        return "\n".join(md)

    @staticmethod
    def to_standalone_html(report: QAReport) -> str:
        report_json = report.model_dump_json()

        score_color = "#10b981" if report.health_score >= 80 else ("#f59e0b" if report.health_score >= 50 else "#ef4444")

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>QA Audit Report - {report.target_url}</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #3b82f6;
      --p0: #ef4444;
      --p1: #f97316;
      --p2: #eab308;
      --p3: #3b82f6;
      --confirmed: #dc2626;
      --suspected: #d97706;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text-main);
      padding: 32px 20px;
      line-height: 1.5;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    header {{
      background: var(--card-bg);
      padding: 24px 32px;
      border-radius: 12px;
      border: 1px solid var(--border);
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .header-left h1 {{ font-size: 24px; font-weight: 700; margin-bottom: 6px; }}
    .header-left p {{ color: var(--text-muted); font-size: 14px; }}
    .health-badge {{
      background: rgba(255,255,255,0.05);
      border: 2px solid {score_color};
      padding: 12px 24px;
      border-radius: 12px;
      text-align: center;
    }}
    .health-badge .score {{ font-size: 36px; font-weight: 800; color: {score_color}; }}
    .health-badge .label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); }}

    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px 20px;
    }}
    .kpi-card .num {{ font-size: 26px; font-weight: 700; margin-bottom: 4px; }}
    .kpi-card .title {{ font-size: 13px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }}

    .summary-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
    }}
    .summary-card h2 {{ font-size: 18px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
    .recommendation-list {{ list-style-type: none; margin-top: 12px; }}
    .recommendation-list li {{
      padding: 8px 12px;
      background: rgba(255,255,255,0.03);
      border-left: 3px solid var(--primary);
      margin-bottom: 8px;
      border-radius: 4px;
      font-size: 14px;
    }}

    .controls {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px 20px;
      margin-bottom: 24px;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      justify-content: space-between;
    }}
    .filter-group {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .btn-filter {{
      background: #334155;
      color: #cbd5e1;
      border: none;
      padding: 8px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      transition: all 0.2s;
    }}
    .btn-filter.active, .btn-filter:hover {{
      background: var(--primary);
      color: #fff;
    }}
    .btn-filter.confirmed-active {{ background: #dc2626 !important; color: white !important; }}
    .btn-filter.suspected-active {{ background: #d97706 !important; color: white !important; }}
    .search-box {{
      background: #0f172a;
      border: 1px solid var(--border);
      padding: 8px 14px;
      border-radius: 6px;
      color: #fff;
      font-size: 13px;
      min-width: 240px;
    }}

    .issue-list {{
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    .issue-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 20px;
      transition: border-color 0.2s;
    }}
    .issue-card:hover {{
      border-color: #64748b;
    }}
    .issue-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 10px;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .issue-title {{
      font-size: 16px;
      font-weight: 600;
      color: #f1f5f9;
    }}
    .badges {{
      display: flex;
      gap: 6px;
      align-items: center;
    }}
    .badge {{
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge-P0_CRITICAL {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }}
    .badge-P1_HIGH {{ background: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid #f97316; }}
    .badge-P2_MEDIUM {{ background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid #eab308; }}
    .badge-P3_LOW {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6; }}
    .badge-CONFIRMED {{ background: #dc2626; color: #fff; }}
    .badge-SUSPECTED {{ background: #d97706; color: #fff; }}
    .badge-cat {{ background: #334155; color: #cbd5e1; }}

    .issue-desc {{
      color: #cbd5e1;
      font-size: 14px;
      margin-bottom: 12px;
    }}
    .code-box {{
      background: #0f172a;
      border: 1px solid #334155;
      padding: 8px 12px;
      border-radius: 6px;
      font-family: monospace;
      font-size: 12px;
      color: #93c5fd;
      margin-bottom: 12px;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }}
    .remediation-box {{
      background: rgba(16, 185, 129, 0.08);
      border-left: 3px solid #10b981;
      padding: 10px 14px;
      border-radius: 4px;
      font-size: 13px;
      color: #a7f3d0;
    }}
    .issue-meta {{
      font-size: 12px;
      color: #64748b;
      margin-top: 10px;
    }}
    .no-results {{
      text-align: center;
      padding: 48px;
      color: var(--text-muted);
      font-size: 16px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="header-left">
        <h1>🛡️ AI Website QA Audit Report</h1>
        <p>Target: <strong>{report.target_url}</strong> &bull; Scanned on {report.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
      </div>
      <div class="health-badge">
        <div class="score">{report.health_score}</div>
        <div class="label">QA Health Score</div>
      </div>
    </header>

    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="num" style="color: #ef4444;">{report.confirmed_count}</div>
        <div class="title">Confirmed Defects</div>
      </div>
      <div class="kpi-card">
        <div class="num" style="color: #f59e0b;">{report.suspected_count}</div>
        <div class="title">Suspected Anomalies</div>
      </div>
      <div class="kpi-card">
        <div class="num" style="color: #3b82f6;">{report.stats.pages_crawled}</div>
        <div class="title">Pages Audited</div>
      </div>
      <div class="kpi-card">
        <div class="num" style="color: #10b981;">{report.stats.total_links_inspected + report.stats.total_images_inspected}</div>
        <div class="title">Total Assets Checked</div>
      </div>
    </div>

    <div class="summary-card">
      <h2>🎯 Executive Synthesis & Remediation Roadmap</h2>
      <ul class="recommendation-list">
        {"".join(f"<li>{r}</li>" for r in report.top_recommendations)}
      </ul>
    </div>

    <div class="controls">
      <div class="filter-group">
        <button class="btn-filter active" onclick="setFilter('status', 'ALL', this)">All ({report.total_issues})</button>
        <button class="btn-filter" onclick="setFilter('status', 'CONFIRMED', this)">Confirmed ({report.confirmed_count})</button>
        <button class="btn-filter" onclick="setFilter('status', 'SUSPECTED', this)">Suspected ({report.suspected_count})</button>
      </div>
      <div class="filter-group">
        <button class="btn-filter" onclick="setFilter('severity', 'P0_CRITICAL', this)">P0 Critical ({report.severity_breakdown.get('P0_CRITICAL', 0)})</button>
        <button class="btn-filter" onclick="setFilter('severity', 'P1_HIGH', this)">P1 High ({report.severity_breakdown.get('P1_HIGH', 0)})</button>
        <button class="btn-filter" onclick="setFilter('severity', 'P2_MEDIUM', this)">P2 Medium ({report.severity_breakdown.get('P2_MEDIUM', 0)})</button>
        <button class="btn-filter" onclick="setFilter('severity', 'P3_LOW', this)">P3 Low ({report.severity_breakdown.get('P3_LOW', 0)})</button>
      </div>
      <input type="text" class="search-box" placeholder="Search issues by keyword..." oninput="handleSearch(this.value)">
    </div>

    <div id="issue-list" class="issue-list"></div>
  </div>

  <script>
    const reportData = {report_json};
    let currentStatus = 'ALL';
    let currentSeverity = 'ALL';
    let searchQuery = '';

    function renderIssues() {{
      const container = document.getElementById('issue-list');
      container.innerHTML = '';

      const filtered = reportData.issues.filter(issue => {{
        if (currentStatus !== 'ALL' && issue.status !== currentStatus) return false;
        if (currentSeverity !== 'ALL' && issue.severity !== currentSeverity) return false;
        if (searchQuery) {{
          const q = searchQuery.toLowerCase();
          const matchTitle = issue.title.toLowerCase().includes(q);
          const matchDesc = issue.description.toLowerCase().includes(q);
          const matchUrl = issue.url.toLowerCase().includes(q);
          if (!matchTitle && !matchDesc && !matchUrl) return false;
        }}
        return true;
      }});

      if (filtered.length === 0) {{
        container.innerHTML = '<div class="no-results">🎉 No issues match your filter criteria!</div>';
        return;
      }}

      filtered.forEach(issue => {{
        const card = document.createElement('div');
        card.className = 'issue-card';
        card.innerHTML = `
          <div class="issue-header">
            <div class="issue-title">${{issue.title}}</div>
            <div class="badges">
              <span class="badge badge-${{issue.status}}">${{issue.status === 'CONFIRMED' ? 'Confirmed Defect' : 'Suspected Anomaly'}}</span>
              <span class="badge badge-${{issue.severity}}">${{issue.severity.replace('_', ' ')}}</span>
              <span class="badge badge-cat">${{issue.category.replace('_', ' ')}}</span>
            </div>
          </div>
          <div class="issue-desc">${{issue.description}}</div>
          ${{issue.element_selector ? `<div class="code-box">Element Context: ${{escapeHtml(issue.element_selector)}}</div>` : ''}}
          <div class="remediation-box">💡 <strong>Remediation:</strong> ${{issue.remediation}}</div>
          <div class="issue-meta">Found on: <code>${{issue.url}}</code> | ID: ${{issue.id}}</div>
        `;
        container.appendChild(card);
      }});
    }}

    function escapeHtml(str) {{
      return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }}

    function setFilter(type, val, btn) {{
      if (type === 'status') {{
        currentStatus = (currentStatus === val && val !== 'ALL') ? 'ALL' : val;
        // update button state
        document.querySelectorAll('.filter-group:nth-child(1) .btn-filter').forEach(b => {{
          b.classList.remove('active', 'confirmed-active', 'suspected-active');
        }});
        if (currentStatus === 'CONFIRMED') btn.classList.add('confirmed-active');
        else if (currentStatus === 'SUSPECTED') btn.classList.add('suspected-active');
        else btn.classList.add('active');
      }} else if (type === 'severity') {{
        currentSeverity = (currentSeverity === val && val !== 'ALL') ? 'ALL' : val;
        document.querySelectorAll('.filter-group:nth-child(2) .btn-filter').forEach(b => b.classList.remove('active'));
        if (currentSeverity !== 'ALL') btn.classList.add('active');
      }}
      renderIssues();
    }}

    function handleSearch(val) {{
      searchQuery = val.trim();
      renderIssues();
    }}

    // Initial render
    renderIssues();
  </script>
</body>
</html>
"""
        return html_template
