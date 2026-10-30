from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class IssueStatus(str, Enum):
    CONFIRMED = "CONFIRMED"  # Definite, verified defect (e.g., HTTP 404, missing title, empty button, raw placeholder)
    SUSPECTED = "SUSPECTED"  # Potential anomaly needing human/contextual review (e.g., heuristic match, length warning)


class Severity(str, Enum):
    P0_CRITICAL = "P0_CRITICAL"  # Blocker / severely degraded user experience or indexing
    P1_HIGH = "P1_HIGH"          # Significant defect (broken visual asset, dead main link, missing core metadata)
    P2_MEDIUM = "P2_MEDIUM"      # Moderate quality defect (missing alt tag, duplicate heading, content inconsistency)
    P3_LOW = "P3_LOW"            # Polish / minor optimization (length advisory, missing social preview tag)


class Category(str, Enum):
    BROKEN_LINKS = "BROKEN_LINKS"
    MISSING_IMAGES = "MISSING_IMAGES"
    CONTENT_CONSISTENCY = "CONTENT_CONSISTENCY"
    UI_LAYOUT = "UI_LAYOUT"
    SEO_METADATA = "SEO_METADATA"


class QAIssue(BaseModel):
    id: str = Field(..., description="Unique issue identifier")
    url: str = Field(..., description="URL of the page where the issue was found")
    category: Category = Field(..., description="Issue category")
    severity: Severity = Field(..., description="Severity priority (P0-P3)")
    status: IssueStatus = Field(..., description="CONFIRMED or SUSPECTED")
    title: str = Field(..., description="Concise summary of the defect")
    description: str = Field(..., description="Detailed explanation of what was observed")
    element_selector: Optional[str] = Field(None, description="CSS selector or HTML snippet of the element")
    evidence: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Diagnostic data (e.g. status code, matched text)")
    remediation: str = Field(..., description="Actionable recommendation on how to fix this issue")


class PageAudit(BaseModel):
    url: str
    status_code: int
    content_type: str
    load_time_ms: float
    title: Optional[str] = None
    links_checked: int = 0
    images_checked: int = 0
    issues: List[QAIssue] = Field(default_factory=list)


class CrawlStats(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    pages_crawled: int = 0
    pages_failed: int = 0
    total_links_inspected: int = 0
    total_images_inspected: int = 0


class QAReport(BaseModel):
    target_url: str
    scan_timestamp: datetime = Field(default_factory=datetime.utcnow)
    stats: CrawlStats
    health_score: int = Field(100, description="Overall website health score from 0 to 100")
    total_issues: int = 0
    confirmed_count: int = 0
    suspected_count: int = 0
    severity_breakdown: Dict[str, int] = Field(default_factory=dict)
    category_breakdown: Dict[str, int] = Field(default_factory=dict)
    status_breakdown: Dict[str, int] = Field(default_factory=dict)
    executive_summary: str = ""
    top_recommendations: List[str] = Field(default_factory=list)
    pages: List[PageAudit] = Field(default_factory=list)
    issues: List[QAIssue] = Field(default_factory=list)
