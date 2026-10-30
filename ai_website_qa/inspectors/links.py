import concurrent.futures
from urllib.parse import urljoin, urlparse, urldefrag
from typing import List, Dict, Any, Optional, Set
from bs4 import BeautifulSoup
import requests

from ai_website_qa.inspectors.base import BaseInspector
from ai_website_qa.models import Category, Severity, IssueStatus, QAIssue


class LinkInspector(BaseInspector):
    category = Category.BROKEN_LINKS

    def __init__(self, session: Optional[requests.Session] = None, link_cache: Optional[Dict[str, Dict[str, Any]]] = None, max_workers: int = 4):
        super().__init__(session)
        self.link_cache = link_cache if link_cache is not None else {}
        self.checked_urls_count = 0
        self.max_workers = max_workers

    def _check_target_url(self, target_url: str) -> Dict[str, Any]:
        """Checks the HTTP status of a target link with caching and fallbacks."""
        if target_url in self.link_cache:
            return self.link_cache[target_url]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Website-QA-Agent/1.0"
        }

        sess = self.session or requests.Session()
        try:
            # First try HEAD request for speed
            resp = sess.head(target_url, headers=headers, allow_redirects=True, timeout=6)
            status = resp.status_code
            if status in (405, 403, 400):
                resp = sess.get(target_url, headers=headers, allow_redirects=True, timeout=6, stream=True)
                res = {"status": resp.status_code, "reason": resp.reason, "error": None}
                resp.close()
            else:
                res = {"status": status, "reason": resp.reason, "error": None}
        except requests.exceptions.Timeout:
            res = {"status": None, "reason": "Timeout", "error": "Connection timed out after 6 seconds"}
        except requests.exceptions.ConnectionError as e:
            res = {"status": None, "reason": "Connection Error", "error": f"Failed to connect: {str(e)}"}
        except Exception as e:
            res = {"status": None, "reason": "Error", "error": str(e)}

        self.link_cache[target_url] = res
        return res

    def inspect(
        self,
        page_url: str,
        soup: BeautifulSoup,
        raw_html: str,
        response_headers: Dict[str, str],
        status_code: int,
        all_crawled_urls: Optional[set] = None
    ) -> List[QAIssue]:
        issues: List[QAIssue] = []
        parsed_page = urlparse(page_url)
        page_domain = parsed_page.netloc

        anchors = soup.find_all("a")
        self.checked_urls_count += len(anchors)

        # Collect page IDs and name attributes for anchor checking
        page_ids: Set[str] = set()
        for el in soup.find_all(True):
            if el.has_attr("id") and el["id"]:
                page_ids.add(el["id"])
            if el.name == "a" and el.has_attr("name") and el["name"]:
                page_ids.add(el["name"])

        # Gather links to test
        links_to_test = []

        for idx, a in enumerate(anchors):
            href = a.get("href")
            anchor_text = a.get_text(strip=True) or "(empty text)"
            str_repr = str(a)[:120]

            # Check 1: Missing href attribute
            if href is None:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P2_MEDIUM,
                        status=IssueStatus.CONFIRMED,
                        title="Anchor tag missing 'href' attribute",
                        description=f"Found <a> element without an 'href' attribute. Text: '{anchor_text}'",
                        remediation="Add a valid destination URL to the 'href' attribute or convert to a <button> if this is an interactive action.",
                        element_selector=str_repr,
                        evidence={"anchor_text": anchor_text}
                    )
                )
                continue

            stripped_href = href.strip()

            if stripped_href == "":
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P2_MEDIUM,
                        status=IssueStatus.CONFIRMED,
                        title="Empty link destination (href='')",
                        description=f"Anchor element has an empty href attribute. Text: '{anchor_text}'",
                        remediation="Provide a valid target URL or anchor identifier instead of an empty href.",
                        element_selector=str_repr,
                        evidence={"anchor_text": anchor_text}
                    )
                )
                continue

            # Check 2: Placeholder links (href="#" or href="javascript:void(0)")
            if stripped_href in ("#", "javascript:void(0)", "javascript:;", "javascript:void(0);"):
                has_js = a.has_attr("onclick") or a.has_attr("@click") or a.has_attr("v-on:click")
                if not has_js:
                    issues.append(
                        self.make_issue(
                            page_url=page_url,
                            severity=Severity.P3_LOW,
                            status=IssueStatus.SUSPECTED,
                            title="Placeholder / Dummy Link Detected",
                            description=f"Anchor has dummy href '{stripped_href}' with no evident JS click listener. Text: '{anchor_text}'",
                            remediation="Replace placeholder href with the actual target route, or use a styled <button type='button'> for scripted actions.",
                            element_selector=str_repr,
                            evidence={"href": stripped_href, "anchor_text": anchor_text}
                        )
                    )
                continue

            # Check 3: Internal page fragment anchors (#section)
            if stripped_href.startswith("#"):
                fragment = stripped_href[1:]
                if fragment and fragment not in page_ids:
                    issues.append(
                        self.make_issue(
                            page_url=page_url,
                            severity=Severity.P2_MEDIUM,
                            status=IssueStatus.CONFIRMED,
                            title="Broken in-page anchor hash",
                            description=f"Link points to internal anchor '{stripped_href}', but no element with id='{fragment}' exists on this page.",
                            remediation=f"Ensure the target section has id='{fragment}' or update the link to point to an existing section.",
                            element_selector=str_repr,
                            evidence={"fragment": fragment, "anchor_text": anchor_text}
                        )
                    )
                continue

            # Ignore non-HTTP schemes
            if stripped_href.startswith(("mailto:", "tel:", "sms:", "data:", "javascript:")):
                continue

            # Resolve absolute URL
            try:
                full_url = urljoin(page_url, stripped_href)
                target_parsed = urlparse(full_url)
                if not target_parsed.scheme.startswith("http"):
                    continue
            except Exception:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P1_HIGH,
                        status=IssueStatus.CONFIRMED,
                        title="Malformed link URL",
                        description=f"Anchor href '{stripped_href}' is a malformed URL that cannot be resolved.",
                        remediation="Correct the link syntax to ensure it forms a valid RFC-compliant URL.",
                        element_selector=str_repr,
                        evidence={"raw_href": stripped_href}
                    )
                )
                continue

            # Clean URL (strip fragment for HTTP status checking)
            clean_url, fragment = urldefrag(full_url)
            links_to_test.append((a, clean_url, stripped_href, anchor_text, fragment))

        # Test links with threadpool if session is active
        if self.session and links_to_test:
            unique_urls = list({item[1] for item in links_to_test})
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, len(unique_urls) or 1)) as executor:
                res_list = list(executor.map(self._check_target_url, unique_urls))
            res_map = dict(zip(unique_urls, res_list))

            for a, clean_url, raw_href, anchor_text, fragment in links_to_test:
                res = res_map.get(clean_url)
                if not res or isinstance(res, Exception):
                    continue

                status = res.get("status")
                error = res.get("error")
                str_repr = str(a)[:120]
                is_internal = urlparse(clean_url).netloc == page_domain

                # Confirmed Broken Link: 404 Not Found, 410 Gone
                if status in (404, 410):
                    issues.append(
                        self.make_issue(
                            page_url=page_url,
                            severity=Severity.P0_CRITICAL if is_internal else Severity.P1_HIGH,
                            status=IssueStatus.CONFIRMED,
                            title=f"Broken Link (HTTP {status})",
                            description=f"Link to '{clean_url}' returned HTTP {status} ({res.get('reason')}). Anchor text: '{anchor_text}'",
                            remediation=f"Update link href from '{raw_href}' to an active endpoint, or remove the link if obsolete.",
                            element_selector=str_repr,
                            evidence={"target_url": clean_url, "status_code": status, "is_internal": is_internal, "anchor_text": anchor_text}
                        )
                    )
                elif status and status >= 500:
                    issues.append(
                        self.make_issue(
                            page_url=page_url,
                            severity=Severity.P0_CRITICAL if is_internal else Severity.P1_HIGH,
                            status=IssueStatus.CONFIRMED,
                            title=f"Server Error on Target Link (HTTP {status})",
                            description=f"Destination '{clean_url}' failed with server error HTTP {status}.",
                            remediation="Inspect destination server logs or correct endpoint route.",
                            element_selector=str_repr,
                            evidence={"target_url": clean_url, "status_code": status, "is_internal": is_internal}
                        )
                    )
                elif error:
                    if "timed out" in error.lower():
                        issues.append(
                            self.make_issue(
                                page_url=page_url,
                                severity=Severity.P3_LOW,
                                status=IssueStatus.SUSPECTED,
                                title="Target Link Connection Timeout",
                                description=f"Connection to '{clean_url}' timed out after 6s. It may be temporarily down or slow.",
                                remediation="Verify target server responsiveness or network firewall settings.",
                                element_selector=str_repr,
                                evidence={"target_url": clean_url, "error": error}
                            )
                        )
                    else:
                        issues.append(
                            self.make_issue(
                                page_url=page_url,
                                severity=Severity.P1_HIGH,
                                status=IssueStatus.CONFIRMED,
                                title="Dead Link / Network Failure",
                                description=f"Failed to connect to destination '{clean_url}': {error}",
                                remediation="Verify domain registration, DNS records, and host accessibility.",
                                element_selector=str_repr,
                                evidence={"target_url": clean_url, "error": error}
                            )
                        )
                elif status in (401, 403, 429):
                    issues.append(
                        self.make_issue(
                            page_url=page_url,
                            severity=Severity.P2_MEDIUM,
                            status=IssueStatus.SUSPECTED,
                            title=f"Access Restricted (HTTP {status})",
                            description=f"Destination '{clean_url}' responded with HTTP {status}. This may indicate authorization required or anti-bot challenge.",
                            remediation="Confirm if authentication or special staging headers are required to view this resource.",
                            element_selector=str_repr,
                            evidence={"target_url": clean_url, "status_code": status}
                        )
                    )

        return issues
