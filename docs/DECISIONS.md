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

## 6. Cloudflare must be Full (strict), and grey-cloud first

**Decision.** Cloudflare SSL/TLS mode is **Full (strict)**. The `dhoa` DNS record
is created **DNS-only (grey cloud)** until GitHub has issued its certificate.

**Why.** Two failure modes that are hard to diagnose after the fact:

1. **Flexible mode causes an infinite redirect loop.** GitHub Pages 301s
   HTTP→HTTPS. In Flexible mode Cloudflare fetches the origin over HTTP, gets the
   301 again, and loops until the browser gives up with
   `ERR_TOO_MANY_REDIRECTS`. GitHub Pages serves a valid publicly-trusted
   certificate for the custom domain, so Full (strict) is both correct and
   working. **Never use Flexible with GitHub Pages.**

2. **A proxied record blocks certificate issuance.** While the record is orange-
   clouded, GitHub cannot complete its ACME HTTP-01 challenge, so "Enforce HTTPS"
   stays greyed out with no useful error message, sometimes for hours. Order:
   grey cloud → wait for the certificate → Enforce HTTPS → *then* optionally
   re-enable the proxy.

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

**Decision.** `hugo.toml` sets `baseURL = "https://dhoa.naponline.net/"` and the
deploy workflow does **not** pass `--baseURL`.

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

## 10. `dhoa.naponline.net` is temporary

**Decision.** The site currently answers on a subdomain of a personally-owned
domain, used for development and testing.

**Risk.** The association's entire web presence depends on an individual's DNS
zone and Cloudflare account. If that person leaves the board or the domain
lapses, the site disappears and the association has no recourse.

**Recommendation.** Register an association-owned domain through a registrar
account the organization controls, and treat `dhoa.naponline.net` as an alias.
Changing `baseURL` later is a one-line edit. Changing who controls a domain after
a falling-out is not.
