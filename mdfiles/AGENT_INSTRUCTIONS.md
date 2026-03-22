# Agent Instructions -- Phase 1 Build

**Last updated:** 2026-03-21

Read `PROJECT_PLAN.md` for the full spec and `PROJECT_STRUCTURE.md` for where files go before you start.

---

## Backend Engineer

### Task: Build the FastAPI backend from scratch

**Priority order -- build in this sequence:**

1. **Project scaffold**
   - Create `backend/` folder structure as defined in `PROJECT_STRUCTURE.md`
   - Write `requirements.txt` with all dependencies
   - Write `.env.example`
   - Write `config.py` using `pydantic-settings` to load `CORS_ORIGINS` and `PORT` from env

2. **URL parser** (`backend/app/services/url_parser.py`)
   - Function: `parse_video_id(url: str) -> str`
   - Must handle: `youtube.com/watch?v=`, `youtu.be/`, `youtube.com/shorts/`, raw 11-char video ID
   - Raise `ValueError` with a clear message for invalid URLs
   - Write tests in `backend/tests/test_url_parser.py` covering all formats + invalid inputs

3. **Transcript service** (`backend/app/services/transcript.py`)
   - Function: `fetch_transcript(video_id: str, language: str = "en") -> list[dict]`
     - Uses `youtube-transcript-api` to fetch transcript
     - Returns raw transcript data (list of segments with `start` and `text`)
   - Function: `format_transcript(segments: list, include_timestamps: bool = True) -> str`
     - If `include_timestamps=True`: format as `[MM:SS] text`
     - If `include_timestamps=False`: just the text, one line per segment
   - Function: `sanitize_filename(name: str) -> str`
     - Strip or replace characters not safe for filenames
   - Function: `build_zip(files: dict[str, str]) -> bytes`
     - Takes a dict of `{filename: content}`, returns ZIP bytes in memory
   - Write tests in `backend/tests/test_transcript_service.py`
     - Mock `youtube-transcript-api` -- do not hit YouTube in tests

4. **Pydantic schemas** (`backend/app/schemas/transcript.py`)
   - `TranscriptRequest`: `urls: list[str]`, `include_timestamps: bool = True`, `language: str = "en"`, `filename: str | None = None`
   - No response schema needed (response is a file download)

5. **Router** (`backend/app/routers/transcript.py`)
   - `POST /api/transcript`
   - Parse each URL, fetch transcript, format it
   - Single URL: return `StreamingResponse` with `.txt` file
   - Multiple URLs: return `StreamingResponse` with `.zip` file
   - Partial failure: include `_errors.txt` in the ZIP
   - All failure: return HTTP 400 with JSON error body
   - Write integration tests in `backend/tests/test_transcript_router.py` using `TestClient`

6. **Main app** (`backend/app/main.py`)
   - Create FastAPI instance
   - Add CORS middleware using `CORS_ORIGINS` from config
   - Register the transcript router

**Important rules:**
- No hardcoded URLs or ports -- everything from env vars
- Use `async` endpoint handlers
- Reference the existing `transcribe.py` for the transcript formatting logic (the `format_time` function and fetch pattern)
- All error messages should be user-friendly, not raw stack traces

---

## Frontend Engineer

### Task: Build the React + Vite + TypeScript frontend

**Priority order -- build in this sequence:**

1. **Project scaffold**
   - Initialize with `npm create vite@latest` (React + TypeScript template)
   - Set up `vite.config.ts` with dev proxy to backend (`/api` -> `http://localhost:8000`)
   - Write `.env.example` with `VITE_API_URL`
   - Clean out default Vite boilerplate

2. **API client** (`frontend/src/api/transcript.ts`)
   - Function: `downloadTranscript(params)` that POSTs to `/api/transcript`
   - Must handle the response as a file download (create a blob URL, trigger download)
   - Read `VITE_API_URL` from env for the base URL
   - Return error information if the request fails

3. **TranscriptForm component** (`frontend/src/components/TranscriptForm.tsx`)
   - Textarea for URLs (placeholder: "Paste YouTube URLs here, one per line")
   - Text input for custom filename (only show when exactly one URL is entered)
   - Timestamps checkbox (default: checked)
   - Language dropdown (use `LanguageSelector` component)
   - Download button
   - On submit: call API client, show loading state, handle errors

4. **LanguageSelector component** (`frontend/src/components/LanguageSelector.tsx`)
   - Dropdown with common languages, default to English (`en`)
   - At minimum include: English, Spanish, French, German, Portuguese, Japanese, Korean, Chinese, Hindi, Arabic
   - Each option shows the language name with its code

5. **ErrorMessage component** (`frontend/src/components/ErrorMessage.tsx`)
   - Accepts error data (could be a single string or a list of per-video errors)
   - Renders error messages in a visible, non-intrusive way (red text, not alerts)

6. **LoadingSpinner component** (`frontend/src/components/LoadingSpinner.tsx`)
   - Simple spinner or loading indicator
   - Shown while the API request is in progress
   - Disable the form controls while loading

7. **App.tsx**
   - Clean layout with a title and the `TranscriptForm` component
   - Keep it simple -- no routing needed for Phase 1

8. **Tests** (`frontend/tests/TranscriptForm.test.tsx`)
   - Form renders all controls
   - Typing in textarea updates state
   - Checkbox toggles
   - Submit calls the API function with correct data
   - Mock fetch -- do not hit the real backend

**Important rules:**
- No hardcoded `localhost` URLs -- always use the env var
- Use controlled components for all form inputs
- No external UI library (no Material UI, Chakra, etc.) -- keep it simple with plain HTML/CSS for now
- TypeScript strict mode -- no `any` types

---

## Code Reviewer

### Task: Review all Phase 1 code before it is considered done

**Checklist:**

- [ ] Backend folder structure matches `PROJECT_STRUCTURE.md`
- [ ] Frontend folder structure matches `PROJECT_STRUCTURE.md`
- [ ] No hardcoded URLs or ports anywhere -- all from env vars
- [ ] URL parser handles all four formats listed in the plan
- [ ] Batch request with partial failures returns a ZIP with `_errors.txt`
- [ ] Single URL request returns `.txt`, not `.zip`
- [ ] `filename` field is only used for single-URL requests
- [ ] Timestamps toggle actually changes the output format
- [ ] Language parameter is passed through to `youtube-transcript-api`
- [ ] CORS middleware is configured from env var, not hardcoded
- [ ] Backend tests exist and pass (URL parser, service, router)
- [ ] Frontend tests exist and pass (form behavior)
- [ ] No `console.log` left in frontend code (except intentional error logging)
- [ ] No unused imports
- [ ] `.env.example` files exist in both `backend/` and `frontend/`
- [ ] The original `transcribe.py` is untouched

**Specific things to watch for:**
- The `youtube-transcript-api` package changed its API in recent versions -- verify the import pattern matches what the backend agent used
- Make sure the ZIP is built in memory, not written to disk
- Make sure file download works in the browser (blob URL approach, not window.open)
- Check that the frontend hides the custom filename field when multiple URLs are entered
