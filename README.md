# Discovery Homeowners Association — Website

The public website for the Discovery Homeowners Association, Inc. of Walkersville,
Frederick County, Maryland.

> **Not published yet.** This site is built and working, but it is not deployed
> and has no public address. It is configured for the association's own domain,
> **`discoveryhomeowners.com`**, which the association owns but does not yet hold
> in an account it controls — the domain still redirects to the old Google Sites
> page. Until it is transferred and repointed, the addresses below do not work.
>
> The association's current website remains the Google Sites page. See
> `docs/DECISIONS.md` #10, and the `domain/` area of the private `technology`
> repository for where the transfer stands.

**Intended site address:** `https://discoveryhomeowners.com/`
**Intended editing address:** `https://discoveryhomeowners.com/admin/`

---

## For board members — editing the site

*Once the site is published,* you will not need to install anything. Go to
**https://discoveryhomeowners.com/admin/**, click **Login with GitHub**, and edit
from any browser, including your phone. Changes go live about two minutes after
you click Publish.

See **[docs/EDITING.md](docs/EDITING.md)** for a walkthrough of adding an
announcement, adding an event, uploading a form, and changing the office phone
number.

---

## For developers

### Requirements

**One binary: [Hugo extended](https://gohugo.io/installation/) v0.146.0 or newer.**
No Node, no npm, no Ruby, no build step beyond Hugo itself. This is deliberate —
see [docs/DECISIONS.md](docs/DECISIONS.md).

```bash
hugo version   # must say "+extended"
```

### Run it locally

```bash
git clone git@github.com:Discovery-Homeowners-Association-Inc/discovery-homeowners-association-inc.github.io.git
cd discovery-homeowners-association-inc.github.io
hugo server -D --navigateToChanged
```

Open http://localhost:1313/.

To reach the dev server from another device — a phone, or another machine over
Tailscale or the LAN — bind it to every interface instead of just loopback:

```bash
hugo server -D --bind 0.0.0.0 --navigateToChanged
```

Then browse to `http://<this-machine's-address>:1313/`. Live reload follows the
address you loaded the page from, so it keeps working from a remote device.

### Other commands

```bash
# Exactly what CI runs — warnings are errors
hugo --gc --minify --panicOnWarning

# Template hygiene: unused templates, duplicate output paths
hugo --printUnusedTemplates --printPathWarnings

# Inspect resolved config and content (catches YAML shape mistakes)
hugo config
hugo list all

# Serve the production build the way GitHub Pages will
hugo --gc --minify && (cd public && python3 -m http.server 8080)
```

> **Warning:** `/admin/` talks to the GitHub API directly, so opening it on
> `localhost` still edits the **live repository**. A "test" publish from
> localhost is a real commit to `main`.

### Where things live

| Path | What |
|---|---|
| `hugo.toml` | Build settings and navigation structure only — **no contact info** |
| `data/organization.yaml` | Single source of truth for address, phone, email, hours, dues, external links |
| `data/*.yaml` | Board roster, committees, community links, who-to-call, parks, trash schedule |
| `content/` | Pages, announcements, events, documents |
| `layouts/` | Templates ([Hugo v0.146+ layout system](https://gohugo.io/templates/new-templatesystem-overview/) — no `_default/`) |
| `assets/css/` | Hand-written CSS, concatenated in filename order |
| `assets/media/` | Images — processed and resized by Hugo |
| `static/documents/` | PDFs — served verbatim so printed links never break |
| `static/admin/` | Sveltia CMS |

### The one rule

`hugo.toml` holds **only** what a developer changes. Every organizational fact —
address, phone, email, office hours, dues, external URLs — lives in
`data/organization.yaml` and nowhere else.

This is enforced at build time: `layouts/_partials/data/validate.html` fails the
build if contact fields reappear under `[params]`. A previous version of this
site stored the office email in two places and shipped `Dhoa@verizon.net` in one
of them.

### Deployment

Every push to `main` triggers `.github/workflows/deploy.yml`, which builds with
Hugo and publishes to GitHub Pages. Cloudflare provides DNS and the certificate
visitors see.

The `dhoa` record is proxied, which means GitHub never issues its own
certificate and the Cloudflare → GitHub hop is unauthenticated. That is a
deliberate tradeoff with one sharp edge — never tick **Enforce HTTPS** while
Cloudflare is on Flexible. See [docs/DECISIONS.md](docs/DECISIONS.md) #6.

---

## License

[MIT](LICENSE) for the site code. Association content, governing documents, and
photographs are the property of the Discovery Homeowners Association, Inc. and
their respective copyright holders.
