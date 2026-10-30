import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bs4 import BeautifulSoup

from ai_website_qa.inspectors import (
    LinkInspector, ImageInspector, ContentInspector,
    UILayoutInspector, SEOInspector
)
from ai_website_qa.models import IssueStatus, Severity, Category


def test_link_inspector_empty_and_broken_hash():
    html = """
    <html>
      <body>
        <a id="top" href="">Empty Link</a>
        <a href="#non-existent">Broken Hash Link</a>
        <a href="#">Dummy Link</a>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    inspector = LinkInspector(session=None)
    issues = inspector.inspect(
        page_url="http://example.com/",
        soup=soup,
        raw_html=html,
        response_headers={},
        status_code=200
    )

    confirmed = [i for i in issues if i.status == IssueStatus.CONFIRMED]
    suspected = [i for i in issues if i.status == IssueStatus.SUSPECTED]

    assert len(confirmed) >= 2
    assert any("Empty link" in i.title for i in confirmed)
    assert any("Broken in-page anchor hash" in i.title for i in confirmed)
    assert any("Placeholder / Dummy Link" in i.title for i in suspected)
    print("✅ LinkInspector test passed!")


def test_image_inspector_missing_src_and_alt():
    html = """
    <html>
      <body>
        <img>
        <img src="" alt="Sample">
        <img src="/static/hero.png">
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    inspector = ImageInspector(session=None)
    issues = inspector.inspect(
        page_url="http://example.com/",
        soup=soup,
        raw_html=html,
        response_headers={},
        status_code=200
    )

    confirmed = [i for i in issues if i.status == IssueStatus.CONFIRMED]
    assert any("missing 'src'" in i.title for i in confirmed)
    assert any("Empty image src" in i.title for i in confirmed)
    assert any("Missing 'alt' attribute" in i.title for i in confirmed)
    print("✅ ImageInspector test passed!")


def test_content_inspector_lorem_and_tokens():
    html = """
    <html>
      <body>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
        <div>Hello {{ user.name }}, welcome!</div>
        <span>TODO: add pricing details</span>
        <p>Founder quote: PrÃ©sentation</p>
        <footer>&copy; 2018 Legacy Company</footer>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    inspector = ContentInspector(session=None)
    issues = inspector.inspect(
        page_url="http://example.com/",
        soup=soup,
        raw_html=html,
        response_headers={},
        status_code=200
    )

    confirmed = [i for i in issues if i.status == IssueStatus.CONFIRMED]
    suspected = [i for i in issues if i.status == IssueStatus.SUSPECTED]

    assert any("Lorem Ipsum" in i.title for i in confirmed)
    assert any("Template" in i.title for i in confirmed)
    assert any("TODO" in i.title for i in confirmed)
    assert any("Mojibake" in i.title for i in confirmed)
    assert any("Outdated Copyright" in i.title for i in suspected)
    print("✅ ContentInspector test passed!")


def test_ui_layout_inspector():
    html = """
    <html>
      <head></head>
      <body>
        <button class="btn"></button>
        <input type="text" name="phone">
        <h2>Skipped Subtitle without H1</h2>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    inspector = UILayoutInspector(session=None)
    issues = inspector.inspect(
        page_url="http://example.com/",
        soup=soup,
        raw_html=html,
        response_headers={},
        status_code=200
    )

    confirmed = [i for i in issues if i.status == IssueStatus.CONFIRMED]
    assert any("Missing Mobile Viewport" in i.title for i in confirmed)
    assert any("Empty Button" in i.title for i in confirmed)
    assert any("Missing Primary Heading" in i.title for i in confirmed)
    assert any("Form Input Missing Accessible Label" in i.title for i in confirmed)
    print("✅ UILayoutInspector test passed!")


def test_seo_inspector():
    html = """
    <html>
      <head>
        <title>Hi</title>
        <meta name="robots" content="noindex, nofollow">
        <link rel="canonical" href="http://example.com/a">
        <link rel="canonical" href="http://example.com/b">
      </head>
      <body>
        <h1>Valid Heading</h1>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    inspector = SEOInspector(session=None)
    issues = inspector.inspect(
        page_url="http://example.com/",
        soup=soup,
        raw_html=html,
        response_headers={},
        status_code=200
    )

    confirmed = [i for i in issues if i.status == IssueStatus.CONFIRMED]
    suspected = [i for i in issues if i.status == IssueStatus.SUSPECTED]

    assert any("Missing HTML Language" in i.title for i in confirmed)
    assert any("Missing Meta Description" in i.title for i in confirmed)
    assert any("Multiple Canonical Tags" in i.title for i in confirmed)
    assert any("noindex" in i.title for i in confirmed)
    assert any("Short <title>" in i.title for i in suspected)
    print("✅ SEOInspector test passed!")


if __name__ == "__main__":
    test_link_inspector_empty_and_broken_hash()
    test_image_inspector_missing_src_and_alt()
    test_content_inspector_lorem_and_tokens()
    test_ui_layout_inspector()
    test_seo_inspector()
    print("\n🎉 ALL INSPECTOR UNIT TESTS PASSED SUCCESSFULLY!")
