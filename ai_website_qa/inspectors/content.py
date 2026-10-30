import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Comment

from ai_website_qa.inspectors.base import BaseInspector
from ai_website_qa.models import Category, Severity, IssueStatus, QAIssue


class ContentInspector(BaseInspector):
    category = Category.CONTENT_CONSISTENCY

    # Common Lorem Ipsum markers
    LOREM_PATTERNS = [
        re.compile(r"\blorem\s+ipsum\b", re.IGNORECASE),
        re.compile(r"\bconsectetur\s+adipiscing\s+elit\b", re.IGNORECASE),
        re.compile(r"\bsed\s+do\s+eiusmod\s+tempor\b", re.IGNORECASE),
        re.compile(r"\bdolor\s+sit\s+amet\b", re.IGNORECASE),
        re.compile(r"\bduis\s+aute\s+irure\b", re.IGNORECASE),
    ]

    # Explicit developer placeholders
    PLACEHOLDER_PATTERNS = [
        (re.compile(r"\bTODO[:\s]", re.IGNORECASE), "Unfinished 'TODO' tag in page text"),
        (re.compile(r"\bFIXME[:\s]", re.IGNORECASE), "Developer 'FIXME' annotation in page text"),
        (re.compile(r"\bREPLACE[_\s]ME\b", re.IGNORECASE), "Unreplaced placeholder 'REPLACE ME' token"),
        (re.compile(r"\bINSERT[_\s][A-Z_]+[_\s]HERE\b", re.IGNORECASE), "Template insertion placeholder"),
        (re.compile(r"\bTBD\b"), "'TBD' placeholder marker in visible content"),
        (re.compile(r"\bSAMPLE[_\s]TEXT\b", re.IGNORECASE), "Generic 'Sample Text' marker"),
        (re.compile(r"\bCOMING\s+SOON\s*\(PLACEHOLDER\)", re.IGNORECASE), "Placeholder banner detected"),
    ]

    # Template token leaks
    TEMPLATE_LEAK_PATTERNS = [
        (re.compile(r"\{\{\s*[\w\.\_\|\-]+\s*\}\}"), "Un-rendered template variable (e.g., {{ variable }})"),
        (re.compile(r"\{%\s*[\w\.\_\|\-\s]+\s*%\}"), "Un-rendered template block tag (e.g., {% tag %})"),
        (re.compile(r"\bundefined\b"), "Literal 'undefined' string rendered in content"),
        (re.compile(r"\[object\s+Object\]", re.IGNORECASE), "Raw JavaScript string coercion '[object Object]' displayed"),
        (re.compile(r"\bNaN\b"), "Literal 'NaN' calculation error rendered in text"),
    ]

    # Mojibake & Encoding corruption patterns
    MOJIBAKE_PATTERNS = [
        re.compile(r"[Ãâ][\x80-\xbf]{1,2}"),  # UTF-8 decoded as Latin-1
        re.compile(r"\ufffd"),               # Unicode Replacement Character
        re.compile(r"&amp;amp;"),             # Double escaped HTML entity
        re.compile(r"&amp;[a-zA-Z]+;"),      # Escaped entity
    ]

    # Repeated words (e.g. "the the")
    REPEATED_WORDS = re.compile(r"\b([a-zA-Z]{3,})\s+\1\b", re.IGNORECASE)

    # Dummy contact data
    DUMMY_CONTACT = [
        (re.compile(r"\b[A-Za-z0-9._%+-]+@example\.(?:com|org|net)\b", re.IGNORECASE), "Dummy example email address"),
        (re.compile(r"\b(?:555|123)[-\s]?(?:01[0-9]{2}|456[-\s]?7890)\b"), "Likely placeholder phone number (555-xxxx or 123-456-7890)"),
        (re.compile(r"\b123\s+(?:Fake|Main|Sample)\s+St(?:reet)?\b", re.IGNORECASE), "Placeholder street address"),
    ]

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

        # Extract visible text elements while skipping scripts and styles
        for element in soup(["script", "style", "noscript", "svg"]):
            element.decompose()

        body = soup.find("body")
        if not body:
            return issues

        # Collect text nodes with their parent elements
        visible_text = body.get_text(separator=" ", strip=True)

        # 1. Lorem Ipsum Check
        for pattern in self.LOREM_PATTERNS:
            match = pattern.search(visible_text)
            if match:
                # Find matching element snippet
                matching_tag = body.find(string=pattern)
                snippet = str(matching_tag.parent)[:150] if matching_tag and matching_tag.parent else match.group(0)
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P1_HIGH,
                        status=IssueStatus.CONFIRMED,
                        title="Lorem Ipsum Placeholder Content Detected",
                        description=f"Found unreplaced Lorem Ipsum dummy text: '{match.group(0)}'. This indicates incomplete draft copy.",
                        remediation="Replace all dummy Latin placeholder copy with finalized product/marketing content.",
                        element_selector=snippet,
                        evidence={"match": match.group(0)}
                    )
                )
                break  # Don't flood with multiple lorem patterns on same page

        # 2. Template Leak Checks
        for pat, desc in self.TEMPLATE_LEAK_PATTERNS:
            match = pat.search(visible_text)
            if match:
                matching_tag = body.find(string=pat)
                snippet = str(matching_tag.parent)[:150] if matching_tag and matching_tag.parent else match.group(0)
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P0_CRITICAL if "{" in match.group(0) else Severity.P1_HIGH,
                        status=IssueStatus.CONFIRMED,
                        title=f"Un-rendered Template / Script Leak: '{match.group(0)}'",
                        description=f"{desc}. Found occurrence: '{match.group(0)}'.",
                        remediation="Ensure server-side rendering or frontend framework populates this variable before rendering DOM.",
                        element_selector=snippet,
                        evidence={"leak": match.group(0)}
                    )
                )

        # 3. Developer Placeholder Markers
        for pat, desc in self.PLACEHOLDER_PATTERNS:
            matches = pat.findall(visible_text)
            if matches:
                matching_tag = body.find(string=pat)
                snippet = str(matching_tag.parent)[:150] if matching_tag and matching_tag.parent else matches[0]
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P1_HIGH,
                        status=IssueStatus.CONFIRMED,
                        title=f"Developer Placeholder Present: '{matches[0]}'",
                        description=f"{desc} was found in the visible page copy.",
                        remediation="Review and complete the unfinished content section.",
                        element_selector=snippet,
                        evidence={"token": matches[0]}
                    )
                )

        # 4. Mojibake / Character Encoding Quirks
        for pat in self.MOJIBAKE_PATTERNS:
            match = pat.search(visible_text)
            if match:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P2_MEDIUM,
                        status=IssueStatus.CONFIRMED,
                        title="Corrupted Character Encoding / Mojibake Detected",
                        description=f"Found garbled character sequence '{match.group(0)}', commonly caused by UTF-8 characters decoded in Windows-1252 or double-escaped entities.",
                        remediation="Verify charset declaration (<meta charset='utf-8'>) and ensure source files and database connections use UTF-8 encoding.",
                        element_selector=match.group(0),
                        evidence={"corrupted_chars": match.group(0)}
                    )
                )
                break

        # 5. Outdated Copyright Year Check
        current_year = datetime.now().year
        copyright_match = re.search(r"(?:©|&copy;|copyright)\s*(?:20\d{2}\s*[-–]\s*)?(20\d{2})", visible_text, re.IGNORECASE)
        if copyright_match:
            stated_year = int(copyright_match.group(1))
            if stated_year < current_year:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P3_LOW,
                        status=IssueStatus.SUSPECTED,
                        title=f"Outdated Copyright Year ({stated_year} vs {current_year})",
                        description=f"Copyright notice displays '{copyright_match.group(0)}', which does not reflect current year {current_year}.",
                        remediation=f"Update copyright year to {current_year} or use a dynamic year snippet (e.g. new Date().getFullYear()).",
                        evidence={"stated_year": stated_year, "current_year": current_year}
                    )
                )

        # 6. Repeated Words
        rep_match = self.REPEATED_WORDS.search(visible_text)
        if rep_match:
            word = rep_match.group(1)
            # Filter common intentional repetitions like "that that" or "bye bye"
            if word.lower() not in ("that", "bye", "ha", "very"):
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P3_LOW,
                        status=IssueStatus.SUSPECTED,
                        title=f"Accidental Repeated Word: '{word} {word}'",
                        description=f"Detected duplicated consecutive word '{word} {word}' in page copy.",
                        remediation=f"Check copywriting and remove duplicate instance of '{word}'.",
                        evidence={"repeated_word": word}
                    )
                )

        # 7. Dummy Contact Info Check
        for pat, desc in self.DUMMY_CONTACT:
            match = pat.search(visible_text)
            if match:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P2_MEDIUM,
                        status=IssueStatus.SUSPECTED,
                        title=f"Suspected Dummy Contact Data: '{match.group(0)}'",
                        description=f"{desc} was discovered in body content. Check if this staging data needs replacing before production launch.",
                        remediation="Replace test contact details with active company communication channels.",
                        evidence={"dummy_val": match.group(0)}
                    )
                )

        return issues
