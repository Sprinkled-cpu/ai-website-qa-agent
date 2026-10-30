import time
from datetime import datetime
from typing import List, Dict, Optional, Callable
from collections import Counter
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ai_website_qa.models import (
    QAReport, PageAudit, QAIssue, CrawlStats,
    Severity, IssueStatus, Category
)
from ai_website_qa.crawler import WebCrawler, CrawledPage
from ai_website_qa.inspectors import (
    LinkInspector, ImageInspector, ContentInspector,
    UILayoutInspector, SEOInspector
)
from ai_website_qa.ai_synthesizer import AISynthesizer


class WebsiteQAAgent:
    """
    Autonomous Website QA Agent that audits a website/staging URL,
    discovers broken links, missing images, content inconsistencies,
    UI/layout defects, and SEO problems, and generates a prioritized QA report
    with strict separation between Confirmed Defects and Suspected Anomalies.
    """

    def __init__(
        self,
        max_pages: int = 10,
        max_depth: int = 2,
        concurrency: int = 4,
        timeout: int = 10,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.timeout = timeout
        self.custom_headers = custom_headers or {}
        self.synthesizer = AISynthesizer()

    def audit(
        self,
        target_url: str,
        progress_cb: Optional[Callable[[str, float], None]] = None
    ) -> QAReport:
        start_time = datetime.utcnow()
        t0 = time.perf_counter()

        def report_progress(msg: str, pct: float):
            if progress_cb:
                progress_cb(msg, pct)

        report_progress(f"Starting inspection for {target_url}...", 0.05)

        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=1)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Automatically mount in-memory mock staging adapter when targeting port 8088
        if "127.0.0.1:8088" in target_url or "localhost:8088" in target_url:
            from mock_staging.mock_adapter import MockStagingAdapter
            mock_adapter = MockStagingAdapter()
            session.mount("http://127.0.0.1:8088", mock_adapter)
            session.mount("http://localhost:8088", mock_adapter)

        try:
            # 1. Crawl pages
            report_progress("Crawling target site...", 0.15)
            crawler = WebCrawler(
                base_url=target_url,
                max_pages=self.max_pages,
                max_depth=self.max_depth,
                concurrency=self.concurrency,
                timeout=self.timeout,
                custom_headers=self.custom_headers
            )

            def on_crawled(url: str, current: int, total: int):
                pct = 0.15 + (current / total) * 0.35
                report_progress(f"Crawled ({current}/{total}): {url}", pct)

            crawled_pages: List[CrawledPage] = crawler.crawl(session, on_page_crawled=on_crawled)

            all_crawled_urls = {p.url for p in crawled_pages}
            report_progress(f"Discovered {len(crawled_pages)} page(s). Running deep multi-inspector engine...", 0.55)

            # Initialize inspectors with shared session & caches
            link_cache: Dict[str, Dict] = {}
            img_cache: Dict[str, Dict] = {}

            link_inspector = LinkInspector(session=session, link_cache=link_cache, max_workers=self.concurrency)
            img_inspector = ImageInspector(session=session, image_cache=img_cache, max_workers=self.concurrency)
            content_inspector = ContentInspector(session=session)
            ui_inspector = UILayoutInspector(session=session)
            seo_inspector = SEOInspector(session=session)

            page_audits: List[PageAudit] = []
            all_issues: List[QAIssue] = []

            # 2. Inspect each crawled page
            for idx, p in enumerate(crawled_pages):
                pct = 0.55 + (idx + 1) / max(len(crawled_pages), 1) * 0.35
                report_progress(f"Inspecting DOM & assets for {p.url}...", pct)

                page_issues: List[QAIssue] = []
                page_issues.extend(link_inspector.inspect(p.url, p.soup, p.html, p.headers, p.status_code, all_crawled_urls))
                page_issues.extend(img_inspector.inspect(p.url, p.soup, p.html, p.headers, p.status_code, all_crawled_urls))
                page_issues.extend(content_inspector.inspect(p.url, p.soup, p.html, p.headers, p.status_code, all_crawled_urls))
                page_issues.extend(ui_inspector.inspect(p.url, p.soup, p.html, p.headers, p.status_code, all_crawled_urls))
                page_issues.extend(seo_inspector.inspect(p.url, p.soup, p.html, p.headers, p.status_code, all_crawled_urls))

                title_tag = p.soup.find("title")
                page_title = title_tag.get_text(strip=True) if title_tag else None

                audit = PageAudit(
                    url=p.url,
                    status_code=p.status_code,
                    content_type=p.content_type,
                    load_time_ms=p.load_time_ms,
                    title=page_title,
                    links_checked=len(p.soup.find_all("a")),
                    images_checked=len(p.soup.find_all("img")),
                    issues=page_issues
                )
                page_audits.append(audit)
                all_issues.extend(page_issues)

        finally:
            session.close()

        report_progress("Synthesizing prioritized QA intelligence...", 0.92)

        # 3. Sort issues by severity (P0 -> P1 -> P2 -> P3), then CONFIRMED before SUSPECTED
        severity_order = {
            Severity.P0_CRITICAL: 0,
            Severity.P1_HIGH: 1,
            Severity.P2_MEDIUM: 2,
            Severity.P3_LOW: 3
        }
        status_order = {
            IssueStatus.CONFIRMED: 0,
            IssueStatus.SUSPECTED: 1
        }

        all_issues.sort(key=lambda x: (severity_order.get(x.severity, 9), status_order.get(x.status, 9), x.category.value))

        # 4. Compute statistics
        duration = round(time.perf_counter() - t0, 2)
        end_time = datetime.utcnow()

        stats = CrawlStats(
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            pages_crawled=len(page_audits),
            pages_failed=len(crawler.failed_urls),
            total_links_inspected=link_inspector.checked_urls_count,
            total_images_inspected=img_inspector.checked_images_count
        )

        health_score = self.synthesizer.compute_health_score(all_issues)
        executive_summary, recommendations = self.synthesizer.generate_executive_summary(
            target_url=target_url,
            stats=stats,
            issues=all_issues,
            health_score=health_score
        )

        confirmed_count = sum(1 for i in all_issues if i.status == IssueStatus.CONFIRMED)
        suspected_count = sum(1 for i in all_issues if i.status == IssueStatus.SUSPECTED)

        sev_breakdown = Counter(i.severity.value for i in all_issues)
        cat_breakdown = Counter(i.category.value for i in all_issues)
        stat_breakdown = Counter(i.status.value for i in all_issues)

        report = QAReport(
            target_url=target_url,
            scan_timestamp=end_time,
            stats=stats,
            health_score=health_score,
            total_issues=len(all_issues),
            confirmed_count=confirmed_count,
            suspected_count=suspected_count,
            severity_breakdown=dict(sev_breakdown),
            category_breakdown=dict(cat_breakdown),
            status_breakdown=dict(stat_breakdown),
            executive_summary=executive_summary,
            top_recommendations=recommendations,
            pages=page_audits,
            issues=all_issues
        )

        report_progress("QA Audit completed successfully!", 1.0)
        return report
