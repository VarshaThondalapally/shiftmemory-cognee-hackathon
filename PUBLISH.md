# Publish Guide

This folder is ready to become a GitHub repository and GitHub Pages site.

Local Git and GitHub CLI are not available in the current Codex environment, so the `.git` database was not initialized here. Run these commands on a machine with Git installed.

## Option A: GitHub CLI

```powershell
cd C:\Users\thond\Documents\Codex\2026-07-04\i\outputs\shiftmemory-hackathon-repo
git init -b main
git add .
git commit -m "Initial ShiftMemory hackathon packet"
gh repo create shiftmemory-cognee-hackathon --public --source=. --remote=origin --push
```

## Option B: GitHub Website

1. Create a new empty GitHub repository.
2. Do not add a README, license, or `.gitignore` from GitHub because this folder already has them.
3. Copy the repository URL.
4. Run:

```powershell
cd C:\Users\thond\Documents\Codex\2026-07-04\i\outputs\shiftmemory-hackathon-repo
git init -b main
git add .
git commit -m "Initial ShiftMemory hackathon packet"
git remote add origin https://github.com/<owner>/<repo>.git
git push -u origin main
```

## Enable GitHub Pages

1. Open the repository on GitHub.
2. Go to Settings.
3. Open Pages.
4. Set Source to GitHub Actions.
5. Open Actions.
6. Run `Deploy GitHub Pages site`.

The workflow publishes the `site/` directory.

## Recommended Repo Name

```text
shiftmemory-cognee-hackathon
```

## Recommended Description

```text
Cognee-backed persistent memory for secure shift handoffs across sessions, agents, and teams.
```

## Before Submitting

- Replace mock memory with real Cognee calls.
- Keep Cognee and LLM keys backend-only.
- Use synthetic data only.
- Confirm `remember`, `recall`, `improve`, and `forget` are visible in judge trace.
