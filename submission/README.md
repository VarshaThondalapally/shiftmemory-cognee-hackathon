# Hackathon Submission Packet

This folder is the final submission packet for the Cognee hackathon.

## What To Submit

- GitHub repo: `https://github.com/VarshaThondalapally/shiftmemory-cognee-hackathon`
- Landing page: `https://varshathondalapally.github.io/shiftmemory-cognee-hackathon/`
- Demo video file to upload to YouTube: `submission/video/caregiver-handoff-memory-demo.mp4`
- Submission form answers: [SUBMISSION_FORM_ANSWERS.md](SUBMISSION_FORM_ANSWERS.md)
- AI usage disclosure: [../handover/AI_USAGE_DISCLOSURE.md](../handover/AI_USAGE_DISCLOSURE.md)
- Demo narration: [DEMO_VIDEO_SCRIPT.md](DEMO_VIDEO_SCRIPT.md)
- Hosting decision: [LIVE_HOSTING_DECISION.md](LIVE_HOSTING_DECISION.md)

## Recommended Submission Strategy

Submit the public GitHub Pages landing page as the deployed link, the GitHub repository as the source link, and the uploaded YouTube video as the live proof.

The current MP4 is a real product walkthrough captured from the running React app against the local FastAPI backend with Cognee Cloud and Gemini active. It is not just a slide explainer.

Do not submit `localhost` as the deployed product. Localhost is useful for recording and local judging walkthroughs, but external reviewers cannot open it.

## Why We Are Not Rushing A Public Backend

The full product requires a hosted React frontend and a hosted FastAPI backend with Cognee and Gemini secrets in server environment variables.

GitHub Pages can host the landing page, but it cannot host the backend. A rushed live backend risks CORS failures, exposed keys, slow memory calls, and an unreliable reviewer experience.

For the current submission window, the strongest path is:

1. Public landing page.
2. Public GitHub repo.
3. Short YouTube demo showing the real local app flow.
4. Clear disclosure that the full interactive product currently runs locally unless deployed separately.

## Demo Claim

The demo should prove one sentence:

"A note saved by one care worker can be remembered, recalled with source, improved by a supervisor, and forgotten when stale, without the next worker pasting context again."
