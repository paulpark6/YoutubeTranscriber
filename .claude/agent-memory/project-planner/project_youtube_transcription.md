---
name: YouTube Transcription project overview
description: Core decisions and architecture for the YouTube Transcription web app -- FastAPI backend, React frontend, batch support, deployment-ready config
type: project
---

YouTube Transcription web app -- replaces a CLI script with a full-stack app (FastAPI + React/Vite/TS).

Key decisions made 2026-03-21:
- Batch URL support from day 1 (ZIP for multiple, .txt for single)
- Timestamps optional (default ON), language selectable (default English)
- All config via env vars -- no hardcoded localhost URLs
- Phase 1: core web app. Phase 2: topic search (YouTube Data API). Phase 3: Supabase integration.
- Original `transcribe.py` kept for reference, not modified.

**Why:** User wants to go from local CLI tool to a hosted web app incrementally. Structured for deployment from the start to avoid refactoring later.

**How to apply:** All planning docs live in `/mdfiles/`. Backend and frontend agents should always read `AGENT_INSTRUCTIONS.md` before starting work. Check that code matches `PROJECT_STRUCTURE.md` after each build phase.
