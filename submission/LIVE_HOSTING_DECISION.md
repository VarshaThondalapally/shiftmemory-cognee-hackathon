# Live Hosting Decision

## Recommendation

Submit with:

- GitHub repository.
- GitHub Pages landing page.
- YouTube demo video.
- Local demo runbook.

Do not rush a public backend unless there is enough time to deploy and verify it carefully.

## Why

The interactive app depends on a FastAPI backend. That backend holds Cognee and Gemini API keys, performs role checks, and calls the memory layer.

GitHub Pages can host static files only. It cannot securely run the backend.

## What A Real Public Deployment Needs

- Hosted React frontend.
- Hosted FastAPI backend.
- Server-side environment variables for Cognee and Gemini keys.
- CORS restricted to the frontend domain.
- HTTPS.
- Rate limits.
- Logs and error tracing.
- Secret rotation.
- Health check endpoint exposed to the host.

## Fast Deployment Options

- Frontend: Vercel, Netlify, or GitHub Pages.
- Backend: Render, Railway, Fly.io, Azure App Service, or Google Cloud Run.
- Secrets: host-managed environment variables.

## Current Honest Statement

"The public link is the landing and demo explainer. The full interactive product runs locally with a FastAPI backend because Cognee and Gemini keys must remain server-side."
