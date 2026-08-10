"""Layout/console smoke check against the local Hugo server.

Uses the chromium Playwright already has on disk, so nothing is downloaded.
  uvx --with playwright python check.py [base_url]
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:1313"

CHROME = next(
    (p for p in Path.home().glob(".cache/ms-playwright/chromium-*/chrome-linux64/chrome")),
    None,
)

PATHS = ["/", "/about/", "/about/history/", "/about/welcome-committee/",
         "/board/", "/board/meetings/", "/board/projects/",
         "/amenities/", "/amenities/pool/", "/amenities/recreation-center/",
         "/amenities/rv-lot/", "/amenities/parks/",
         "/rules/", "/rules/architectural-control/", "/rules/trash-recycling/",
         "/rules/report-a-problem/",
         "/news/", "/news/2026/pool-passes-for-2026-are-on-sale/", "/events/",
         "/events/2026-05-23-pool-opening/", "/documents/",
         "/contact/", "/contact/committees/", "/contact/community-links/",
         "/search/", "/search/?q=pool", "/404.html"]

WIDTHS = [(320, "xs"), (390, "phone"), (768, "tablet"), (1024, "laptop"), (1440, "desktop")]

failures = []

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=str(CHROME))
    for scheme in ("light", "dark"):
        ctx = browser.new_context(color_scheme=scheme)
        page = ctx.new_page()

        console = []
        page.on("console", lambda m: console.append(m) if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: failures.append(f"JS ERROR {page.url}: {e}"))

        for path in PATHS:
            resp = page.goto(BASE + path, wait_until="networkidle")
            if resp and resp.status >= 400 and path != "/404.html":
                failures.append(f"HTTP {resp.status} {path}")

            for width, label in WIDTHS:
                page.set_viewport_size({"width": width, "height": 900})
                page.wait_for_timeout(60)
                over = page.evaluate("""() => {
                    const d = document.documentElement;
                    const scroll = d.scrollWidth, client = d.clientWidth;
                    if (scroll <= client + 1) return null;
                    // name the widest offending element
                    let worst = null, worstW = 0;
                    for (const el of document.querySelectorAll('body *')) {
                        const r = el.getBoundingClientRect();
                        if (r.right > client + 1 && r.width > worstW) {
                            worstW = r.width;
                            worst = el.tagName.toLowerCase() +
                                (el.className && typeof el.className === 'string'
                                  ? '.' + el.className.trim().split(/\\s+/).join('.') : '');
                        }
                    }
                    return {scroll, client, worst};
                }""")
                if over:
                    failures.append(
                        f"OVERFLOW {scheme} {label}({width}px) {path}: "
                        f"scrollWidth={over['scroll']} clientWidth={over['client']} "
                        f"widest={over['worst']}")

        for m in console:
            failures.append(f"CONSOLE {m.type} ({scheme}): {m.text}")
        ctx.close()
    browser.close()

if failures:
    print(f"FAIL — {len(failures)} issue(s):")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print(f"PASS — {len(PATHS)} pages x {len(WIDTHS)} widths x 2 schemes, no overflow or console errors.")
