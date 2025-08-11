# Fleet Commander

Quickstart
- Set env vars: `GITHUB_WEBHOOK_SECRET` and one of `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`. Optional: `VERCEL_TOKEN`, `GITHUB_TOKEN`.
- Run: `uvicorn api:app --reload`
- Health: GET `/health` for env hints.
- Configure GitHub webhook to POST `/webhook/github` with your secret.
- On push, you’ll get `{ ok, deployment_id }`. Connect WS `/ws/status?deployment_id=...` to watch.
- Replay: GET `/replay/{id}` or POST `/replay/{id}/broadcast?speed=1.0`.

What it does
- Clones repo at pushed commit → runs agents → deploys (Vercel when enabled) → monitors health.
- Logs agent steps (prompts, tool calls, outputs) for replay and compliance.

Setup docs: see `docs/SETUP.md` for environment variables (Gmail, MongoDB, GitHub, Vercel) and webhook configuration.

<img width="5088" height="3696" alt="image" src="https://github.com/user-attachments/assets/131feae9-ac68-44b2-a3b5-518434257218" />
