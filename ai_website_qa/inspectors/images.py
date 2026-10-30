import concurrent.futures
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import requests

from ai_website_qa.inspectors.base import BaseInspector
from ai_website_qa.models import Category, Severity, IssueStatus, QAIssue


class ImageInspector(BaseInspector):
    category = Category.MISSING_IMAGES

    def __init__(self, session: Optional[requests.Session] = None, image_cache: Optional[Dict[str, Dict[str, Any]]] = None, max_workers: int = 4):
        super().__init__(session)
        self.image_cache = image_cache if image_cache is not None else {}
        self.checked_images_count = 0
        self.max_workers = max_workers

    def _check_image_url(self, img_url: str) -> Dict[str, Any]:
        if img_url in self.image_cache:
            return self.image_cache[img_url]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Website-QA-Agent/1.0"
        }

        sess = self.session or requests.Session()
        try:
            resp = sess.get(img_url, headers=headers, timeout=6, stream=True)
            content_length = resp.headers.get("Content-Length")
            content_type = resp.headers.get("Content-Type", "")
            status = resp.status_code

            size_bytes = int(content_length) if (content_length and content_length.isdigit()) else None
            resp.close()
            res = {
                "status": status,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "error": None
            }
        except requests.exceptions.Timeout:
            res = {"status": None, "content_type": "", "size_bytes": None, "error": "Timeout"}
        except requests.exceptions.ConnectionError as e:
            res = {"status": None, "content_type": "", "size_bytes": None, "error": str(e)}
        except Exception as e:
            res = {"status": None, "content_type": "", "size_bytes": None, "error": str(e)}

        self.image_cache[img_url] = res
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
        imgs = soup.find_all("img")
        self.checked_images_count += len(imgs)

        images_to_test = []

        for img in imgs:
            src = img.get("src")
            str_repr = str(img)[:140]

            # Check 1: Missing or empty src
            if src is None:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P1_HIGH,
                        status=IssueStatus.CONFIRMED,
                        title="Image missing 'src' attribute",
                        description="An <img> tag was discovered with no 'src' attribute specified.",
                        remediation="Add a valid image URL to the 'src' attribute.",
                        element_selector=str_repr
                    )
                )
                continue

            stripped_src = src.strip()
            if not stripped_src:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P1_HIGH,
                        status=IssueStatus.CONFIRMED,
                        title="Empty image src (src='')",
                        description="An <img> tag has an empty 'src' attribute, causing an unnecessary redundant network fetch or broken icon.",
                        remediation="Provide the correct path or asset filename in the 'src' attribute.",
                        element_selector=str_repr
                    )
                )
                continue

            # Check 2: Alt attribute validation
            has_alt = img.has_attr("alt")
            alt_text = img.get("alt", "")

            if not has_alt:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P2_MEDIUM,
                        status=IssueStatus.CONFIRMED,
                        title="Missing 'alt' attribute on image",
                        description=f"Image '{stripped_src}' lacks an 'alt' attribute entirely (WCAG 2.1 Success Criterion 1.1.1 defect).",
                        remediation="Add a descriptive alt attribute (e.g., alt='Company logo') or alt='' if purely decorative.",
                        element_selector=str_repr,
                        evidence={"src": stripped_src}
                    )
                )
            else:
                lower_alt = alt_text.lower().strip()
                suspicious_alts = ["image", "picture", "photo", "img", "untitled", "icon", "placeholder"]
                if lower_alt in suspicious_alts or lower_alt.endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
                    issues.append(
                        self.make_issue(
                            page_url=page_url,
                            severity=Severity.P3_LOW,
                            status=IssueStatus.SUSPECTED,
                            title="Low-quality or filename alt text",
                            description=f"Image alt text '{alt_text}' appears to be a generic placeholder or filename rather than meaningful description.",
                            remediation="Provide a concise, contextual description of what the image depicts.",
                            element_selector=str_repr,
                            evidence={"src": stripped_src, "alt": alt_text}
                        )
                    )

            # Check 3: Layout shift (CLS) attributes (width & height)
            has_width = img.has_attr("width")
            has_height = img.has_attr("height")
            has_style = img.has_attr("style") and ("aspect-ratio" in img["style"] or ("width" in img["style"] and "height" in img["style"]))

            if not (has_width and has_height) and not has_style and not stripped_src.startswith("data:"):
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P3_LOW,
                        status=IssueStatus.SUSPECTED,
                        title="Missing explicit image dimensions (CLS risk)",
                        description=f"Image '{stripped_src}' lacks explicit 'width' and 'height' attributes, which may cause Cumulative Layout Shift (CLS).",
                        remediation="Set explicit width and height attributes or CSS aspect-ratio to reserve layout space while loading.",
                        element_selector=str_repr,
                        evidence={"src": stripped_src}
                    )
                )

            # Ignore data URIs for network fetch
            if stripped_src.startswith("data:"):
                continue

            try:
                full_img_url = urljoin(page_url, stripped_src)
                if urlparse(full_img_url).scheme.startswith("http"):
                    images_to_test.append((img, full_img_url, stripped_src))
            except Exception:
                issues.append(
                    self.make_issue(
                        page_url=page_url,
                        severity=Severity.P1_HIGH,
                        status=IssueStatus.CONFIRMED,
                        title="Malformed image URL",
                        description=f"Image src '{stripped_src}' cannot be parsed into a valid URL.",
                        remediation="Correct the image path formatting.",
                        element_selector=str_repr
                    )
                )

        # Threadpool verification of image URLs
        if self.session and images_to_test:
            unique_urls = list({item[1] for item in images_to_test})
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, len(unique_urls) or 1)) as executor:
                res_list = list(executor.map(self._check_image_url, unique_urls))
            res_map = dict(zip(unique_urls, res_list))

            for img, full_img_url, raw_src in images_to_test:
                res = res_map.get(full_img_url)
                if not res or isinstance(res, Exception):
                    continue

                status = res.get("status")
                size_bytes = res.get("size_bytes")
                str_repr = str(img)[:140]

                if status in (404, 410):
                    issues.append(
                        self.make_issue(
                            page_url=page_url,
                            severity=Severity.P1_HIGH,
                            status=IssueStatus.CONFIRMED,
                            title="Broken / Missing Image (HTTP 404)",
                            description=f"Image '{raw_src}' returned HTTP 404 Not Found at '{full_img_url}'.",
                            remediation="Verify the image file exists in the static asset directory or update the src route.",
                            element_selector=str_repr,
                            evidence={"img_url": full_img_url, "status_code": 404}
                        )
                    )
                elif status and status >= 500:
                    issues.append(
                        self.make_issue(
                            page_url=page_url,
                            severity=Severity.P1_HIGH,
                            status=IssueStatus.CONFIRMED,
                            title=f"Server Error Loading Image (HTTP {status})",
                            description=f"Asset server returned HTTP {status} when requesting image '{full_img_url}'.",
                            remediation="Check the CDN or media storage service logs.",
                            element_selector=str_repr,
                            evidence={"img_url": full_img_url, "status_code": status}
                        )
                    )
                elif size_bytes is not None and size_bytes == 0:
                    issues.append(
                        self.make_issue(
                            page_url=page_url,
                            severity=Severity.P1_HIGH,
                            status=IssueStatus.CONFIRMED,
                            title="Empty Image File (0 Bytes)",
                            description=f"Image at '{full_img_url}' was served with 0 bytes (empty file).",
                            remediation="Re-upload or re-export the image asset.",
                            element_selector=str_repr,
                            evidence={"img_url": full_img_url, "size_bytes": 0}
                        )
                    )
                elif size_bytes is not None and size_bytes > 3 * 1024 * 1024:
                    mb_size = round(size_bytes / (1024 * 1024), 2)
                    issues.append(
                        self.make_issue(
                            page_url=page_url,
                            severity=Severity.P2_MEDIUM,
                            status=IssueStatus.SUSPECTED,
                            title=f"Excessive Image File Size ({mb_size} MB)",
                            description=f"Image at '{full_img_url}' is {mb_size} MB, which severely impacts page load speed.",
                            remediation="Compress the image or convert to modern formats like WebP or AVIF.",
                            element_selector=str_repr,
                            evidence={"img_url": full_img_url, "size_bytes": size_bytes}
                        )
                    )

        return issues
