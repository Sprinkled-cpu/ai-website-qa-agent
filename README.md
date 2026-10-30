# 🛡️ AI Website QA Agent

An autonomous website & staging QA inspection agent designed to audit websites for broken links, missing/broken images, content inconsistencies, obvious UI/layout defects, and SEO problems, generating a prioritized, actionable QA report with **strict separation between Confirmed Defects and Suspected Anomalies**.

---

## 🌐 Live Public Demo (Active Link)

**Shareable Live Dashboard:**  
👉 **[https://acad11819d4843.lhr.life](https://acad11819d4843.lhr.life)**

*Fully hosted live with persistent keep-alive heartbeat, interactive magnetic particle background, Web Audio sound effects, live bug radar, Whack-a-Bug mini-game, and defect squasher simulator.*

---

## 🌟 Key Features

### 1. Distinct Defect Classification
- **🚨 Confirmed Defects (Verified):** Deterministic, reproducible failures verified by HTTP status codes or clear DOM violations:
  - Dead links returning HTTP 404/410/500
  - Broken image assets (`src` missing, empty, or returning HTTP 404/500/0 bytes)
  - Un-rendered template tags (e.g., `{{ company.tagline }}`)
  - Raw placeholder copy ("Lorem ipsum dolor sit amet...")
  - Explicit developer TODO/FIXME markers
  - Clickable `<button>` or `<a class="btn">` with no text, icon, or `aria-label`
  - Broken internal page anchors (`#target` where ID does not exist)
  - Missing mobile viewport `<meta name="viewport">`
  - Missing document `<title>` tag
  - Conflicting multiple `<link rel="canonical">` declarations
  - Active `noindex` directives
- **⚠️ Suspected Anomalies (Contextual Review):** Heuristic warnings and best-practice advisories requiring human or editorial review:
  - Suspicious placeholder numbers (e.g. `555-0199`) or dummy emails (`test@example.com`)
  - Outdated copyright year (e.g., `© 2019`)
  - Overly long or short page `<title>` / `<meta name="description">`
  - Image missing descriptive `alt` attribute or layout dimensions (Cumulative Layout Shift risk)
  - Skipped heading hierarchy (e.g. `<h1>` followed directly by `<h4>`)
  - Multiple `<h1>` primary headings
  - External link network timeouts or 403 access challenges

### 2. Prioritized Severity System
Every discovered issue is scored and prioritized across standard engineering tiers:
- **P0 - Critical:** Blocker defects (broken primary routes, missing mobile viewport, raw template syntax).
- **P1 - High:** Significant defects (404 images, empty buttons, missing page title, unreplaced Lorem Ipsum hero text).
- **P2 - Medium:** Quality & SEO defects (missing alt tags, broken hash anchors, missing meta description, duplicate H1s).
- **P3 - Low:** Polish & optimization items (title/meta length warnings, missing OpenGraph tags, outdated copyright).

### 3. Comprehensive Inspection Engines
1. **Broken Links Inspector:** Validates all internal & external anchors, detects dead in-page hashes, placeholder hrefs (`#`, `javascript:;`), and malformed URLs.
2. **Missing Images Inspector:** Evaluates `<img>` src paths, 404 loads, 0-byte corrupted images, alt tags, and CLS dimensions.
3. **Content Consistency Inspector:** Scans for Lorem Ipsum, un-rendered template tokens (`{{...}}`), developer TODOs, Mojibake encoding artifacts (`â€™`, `Ã©`), doubled words, and placeholder contact information.
4. **UI & Layout Inspector:** Detects empty buttons, unlabelled form inputs, broken heading outlines, and missing responsive viewport configurations.
5. **SEO & Metadata Inspector:** Validates document `<title>`, meta description length, canonical tags, OpenGraph sharing tags, HTML `lang` attributes, and indexing robots directives.

---

## 🚀 Quick Start

### 1. Run the Built-In Demo (Immediate Evaluation)
The project includes a built-in mock staging environment pre-configured with realistic multi-page QA defects. To run an autonomous audit and generate the report:
```bash
python run.py demo
```
This audits the staging portal and automatically generates `staging_qa_report.html`.

### 2. Launch the Interactive Web Dashboard
```bash
python run.py serve --port 8000
```
Then open **`http://127.0.0.1:8000`** in your browser to:
- Enter any custom website or staging URL
- Configure crawl depth (1-3) and page limits (1-20)
- Watch real-time audit progress
- Filter interactively between **Confirmed Defects** and **Suspected Anomalies**
- Filter by severity (P0 Critical, P1 High, P2 Medium, P3 Low)
- One-click export to standalone **HTML**, **Markdown**, or **JSON**

### 3. Run via CLI for Any Website
```bash
# Audit any URL and export to standalone HTML report
python run.py audit https://staging.example.com --pages 10 --depth 2 --output qa_report.html

# Export to Markdown for GitHub PR or Jira
python run.py audit https://staging.example.com --output report.md --format md

# Export to JSON for CI/CD pipelines
python run.py audit https://staging.example.com --output report.json --format json
```

### 4. Run the Test Suite
```bash
python tests/test_inspectors.py
```

---

## 📁 Project Architecture

```
ai-website-qa-agent/
├── ai_website_qa/
│   ├── __init__.py
│   ├── models.py            # Pydantic schema (IssueStatus, Severity, Category, QAReport)
│   ├── agent.py             # Autonomous QA Orchestrator & Multi-page Auditor
│   ├── crawler.py           # Thread-safe Web Crawler with domain boundary control
│   ├── ai_synthesizer.py    # Health scoring algorithm & prioritized remediation synthesis
│   ├── exporter.py          # Exporters for Markdown, standalone HTML, and JSON
│   └── inspectors/
│       ├── __init__.py
│       ├── base.py          # BaseInspector abstraction
│       ├── links.py         # Broken links & in-page hash checker
│       ├── images.py        # Broken images & alt tag checker
│       ├── content.py       # Lorem Ipsum, templates, mojibake & copy scanner
│       ├── ui_layout.py     # Empty controls, form labels & viewport inspector
│       └── seo.py           # Titles, meta description, canonicals & robots inspector
├── mock_staging/
│   ├── server.py            # Realistic defect staging site
│   └── mock_adapter.py      # Direct in-memory HTTP adapter for 0-latency testing
├── tests/
│   └── test_inspectors.py   # Unit test suite verifying all 5 inspectors
├── run.py                   # Unified CLI runner (audit, demo, serve, mock)
├── web_app.py               # FastAPI backend & reactive Web Dashboard
└── README.md
```

---

## 📊 Sample Audit Output

```text
================================================================================
🎯 QA AUDIT REPORT FOR: http://127.0.0.1:8088/
🏆 Health Score: 0/100 (Critical Risk)
📄 Pages Audited: 4 in 0.05s
🔍 Assets Checked: 14 links, 2 images
--------------------------------------------------------------------------------
🚨 CONFIRMED DEFECTS : 17
⚠️  SUSPECTED ANOMALIES: 13
📊 Severity Breakdown: P0=3, P1=7, P2=12, P3=8
================================================================================

🚨 TOP CONFIRMED DEFECTS (MUST FIX):
  1. [P0_CRITICAL] Broken Link (HTTP 404)
     URL: http://127.0.0.1:8088/
     Fix: Update link href from '/non-existent-page' to an active endpoint.
  2. [P0_CRITICAL] Un-rendered Template / Script Leak: '{{ company.tagline }}'
     URL: http://127.0.0.1:8088/
     Fix: Ensure template engine populates variable before rendering DOM.
  3. [P0_CRITICAL] Missing Mobile Viewport Meta Tag
     URL: http://127.0.0.1:8088/contact
     Fix: Add '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
  4. [P1_HIGH] Lorem Ipsum Placeholder Content Detected
     URL: http://127.0.0.1:8088/about
     Fix: Replace dummy Latin copy with finalized product copy.

⚠️  TOP SUSPECTED ANOMALIES (REVIEW NEEDED):
  1. [P2_MEDIUM] Suspected Dummy Contact Data: 'test@example.com'
  2. [P2_MEDIUM] Suspected Dummy Contact Data: '555-0199'
  3. [P2_MEDIUM] Missing Canonical Link Tag
  4. [P3_LOW] Outdated Copyright Year (2019 vs 2026)
```
