import os
from typing import List, Dict, Tuple
from collections import Counter
from ai_website_qa.models import QAIssue, Severity, IssueStatus, Category, CrawlStats


class AISynthesizer:
    """
    Intelligent synthesis engine that analyzes all inspection findings,
    computes an objective Health Score, isolates Confirmed vs. Suspected defects,
    and drafts an executive summary and prioritized remediation roadmap.
    """

    def compute_health_score(self, issues: List[QAIssue]) -> int:
        score = 100
        for issue in issues:
            if issue.severity == Severity.P0_CRITICAL:
                score -= 20 if issue.status == IssueStatus.CONFIRMED else 10
            elif issue.severity == Severity.P1_HIGH:
                score -= 8 if issue.status == IssueStatus.CONFIRMED else 4
            elif issue.severity == Severity.P2_MEDIUM:
                score -= 3 if issue.status == IssueStatus.CONFIRMED else 1.5
            elif issue.severity == Severity.P3_LOW:
                score -= 1 if issue.status == IssueStatus.CONFIRMED else 0.5
        return max(0, min(100, int(round(score))))

    def generate_executive_summary(
        self,
        target_url: str,
        stats: CrawlStats,
        issues: List[QAIssue],
        health_score: int
    ) -> Tuple[str, List[str]]:
        confirmed_issues = [i for i in issues if i.status == IssueStatus.CONFIRMED]
        suspected_issues = [i for i in issues if i.status == IssueStatus.SUSPECTED]

        crit_count = sum(1 for i in issues if i.severity == Severity.P0_CRITICAL)
        high_count = sum(1 for i in issues if i.severity == Severity.P1_HIGH)
        med_count = sum(1 for i in issues if i.severity == Severity.P2_MEDIUM)
        low_count = sum(1 for i in issues if i.severity == Severity.P3_LOW)

        cat_counts = Counter(i.category.value for i in issues)

        # Health tier description
        if health_score >= 90:
            health_desc = "EXCELLENT. The target exhibits high technical quality with only minor polish recommendations."
        elif health_score >= 75:
            health_desc = "GOOD, with moderate defects identified that should be resolved prior to release."
        elif health_score >= 50:
            health_desc = "NEEDS ATTENTION. Noticeable functional, visual, or SEO regressions require remediation."
        else:
            health_desc = "CRITICAL RISK. High density of blocking defects, broken paths, or missing core metadata."

        summary_paragraphs = [
            f"### Executive QA Summary for {target_url}\n",
            f"**Overall Health Score: {health_score}/100** — {health_desc}\n",
            f"The QA Agent audited **{stats.pages_crawled} page(s)** in {stats.duration_seconds:.2f}s, evaluating **{stats.total_links_inspected} links** and **{stats.total_images_inspected} images/assets**.",
            f"\n#### Findings Overview:",
            f"- **Confirmed Defects:** {len(confirmed_issues)} verified issues requiring immediate engineering or editorial correction.",
            f"- **Suspected Anomalies:** {len(suspected_issues)} contextual or heuristic issues recommended for manual verification.",
            f"- **Severity Distribution:** {crit_count} Critical (P0), {high_count} High (P1), {med_count} Medium (P2), and {low_count} Low (P3).",
        ]

        # Top recommendations logic
        recommendations: List[str] = []

        if crit_count > 0:
            p0_titles = [i.title for i in confirmed_issues if i.severity == Severity.P0_CRITICAL][:3]
            recommendations.append(f"🚨 **Blocker Resolution (P0):** Fix critical path blockers: {', '.join(p0_titles)}.")

        if cat_counts.get(Category.BROKEN_LINKS.value, 0) > 0:
            dead_links = [i for i in confirmed_issues if i.category == Category.BROKEN_LINKS]
            if dead_links:
                recommendations.append(f"🔗 **Fix Dead Links ({len(dead_links)} confirmed):** Update or remove broken URLs returning HTTP 404/500 errors to maintain navigation integrity.")

        if cat_counts.get(Category.MISSING_IMAGES.value, 0) > 0:
            missing_imgs = [i for i in confirmed_issues if i.category == Category.MISSING_IMAGES]
            if missing_imgs:
                recommendations.append(f"🖼️ **Fix Missing Visuals ({len(missing_imgs)} confirmed):** Restore 404 image assets and ensure all <img> tags have valid src and accessible alt attributes.")

        if cat_counts.get(Category.CONTENT_CONSISTENCY.value, 0) > 0:
            content_issues = [i for i in confirmed_issues if i.category == Category.CONTENT_CONSISTENCY]
            if content_issues:
                recommendations.append(f"✍️ **Content Sanitization:** Purge draft placeholder text (Lorem Ipsum, TODOs, raw template tags) and fix character encoding glitches before public release.")

        if cat_counts.get(Category.UI_LAYOUT.value, 0) > 0:
            ui_issues = [i for i in confirmed_issues if i.category == Category.UI_LAYOUT]
            if ui_issues:
                recommendations.append(f"🎨 **UI & Accessibility Fixes:** Supply missing button text/labels, correct heading hierarchy, and verify mobile viewport responsiveness.")

        if cat_counts.get(Category.SEO_METADATA.value, 0) > 0:
            seo_issues = [i for i in issues if i.category == Category.SEO_METADATA]
            if seo_issues:
                recommendations.append(f"🔍 **SEO & Indexability:** Populate missing <title> and meta descriptions, verify canonical tags, and check robots directives.")

        if not recommendations:
            recommendations.append("✅ No critical defects identified. The staging environment passed all automated QA checks.")

        return "\n".join(summary_paragraphs), recommendations
