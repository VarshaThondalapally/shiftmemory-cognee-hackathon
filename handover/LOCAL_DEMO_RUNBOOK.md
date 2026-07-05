# Local Demo Runbook

## URLs

- Product app: `http://127.0.0.1:5173/`
- Backend health: `http://127.0.0.1:8001/healthz`
- Public-style landing page: `http://127.0.0.1:8088/index.html`
- Demo runbook page: `http://127.0.0.1:8088/demo.html`

## Start Backend

```powershell
cd C:\Users\thond\Documents\Codex\2026-07-04\i\outputs\shiftmemory-hackathon-repo\apps\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Check:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/healthz
```

Expected final-mode health should show:

- `memory.backend`: `cognee-cloud`
- `memory.configured`: `true`
- `memory.strict`: `true`
- `intelligence.provider`: `gemini`
- `intelligence.strict`: `true`

## Start Frontend

```powershell
cd C:\Users\thond\Documents\Codex\2026-07-04\i\outputs\shiftmemory-hackathon-repo\apps\frontend
pnpm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173/
```

## Start Static Site

```powershell
cd C:\Users\thond\Documents\Codex\2026-07-04\i\outputs\shiftmemory-hackathon-repo\site
python -m http.server 8088 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:8088/index.html
http://127.0.0.1:8088/demo.html
```

## Demo Login Flow

1. Sign in as `Rosa Lee`.
   - Role: supervisor.
   - Show assigned care recipients.
   - Assign the night caregiver and morning lead.
   - Show that the supervisor sees controls that caregivers do not.

2. Sign out and sign in as `Nia Brooks`.
   - Role: night caregiver.
   - Show that she only sees assigned care recipients.
   - Add a note such as:

```text
At 3 AM Avery woke up twice, asked for water, and settled after the room was kept quiet. Morning worker should watch for tiredness before breakfast.
```

3. Refresh the browser.
   - The note should still be available through backend memory.

4. Sign out and sign in as `Omar Chen`.
   - Role: morning lead.
   - Generate the morning handoff.
   - Confirm the 3 AM note appears with a source.
   - Ask: `What should I tell the family?`

5. Sign out and sign in as `Rosa Lee`.
   - Mark the 3 AM note important.
   - Remove a stale note if present.
   - Generate another handoff and confirm the changed memory behavior.

6. Sign in as `Hackathon Judge`.
   - Open proof mode.
   - Show memory backend, reasoning layer, source IDs, and redacted traces.

## What To Say During Demo

"The worker does not use Cognee directly. They do normal shift work. Cognee is the memory layer behind the backend. The proof is that a note saved by one role can be recalled later by another role, cited to its source, improved by supervisor feedback, and removed from future answers."

## Troubleshooting

- If the UI looks stale, use `Ctrl+F5`.
- If the wrong role is visible, sign out and sign in again.
- If a caregiver cannot access a patient, check supervisor assignments.
- If a request returns `403`, that is expected when the role is not allowed to perform the action.
- Cognee Cloud calls can be slower than local memory. Wait for the backend response before clicking again.
- If proof mode says local demo memory is active, check the backend `.env` and `/healthz`.

## Important Demo Boundary

Do not present this as production healthcare software. Present it as a hackathon MVP proving persistent, source-backed memory for shift handoffs.
