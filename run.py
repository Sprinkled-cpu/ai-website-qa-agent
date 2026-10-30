"""
AI Website QA Agent - CLI & Unified Runner
Usage:
  python run.py audit <URL> [--pages 5] [--depth 2] [--output report.html]
  python run.py demo
  python run.py serve [--port 8000]
  python run.py mock [--port 8088]
"""

import sys
import argparse
import uvicorn
import time
import threading

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from ai_website_qa.agent import WebsiteQAAgent
from ai_website_qa.models import IssueStatus, Severity
from ai_website_qa.exporter import QAExporter


def print_banner():
    banner = r"""
   ___    ____   _      __     __         _  __          ____   ___       ___                      __ 
  /   |  /  _/  | | /| / /__  / /_  _____(_)/ /____     / __ \ /   |     /   | ____ _ ___   ____  / /_
 / /| |  / /    | |/ |/ // -_)/ _ \/ ___// // __/ -_)   / / / // /| |    / /| |/ __ `// -_) / _ \ / __/
/_/ |_|/___/    |__/|__/ \__//_.__/\___//_/ \__/\__/   / /_/ //_/ |_|   /_/ |_|\__, / \__/ /_//_/ \__/ 
                                                       \___\_\                 /___/                    
    """
    print(banner)
    print(" 🛡️  Prioritized Defect Inspector (Confirmed vs Suspected Classification)\n")


def run_audit_command(url: str, max_pages: int, max_depth: int, output_file: str, fmt: str):
    print_banner()
    print(f"🚀 Inspecting target: {url}")
    print(f"⚙️  Configuration: Max Pages = {max_pages}, Max Depth = {max_depth}\n")

    def progress_callback(msg: str, pct: float):
        percent = int(pct * 100)
        bar = "█" * (percent // 5) + "░" * (20 - (percent // 5))
        sys.stdout.write(f"\r[{bar}] {percent}% | {msg[:60]:<60}")
        sys.stdout.flush()

    agent = WebsiteQAAgent(max_pages=max_pages, max_depth=max_depth)
    report = agent.audit(url, progress_cb=progress_callback)
    print("\n")

    # Terminal Summary Table
    print("=" * 80)
    print(f"🎯 QA AUDIT REPORT FOR: {report.target_url}")
    print(f"🕒 Timestamp: {report.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"🏆 Health Score: {report.health_score}/100")
    print(f"📄 Pages Audited: {report.stats.pages_crawled} in {report.stats.duration_seconds}s")
    print(f"🔍 Assets Checked: {report.stats.total_links_inspected} links, {report.stats.total_images_inspected} images")
    print("-" * 80)
    print(f"🚨 CONFIRMED DEFECTS : {report.confirmed_count}")
    print(f"⚠️  SUSPECTED ANOMALIES: {report.suspected_count}")
    print(f"📊 Severity Breakdown: P0={report.severity_breakdown.get('P0_CRITICAL', 0)}, "
          f"P1={report.severity_breakdown.get('P1_HIGH', 0)}, "
          f"P2={report.severity_breakdown.get('P2_MEDIUM', 0)}, "
          f"P3={report.severity_breakdown.get('P3_LOW', 0)}")
    print("=" * 80)

    # Print Top 5 Confirmed Issues
    confirmed = [i for i in report.issues if i.status == IssueStatus.CONFIRMED]
    if confirmed:
        print("\n🚨 TOP CONFIRMED DEFECTS (MUST FIX):")
        for i, issue in enumerate(confirmed[:6], 1):
            print(f"  {i}. [{issue.severity.value}] {issue.title}")
            print(f"     URL: {issue.url}")
            print(f"     Fix: {issue.remediation}")
            if issue.element_selector:
                print(f"     Element: {issue.element_selector[:100]}")
            print()

    # Print Top 3 Suspected Issues
    suspected = [i for i in report.issues if i.status == IssueStatus.SUSPECTED]
    if suspected:
        print("\n⚠️  TOP SUSPECTED ANOMALIES (REVIEW NEEDED):")
        for i, issue in enumerate(suspected[:4], 1):
            print(f"  {i}. [{issue.severity.value}] {issue.title}")
            print(f"     URL: {issue.url}")
            print(f"     Observation: {issue.description}")
            print(f"     Fix: {issue.remediation}\n")

    print("=" * 80)
    print("📋 RECOMMENDED ACTIONS:")
    for rec in report.top_recommendations:
        print(f"  * {rec}")
    print("=" * 80)

    # Save to file if requested
    if output_file:
        if fmt == "html" or output_file.endswith(".html"):
            content = QAExporter.to_standalone_html(report)
        elif fmt == "json" or output_file.endswith(".json"):
            content = QAExporter.to_json(report)
        else:
            content = QAExporter.to_markdown(report)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n💾 Report successfully saved to: {output_file}")


def start_mock_server_background(port: int = 8088):
    from mock_staging.server import app as mock_fastapi_app
    config = uvicorn.Config(mock_fastapi_app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.2)  # Give time to spin up
    return server


def run_demo_flow():
    print_banner()
    print("📦 Launching built-in Defect Staging Server on http://127.0.0.1:8088...")
    start_mock_server_background(8088)
    print("✅ Staging server ready with intentional multi-page defects.")
    print("🎯 Executing autonomous multi-page audit...\n")
    run_audit_command(
        url="http://127.0.0.1:8088",
        max_pages=5,
        max_depth=2,
        output_file="staging_qa_report.html",
        fmt="html"
    )
    print("\n✨ Demo complete! You can open 'staging_qa_report.html' in your browser.")


def main():
    parser = argparse.ArgumentParser(description="AI Website QA Agent - Autonomous Staging & Production Inspector")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Audit a website/staging URL")
    audit_parser.add_argument("url", type=str, help="Target website URL")
    audit_parser.add_argument("--pages", type=int, default=5, help="Max pages to crawl (default: 5)")
    audit_parser.add_argument("--depth", type=int, default=2, help="Max crawl depth (default: 2)")
    audit_parser.add_argument("--output", "-o", type=str, default="qa_report.html", help="Output report file path")
    audit_parser.add_argument("--format", "-f", choices=["html", "md", "json"], default="html", help="Report format")

    # Demo command
    subparsers.add_parser("demo", help="Spin up mock staging server and run demonstration audit")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the interactive web dashboard & API")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    serve_parser.add_argument("--mock-port", type=int, default=8088, help="Port for background mock staging site")

    # Mock server command
    mock_parser = subparsers.add_parser("mock", help="Start only the mock staging server")
    mock_parser.add_argument("--port", type=int, default=8088, help="Port for mock server (default: 8088)")

    args = parser.parse_args()

    if args.command == "audit":
        run_audit_command(args.url, args.pages, args.depth, args.output, args.format)
    elif args.command == "demo":
        run_demo_flow()
    elif args.command == "serve":
        print_banner()
        print(f"📦 Starting background mock staging server on http://127.0.0.1:{args.mock_port}...")
        start_mock_server_background(args.mock_port)
        print(f"🚀 Starting AI Website QA Dashboard on http://127.0.0.1:{args.port}")
        print("💡 Open http://127.0.0.1:8000 in your browser to interact with the UI.\n")
        uvicorn.run("web_app:app", host="127.0.0.1", port=args.port, reload=False)
    elif args.command == "mock":
        print(f"📦 Starting Mock Staging Site on http://127.0.0.1:{args.port}...")
        uvicorn.run("mock_staging.server:app", host="127.0.0.1", port=args.port, reload=False)
    else:
        run_demo_flow()


if __name__ == "__main__":
    main()
