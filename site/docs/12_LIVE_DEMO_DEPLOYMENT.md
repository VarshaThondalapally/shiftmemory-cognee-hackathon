# Live Demo Deployment

Date: 2026-07-05

This repo is ready to run as one hosted web service: FastAPI serves the API and the built React app from the same origin.

## API Key Rule

Never put Cognee or Gemini keys in:

- GitHub Pages.
- React/Vite environment variables exposed to the browser.
- screenshots, videos, docs, or the hackathon form.

Keys belong only in backend server environment variables on the host.

## Recommended Host

Use Render or an equivalent Docker web-service host.

The included files are:

- `Dockerfile`: builds React, installs FastAPI, and serves both from one container.
- `render.yaml`: optional Render blueprint with non-secret defaults and secret variables marked `sync: false`.
- `.dockerignore`: excludes local env files, local memory cache, build artifacts, and dependency folders.

## Required Server Environment Variables

Set these in the host dashboard:

```text
MEMORY_BACKEND=cognee
COGNEE_BASE_URL=https://tenant-your-tenant-id.aws.cognee.ai
COGNEE_API_KEY=<set in host secret manager>
COGNEE_TENANT_ID=<set in host secret manager>
COGNEE_STRICT=true
COGNEE_DATASET_PREFIX=handoff-live-demo
COGNEE_ALLOW_LOCAL_RANK_FALLBACK=false
COGNEE_FAST_DEMO_RECALL=true
COGNEE_TIMEOUT_SECONDS=120
COGNEE_MAX_RETRIES=2
LLM_PROVIDER=gemini
GEMINI_API_KEY=<set in host secret manager>
GEMINI_MODEL=gemini-flash-lite-latest
LLM_STRICT=true
APP_ENV=demo
DEMO_SYNTHETIC_DATA_ONLY=true
JWT_SECRET=<host-generated random secret>
```

## Balance Protection

The public backend includes a lightweight per-IP rate limiter:

- `DEMO_RATE_LIMIT_WINDOW_SECONDS=600`
- `DEMO_RATE_LIMIT_API_REQUESTS=240`
- `DEMO_RATE_LIMIT_MUTATION_REQUESTS=60`

This is not enterprise abuse prevention. It is enough to keep a public hackathon demo from casually draining Cognee or Gemini credits.

## Deployment Flow

1. Push the repo to GitHub.
2. Create a Docker web service from the GitHub repo.
3. Set the server environment variables above in the host dashboard.
4. Deploy.
5. Open `/healthz` and confirm:
   - `memory.name` is `cognee-cloud`.
   - `memory.strict` is `true`.
   - `intelligence.name` is `gemini`.
6. Open `/` and run the demo with:
   - Night caregiver: `night-demo` / `demo`
   - Morning lead: `morning-demo` / `demo`
   - Supervisor: `supervisor-demo` / `demo`
   - Technical reviewer: `judge-demo` / `demo`

## Temporary Tunnel Option

If a permanent host is not available before submission, a Cloudflare quick tunnel can expose the local FastAPI server without putting keys in the browser.

This is acceptable only as a short-lived backup because the URL works only while the laptop, backend, and tunnel stay running.

Submitted stable live URL:

```text
https://varshathondalapally.github.io/shiftmemory-cognee-hackathon/live.html
```

Current quick-tunnel target:

```text
https://travels-makeup-founder-poems.trycloudflare.com
```

## Verified Locally

The secured smoke test was run against Cognee Cloud and Gemini after the deployment packaging changes:

```text
PASS: handoff memory demo lifecycle works end to end
```
