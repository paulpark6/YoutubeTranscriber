---
name: youtube-transcript-api version and API surface
description: Key facts about the youtube-transcript-api library version installed in this project
type: project
---

Installed version: 1.2.3 (latest as of 2026-03-21 is 1.2.4; 0.6.3 does not exist).

**API surface used:**
- `api = YouTubeTranscriptApi()` then `api.fetch(video_id=..., languages=[lang])` — returns `FetchedTranscript` (iterable of segment objects)
- Segment objects have `.start` (float), `.text` (str), `.duration` (float)
- Error classes live in `youtube_transcript_api._errors`: `NoTranscriptFound(video_id, language_codes, transcript_data)`, `TranscriptsDisabled(video_id)`, `VideoUnavailable(video_id)`
- `NoTranscriptFound` third arg (`transcript_data`) accepts a `MagicMock()` in tests — it is a `TranscriptList`, not a plain dict

**Why:** The library changed significantly from 0.x to 1.x. This note prevents regressing to the wrong API pattern.

**How to apply:** Always check this when writing or updating transcript service code or tests.
