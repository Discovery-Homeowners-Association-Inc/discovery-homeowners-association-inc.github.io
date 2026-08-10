# Tools

Scripts that are **not** part of the build. The site builds with the Hugo
binary alone; everything here is for people working on it.

| Script | What it does |
|---|---|
| `check-cms-schema.py` | Fails if `static/admin/config.yml` has drifted from the data files it edits, which would destroy keys on the next Publish. **Runs in CI.** |
| `check.py` | Loads every page at five widths in both colour schemes, failing on horizontal overflow or console errors. |
| `features.py` | Drives the search and document filter in a real browser, then repeats the important paths with JavaScript disabled. |
| `a11y.py` | Runs axe-core over every page in both colour schemes, plus a keyboard check. |
| `render-dhoa-mark.py` | Regenerates `assets/brand/dhoa-mark.svg` from the measured control points. |
| `render-neighborhood-map.py` | Regenerates `assets/map/discovery-map.svg` from the cached OpenStreetMap data. |

## Running the browser checks

They need a local server and a copy of Chromium. Start the site first:

```bash
hugo server --renderToMemory
```

then, in another terminal:

```bash
uvx --with playwright python tools/check.py
uvx --with playwright python tools/features.py
uvx --with playwright python tools/a11y.py
```

They expect `http://127.0.0.1:1313` and reuse whatever Chromium Playwright has
already downloaded, so nothing new is installed.

## The schema check

This one is worth running by hand any time you touch a `data/*.yaml`:

```bash
uvx --with pyyaml python tools/check-cms-schema.py
```

It is also the first step in CI, because the failure it prevents — a board
member pressing Publish and silently deleting a field nobody declared — is
invisible until somebody notices the phone number has gone.
