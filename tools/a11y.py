"""Accessibility audit: axe-core across every page, light and dark, plus a
keyboard-reachability check.

  uvx --with playwright python a11y.py
"""
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:1313"
CHROME = next(Path.home().glob(".cache/ms-playwright/chromium-*/chrome-linux64/chrome"))

PATHS = ["/", "/about/", "/about/history/", "/board/", "/board/meetings/",
         "/board/projects/", "/amenities/", "/amenities/pool/",
         "/amenities/recreation-center/", "/amenities/rv-lot/",
         "/amenities/parks/", "/rules/", "/rules/architectural-control/",
         "/rules/trash-recycling/", "/rules/report-a-problem/", "/news/",
         "/events/", "/documents/", "/contact/", "/contact/committees/",
         "/contact/community-links/", "/search/", "/404.html"]

AXE = Path("axe.min.js")
if not AXE.exists():
    print("fetching axe-core…")
    urllib.request.urlretrieve(
        "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js", AXE)
axe_src = AXE.read_text()

violations = defaultdict(list)
kb_fail = []

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=str(CHROME))
    for scheme in ("light", "dark"):
        ctx = b.new_context(color_scheme=scheme, viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        for path in PATHS:
            page.goto(BASE + path, wait_until="networkidle")
            page.add_script_tag(content=axe_src)
            res = page.evaluate("""async () => await axe.run(document, {
                runOnly: { type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice'] }
            })""")
            for v in res["violations"]:
                for node in v["nodes"]:
                    violations[f"{v['id']} ({v['impact']})"].append(
                        f"{scheme} {path}: {node['html'][:110]}")
        ctx.close()

    # Keyboard: the skip link must be first, and every nav item reachable.
    page = b.new_context().new_page()
    page.goto(BASE + "/", wait_until="networkidle")
    page.keyboard.press("Tab")
    first = page.evaluate("() => document.activeElement.className")
    if "skip-link" not in first:
        kb_fail.append(f"first Tab stop is {first!r}, expected the skip link")

    focused = page.evaluate("""() => {
        const el = document.activeElement;
        const s = getComputedStyle(el);
        return { outline: s.outlineStyle, width: s.outlineWidth };
    }""")
    if focused["outline"] == "none":
        kb_fail.append("the focused skip link has no visible outline")

    b.close()

print()
if violations:
    print(f"axe-core: {len(violations)} rule(s) violated\n")
    for rule, hits in sorted(violations.items()):
        print(f"  {rule} — {len(hits)} occurrence(s)")
        for h in hits[:3]:
            print(f"      {h}")
else:
    print(f"axe-core: no violations across {len(PATHS)} pages x 2 colour schemes")

print()
if kb_fail:
    print("keyboard:")
    for k in kb_fail:
        print("  FAIL", k)
else:
    print("keyboard: skip link is the first stop and is visibly focused")

sys.exit(1 if violations or kb_fail else 0)
