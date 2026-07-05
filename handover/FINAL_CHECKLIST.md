# Final Submission Checklist

## Done

- Repository created and pushed to GitHub.
- GitHub Pages landing page created.
- Product reframed around a real care-handoff workflow.
- JWT demo authentication added.
- Role-based access control added.
- Assigned care-recipient filtering added.
- Supervisor assignment dashboard added.
- Night caregiver, morning lead, supervisor, and proof workspaces separated.
- Cognee Cloud final-mode configuration added.
- Gemini final-mode configuration added.
- Proof mode added for memory lifecycle inspection.
- README updated with final architecture.
- Landing page and runbook updated.
- AI usage disclosure included in this handover bundle.

## Locally Verified

- Product app loads at `http://127.0.0.1:5173/`.
- Static landing page loads at `http://127.0.0.1:8088/index.html`.
- Demo runbook loads at `http://127.0.0.1:8088/demo.html`.
- Backend health reports Cognee/Gemini final-mode configuration when keys are present.
- Supervisor login opens assignment dashboard.
- Night caregiver sees assigned patients only.
- Morning lead sees handoff workflow only.
- Demo reviewer can inspect all workspaces and proof mode.

## Needs Final Human Decision

- Decide whether to submit the local interactive app plus GitHub Pages, or deploy the full frontend/backend publicly.
- Upload the replacement real product-flow video at `submission/video/caregiver-handoff-memory-demo.mp4` to YouTube as unlisted and paste that URL in the form.
- Confirm the final submitted title. Recommended: `Caregiver Handoff Memory`.
- Confirm no secrets are committed before final submission.

## Honest Risk Notes

- Public GitHub Pages is a presentation site, not the full interactive backend app.
- Full public live access requires hosting the FastAPI backend and React frontend on a service such as Render, Railway, Fly.io, Vercel plus backend host, or similar.
- The current app is a hackathon MVP. It is not production healthcare software.
- Demo auth is not production auth.
- Demo data is synthetic.

## Final Demo Standard

The demo should prove this sentence:

"A note saved by one care worker can be remembered, recalled with source, improved by a supervisor, and forgotten when stale, without the next worker pasting context again."
