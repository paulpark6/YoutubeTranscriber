---
name: frontend_scaffold
description: Frontend scaffold built for YouTube Transcription Web App — stack, file locations, key decisions
type: project
---

React + Vite + TypeScript frontend was built at `frontend/` inside the repo root.

**Why:** Phase 1 of the project plan. Replaces the original `transcribe.py` CLI script with a full-stack web app.

**How to apply:** All future frontend work lives under `frontend/src/`. Components go in `frontend/src/components/`, API clients in `frontend/src/api/`, tests in `frontend/tests/`.

Key decisions made during scaffold:

- `vite.config.ts` proxies `/api` to `http://localhost:8000` (dev only). Production uses `VITE_API_URL` env var.
- `tsconfig.node.json` added alongside `tsconfig.json` — required by Vite's `moduleResolution: "bundler"` setup.
- Vitest configured inside `vite.config.ts` (not a separate config file) with `environment: 'jsdom'` and `setupFiles: ['./tests/setup.ts']`.
- `tests/setup.ts` imports `@testing-library/jest-dom` for DOM matchers.
- No external UI libraries — plain HTML/CSS with inline styles only.
- `downloadTranscript` in `api/transcript.ts` triggers a real browser file download via a blob URL anchor click; it never throws — errors are returned as `{ error }`.
