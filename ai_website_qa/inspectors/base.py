from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import uuid
from bs4 import BeautifulSoup
from ai_website_qa.models import QAIssue, Category, Severity, IssueStatus


class BaseInspector(ABC):
    category: Category

    def __init__(self, session=None):
        self.session = session

    @abstractmethod
    def inspect(
        self,
        page_url: str,
        soup: BeautifulSoup,
        raw_html: str,
        response_headers: Dict[str, str],
        status_code: int,
        all_crawled_urls: Optional[set] = None
    ) -> List[QAIssue]:
        """Runs page-level inspection and yields a list of QAIssue objects."""
        pass

    def make_issue(
        self,
        page_url: str,
        severity: Severity,
        status: IssueStatus,
        title: str,
        description: str,
        remediation: str,
        category: Optional[Category] = None,
        element_selector: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None
    ) -> QAIssue:
        issue_id = f"ISSUE-{uuid.uuid4().hex[:8].upper()}"
        return QAIssue(
            id=issue_id,
            url=page_url,
            category=category or self.category,
            severity=severity,
            status=status,
            title=title,
            description=description,
            element_selector=element_selector,
            evidence=evidence or {},
            remediation=remediation
        )
