from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from ai_website_qa.inspectors.base import BaseInspector
from ai_website_qa.models import Category, Severity, IssueStatus, QAIssue


class SEOInspector(BaseInspector):
    category = Category.SEO_METADATA

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

        # 1. HTML lang attribute
        html_tag = soup.find("html")
        if not html_tag or not html_tag.get("lang"):
            issues.append(
                self.make_issue(
                    page_url=page_url,
                    severity=Severity.P2_MEDIUM,
                    status=IssueStatus.CONFIRMED,
                    title="Missing HTML Language Attribute (<html lang='...'>)",
                    description="The <html> element does not specify a 'lang' attribute, preventing screen readers and search engines from identifying page language.",
                    remediation="Add a valid ISO language code to the root element, e.g. <html lang='en'>."
                )
            )

        # 2. Document Title
        title_tag = soup.find("title")
        if not title_tag:
            issues.append(
                self.make_issue(
                    page_url=page_url,
                    severity=Severity.P1_HIGH,
                    status=IssueStatus.CONFIRMED,
                    title="Missing Document <title> Tag",
                    description="Page is missing a <title> tag in the <head>. This is a primary SEO ranking and browser tab indicator.",
                    remediation="Add a descriptive <title> tag inside the <head> element (recommended length: 30-60 characters)."
                )
            )
        else:
            title_text = title_tag.get_text(strip=True)
            if not title_text:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P1_HIGH,
                        status=IssueStatus.CONFIRMED,
                        title="Empty Document <title> Tag",
                        description="The <title> element exists but contains no text.",
                        remediation="Provide a concise, branded title inside <title>."
                    )
                )
            elif len(title_text) < 10 or title_text.lower() in ("home", "untitled", "index", "page", "welcome"):
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P2_MEDIUM,
                        status=IssueStatus.SUSPECTED,
                        title=f"Generic or Overly Short <title> ('{title_text}')",
                        description=f"Page title '{title_text}' is only {len(title_text)} characters and lacks descriptive keywords.",
                        remediation="Expand the title to 30-60 characters highlighting page value and brand identity.",
                        evidence={"title": title_text, "length": len(title_text)}
                    )
                )
            elif len(title_text) > 65:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P3_LOW,
                        status=IssueStatus.SUSPECTED,
                        title=f"Page <title> Exceeds Optimal Length ({len(title_text)} chars)",
                        description=f"Title is {len(title_text)} characters long and may be truncated in Google search snippets (recommended max 60-65 chars).",
                        remediation="Condense the title to keep key keywords within the initial 60 characters.",
                        evidence={"title": title_text, "length": len(title_text)}
                    )
                )

        # 3. Meta Description
        meta_desc = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "description"})
        if not meta_desc:
            issues.append(
                self.make_issue(
                    page_url=page_url,
                    severity=Severity.P2_MEDIUM,
                    status=IssueStatus.CONFIRMED,
                    title="Missing Meta Description",
                    description="No <meta name='description'> found. Search engines will generate automated snippets from page body.",
                    remediation="Add '<meta name=\"description\" content=\"...\">' with a compelling summary (120-160 characters)."
                )
            )
        else:
            desc_content = meta_desc.get("content", "").strip()
            if not desc_content:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P2_MEDIUM,
                        status=IssueStatus.CONFIRMED,
                        title="Empty Meta Description Content",
                        description="The meta description tag has an empty content attribute.",
                        remediation="Supply a meaningful summary in the content attribute."
                    )
                )
            elif len(desc_content) < 50:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P3_LOW,
                        status=IssueStatus.SUSPECTED,
                        title=f"Short Meta Description ({len(desc_content)} chars)",
                        description=f"Meta description is only {len(desc_content)} characters. Typical ideal range is 120-160 characters.",
                        remediation="Expand the description to provide more context and improve organic CTR.",
                        evidence={"content": desc_content, "length": len(desc_content)}
                    )
                )
            elif len(desc_content) > 165:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P3_LOW,
                        status=IssueStatus.SUSPECTED,
                        title=f"Lengthy Meta Description ({len(desc_content)} chars)",
                        description=f"Meta description length is {len(desc_content)} characters and will likely be truncated on SERP viewports.",
                        remediation="Shorten meta description to under 160 characters.",
                        evidence={"content": desc_content, "length": len(desc_content)}
                    )
                )

        # 4. Canonical Tag
        canonical_tags = soup.find_all("link", attrs={"rel": lambda x: x and "canonical" in x})
        if len(canonical_tags) == 0:
            issues.append(
                self.make_issue(
                    page_url=page_url,
                    severity=Severity.P2_MEDIUM,
                    status=IssueStatus.SUSPECTED,
                    title="Missing Canonical Link Tag",
                    description="No <link rel='canonical' href='...'> tag found. This can lead to duplicate content penalties.",
                    remediation=f"Specify preferred canonical URL: <link rel='canonical' href='{page_url}'>."
                )
            )
        elif len(canonical_tags) > 1:
            issues.append(
                self.make_issue(
                    page_url=page_url,
                    severity=Severity.P1_HIGH,
                    status=IssueStatus.CONFIRMED,
                    title="Multiple Canonical Tags Detected",
                    description=f"Page contains {len(canonical_tags)} conflicting canonical declarations, causing search engines to ignore them.",
                    remediation="Ensure only one canonical tag is emitted in the page <head>."
                )
            )

        # 5. Robots / Indexing directive
        meta_robots = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "robots"})
        x_robots_header = response_headers.get("x-robots-tag", "").lower()

        robots_content = (meta_robots.get("content", "") if meta_robots else "").lower()
        if "noindex" in robots_content or "noindex" in x_robots_header:
            issues.append(
                self.make_issue(
                    page_url=page_url,
                    severity=Severity.P1_HIGH,
                    status=IssueStatus.CONFIRMED,
                    title="Page Has 'noindex' Directive Active",
                    description=f"Search engines are instructed not to index this page (robots directive: '{robots_content or x_robots_header}'). Normal on staging, but fatal on production.",
                    remediation="Confirm whether this page is intended to be excluded from search indexes before deploying to production.",
                    evidence={"meta_robots": robots_content, "x_robots": x_robots_header}
                )
            )

        # 6. OpenGraph Social Meta
        og_tags = {
            "og:title": soup.find("meta", attrs={"property": "og:title"}),
            "og:image": soup.find("meta", attrs={"property": "og:image"}),
            "og:description": soup.find("meta", attrs={"property": "og:description"}),
        }
        missing_og = [k for k, v in og_tags.items() if not v or not v.get("content")]
        if missing_og:
            issues.append(
                self.make_issue(
                    page_url=page_url,
                    severity=Severity.P3_LOW,
                    status=IssueStatus.SUSPECTED,
                    title=f"Missing OpenGraph Social Meta Tags ({', '.join(missing_og)})",
                    description=f"Missing Open Graph tags ({', '.join(missing_og)}) will cause broken card previews when shared on Slack, Twitter/X, or LinkedIn.",
                    remediation=f"Add missing OpenGraph meta tags in <head>: {', '.join(missing_og)}.",
                    evidence={"missing_tags": missing_og}
                )
            )

        return issues
