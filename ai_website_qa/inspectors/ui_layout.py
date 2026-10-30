from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from ai_website_qa.inspectors.base import BaseInspector
from ai_website_qa.models import Category, Severity, IssueStatus, QAIssue


class UILayoutInspector(BaseInspector):
    category = Category.UI_LAYOUT

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

        # 1. Mobile Viewport Check
        viewport = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "viewport"})
        if not viewport:
            issues.append(
                self.make_issue(
                    page_url=page_url,
                    severity=Severity.P0_CRITICAL,
                    status=IssueStatus.CONFIRMED,
                    title="Missing Mobile Viewport Meta Tag",
                    description="No <meta name='viewport'> tag detected. Mobile devices will render the desktop viewport causing distorted layouts and zoom issues.",
                    remediation="Add '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">' inside the <head> tag."
                )
            )

        # 2. Empty Buttons and Unlabelled Interactive Controls
        buttons = soup.find_all(["button", "div", "a"])
        for btn in buttons:
            is_button = btn.name == "button" or btn.get("role") == "button" or "btn" in " ".join(btn.get("class", []))
            if not is_button:
                continue

            btn_text = btn.get_text(strip=True)
            has_aria = bool(btn.get("aria-label") or btn.get("aria-labelledby") or btn.get("title"))
            has_inner_img = bool(btn.find(["img", "svg", "i"]))

            if not btn_text and not has_aria and not has_inner_img:
                str_repr = str(btn)[:140]
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P1_HIGH,
                        status=IssueStatus.CONFIRMED,
                        title="Empty Button / Unlabelled Interactive Element",
                        description=f"A clickable <{btn.name}> has no visible text, no icon, and no aria-label, rendering it invisible or unusable for users and screen readers.",
                        remediation="Add visible text or an aria-label attribute (e.g. aria-label='Close dialog').",
                        element_selector=str_repr
                    )
                )

        # 3. Form Input Labeling
        inputs = soup.find_all(["input", "textarea", "select"])
        for inp in inputs:
            inp_type = inp.get("type", "text").lower()
            if inp_type in ("hidden", "submit", "button", "reset", "image"):
                continue

            inp_id = inp.get("id")
            has_aria = bool(inp.get("aria-label") or inp.get("aria-labelledby") or inp.get("title") or inp.get("placeholder"))
            has_parent_label = bool(inp.find_parent("label"))
            has_for_label = False

            if inp_id:
                has_for_label = bool(soup.find("label", attrs={"for": inp_id}))

            if not (has_parent_label or has_for_label or has_aria):
                str_repr = str(inp)[:140]
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P2_MEDIUM,
                        status=IssueStatus.CONFIRMED,
                        title=f"Form Input Missing Accessible Label ({inp.name} type='{inp_type}')",
                        description="Form field has no associated <label>, aria-label, or title attribute.",
                        remediation="Associate a <label for='...'> or provide an aria-label attribute for accessibility.",
                        element_selector=str_repr
                    )
                )

        # 4. Heading Hierarchy Validation (h1 - h6)
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        h1_tags = soup.find_all("h1")

        if len(h1_tags) == 0:
            issues.append(
                self.make_issue(
                    page_url=page_url,
                    severity=Severity.P1_HIGH,
                    status=IssueStatus.CONFIRMED,
                    title="Missing Primary Heading (<h1>)",
                    description="Page does not contain an <h1> element, which weakens page structure and document outline.",
                    remediation="Add a single descriptive <h1> representing the primary subject of the page."
                )
            )
        elif len(h1_tags) > 1:
            issues.append(
                self.make_issue(
                    page_url=page_url,
                    severity=Severity.P2_MEDIUM,
                    status=IssueStatus.SUSPECTED,
                    title=f"Multiple Primary Headings Detected ({len(h1_tags)} <h1> tags)",
                    description="Found multiple <h1> tags on a single page. While valid in HTML5 sections, best practice recommends a single main page <h1>.",
                    remediation="Reserve <h1> for the main page title and structure sub-sections using <h2> through <h6>.",
                    evidence={"count": len(h1_tags)}
                )
            )

        # Check for empty headings & skipped heading levels
        last_level = 0
        for h in headings:
            text = h.get_text(strip=True)
            level = int(h.name[1])

            if not text and not h.find(["img", "svg"]):
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P2_MEDIUM,
                        status=IssueStatus.CONFIRMED,
                        title=f"Empty Heading Tag (<{h.name}>)",
                        description=f"Encountered an empty <{h.name}> element with no inner text.",
                        remediation=f"Remove the empty <{h.name}> tag or add descriptive text.",
                        element_selector=str(h)[:120]
                    )
                )

            # Check for skipped heading level (e.g. h1 directly followed by h4)
            if last_level > 0 and level > last_level + 1:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P3_LOW,
                        status=IssueStatus.SUSPECTED,
                        title=f"Skipped Heading Hierarchy Level (h{last_level} to h{level})",
                        description=f"Heading order skipped a level from <h{last_level}> directly to <h{level}> ('{text[:40]}').",
                        remediation="Maintain a sequential heading hierarchy without skipping intermediate levels.",
                        element_selector=str(h)[:120],
                        evidence={"from_level": last_level, "to_level": level}
                    )
                )
            last_level = level

        return issues
