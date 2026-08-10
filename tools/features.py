"""Functional test of the two JavaScript features, and of the site without JS.

  uvx --with playwright python features.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:1313"
CHROME = next(Path.home().glob(".cache/ms-playwright/chromium-*/chrome-linux64/chrome"))

fails = []
def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not cond else ""))
    if not cond:
        fails.append(f"{name}: {detail}")

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=str(CHROME))

    # ── with JavaScript ────────────────────────────────────────────────────
    print("\nWITH JAVASCRIPT")
    p = b.new_context().new_page()

    p.goto(f"{BASE}/search/", wait_until="networkidle")
    p.fill("#q", "pool")
    p.wait_for_timeout(500)
    txt = p.inner_text("#search-status")
    n = p.locator("#search-results li").count()
    check("search finds 'pool'", n > 0, f"{n} results, status={txt!r}")
    check("search highlights the term", p.locator("#search-results mark").count() > 0)
    check("search URL is shareable", "q=pool" in p.url, p.url)

    p.fill("#q", "rv lot")
    p.wait_for_timeout(500)
    hrefs = p.eval_on_selector_all("#search-results a", "els => els.map(e => e.getAttribute('href'))")
    check("a PDF is reachable from search", any(h.endswith(".pdf") for h in hrefs), str(hrefs))

    p.fill("#q", "zzzzqqq")
    p.wait_for_timeout(500)
    check("no-match shows the browse fallback",
          p.locator("#search-fallback").is_visible())

    p.goto(f"{BASE}/documents/", wait_until="networkidle")
    check("filter bar is revealed by JS", p.locator("#doc-filter").is_visible())
    total = p.locator(".doc").count()
    p.click('[data-filter="rv-lot"]')
    p.wait_for_timeout(250)
    vis = p.eval_on_selector_all(".doc", "els => els.filter(e => !e.hidden).length")
    check("category chip filters", 0 < vis < total, f"{vis} of {total}")
    check("filtered view is linkable", "category=rv-lot" in p.url, p.url)
    heads = p.eval_on_selector_all(".doc-group", "els => els.filter(e => !e.hidden).length")
    check("empty category headings hide", heads == 1, f"{heads} groups visible")

    p.click('[data-filter="all"]')
    p.fill("#doc-search", "rental")
    p.wait_for_timeout(250)
    vis = p.eval_on_selector_all(".doc", "els => els.filter(e => !e.hidden).length")
    check("text filter narrows", 0 < vis < total, f"{vis} of {total}")

    # deep link straight into a filtered view
    p.goto(f"{BASE}/documents/?category=acc", wait_until="networkidle")
    p.wait_for_timeout(250)
    check("?category= deep link is honoured",
          p.get_attribute('[data-filter="acc"]', "aria-pressed") == "true"
          if p.locator('[data-filter="acc"]').count() else True)

    # ── without JavaScript ─────────────────────────────────────────────────
    print("\nWITHOUT JAVASCRIPT")
    ctx = b.new_context(java_script_enabled=False)
    q = ctx.new_page()

    q.goto(f"{BASE}/documents/", wait_until="load")
    shown = q.eval_on_selector_all(".doc", "els => els.filter(e => !e.hidden).length")
    check("every document is visible", shown == total, f"{shown} of {total}")
    check("no dead filter controls", not q.locator("#doc-filter").is_visible())

    q.goto(f"{BASE}/search/?q=pool", wait_until="load")
    check("search page offers a browse fallback", q.locator("#search-fallback").is_visible())
    check("no empty results box", not q.locator("#search-results").is_visible())

    q.goto(f"{BASE}/events/", wait_until="load")
    check("events list renders", q.locator(".event").count() > 0,
          f"{q.locator('.event').count()} events")
    check("subscribe link present", q.locator('a[href$=".ics"]').count() > 0)

    q.set_viewport_size({"width": 390, "height": 800})
    q.goto(f"{BASE}/", wait_until="load")
    q.click(".nav__toggle")
    check("mobile menu opens without JS", q.locator(".nav__link").first.is_visible())

    b.close()

print()
if fails:
    print(f"{len(fails)} FAILURE(S)")
    sys.exit(1)
print("All feature checks passed.")
