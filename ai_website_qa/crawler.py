import time
import concurrent.futures
from urllib.parse import urlparse, urljoin, urldefrag
from typing import Set, List, Dict, Optional, Callable
from bs4 import BeautifulSoup
import requests


class CrawledPage:
    def __init__(self, url: str, status_code: int, content_type: str, html: str, soup: BeautifulSoup, load_time_ms: float, headers: Dict[str, str]):
        self.url = url
        self.status_code = status_code
        self.content_type = content_type
        self.html = html
        self.soup = soup
        self.load_time_ms = load_time_ms
        self.headers = headers


class WebCrawler:
    def __init__(
        self,
        base_url: str,
        max_pages: int = 10,
        max_depth: int = 2,
        concurrency: int = 4,
        timeout: int = 10,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        self.parsed_base = urlparse(base_url)
        path = self.parsed_base.path or "/"
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        self.base_url = f"{self.parsed_base.scheme}://{self.parsed_base.netloc}{path}"
        self.base_domain = self.parsed_base.netloc
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.timeout = timeout
        self.custom_headers = custom_headers or {}

        self.visited_urls: Set[str] = set()
        self.crawled_pages: List[CrawledPage] = []
        self.failed_urls: Dict[str, str] = {}

    def _normalize_url(self, raw_url: str, current_page_url: str) -> Optional[str]:
        if not raw_url:
            return None

        stripped = raw_url.strip()
        if stripped.startswith(("#", "javascript:", "mailto:", "tel:", "sms:", "data:")):
            return None

        try:
            full_url = urljoin(current_page_url, stripped)
            clean_url, _ = urldefrag(full_url)
            parsed = urlparse(clean_url)

            # Restrict to HTTP/HTTPS
            if parsed.scheme not in ("http", "https"):
                return None

            # Enforce same domain or subdomain
            if parsed.netloc != self.base_domain and not parsed.netloc.endswith(f".{self.base_domain}"):
                return None

            # Normalize path: strip trailing slash for consistency (unless root domain)
            path = parsed.path
            if path and path != "/" and path.endswith("/"):
                path = path.rstrip("/")
            elif not path:
                path = "/"
            
            clean_url = f"{parsed.scheme}://{parsed.netloc}{path}"
            if parsed.query:
                clean_url += f"?{parsed.query}"

            # Avoid binary asset file extensions
            disallowed_ext = (
                ".pdf", ".zip", ".tar", ".gz", ".rar", ".7z", ".exe", ".dmg",
                ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
                ".mp4", ".mov", ".avi", ".mp3", ".wav", ".css", ".js", ".json"
            )
            if any(parsed.path.lower().endswith(ext) for ext in disallowed_ext):
                return None

            return clean_url
        except Exception:
            return None

    def _fetch_page(self, session: requests.Session, url: str, depth: int):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Website-QA-Agent/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            **self.custom_headers
        }

        start_time = time.perf_counter()
        try:
            resp = session.get(url, headers=headers, allow_redirects=True, timeout=self.timeout)
            status = resp.status_code
            content_type = resp.headers.get("Content-Type", "")
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            resp_headers = dict(resp.headers)

            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return None, []

            raw_html = resp.text
            soup = BeautifulSoup(raw_html, "html.parser")

            crawled = CrawledPage(
                url=url,
                status_code=status,
                content_type=content_type,
                html=raw_html,
                soup=soup,
                load_time_ms=elapsed_ms,
                headers=resp_headers
            )

            outgoing: List[str] = []
            if depth < self.max_depth:
                for a in soup.find_all("a", href=True):
                    norm = self._normalize_url(a["href"], url)
                    if norm and norm not in self.visited_urls:
                        outgoing.append(norm)

            return crawled, outgoing
        except Exception as e:
            self.failed_urls[url] = str(e)
            return None, []

    def crawl(
        self,
        session: requests.Session,
        on_page_crawled: Optional[Callable[[str, int, int], None]] = None
    ) -> List[CrawledPage]:
        queue: List[tuple[str, int]] = [(self.base_url, 0)]
        self.visited_urls.add(self.base_url)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            while queue and len(self.crawled_pages) < self.max_pages:
                current_batch = []
                while queue and (len(self.crawled_pages) + len(current_batch)) < self.max_pages:
                    current_batch.append(queue.pop(0))

                if not current_batch:
                    break

                futures = [executor.submit(self._fetch_page, session, u, d) for u, d in current_batch]
                for fut in concurrent.futures.as_completed(futures):
                    crawled, outgoing = fut.result()
                    if crawled:
                        self.crawled_pages.append(crawled)
                        if on_page_crawled:
                            on_page_crawled(crawled.url, len(self.crawled_pages), self.max_pages)

                    for next_url in outgoing:
                        if next_url not in self.visited_urls and len(self.visited_urls) < self.max_pages * 2:
                            self.visited_urls.add(next_url)
                            queue.append((next_url, 1))

        return self.crawled_pages
