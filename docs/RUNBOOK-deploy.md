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

Same page → **Custom domain** → `dhoa.naponline.net` → Save.

> `static/CNAME` is already committed, and the deploy workflow fails the build
> if it is missing from the artifact. That matters: with the Actions source
> GitHub reads `CNAME` from the *published output*, not from the repository, so
> a missing one can silently clear this setting on the next deploy.

## 3. Verify the domain at the organization level

Organization → **Settings → Pages → Verified domains** → add `naponline.net`,
then create the `_github-pages-challenge-...` TXT record it gives you in
Cloudflare.

This stops anyone else claiming the hostname on GitHub Pages if this site is
ever deleted while DNS still points at it. It takes two minutes and closes a
real takeover route.

## 4. Cloudflare DNS — grey cloud **first**

Create the record:

```
Type: CNAME   Name: dhoa   Target: discovery-homeowners-association-inc.github.io
Proxy status: DNS only  (grey cloud)
```

**Leave it grey-clouded until GitHub has issued the certificate.**

While the record is proxied, GitHub cannot complete its ACME HTTP-01 challenge.
The symptom is unhelpful: the **Enforce HTTPS** checkbox in Settings → Pages
stays greyed out saying the certificate is not yet issued, sometimes for hours,
with nothing explaining why.

Correct order:

1. Grey cloud.
2. Wait for Settings → Pages to say *"Your site is published at
   https://dhoa.naponline.net"* and show the certificate as issued.
3. Tick **Enforce HTTPS**.
4. *Then*, if you want Cloudflare's caching, switch to the orange cloud.

## 5. Cloudflare SSL mode — **Full (strict)**

Cloudflare → **SSL/TLS → Overview → Full (strict)**.

**Never use Flexible.** With Flexible, GitHub Pages redirects HTTP to HTTPS,
Cloudflare fetches the origin over HTTP, receives the redirect again, and loops
until the browser gives up with `ERR_TOO_MANY_REDIRECTS`. The site appears
completely broken and the cause is not obvious from either dashboard.

GitHub Pages serves a valid publicly-trusted certificate for the custom domain,
so Full (strict) is both correct and works.

Once that is right, **SSL/TLS → Edge Certificates → Always Use HTTPS: On** is
safe and worth having.

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

`dhoa.naponline.net` is a subdomain of a **personally owned** domain, used while
the site is being built.

That means the association's entire web presence currently depends on one
person's DNS zone and Cloudflare account. If that person leaves the board, or
the domain lapses, the site disappears and the association has no way to get it
back.

**Register an association-owned domain** through a registrar account the
organization controls, and treat `dhoa.naponline.net` as a temporary alias.
Changing `baseURL` afterwards is a one-line edit in `hugo.toml`. Recovering a
domain after a falling-out is not a one-line anything.
