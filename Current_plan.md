# Current_plan.md — Pre-CI rollout work

Working doc for the conversation between Paul and the agent. The user writes issues here; the agent replies inline below each issue using the format `<issue-name> + AGENT_Response_<n>`. Resolved items get deleted by the user. This file is throwaway — delete it once the GitHub issues are filed and Testing & CI rollout #3 is unblocked. Once everything is confirmed, we will create new issues in github. As of right now talk to the user inside this file with the convention mentioned above.

Legend: `[x]` done · `[~]` in progress · `[ ]` not started

---

## Goal

All issues below must be completed (in written order) **before** GitHub issue **#3 Testing & CI rollout** is started. The agent should either (a) update issue #3 to depend on these, or (b) create new GitHub issues for each item below and link #3 as blocked-by. Recommendation will be discussed inline.

---
## Backend-issue1 — Resolve duplicate `transcript.py` filenames

Two files named `transcript.py` (possibly more) cause confusion:

- `backend/app/schemas/transcript.py`
- `backend/app/services/transcript.py`

**Files that must change (backend only):**

| # | File | Line | Current | New |
|---|---|---|---|---|
| 1 | `backend/app/schemas/transcript.py` | (whole file) | path: `backend/app/schemas/transcript.py` | rename to `backend/app/schemas/transcript_schema.py` |
| 2 | `backend/app/schemas/transcript.py` | 4 | `class TranscriptRequest(BaseModel):` | `class TranscriptSchema(BaseModel):` |
| 3 | `backend/app/routers/transcript.py` | 17 | `from app.schemas.transcript import TranscriptRequest` | `from app.schemas.transcript_schema import TranscriptSchema` |
| 4 | `backend/app/routers/transcript.py` | 32 | `async def post_transcript(request: TranscriptRequest) -> StreamingResponse:` | `async def post_transcript(request: TranscriptSchema) -> StreamingResponse:` |
Naming:
- `backend/app/schemas/transcript.py` → `transcript_schema.py` — change the class name `TranscriptSchema`. Make sure to edit dependent files too.
- `backend/app/services/transcript.py` → leave as is.

- [x] Done

### Backend-issue1 + AGENT_Response_1

Done. Dispatched `backend-agent` with the impact table from this file. Changes made:

- `git mv backend/app/schemas/transcript.py backend/app/schemas/transcript_schema.py` (history preserved).
- `backend/app/schemas/transcript_schema.py` line 4: `class TranscriptRequest` → `class TranscriptSchema`.
- `backend/app/routers/transcript.py` line 17: `from app.schemas.transcript import TranscriptRequest` → `from app.schemas.transcript_schema import TranscriptSchema`.
- `backend/app/routers/transcript.py` line 32: `request: TranscriptRequest` → `request: TranscriptSchema`.

Verification (re-run by the main session, not just the agent):

- `grep -rn "TranscriptRequest" backend/` → 0 hits.
- `grep -rn "app.schemas.transcript[^_]" backend/` → 0 hits (only `transcript_schema` matches now).
- `ls backend/app/schemas/` → `transcript_schema.py` (no `transcript.py`).
- `pytest`: **73 passed, 6 failed.** The 6 failures are all in `test_url_parser.py` and are **pre-existing** (confirmed by running against the original code before the rename — they test scheme-less URLs like `youtube.com/watch?v=…` without `https://`, which the parser doesn't handle). Unrelated to the rename. I'll note this as a candidate Backend-issue when we discuss issue2 — let me know if you want a separate item filed.

Out-of-scope notes:

- `frontend/src/api/transcript.ts` has a TypeScript interface also named `TranscriptRequest`. This is independent of the Python class — JSON-over-HTTP wire format isn't affected by Python class renames. Leaving it alone unless you want symmetry on both sides; flag if you do.

### Backend-issue1 + AGENT_Response_2

Two follow-up items from your inline NOTEs:

**1. "I don't see any changes locally — what happened here?"**

Changes are present locally. Confirmed with `git status` from repo root:

- `backend/app/schemas/transcript.py` is **deleted** (staged).
- `backend/app/schemas/transcript_schema.py` is **new** (staged).
- `backend/app/routers/transcript.py` is **modified** (unstaged — diff shows the import + type annotation update).
- `git diff --stat HEAD` shows the rename as `schemas/{transcript.py => transcript_schema.py}` (git detected it as a rename of one line).

`ls backend/app/schemas/` shows only `transcript_schema.py` (and `__init__.py` / `__pycache__`). The original `transcript.py` no longer exists on disk.

Likely reasons you weren't seeing it:
- IDE showing a stale buffer — try reloading the file tree (VS Code: `Cmd+Shift+P` → "Developer: Reload Window", or just close+reopen the schemas folder).
- You were looking at a different working directory.
- Nothing was committed yet — if you were checking GitHub, the change is local-only until you commit + push.

If after reloading the IDE you still don't see it, paste the output of `git status` and I'll dig further.

**2. "Change frontend so it's symmetric."**

Will dispatch `frontend-engineer` to rename:
- `TranscriptRequest` → `TranscriptSchema` in `frontend/src/api/transcript.ts` (and any other frontend file that imports it).

Doing that now. See `Backend-issue1 + AGENT_Response_3` below for the result.

### Backend-issue1 + AGENT_Response_3 — frontend symmetry rename

Done. Dispatched `frontend-engineer`. Result:

- **File changed:** `frontend/src/api/transcript.ts` — two edits (interface declaration and the param type annotation in the `downloadTranscript` signature).
- **No other frontend files** imported `TranscriptRequest`. `TranscriptForm.tsx` uses `downloadTranscript` without importing the type, so no further changes needed.
- **Vitest:** 8/8 passed.
- **`tsc --noEmit`:** clean, zero type errors.
- **Verification:** `grep -rn "TranscriptRequest" frontend/ backend/` → **0 hits anywhere in the repo.**

Backend and frontend are now symmetric on `TranscriptSchema`. No wire-format change — the request body JSON is unchanged.


---

## Backend-issue2 — Fix 6 pre-existing `test_url_parser.py` failures

These 6 tests were failing **before** the schema rename. Confirmed pre-existing by running pytest against the unchanged code prior to the rename. Captured here so they're tracked and fixed before the test-improvement work in Backend-issue3.

**Failing test cases (all parametrize entries of `test_real_url_extracts_expected_id`):**

| # | Input URL | Expected ID |
|---|---|---|
| 1 | `youtu.be/dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| 2 | `youtube.com/watch?v=dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| 3 | `www.youtube.com/watch?v=dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| 4 | `m.youtube.com/watch?v=dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| 5 | `music.youtube.com/watch?v=dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| 6 | `www.youtube.com/shorts/aQvpqlSiUIQ` | `aQvpqlSiUIQ` |

**What's happening:** all 6 inputs are **scheme-less** (no `http://` or `https://`). The parser uses `urllib.parse.urlparse(url)`, which only recognizes the hostname when a scheme is present. Without a scheme, `urlparse("youtube.com/watch?v=…")` returns `hostname = ""` and treats the whole string as a relative path. The function then falls through every hostname branch and hits the final `raise ValueError("Not a recognised YouTube URL...")` at `backend/app/services/url_parser.py:97`.

**Why it happened (NOT the rename):**
- The schema rename only touched `backend/app/schemas/` and one import + one type annotation in `backend/app/routers/transcript.py`. It did not touch `backend/app/services/url_parser.py` or `backend/tests/test_url_parser.py`.
- I ran the failing tests against `git stash`-ed original code (pre-rename) and got the **same 6 failures** with the same `ValueError` at the same line. The rename did not introduce these.
- These tests were likely added when someone expected `urlparse` to handle scheme-less inputs, but it doesn't.

**Proposed fix (for the future GitHub issue, not to apply now unless you say so):**
- In `parse_video_id`, before calling `urlparse`, detect scheme-less inputs that look like a URL (contain `/` or `.`) and prepend `https://`. Roughly:
  ```python
  if "://" not in url and ("/" in url or "." in url):
      url = "https://" + url
  ```
- Re-run the test file — all 6 should pass, and the existing 32 passing tests should stay green.
- Also worth adding parametrize cases for `http://...` (currently only `https://` and scheme-less are tested).

**Decision needed:** do you want me to fix this now (dispatch `backend-agent`) so the test suite is green before we tackle Backend-issue3, or do you want this only documented here and fixed in a dedicated GitHub issue later? My recommendation: **fix now**, because (a) it's a small, isolated change, (b) issue3 critiques the test suite and a green baseline makes that critique cleaner, and (c) it removes noise from CI when issue3 lands.

- [ ] Open

NOTE: tell me your decision (fix now / fix later) and I'll act.

---

## Backend-issue3 — Per-folder description md files

Need to review naming of backend files and document the structure. Create one md file **per folder** under `backend/` that describes:
### Detailed instructions
- One md per folder under `backend/`. Initial set based on current tree:
  - `backend_description.md` — covers `backend/` (top-level: `app/`, `tests/`, plus any config files like `requirements.txt`, `pytest.ini`, etc.)
  - `backend_app_description.md` — covers `backend/app/` (subfolders `routers/`, `schemas/`, `services/`; files `__init__.py`, `config.py`, `main.py`)
  - `backend_app_routers_description.md` — covers `backend/app/routers/` and files under this folder
  - `backend_app_schemas_description.md` — covers `backend/app/schemas/` and files under this folder
  - `backend_app_services_description.md` — covers `backend/app/services/` and files under this folder
  - `backend_tests_description.md` — covers `backend/tests/` (if it has subfolders, one md per subfolder too). For the tests, write what it is currently testing, write any flaws, use /TDD agent to help you come up with limitations and what is wrong with current apporach and how to make it better. Once you get a response from /TDD agent, create other issues for each python tests in the folder. So the title should be the file name and fix. Each section for that issue should talk about current limitations, what is wrong with current apporach, what it is not testing, and how to improve testing. Also make sure no hardcoded values in test. Write this like the backend-issue-<name_of_test_file> no need for numbers. Just for the tests not the other files. For this you are not creating a new md file, you are editing this current_plan.md file and adding new issues at the very end for each python file.
### What to include in md files.
- what the folder is
- what subfolders it contains, also a brief description about the subfolder (should be around one sentence)
- what python (or other non-temporary) files it has
- for each python (or other non-temporary) file: write down what it does, who depends on it...etc
- for each function: name, parameters, type hints (if exists), default values (if exists), purpose, what it inherits, who calls it / why, the effect (what it does), and a use case, write down limitations too.
Plan for the docs:

- Per-function entry format (proposed, short):
  - **`func_name(param: Type = default) -> ReturnType`**
  - Purpose: one line or more if needed
  - Inherits / called by: one line (or "—" if standalone).
  - Effect: one line or more if needed.
  - Use case: one line or more if needed.
- Where do these md files live? Two options:
  1. Inside the folder they describe (e.g. `backend/app/backend_app_description.md`). Pro: co-located, easy to find while reading code. Con: clutters source folders.
Keep descriptions short, clean, concise.

**Naming convention:** `RelativeFolderName_description.md`. Example: for `backend/app/`, file is `backend_app_description.md`. It should explain that `routers/`, `schemas/`, `services/` are subfolders, and document `__init__.py`, `config.py`, `main.py`. Then a separate `backend_app_schemas_description.md` for `backend/app/schemas/`, and so on for every folder that has non-temporary files.

- [x] Done

### Backend-issue3 + AGENT_Response_2 — execution complete

Description md files created (all co-located inside their folder):

- `backend/backend_description.md`
- `backend/app/backend_app_description.md`
- `backend/app/routers/backend_app_routers_description.md`
- `backend/app/schemas/backend_app_schemas_description.md`
- `backend/app/services/backend_app_services_description.md` *(documents all 4 service modules: `url_parser`, `transcript`, `transcript_format`, `zip_builder`)*
- `backend/tests/backend_tests_description.md`

Each one follows the format you approved: folder purpose → subfolders w/ one-line description → files w/ description + dependents → per-function entries (`name(params: Types = defaults) -> ReturnType`, Purpose / Inherits / called by / Effect / Use case / Limitations). Empty `__init__.py` files are noted as "empty package marker — no exports."

Code-reviewer was dispatched against `backend/tests/`. Findings appended below as 3 new issues at the end of this file: `Backend-issue-test_url_parser`, `Backend-issue-test_transcript_service`, `Backend-issue-test_transcript_router`.

Note: per your "two separate issues" instruction for `test_url_parser.py`, the **parser bug** itself (the 6 scheme-less failures) is already filed as **Backend-issue2** at the top of this file. The new `Backend-issue-test_url_parser` covers **test-quality improvements** (xfail markers, embed error path, weak assertions, hardcoded values). They're complementary — fix the parser in issue2, harden the tests in `Backend-issue-test_url_parser`.

### Backend-issue3 + AGENT_Response_1 — discussion before I start

Before I write any docs, a few things to lock down. Please answer inline below each numbered question.

**1. Scope of test files to spin out as new issues.**
Current `backend/tests/` contents (need your call on each):

- `test_url_parser.py` — *also* has 6 currently-failing tests for scheme-less URLs (see Backend-issue1 response). Two ways to handle:
  - (a) one issue covering both "improve coverage / hardcoded values" AND "fix the 6 pre-existing failures", or
  - (b) two separate issues: one for test improvements, one specifically for the parser bug.
- `test_transcript_service.py` (or whatever the services tests are named — I'll list real filenames after I `ls` the folder, but assume one issue per test file).
NOTE: create multiple issues, multiples for test improvments and one specifically for the parser bug.

- `test_zip_builder.py`
- `test_routers_transcript.py` (integration test for the endpoint)
- Any conftest / fixtures file — usually not its own issue.

**Question 1a:** confirm "one new issue per test file in `backend/tests/`" — or do you want me to also include any non-test files (e.g. `conftest.py`)? I'd say tests only.
NOTE: Test only, so new issues per test file only

**Question 1b:** for `test_url_parser.py`, do you want option (a) one combined issue or (b) two separate issues?
NOTE: TWO Separate issues

**2. Where the test issues live in this file.**
Your spec says "adding new issues at the very end for each python file." I'll add a new section at the very bottom titled `## Test-improvement issues (appended)` and put each one underneath as `### Backend-issue-<test_file_name_without_extension>` (e.g. `### Backend-issue-test_url_parser`). Each will have the sub-sections you specified:

- Current limitations
- What's wrong with current approach
- What it is not testing
- How to improve testing
- Hardcoded values check (list any found)

NOTE: GOOD JOB, proceed

**Question 2:** confirm naming `Backend-issue-test_url_parser` (keeps the `test_` prefix from the filename) — or strip it and use `Backend-issue-url_parser`? I'd lean keep-the-prefix, so the filename and issue title match 1:1.
NOTE: keep prefix

**3. TDD skill input.**
The `tdd` skill is described as "Follow strict TDD for *this* task" — it's a workflow skill, not a code-review skill. It won't critique existing tests; it drives writing new code test-first. So invoking it on existing test files isn't quite the right tool.
NOTE: ok dont use that.

**Question 3:** two options:
- (a) I do the test critique myself by reading each test file, listing what's tested vs. not tested, flagging hardcoded values, and proposing improvements. I can be thorough — I just won't get a second opinion.
- (b) I dispatch the `code-reviewer` agent on `backend/tests/` with a prompt to critique coverage, hardcoded values, brittleness, and missing edge cases. That's actually the agent shaped for this job.

I'd lean **(b)** — `code-reviewer` is the right tool. Confirm.
NOTE: yes use code-reviewer, I allow you to use it.

**4. Doc location for Backend-issue2 md files.**
You left option 1 (co-located in each folder) in the file but didn't explicitly confirm. Just want to lock it: each md file lives inside the folder it describes (e.g. `backend/app/backend_app_description.md`, `backend/app/services/backend_app_services_description.md`). Confirm.
NOTE: yes confirmed

**5. Handling `__init__.py`.**
Most `__init__.py` files in this project are empty. I'll list them in the parent folder's md as "empty package marker — no exports" rather than giving them their own entry. Confirm.
NOTE: yes confirmed.

**6. Order of work for Backend-issue3.**
Proposed sequence once you've answered 1–5:
1. Write the 6 description md files (one per folder).
2. Run `code-reviewer` over `backend/tests/`.
3. Append the per-test-file issues at the bottom of `Current_plan.md`.
4. Check the Backend-issue3 box and remove its NOTE line.

Tell me to proceed (and answer the questions above) and I'll execute in one go.
NOTE: Proceeed if you dont have any more questions.
---

## Test-improvement issues (appended)

These were generated from a `code-reviewer` pass over `backend/tests/`. One issue per test file. Each will become its own GitHub issue when we batch-create. **Backend-issue2** (the parser bug) is separate from `Backend-issue-test_url_parser` (test improvements only).

---

### Backend-issue-test_url_parser

#### Current limitations

- The 6 scheme-less cases (`youtu.be/dQw4w9WgXcQ`, `youtube.com/watch?v=...`, `www.youtube.com/watch?v=...`, `m.youtube.com/watch?v=...`, `music.youtube.com/watch?v=...`, `www.youtube.com/shorts/...`) are in `REAL_URLS` and currently fail. They are real runtime failures (the bug is tracked in **Backend-issue2**) but they are not marked `@pytest.mark.xfail`, so CI sees them as red regressions instead of documented known gaps.
- The `embed` happy path is tested but the `embed` error path is not. The parser falls through silently on a malformed embed URL because the embed branch lacks a final `raise` after the validity check fails — undetected by tests.
- No test that `https://www.youtube.com/embed/tooshort` raises a useful, specific error.

#### What's wrong with current approach

- Failing-by-design entries should be marked `@pytest.mark.xfail(strict=True, reason="...")` or moved to a separate `SCHEME_LESS_URLS` table with that mark. Mixing them unmarked into `REAL_URLS` pollutes CI and hides genuine regressions.
- `INVALID_URLS` rows with empty expected substring (`""`) provide no message contract. Any `ValueError` passes — including a misleading one. At minimum these should assert the message does not contain a valid-looking 11-char video ID (guard against false positives).
- The "garbage with 11-char ID buried inside" comment ("must NOT be scraped out") is slightly misleading: the protection comes from the raw-ID gate (`_is_valid_video_id`), not from any anti-scraping logic.

#### What it is not testing

- 6 scheme-less URL formats (covered separately in Backend-issue2 — tests need xfail markers regardless).
- Embed error path (`/embed/tooshort` → expected message containing `"embed"`).
- `https://youtu.be/` (empty path).
- All-uppercase 11-char ID.
- `?si=` tracking param on a `watch` URL (only tested for `youtu.be`).
- Tab-only / newline-only inputs.
- The `except Exception` branch around `urlparse` is dead code in CPython — no test confirms behavior.

#### How to improve testing

- Add `@pytest.mark.xfail(strict=True, reason="scheme-less URLs: known bug — see Backend-issue2")` to the 6 scheme-less entries (or extract them into a `SCHEME_LESS_URLS` table with that mark applied at the parametrize level).
- Add `INVALID_URLS` rows: `("https://www.youtube.com/embed/tooshort", "embed")` and `("https://youtu.be/", "youtu.be URL")`.
- Replace empty-substring rows with at least `"not a recognised"` / `"unrecognised"` to give assertions teeth.
- Add a parametrized `watch?v=...&si=...` row.
- Define `_RICK_ROLL_ID = "dQw4w9WgXcQ"` at module level and reference it from the 9 rows that currently inline it.

#### Hardcoded values check

- `"dQw4w9WgXcQ"` — repeated 9× in `REAL_URLS`. Extract to module-level constant `_RICK_ROLL_ID`.
- `"PLxyz"` — appears in 2 rows. Optional constant `_FAKE_PLAYLIST = "PLxyz"`.
- `"9bZkp7q19f0"`, `"N5Zk-xH1e0k"`, `"8vIDZO_w7lY"`, `"aQvpqlSiUIQ"`, `"xS-fX-CL3Ys"`, `"abc-def_ghi"` — each appears once; leave inline unless the table grows.

---

### Backend-issue-test_transcript_service

#### Current limitations

- `_setup_fetch_mock` does not assert `list(video_id)` is called with the right `video_id`. A refactor that swaps argument positions would not be caught.
- `test_raises_value_error_on_no_transcript_found` raises `NoTranscriptFound` from `.fetch()`, but the real library raises it from `find_transcript()` or its internal resolution. The test passes for the right reason (the `except` clause catches it anywhere in the chain) but the mock does not faithfully model real call order — silent drift if the library's exception layer changes.
- `test_only_illegal_chars_falls_back` asserts only `len(result) > 0`. The implementation produces exactly `"transcript"` for input `'<>:"/\\|?*'` — the assertion should be `result == "transcript"`.
- `test_strips_leading_trailing_underscores_and_dots` only tests the underscore side, not the dot side. Leading dots create hidden files on Unix — important to test (`".hidden"`, `"...name..."`).
- `format_transcript`, `sanitize_filename`, and `build_zip` tests live in this file, but they test 3 different modules (`transcript_format.py`, `transcript.py`, `zip_builder.py`). The file docstring says "Unit tests for `transcript.py`" — misleading.

#### What's wrong with current approach

- Mock chain duplication: `_setup_fetch_mock` (this file) and `_setup_mock` (router test) wire the same 4-level mock differently. Should be a shared fixture in `conftest.py`.
- No contract / smoke test against the real `youtube-transcript-api`. A library major-version bump that changes `api.list(video_id).find_transcript(...)` would silently keep mocks green while breaking production. A single `@pytest.mark.integration`-gated real-library call (against a known public video) catches this class of breakage.
- Exception types imported inside test methods (`from youtube_transcript_api._errors import NoTranscriptFound`). Inconsistent with Python convention; move to module level.
- `build_zip` tests in this file should arguably be in a sibling `test_zip_builder.py`. Low priority but worth flagging.

#### What it is not testing

- `fetch_transcript("vid")` with **default language** (no `language` arg) — confirms it defaults to `"en"` and passes `["en"]` to `find_transcript`.
- `fetch_transcript` returning `[]` segments (empty transcript edge case).
- `sanitize_filename` with leading/trailing dots: `".hidden"`, `"name."`, `"...name..."`.
- `sanitize_filename` with `\t` or `\n` in input.
- `sanitize_filename` truncation at exactly 200 — pin `len(result) == 200` for ≥200-char input.
- `_format_time` >1h documented as intentional limitation rather than just an observed behavior. The current `[61:01]` assertion exists but is not marked as locking a known design choice (CLAUDE.md notes "no hours bucket" — link this in a comment or use `pytest.mark.xfail` if/when a hours bucket is intended).

#### How to improve testing

- Move all `_errors` imports to module level.
- Tighten `test_only_illegal_chars_falls_back` to `assert result == "transcript"`.
- Add `test_strips_leading_dot` and `test_strips_trailing_dot`.
- Add `test_fetch_transcript_default_language_is_en`.
- Add `test_fetch_transcript_returns_empty_list_for_empty_segments`.
- Add `assert_called_once_with(video_id)` on `mock_api_cls.return_value.list` to cover the missing arg-position assertion.
- Add an `@pytest.mark.integration` smoke test (real library, real public video) gated behind a `--run-integration` pytest flag or `PYTEST_INTEGRATION=1` env var.
- Move `_make_segment` to `conftest.py` as a fixture / factory helper.

#### Hardcoded values check

- `"dQw4w9WgXcQ"` — used here AND in router tests. Extract to `tests/constants.py` or a shared `conftest.py` constant: `RICK_ROLL_VIDEO_ID = "dQw4w9WgXcQ"`.
- `"vid"` — bare placeholder used in 4+ error-path tests. Extract to module-level `_FAKE_VIDEO_ID = "vid"` to avoid silent typos.
- Timestamp values `0.0`, `3.5`, `5.0`, `65.0`, `3661.0` — fine inline; `3661` already has an explanatory comment.
- `"my_video"`, `'vi<de>o: "name"'`, `"hello world"`, `"___name___"`, `"path/to/file"`, `'<>:"/\\|?*'`, `"a.txt"`, `"b.txt"`, etc. — single-use literals; fine as-is.

---

### Backend-issue-test_transcript_router

#### Current limitations

- `client` is `scope="session"`. App and client are shared across all tests. Currently safe (no test mutates `app`) but fragile: a future test that fails mid-request and leaves a mock partially configured would leak into the next test.
- `TestPartialFailure` uses `call_count` closures to differentiate first vs. second `find_transcript` calls. This is order-dependent — would silently break under concurrent URL processing or different parametrize ordering.
- `test_errors_txt_lists_failed_url` asserts `"9bZkp7q19f0" in errors_content or "youtu.be" in errors_content`. The `or` makes the assertion overly permissive — either condition alone passes, even if the errors file contained something unrelated.
- `test_returns_400_for_empty_urls` posts `{"urls": ["   ", "   "]}`. The router strips and skips, `successful` is empty, `errors` is also empty → 400 with `"No valid URLs provided."`. The test only checks status, not the message — under-tested semantics.
- `test_language_parameter_passed_through` asserts the mock call args but doesn't check `resp.status_code`. A 5xx response would still pass.

#### What's wrong with current approach

- **No CORS `expose_headers` test.** CLAUDE.md flags this as a key invariant ("`Content-Disposition` must be in expose_headers, otherwise the frontend cannot read the filename in browsers"). A misconfiguration in `main.py` would not be caught by these tests but would silently break production downloads. Single most likely production failure mode.
- `_setup_mock` and `_make_segment` duplicated across this file and `test_transcript_service.py`. Move to `conftest.py`.
- `content-type` assertion inconsistency: `test_returns_txt_file` uses `"text/plain" in ...` but `test_returns_zip_file` uses `== "application/zip"`. The exact-equality form will fail if FastAPI ever appends `; charset=...`. Use `in` for both.

#### What it is not testing

- **Duplicate-video-ID suffix logic** (`router.transcript:76-80`). Two identical URLs should produce `dQw4w9WgXcQ.txt` and `dQw4w9WgXcQ_1.txt` in the ZIP. Completely untested.
- **CORS `expose_headers` for `Content-Disposition`** (see above).
- **`filename` requiring sanitization** in a single-URL request: e.g., `{"filename": "my/bad:name"}`. Verify the response `Content-Disposition` has no `/` or `:` and no path traversal artifacts.
- **`filename` with path traversal**: `{"filename": "evil/path/../name"}`. Confirm `..` is stripped or replaced.
- **Malformed JSON body** with `Content-Type: application/json`. Should yield 422.
- **Mixed empty + valid URLs**: `["url1", "", "url2"]`. Router strips empties — confirm response is a 2-URL ZIP, not a 3-URL ZIP with an error entry.
- **Large URL list / long URL string**: no `max_length` on `urls`. A 10,000-URL request is currently accepted. Decide on a limit + add a test.
- **Invalid `language` codes**: `""`, `"zz-BOGUS"`. Confirm error surface (currently `NoTranscriptFound` from upstream).
- **`_errors.txt` content format**: only its presence is tested. The leading header line `"The following videos could not be transcribed:"` is not asserted.
- **`Content-Disposition` quoting** for filenames containing spaces (after sanitization, spaces become underscores so this is moot, but the test should pin it).

#### How to improve testing

- Add `test_duplicate_video_id_gets_suffixed` — POST two identical URLs, unzip, assert both `<id>.txt` and `<id>_1.txt` are in the archive.
- Add `test_cors_exposes_content_disposition` — inspect `app.user_middleware` or send a preflight `OPTIONS /api/transcript` with `Origin: http://localhost:5173` and verify `access-control-expose-headers` includes `Content-Disposition`.
- Replace the `or` in `test_errors_txt_lists_failed_url` with a single `in` assertion (the failed video ID, not "youtu.be").
- Add `assert resp.status_code == 200` to `test_language_parameter_passed_through`.
- Add `test_filename_with_path_traversal_is_sanitized` — POST `{"filename": "evil/../name"}` (single URL), assert the response `Content-Disposition` contains no `/` or `..`.
- Add `test_malformed_json_returns_422`.
- Add `test_mixed_empty_and_valid_urls_returns_two_url_zip`.
- Add `test_errors_txt_contains_header_line`.
- Change `== "application/zip"` to `"application/zip" in resp.headers["content-type"]`.
- Move `_make_segment`, `_setup_mock`, `_fake_segments` to `conftest.py`.

#### Hardcoded values check

- `"https://youtu.be/dQw4w9WgXcQ"` — used in 8 tests. Extract to module constant `_URL_1 = "https://youtu.be/dQw4w9WgXcQ"`.
- `"https://youtu.be/9bZkp7q19f0"` — used in 8 tests. Extract to `_URL_2`.
- `"dQw4w9WgXcQ"` and `"9bZkp7q19f0"` appear both inside URL literals and as standalone strings in assertions. Extract bare IDs (`_VIDEO_ID_1`, `_VIDEO_ID_2`) and build the URLs from them so the coupling is explicit.
- `_API_TARGET = "app.services.transcript.YouTubeTranscriptApi"` — already a constant. Good.
- `"my_custom_name"`, `"should_be_ignored"` — single-use; fine inline.
- `0.0`, `5.0` in `_fake_segments()` — promote to a `pytest.fixture` in `conftest.py` so router and service tests share segment data.
