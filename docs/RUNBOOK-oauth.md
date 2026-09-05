# Runbook: sign-in for the admin panel

Board members edit the site at **https://discoveryhomeowners.com/admin/** by clicking
**Login with GitHub**. Nobody handles an access token.

Making that work needs one small piece of infrastructure: a Cloudflare Worker
that relays the GitHub OAuth handshake. It is free, it is about thirty lines of
someone else's code, and once it is set up it needs no maintenance.

**This is a do-once job, about twenty minutes.**

---

## Before you start

Decide **who owns this**. The GitHub OAuth App and the Cloudflare Worker should
belong to the **organization**, not to an individual's personal account. A board
changes; a personal account leaves with the person. Record the answer at the
bottom of this file.

---

## 1. Deploy the Worker

The Worker is [`sveltia/sveltia-cms-auth`](https://github.com/sveltia/sveltia-cms-auth).
Clone it somewhere **outside this repository** — it is not part of the website,
and keeping it out is what preserves "the site builds with Hugo alone".

```bash
git clone https://github.com/sveltia/sveltia-cms-auth
cd sveltia-cms-auth
npx wrangler login
npx wrangler deploy
```

There is also a one-click "Deploy to Cloudflare Workers" button in that repo's
README if you would rather not use the command line.

## 2. Write down the Worker URL

It looks like:

```
https://sveltia-cms-auth.SOMETHING.workers.dev
```

Everything below needs it.

## 3. Create the GitHub OAuth App

Go to the **organization's** settings — Organization → Settings → Developer
settings → OAuth Apps → New OAuth App. (A personal app at
`github.com/settings/applications/new` also works, but see "Before you start".)

| Field | Value |
|---|---|
| Application name | `Discovery HOA Content Manager` |
| Homepage URL | `https://discoveryhomeowners.com/` |
| Authorization callback URL | `<WORKER_URL>/callback` |

**The `/callback` suffix is required.** Leaving it off is the single most common
cause of the error in step 8.

## 4. Generate a client secret

Copy both the **Client ID** and the **Client Secret** now. GitHub shows the
secret exactly once.

## 5. Give the Worker its credentials

Cloudflare dashboard → Workers & Pages → `sveltia-cms-auth` → Settings →
Variables and Secrets:

| Name | Value | Notes |
|---|---|---|
| `GITHUB_CLIENT_ID` | the Client ID | plain text |
| `GITHUB_CLIENT_SECRET` | the Client Secret | **press Encrypt** |
| `ALLOWED_DOMAINS` | `discoveryhomeowners.com` | comma-separated; wildcards allowed |

> **This value lives in Cloudflare, not in this repository.** Changing the table
> above changes documentation only. The Worker keeps its own copy of
> `ALLOWED_DOMAINS`, and it still holds the retired development hostname until
> somebody updates it in the Cloudflare dashboard. Until then `/admin/` sign-in
> will fail on the new hostname with the popup closing and nothing happening —
> see the troubleshooting table at the end of this runbook.
>
> The same applies to the GitHub OAuth App's Homepage and Authorization callback
> URLs, which are set on github.com rather than here.

Do **not** set `GITHUB_HOSTNAME` — that is only for GitHub Enterprise Server.

Then redeploy so the variables take effect.

## 6. Point the CMS at the Worker

In [`static/admin/config.yml`](../static/admin/config.yml), replace the
placeholder:

```yaml
backend:
  base_url: https://sveltia-cms-auth.SOMETHING.workers.dev
```

No trailing slash, and **no `/callback`** — that belongs only in the GitHub app
settings. Commit and let the site deploy.

## 7. Give each editor access

Every board member who will edit the site needs, in order:

1. a GitHub account,
2. membership of the `Discovery-Homeowners-Association-Inc` organization,
3. **Write** permission on this repository.

Nothing else. They do not need to install anything or learn git.

## 8. Test it

Open `https://discoveryhomeowners.com/admin/` in a private window. You should get a
GitHub consent screen, then land in the CMS with the collections listed.

Make a trivial edit — change the tagline — press Publish, and check that a
commit appears on `main` and the deploy runs.

### If it does not work

| What you see | What it means |
|---|---|
| "Redirect URI mismatch" | The callback URL in step 3 is not exactly `<WORKER_URL>/callback` |
| The popup closes and nothing happens | The hostname you are on is not in `ALLOWED_DOMAINS` |
| You sign in but see no collections | `backend.repo` is wrong, or the user lacks **Write** on the repo |
| Worker returns 500 | `GITHUB_CLIENT_SECRET` is unset, or set on the wrong environment |

---

## Upgrading Sveltia CMS

The CMS is pinned to an exact version with a Subresource Integrity hash in
[`static/admin/index.html`](../static/admin/index.html). That script is granted
write access to this repository, so it is deliberately not tracking `@latest`.

To upgrade:

```bash
VERSION=0.185.0   # whatever the new release is
curl -sL "https://unpkg.com/@sveltia/cms@$VERSION/dist/sveltia-cms.js" \
  | openssl dgst -sha384 -binary | openssl base64 -A
```

Put the new version and hash in `static/admin/index.html`, then open `/admin/`
and confirm it still loads **before** committing. If the hash is wrong the
browser refuses to run the file and the admin panel is simply blank.

---

## Custody

Fill this in and keep it current. This is a bus-factor record.

| Thing | Who owns it | Where it lives |
|---|---|---|
| GitHub OAuth App | _to be completed_ | |
| Cloudflare account running the Worker | _to be completed_ | |
| Worker URL | _to be completed_ | |
| Who holds the client secret | _to be completed_ | |
| Domain registrar / DNS | _to be completed_ | |
