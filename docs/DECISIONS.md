# Architecture decisions

Short records of choices that are expensive to reverse or easy to accidentally
undo. Each says what was decided, why, and what would make us revisit it.

---

## 1. Hugo, and no Node in the build

**Decision.** The site is built by the Hugo extended binary alone. Nothing in the
build requires Node, npm, a package manager, or a lockfile.

**Why.** This site will be maintained intermittently by volunteers over many
years. A JavaScript toolchain rots: lockfiles go stale, transitive dependencies
break, and a site nobody has touched in 18 months stops building for reasons
unrelated to the site. A single versioned binary that reads plain files does not
have that failure mode.

A previous attempt used Tailwind, which pulled in 66 npm packages and 15 MB of
`node_modules` to produce one CSS file. That is a real ongoing maintenance
liability for a volunteer HOA board, and it bought nothing a hand-written
stylesheet with custom properties does not.

Hugo extended already contains everything needed: libwebp for image encoding,
esbuild for JavaScript bundling, and a CSS concatenator/minifier.

**Verified.** With a `PATH` containing only `hugo` and `git`, and `node`/`npm`
absent, `hugo --gc --minify --panicOnWarning` completes and still emits the
bundled, minified, fingerprinted JavaScript.

**The one other binary.** `git` is required, because `enableGitInfo = true` gives
every page a real `.Lastmod` from commit history rather than a file mtime. That
is not an extra dependency in practice — you already need git to clone the
repository, and the CI checkout provides it. Set `enableGitInfo = false` if you
ever need to build from a plain source tarball.

**Revisit if.** The design needs something genuinely impossible without a
preprocessor. It has not yet.

---

## 2. Organizational facts live in `data/`, never in `hugo.toml`

**Decision.** `hugo.toml` holds build settings and navigation structure. Every
fact a board member might change — address, phone, fax, email, office hours,
assessment amounts, external service URLs — lives in `data/organization.yaml`.
Templates never read `.Site.Params` for an organizational fact.

**Why.** The previous version stored contact details in *both*
`hugo.toml [params]` and `data/contact.yaml`. They drifted, and the site shipped
`Dhoa@verizon.net` in one place and `dhoa@verizon.net` in another. Two sources of
truth is zero sources of truth.

Putting these values in `data/` also makes them editable through the CMS, which
`hugo.toml` is not.

**Enforcement.** `layouts/_partials/data/validate.html` runs on every build and
calls `errorf` — which fails the build — if `phone`, `email`, `address`,
`mailing`, `officeHours`, or `fax` appear under `[params]`, if a required
`organization.yaml` key is missing, or if any `email_key` reference points at an
address that does not exist. Hugo has no test runner; this is the substitute.

---

## 3. Images in `assets/`, PDFs in `static/`

**Decision.** Images are uploaded to `assets/media/` and processed by Hugo into
resized, fingerprinted WebP derivatives. PDFs are uploaded to `static/documents/`
and served byte-for-byte at a stable `/documents/…` URL.

**Why.** These two file types have opposite requirements.

Images need to be resized — the source archive contains 2 MB JPEGs — and nobody
deep-links a photograph, so changing their URLs is free.

PDF URLs are the opposite. Forms get printed in newsletters, pasted into emails,
and referenced by the county. `/documents/acc-application-for-exterior-change.pdf`
must still work in five years. Fingerprinting would break that on every re-upload.

**Consequence to know about.** A raw link to `/media/photo.jpg` returns 404,
because originals are never published — only derivatives are. This is documented
in `docs/EDITING.md`.

The CMS writes a nominal `/media/…` path into front matter and markdown.
`layouts/_partials/media/resolve.html` is the single place that maps it to a real
resource; the Goldmark image render hook and the front-matter image partial both
delegate to it. If a path cannot be resolved it emits a warning naming the page,
which fails CI under `--panicOnWarning` rather than silently 404ing.

---

## 4. Sveltia CMS with GitHub OAuth, not personal access tokens

**Decision.** Board members authenticate at `/admin/` by clicking "Login with
GitHub". A small Cloudflare Worker (`sveltia/sveltia-cms-auth`) relays the OAuth
handshake.

**Why.** The alternative — each editor generating a GitHub personal access token
and pasting it into the CMS — is a genuine barrier for non-technical volunteers,
and tokens expire silently. The Worker is free, is about thirty lines, and needs
no maintenance.

**Security notes.**
- `static/admin/index.html` pins an **exact** Sveltia version. Never `@latest`.
  That script has commit access to this repository, so an unreviewed CDN update
  is a supply-chain risk. Vendoring the file into `static/admin/` is the
  recommended hardening step once the site is stable.
- The GitHub OAuth App and the Cloudflare Worker should be owned by the
  **organization**, not an individual's account, so they survive a board change.
  Custody is recorded in `docs/RUNBOOK-oauth.md`.

---

## 5. `publish_mode: simple` — Publish goes straight to `main`

**Decision.** Clicking Publish in the CMS commits directly to `main` and the site
rebuilds.

**Why.** Sveltia's `editorial_workflow` opens a pull request per edit and adds a
draft/review queue. That is genuinely useful, but it introduces a concept
non-technical editors find confusing, and every change is already in git, so any
mistake is one revert away.

**Revisit if.** After a few months of real use the board wants a second pair of
eyes before content goes live. Switching is a one-line config change.

---

## 6. If Cloudflare fronts the site, it stays proxied and the origin hop is unvalidated

**Decision.** If the site is fronted by Cloudflare, the record stays
**orange-clouded (proxied)**, GitHub therefore never issues a certificate for the
custom domain, and Cloudflare SSL/TLS is **Flexible or Full (non-strict)** —
*not* Full (strict).

**Status: not currently deployed.** This was measured in August 2026 against a
temporary development hostname on a personally-owned domain. That hostname has
been retired and its DNS record deleted. The site is not published anywhere
today, and Cloudflare is a proposal rather than a service the association uses.

The record is kept because the tradeoff and its landmine are real and will apply
the moment the site goes live behind a proxy. What was observed then:

```
https_certificate:   null            GitHub had never issued one
origin certificate:  CN=*.github.io  did not match the custom domain
origin over HTTP:    200, no redirect
Enforce HTTPS:       unavailable (greyed out; the API reported null)
```

Visitors would be unaffected — Cloudflare presents its own valid edge
certificate, so the site is HTTPS in the browser. The unauthenticated hop is
Cloudflare → GitHub.

**Why.** A GitHub certificate requires an ACME HTTP-01 challenge, and GitHub
cannot complete one while the record is proxied. That would mean a temporary
DNS-only window, and we chose not to take one.

**What it costs.**

- Full (strict) is unavailable. Enabling it without a GitHub certificate makes
  Cloudflare reject the origin certificate and serve `526 Invalid SSL
  Certificate` on every request.
- The Cloudflare → GitHub hop is either plaintext (Flexible) or encrypted but
  unauthenticated (Full non-strict). Which one is not detectable from outside;
  read it off SSL/TLS → Overview.
- **Enforce HTTPS** in Settings → Pages can never be ticked.

**The landmine.** If someone later obtains a certificate and ticks Enforce HTTPS
**while Cloudflare is still on Flexible**, GitHub will 301 HTTP→HTTPS, Cloudflare
will fetch the origin over HTTP, receive the 301 again, and loop until the
browser gives up with `ERR_TOO_MANY_REDIRECTS`. The site looks completely broken
and neither dashboard explains why.

This is unreachable today, because no certificate exists to enable it with.

**Safe in any mode.** SSL/TLS → Edge Certificates → **Always Use HTTPS: On**
acts at the Cloudflare edge, before the origin fetch, so it cannot cause the
loop and is worth having.

**Revisit if** you want the origin hop authenticated. The reversal is about
fifteen minutes and ends with the record proxied again, exactly as it is now:

1. Cloudflare → DNS → `dhoa` → Proxy status: **DNS only**.
2. Wait for Settings → Pages to show the certificate as issued.
3. Tick **Enforce HTTPS**.
4. Cloudflare → SSL/TLS → **Full (strict)**.
5. Cloudflare → DNS → `dhoa` → Proxy status: **Proxied**.

Order matters. Step 4 must precede step 5, and step 3 must not happen while the
mode is still Flexible.

---

## 7. `CNAME` lives in `static/`, not the repository root

**Decision.** The custom-domain `CNAME` file is `static/CNAME`.

**Why.** Hugo only copies `static/` into `public/`. With the Pages source set to
GitHub Actions, GitHub reads `CNAME` from the *published artifact* — not from the
repository. A root-level `CNAME` never reaches `public/`, and GitHub can silently
clear the custom domain setting on deploy.

The deploy workflow asserts `public/CNAME` exists and contains the right hostname,
so this cannot regress unnoticed.

---

## 8. baseURL is never overridden on the command line

**Decision.** `hugo.toml` sets `baseURL = "https://discoveryhomeowners.com/"` and the
deploy workflow does **not** pass `--baseURL`.

**This is a forward declaration.** `discoveryhomeowners.com` is the association's
own domain and the intended home of this site, but it is not yet held in an
account the association controls and does not point at GitHub — it currently
redirects to the old Google Sites page. Until the domain is transferred and its
DNS repointed, Pages will report the custom domain as unverified and will not
serve there. Nothing breaks in the meantime, because the site is not published.

See the `domain/` area of the private `technology` repository for the current
state of the transfer, including the registry locks that have to be lifted first.

**Why.** The previous attempt lived at `https://napalm255.github.io/hoa/` while
its README claimed a different custom domain, producing links with a stale
`/hoa/` prefix. Passing the Pages default URL on the command line is exactly how
that mismatch happens. CI greps the built output for stale hostnames and fails if
it finds one.

**Note.** This repository is named `<org>.github.io`, so Pages serves it at the
**root** path. There is no subpath. Any `/hoa/`-style prefix is a bug.

---

## 9. Spanish is per-block, not a parallel site

**Decision.** Spanish translations are wrapped inline by an `{{< es >}}`
shortcode, which emits `<section lang="es">`. Documents carry a `language` field.
Hugo's multilingual mode is not used.

**Why.** Only two pages need Spanish (Architectural Control and the RV Lot).
Multilingual mode would double every page, every CMS entry, and every editor's
workload for the entire site to serve two pages, and would leave most of the
Spanish site permanently untranslated.

The `lang` attribute matters: it makes screen readers switch pronunciation.

**Caution.** These pages carry towing and enforcement consequences. Machine
translation is not appropriate; a human should review Spanish copy.

---

## 10. The site has no association-controlled domain yet

**Decision.** The site is built for `discoveryhomeowners.com` and is published
nowhere until that domain is under the association's control.

**History.** Development and review were done on a subdomain of a personally
owned domain. That was always temporary, it was never given to residents, and it
has now been retired — the DNS record is deleted and the hostname appears nowhere
in this repository. Do not reintroduce it.

**The risk it existed to illustrate has not gone away.** It has moved. The
association does own `discoveryhomeowners.com`, and has published under it since
2011, but:

- the registration sits in a Squarespace account whose custody has not been
  established;
- the registry has both `clientTransferProhibited` and `clientDeleteProhibited`
  set, and lifting them requires that same account;
- DNSSEC is enabled, so its DS record must be removed before any transfer or the
  name stops resolving;
- the registration expires **14 October 2027**.

**Recommendation.** Establish who controls the Squarespace account, then transfer
the domain into a registrar account registered and billed to the association,
with a board officer holding recovery access. Changing `baseURL` afterwards is a
one-line edit. Establishing who controls a domain after a falling-out is not.

Evidence for every statement above, with the commands that reproduce it, is in
the private `technology` repository under `domain/`.
