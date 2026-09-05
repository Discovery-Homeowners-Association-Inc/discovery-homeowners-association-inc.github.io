# Runbook: publishing the site

Every push to `main` builds with Hugo and publishes to GitHub Pages. Cloudflare
provides DNS and the certificate.

The build is automatic. The steps below are the **one-time setup** — and two of
them have failure modes that waste an afternoon if you get the order wrong, so
they are spelled out.

---

## 1. Point GitHub Pages at the workflow

Repository → **Settings → Pages**:

- **Source: GitHub Actions.** Not "Deploy from a branch". The workflow in
  `.github/workflows/deploy.yml` does the building.

## 2. Set the custom domain

Same page → **Custom domain** → `discoveryhomeowners.com` → Save.

> `static/CNAME` is already committed, and the deploy workflow fails the build
> if it is missing from the artifact. That matters: with the Actions source
> GitHub reads `CNAME` from the *published output*, not from the repository, so
> a missing one can silently clear this setting on the next deploy.

## 3. Verify the domain at the organization level

Organization → **Settings → Pages → Verified domains** → add `discoveryhomeowners.com`,
then create the `_github-pages-challenge-...` TXT record it gives you in
Cloudflare.

This stops anyone else claiming the hostname on GitHub Pages if this site is
ever deleted while DNS still points at it. It takes two minutes and closes a
real takeover route.

## 4. Cloudflare DNS — the record stays proxied

```
Type: CNAME   Name: dhoa   Target: discovery-homeowners-association-inc.github.io
Proxy status: Proxied  (orange cloud)
```

This is a deliberate tradeoff, recorded in `docs/DECISIONS.md` #6. The short
version: while the record is proxied, GitHub cannot complete its ACME HTTP-01
challenge, so it never issues a certificate for the custom domain and **Enforce
HTTPS** in Settings → Pages stays permanently greyed out.

Visitors are unaffected. Cloudflare presents its own valid certificate, so the
site is HTTPS in the browser. What is unauthenticated is the Cloudflare → GitHub
hop behind it.

## 5. Cloudflare SSL mode — **not** Full (strict)

Cloudflare → **SSL/TLS → Overview**. This must be **Flexible** or **Full**.

Do **not** set Full (strict). It validates the origin certificate, and GitHub
Pages has issued none for `discoveryhomeowners.com` — it presents its default
`CN=*.github.io`, which does not match. Cloudflare rejects it and serves `526
Invalid SSL Certificate` on every request.

**Never tick Enforce HTTPS while the mode is Flexible.** GitHub would redirect
HTTP→HTTPS, Cloudflare would fetch the origin over HTTP, receive the redirect
again, and loop until the browser gives up with `ERR_TOO_MANY_REDIRECTS`. That
is unreachable today — no certificate exists, so the checkbox is greyed out —
but it is the failure mode to remember if that ever changes.

**SSL/TLS → Edge Certificates → Always Use HTTPS: On** is safe in any mode. It
acts at the edge, before the origin fetch, so it cannot cause the loop.

If you later want the origin hop authenticated, the reversal takes about fifteen
minutes and ends with the record proxied again. The numbered procedure is in
`docs/DECISIONS.md` #6.

---

## 6. Optional: caching, once proxied

GitHub Pages caps `Cache-Control` at about ten minutes and gives you no way to
set headers, so proxying through Cloudflare is the only way to get real caching.

A Cache Rule with an Edge TTL of a year is safe for:

```
/css/*   /js/*   /fonts/*   /media/*
```

Those filenames are fingerprinted by Hugo, so a change produces a new filename.

Do **not** long-cache `/*.html`, `/index.json`, or `/documents/*` — those keep
their names when their contents change.

---

## What the build checks

`.github/workflows/check.yml` runs on every pull request and refuses to merge if:

- the CMS config has drifted from the data files it edits, so a Publish would
  destroy a key (`tools/check-cms-schema.py`)
- Hugo emits **any** warning — a missing image, an image with no alt text, a
  duplicate output path (`--panicOnWarning`)
- a template is unused, which means either dead code or a lookup that is not
  matching
- the calendar feed is not valid iCalendar, has duplicate UIDs, or has an event
  ending before it starts
- the CSS exceeds its 12 KB gzipped budget
- any link does not resolve

`.github/workflows/deploy.yml` additionally refuses to publish if `CNAME` is
missing or wrong, if any expected file was not generated, or if a stale hostname
leaked into the output.

---

## Rolling back

Every change is a commit, including the ones made through `/admin/`. To undo
one:

```bash
git revert <commit>
git push
```

The site rebuilds and republishes in about two minutes.

---

## The domain is a risk worth closing

`discoveryhomeowners.com` is a subdomain of a **personally owned** domain, used while
the site is being built.

That means the association's entire web presence currently depends on one
person's DNS zone and Cloudflare account. If that person leaves the board, or
the domain lapses, the site disappears and the association has no way to get it
back.

**Register an association-owned domain** through a registrar account the
organization controls, and treat `discoveryhomeowners.com` as a temporary alias.
Changing `baseURL` afterwards is a one-line edit in `hugo.toml`. Recovering a
domain after a falling-out is not a one-line anything.
