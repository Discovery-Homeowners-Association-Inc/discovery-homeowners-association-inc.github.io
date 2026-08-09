# Fonts

## Fraunces (`fraunces-display.woff2`)

Used for headings only. Body text uses the system font stack, so this is the
only font file the site downloads.

- **License:** SIL Open Font License 1.1 — see [`OFL.txt`](OFL.txt).
- **Copyright:** 2018 The Fraunces Project Authors,
  <https://github.com/undercasetype/Fraunces>
- **Variable axis:** `wght` 400–700. The optical-size axis is pinned at
  `opsz=40`, which is where the face reads best at display sizes.
- **Size:** ~31 KB.

### How it was produced

A one-time offline step. **This is not part of the build** — the site builds
with the Hugo binary alone, and this file is committed. Only repeat it if the
character coverage or the weight range needs to change.

```bash
# 1. Get the latin subset Google serves
curl -sS -A "Mozilla/5.0" \
  "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&display=swap" \
  -o fraunces.css
curl -sS "$(grep -oE 'https://[^)]*\.woff2' fraunces.css | tail -1)" -o fraunces-latin.woff2

# 2. Pin the optical-size axis, keep weight 400–700 variable
uvx --from "fonttools[woff,unicode]" fonttools varLib.instancer \
  fraunces-latin.woff2 opsz=40 wght=400:700 -o /tmp/fraunces-inst.ttf

# 3. Subset to the characters this site actually sets
uvx --from "fonttools[woff,unicode]" pyftsubset /tmp/fraunces-inst.ttf \
  --output-file=fraunces-display.woff2 --flavor=woff2 \
  --layout-features='kern,liga,calt,ccmp,locl' \
  --unicodes='U+0020-007E,U+00A0-00FF,U+0152-0153,U+2010-2011,U+2013-2014,U+2018-201A,U+201C-201E,U+2020-2022,U+2026,U+2030,U+2039-203A,U+2044,U+20AC,U+2122' \
  --desubroutinize --name-IDs='0,1,2,3,4,5,6'
```

Coverage includes Latin-1 Supplement, so Spanish content (`á é í ó ú ñ ü ¿ ¡`)
renders correctly.

### Why self-hosted

Loading fonts from Google's CDN would leak every visitor's IP address to a third
party and add a DNS lookup plus a connection to the critical path. The site makes
**zero** third-party requests on every page except `/admin/`.
