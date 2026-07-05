# Live Hosting Decision

## Recommendation

Submit with a hosted FastAPI/React product URL if the deployment is verified before the deadline.

Also include:

- GitHub repository.
- GitHub Pages landing page.
- Demo video.
- Local runbook and AI usage disclosure.

## Submitted Live URL

`https://factors-needle-issued-partition.trycloudflare.com`

This is a Cloudflare quick tunnel to the local FastAPI/React app. Cognee and Gemini keys remain server-side in the backend process. The URL works only while the laptop, backend server, and tunnel process stay running.

## API Key Rule

Cognee and Gemini keys must stay server-side.

Do not put keys in:

- GitHub Pages.
- React/Vite browser env vars.
- form answers.
- screenshots or videos.
- repository files.

Use the host's environment-variable UI or secret manager.

## Current Deployment Readiness

The repo includes:

- `Dockerfile`: one service that builds React and serves it from FastAPI.
- `render.yaml`: Render blueprint with Cognee/Gemini secrets marked `sync: false`.
- `.dockerignore`: excludes local env files and local memory cache.
- same-origin frontend API fallback.
- JWT auth and role-based access control.
- public-demo rate limits to protect Cognee/Gemini balance.
- Cognee retry logic for transient transport/server failures.

## Backup If Hosting Is Not Finished

If a hosted backend cannot be verified in time, submit:

1. GitHub Pages landing page.
2. GitHub repo.
3. Demo video showing the real app flow.
4. Honest note that the interactive product is deploy-ready and was verified locally against Cognee Cloud and Gemini.

Do not submit `localhost`.
