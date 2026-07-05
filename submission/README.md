# Hackathon Submission Packet

This folder is the final submission packet for the Cognee hackathon.

## What To Submit

- GitHub repo: `https://github.com/VarshaThondalapally/shiftmemory-cognee-hackathon`
- Landing page: `https://varshathondalapally.github.io/shiftmemory-cognee-hackathon/`
- Live product URL submitted: `https://factors-needle-issued-partition.trycloudflare.com`
- Demo video file to upload to YouTube: `submission/video/caregiver-handoff-memory-demo.mp4`
- Submission form answers: [SUBMISSION_FORM_ANSWERS.md](SUBMISSION_FORM_ANSWERS.md)
- AI usage disclosure: [../handover/AI_USAGE_DISCLOSURE.md](../handover/AI_USAGE_DISCLOSURE.md)
- Demo narration: [DEMO_VIDEO_SCRIPT.md](DEMO_VIDEO_SCRIPT.md)
- Hosting decision: [LIVE_HOSTING_DECISION.md](LIVE_HOSTING_DECISION.md)

## Recommended Submission Strategy

Submit the hosted FastAPI/React product URL as the deployed link if it is live before the deadline. Submit the GitHub repository as the source link, the GitHub Pages landing page as the explainer link, and the uploaded YouTube video as the walkthrough proof.

The current MP4 is a real product walkthrough captured from the running React app against the local FastAPI backend with Cognee Cloud and Gemini active. It is not just a slide explainer.

Do not submit `localhost` as the deployed product. Localhost is useful for recording and local walkthroughs, but external reviewers cannot open it.

## Live Backend Status

The repo now includes a deployable Docker service:

- `Dockerfile` builds the React app and serves it from FastAPI.
- `render.yaml` marks Cognee and Gemini keys as host-only secrets.
- The backend includes JWT auth, role-based access, Cognee/Gemini strict mode, redacted traces, and demo rate limits.

If the hosted deployment is not complete before the deadline, the backup path is:

1. Public landing page.
2. Public GitHub repo.
3. Short YouTube demo showing the real app flow.
4. Clear disclosure that the full interactive product is deploy-ready and was verified locally against Cognee Cloud and Gemini.

## Demo Claim

The demo should prove one sentence:

"A note saved by one care worker can be remembered, recalled with source, improved by a supervisor, and forgotten when stale, without the next worker pasting context again."
