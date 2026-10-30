"""
Mock Staging Website Server
Runs a multi-page realistic staging site embedded with representative QA defects
(broken links, missing images, unrendered templates, Lorem Ipsum, missing viewport,
empty buttons, duplicate headings, outdated copyright, and SEO issues)
for automated evaluation and demonstration.
"""

from fastapi import FastAPI, Response, status
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Realistic QA Test Staging Site")


@app.get("/", response_class=HTMLResponse)
async def home():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acme Cloud Solutions - Next Gen Staging Portal</title>
    <meta name="description" content="Acme Cloud Solutions delivers cutting-edge developer tools and scalable cloud infrastructure for modern enterprise teams worldwide.">
    <link rel="canonical" href="http://localhost:8088/">
    <meta property="og:title" content="Acme Cloud Solutions">
</head>
<body>
    <header>
        <nav>
            <a href="/">Home</a> |
            <a href="/about">About Us</a> |
            <a href="/pricing">Pricing</a> |
            <a href="/contact">Contact</a> |
            <!-- Confirmed Broken Link: 404 -->
            <a href="/non-existent-page">Enterprise Feature Preview</a> |
            <!-- Broken hash -->
            <a href="#non-existent-section">Jump to Specs</a>
        </nav>
    </header>

    <main>
        <!-- Multiple H1 issue -->
        <h1>Welcome to Acme Cloud Platform</h1>
        <h1>Next Generation Hosting</h1>

        <!-- Template leak -->
        <p>Current Organization: {{ company.tagline }}</p>

        <!-- Broken image (HTTP 404) -->
        <img src="/static/missing-hero-banner.jpg" alt="Platform Architecture Overview" width="600" height="300">

        <!-- Image missing alt entirely -->
        <img src="/static/valid-logo.png" width="120" height="40">

        <!-- Empty button defect -->
        <div style="margin: 20px 0;">
            <button class="btn btn-primary"></button>
            <button type="button">Valid Get Started</button>
        </div>

        <section id="features">
            <h2>Scalable Infrastructure</h2>
            <p>Deploy containers in seconds with our globally distributed edge network.</p>
        </section>

        <!-- Outdated copyright and dummy phone -->
        <footer>
            <p>Support Hotline: 555-0199 | Email: test@example.com</p>
            <p>&copy; 2019 Acme Corp. All rights reserved.</p>
        </footer>
    </main>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/about", response_class=HTMLResponse)
async def about():
    # Defect: Missing <title> tag, Lorem ipsum, Mojibake encoding
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Notice: Missing <title> tag entirely -->
    <meta name="description" content="This is an excessively long meta description crafted specifically to test SEO truncation warnings. It keeps going on and on beyond one hundred and sixty characters to ensure that the AI Website QA Agent properly flags it as a suspected truncation risk in search engine result pages.">
</head>
<body>
    <nav>
        <a href="/">Home</a> |
        <a href="/about">About Us</a> |
        <a href="/contact">Contact</a>
    </nav>

    <h1>About Acme Corporation</h1>

    <!-- Confirmed Lorem Ipsum copy -->
    <div class="team-bio">
        <h3>Leadership Team</h3>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
    </div>

    <!-- Confirmed Mojibake encoding error -->
    <p>Our founder stated: â€™Quality is our core missionâ€™. PrÃ©sentation matters.</p>

    <!-- Confirmed Empty href -->
    <a href="">Click for more leadership information</a>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/contact", response_class=HTMLResponse)
async def contact():
    # Defect: Missing mobile viewport, form input without label, TODO placeholder
    html = """<!DOCTYPE html>
<html>
<head>
    <!-- Notice: Missing viewport meta tag! -->
    <title>Contact Us - Acme Cloud</title>
</head>
<body>
    <nav><a href="/">Home</a> | <a href="/contact">Contact</a></nav>
    <h1>Get in Touch</h1>

    <!-- Developer TODO leak -->
    <p class="notice">TODO: Connect SendGrid backend before release.</p>

    <form action="/submit-contact" method="POST">
        <!-- Form input with no label or aria-label -->
        <input type="text" name="customer_inquiry" placeholder="Inquiry notes">
        <button type="submit">Submit Inquiry</button>
    </form>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/pricing", response_class=HTMLResponse)
async def pricing():
    # Defect: noindex directive on staging, skipped heading levels (h1 -> h4), duplicate canonicals
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pricing Plans - Acme Cloud</title>
    <meta name="robots" content="noindex, nofollow">
    <!-- Duplicate canonicals -->
    <link rel="canonical" href="http://localhost:8088/pricing">
    <link rel="canonical" href="http://localhost:8088/pricing-alt">
</head>
<body>
    <nav><a href="/">Home</a> | <a href="/pricing">Pricing</a></nav>
    <h1>Transparent Cloud Pricing</h1>
    <!-- Skipped heading: h1 directly to h4 -->
    <h4>Developer Tier ($0/mo)</h4>
    <p>Free tier with 1,000 requests per minute.</p>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/static/valid-logo.png")
async def valid_logo():
    # Minimal 1x1 transparent PNG bytes
    png_bytes = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00'
        b'\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return Response(content=png_bytes, media_type="image/png")


# /static/missing-hero-banner.jpg and /non-existent-page are omitted, so they will return HTTP 404!


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8088)
