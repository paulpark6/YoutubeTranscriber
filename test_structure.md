# Backend Test Structure Audit

_Audited: 2026-04-30. Test suite: 63 tests, all passing._

---

## 1. Test Inventory

### `tests/test_url_parser.py`

#### New Tests
We need to add in more features to parse_video_id where when user pastes in a video with a timestamp on it for example like this: "https://www.youtube.com/watch?v=N5Zk-xH1e0k&t=596s" or what if the user copies the link from shared video "https://youtu.be/8vIDZO_w7lY?si=_A4rcB8rw8vjODBI" with this format? We have to look into this.

**Class `TestRawVideoId`**
- `test_accepts_11_char_alphanumeric` — asserts `parse_video_id(VALID_ID) == VALID_ID` (exact match)
- `test_accepts_id_with_hyphen` — asserts 11-char ID containing `-` and `_` is returned unchanged
- `test_rejects_10_char_string` — asserts `ValueError` matching "Not a recognised YouTube URL"
- `test_rejects_12_char_string` — asserts `ValueError` matching "Not a recognised YouTube URL"
- `test_rejects_empty_string` — asserts `ValueError` matching "must not be empty"
- `test_rejects_whitespace_only` — asserts `ValueError` matching "must not be empty" (strips to empty)

**Class `TestWatchUrl`**
- `test_standard_watch_url` — asserts `https://www.youtube.com/watch?v=ID` extracts ID
- `test_watch_url_without_www` — asserts `https://youtube.com/watch?v=ID` extracts ID
- `test_watch_url_with_extra_params` — asserts extra query params (`t=`, `list=`) are ignored
- `test_watch_url_missing_v_param` — asserts `ValueError` matching "Missing or invalid 'v' query parameter"
- `test_watch_url_invalid_v_param` — asserts short/invalid `v` value raises `ValueError`

**Class `TestShortenedUrl`**
- `test_youtu_be_url` — asserts `https://youtu.be/ID` extracts ID
- `test_youtu_be_url_with_params` — asserts `?t=42` suffix is ignored for youtu.be
- `test_youtu_be_invalid_id` — asserts `ValueError` matching "youtu.be URL" for short/bad path

**Class `TestShortsUrl`**
- `test_shorts_url` — asserts `https://www.youtube.com/shorts/ID` extracts ID
- `test_shorts_url_without_www` — asserts `https://youtube.com/shorts/ID` extracts ID
- `test_shorts_url_invalid_id` — asserts `ValueError` matching "Shorts URL" for bad path

**Class `TestEmbedUrl`**
- `test_embed_url` — asserts `https://www.youtube.com/embed/ID` extracts ID

**Class `TestInvalidUrls`**
- `test_non_youtube_domain` — asserts `ValueError` matching "Not a recognised YouTube URL" for vimeo.com
- `test_completely_random_string` — asserts `ValueError` for a non-URL string longer than 11 chars
- `test_whitespace_is_stripped_before_parsing` — asserts leading/trailing spaces on a raw ID are stripped before matching
- `test_youtube_channel_url` — asserts `ValueError` for `/channel/` path

---

### `tests/test_transcript_service.py`

**Class `TestFetchTranscript`**
- `test_returns_list_of_dicts` — asserts return value is a list of `{"start": float, "text": str}` dicts and `find_transcript` was called with `["en"]`
- `test_raises_value_error_on_no_transcript_found` — asserts `ValueError` matching "No transcript found" when `NoTranscriptFound` is raised
- `test_raises_value_error_on_transcripts_disabled` — asserts `ValueError` matching "disabled" when `TranscriptsDisabled` is raised
- `test_raises_value_error_on_video_unavailable` — asserts `ValueError` matching "unavailable" when `VideoUnavailable` is raised
- `test_raises_runtime_error_on_unexpected_exception` — asserts `RuntimeError` matching "unexpected error" for a generic `ConnectionError`

**Class `TestFormatTranscript`**
- `test_with_timestamps` — asserts `[00:00] Hello\n[01:05] World` for segments at 0.0 and 65.0 seconds
- `test_without_timestamps` — asserts `Hello\nWorld` with `include_timestamps=False`
- `test_empty_segments_returns_empty_string` — asserts `""` for both `True` and `False` timestamp modes
- `test_skips_segments_with_empty_text` — asserts blank/whitespace-only text segments are omitted from output
- `test_timestamp_zero_padding` — asserts single-digit seconds produce `[00:05]` format
- `test_timestamp_over_one_hour` — asserts 3661 seconds produces `[61:01]` (total minutes, not HH:MM:SS)
- `test_default_include_timestamps_is_true` — asserts calling `format_transcript(segments)` without the flag produces timestamp-prefixed lines

**Class `TestSanitizeFilename`**
- `test_plain_name_unchanged_structure` — asserts `"my_video"` returns `"my_video"`
- `test_replaces_illegal_characters` — asserts `<`, `>`, `:`, `"` are absent from output
- `test_collapses_spaces_to_underscore` — asserts `"hello world"` becomes `"hello_world"`
- `test_strips_leading_trailing_underscores_and_dots` — asserts `"___name___"` has no leading/trailing underscores
- `test_truncates_long_names` — asserts 300-char input produces output with `len <= 200`
- `test_empty_string_falls_back` — asserts `""` input returns `"transcript"`
- `test_only_illegal_chars_falls_back` — asserts all-illegal input produces a non-empty result
- `test_slashes_replaced` — asserts `"path/to/file"` has no `/` in output

**Class `TestBuildZip`**
- `test_returns_bytes` — asserts return type is `bytes`
- `test_zip_contains_correct_files` — asserts both filenames appear in `zf.namelist()`
- `test_zip_file_content_matches` — asserts file content round-trips correctly through ZIP
- `test_empty_dict_produces_valid_zip` — asserts empty input produces a valid ZIP with empty namelist
- `test_unicode_content_encoded_as_utf8` — asserts Japanese characters survive a UTF-8 encode/decode round-trip

---

### `tests/test_transcript_router.py`

**Class `TestSingleUrl`**
- `test_returns_txt_file` — asserts HTTP 200, `content-type` contains `text/plain`, and `.txt` appears in `content-disposition`
- `test_txt_content_includes_timestamps_by_default` — asserts response body contains `[00:00]` and `"Hello"` when `include_timestamps` is omitted
- `test_txt_content_no_timestamps` — asserts response body has no `[` characters and contains `"Hello"` when `include_timestamps=False`
- `test_custom_filename_honoured` — asserts `content-disposition` header contains `"my_custom_name.txt"` when `filename` is provided
- `test_language_parameter_passed_through` — asserts `find_transcript` was called with `["es"]` when `language="es"` is in the request

**Class `TestMultipleUrls`**
- `test_returns_zip_file` — asserts HTTP 200, `content-type` is `application/zip`, and `"transcripts.zip"` in `content-disposition`
- `test_zip_contains_txt_for_each_url` — asserts exactly 2 `.txt` files exist in the returned ZIP for 2 URLs
- `test_custom_filename_ignored_for_multiple_urls` — asserts the custom `filename` value does not appear in any ZIP entry name

**Class `TestPartialFailure`**
- `test_zip_includes_errors_txt_on_partial_failure` — asserts HTTP 200, `application/zip` response, and `"_errors.txt"` in ZIP namelist when the second URL raises `NoTranscriptFound`
- `test_errors_txt_lists_failed_url` — asserts `_errors.txt` content contains the failed URL's video ID or domain when second URL raises `TranscriptsDisabled`

**Class `TestAllFailure`**
- `test_returns_400_when_all_urls_fail` — asserts HTTP 400 when both URLs raise `VideoUnavailable`
- `test_400_body_contains_detail` — asserts HTTP 400 response JSON contains a `"detail"` key
- `test_returns_400_for_all_invalid_urls` — asserts HTTP 400 when all URLs fail URL parsing (no mock needed)
- `test_returns_400_for_empty_urls` — asserts HTTP 400 when all URLs are whitespace-only strings (exercising the `.strip()` skip path)

**Class `TestInputValidation`**
- `test_missing_urls_field_returns_422` — asserts HTTP 422 when the `urls` field is absent from the request body
- `test_empty_urls_list_returns_422` — asserts HTTP 422 when `urls` is an empty list (Pydantic `min_length=1` constraint)

---

## 2. Coverage Map (Function → Tests)

| Function | Module | Tested by | Notes |
|---|---|---|---|
| `parse_video_id` | `services/url_parser.py` | `TestRawVideoId`, `TestWatchUrl`, `TestShortenedUrl`, `TestShortsUrl`, `TestEmbedUrl`, `TestInvalidUrls` (all in `test_url_parser.py`); also exercised indirectly by every router test | Comprehensive direct coverage |
| `_is_valid_video_id` | `services/url_parser.py` | — | Private helper; covered transitively through `parse_video_id` tests |
| `fetch_transcript` | `services/transcript.py` | `TestFetchTranscript` in `test_transcript_service.py`; indirectly by all router integration tests | All 3 named exception branches and the catch-all branch are covered |
| `sanitize_filename` | `services/transcript.py` | `TestSanitizeFilename` in `test_transcript_service.py`; indirectly by router tests that inspect `content-disposition` | Truncation and fallback covered; multibyte truncation boundary not asserted |
| `format_transcript` | `services/transcript_format.py` | `TestFormatTranscript` in `test_transcript_service.py` | Code is in `transcript_format.py`; tests live in the old `test_transcript_service.py` |
| `_format_time` | `services/transcript_format.py` | — | Private helper; covered transitively through `TestFormatTranscript` |
| `build_zip` | `services/zip_builder.py` | `TestBuildZip` in `test_transcript_service.py` | Code is in `zip_builder.py`; tests live in the old `test_transcript_service.py` |
| `post_transcript` (router handler) | `routers/transcript.py` | `TestSingleUrl`, `TestMultipleUrls`, `TestPartialFailure`, `TestAllFailure`, `TestInputValidation` in `test_transcript_router.py` | Duplicate filename dedup loop not directly tested |
| `health_check` | `main.py` | — | No test exists for `GET /health` |
| `TranscriptRequest` (Pydantic model) | `schemas/transcript.py` | `TestInputValidation` covers `urls` min_length; other field defaults exercised via router tests | `language` accepts any string; no test for exotic/empty language codes |

---

## 3. What's Covered Well

- **URL parser has dedicated tests for every supported format**: raw 11-char IDs (with and without `-`/`_`), `watch?v=`, `youtu.be/`, `/shorts/`, and `/embed/` all have at least one success case and at least one rejection case. Edge conditions like extra query params, leading/trailing whitespace, and the no-`www` variant are also exercised.

- **All four `fetch_transcript` exception branches are tested**: `NoTranscriptFound`, `TranscriptsDisabled`, `VideoUnavailable`, and the generic `Exception` catch-all are each given their own test in `TestFetchTranscript`, and the mapping from each exception to its output type (`ValueError` vs. `RuntimeError`) is explicitly asserted.

- **`format_transcript` timestamp logic is thoroughly exercised**: zero-padding, sub-60-second values, values that roll past 60 minutes (asserting the `[61:01]` total-minutes representation), blank segment skipping, and the default-parameter behavior are all directly asserted.

- **Router integration tests cover the four major response modes**: single-URL `.txt` success, multi-URL `.zip` success, partial failure `.zip` with `_errors.txt`, and all-failure HTTP 400. These tests drive the full stack through the FastAPI `TestClient`.

- **Pydantic schema constraints are integration-tested**: missing `urls` field returns 422, and an empty `urls` list returns 422 (the `min_length=1` constraint on the `Field`).

- **`build_zip` covers the happy path and two important edge cases**: empty input, multi-file content, and multibyte UTF-8 content are all asserted at the byte level by reading back entries from the real `zipfile.ZipFile`.

---

## 4. What's Missing or Thin

**`GET /health` endpoint — no test at all.**
`main.py` line 36–39 defines `health_check()`. There is no test in any file that calls `GET /health` and asserts `{"status": "ok"}` with HTTP 200. As a liveness probe this is low-risk, but it means the endpoint can silently break (e.g., a bad import breaks app startup) without any test catching it.

**Filename dedup loop in the router — no test.**
`routers/transcript.py` lines 76–80 implement a `_1`, `_2`, … suffix strategy when multiple URLs in a batch resolve to the same base filename (i.e., two raw video IDs that are identical, or two URLs where `sanitize_filename` produces the same result). There is no test that submits two URLs that would produce the same base name and then asserts the ZIP contains two distinct `.txt` entries. This loop is the only non-trivial branching logic in the router handler that is unexercised.

**`parse_video_id` for `m.youtube.com` and `music.youtube.com` — not covered.**
`url_parser.py` line 64 explicitly lists `"m.youtube.com"` and `"music.youtube.com"` as accepted hostnames alongside `"youtube.com"`. `TestWatchUrl` and `TestShortsUrl` only send `www.youtube.com` and plain `youtube.com` URLs. There is no test for `https://m.youtube.com/watch?v=ID` or `https://music.youtube.com/watch?v=ID`.

**`parse_video_id` `/embed/` invalid-ID case — not covered.**
`TestEmbedUrl` only has `test_embed_url` for the success path. The code at `url_parser.py` lines 87–91 falls through to the generic "Unrecognised YouTube URL path" `ValueError` when the embed path contains a bad ID. There is no test for `https://www.youtube.com/embed/tooshort`.

**`sanitize_filename` truncation with multibyte characters — not asserted at boundary.**
`transcript.py` line 87 truncates with `sanitized[:200]`, which operates on Python Unicode code points, not bytes. A 200-character Japanese string truncated at position 200 may produce up to 600 bytes — potentially violating filesystem byte limits on some systems. The existing `test_truncates_long_names` only tests ASCII (`"a" * 300`) and asserts `len(result) <= 200` on the str length. There is no test that passes a 300-character multibyte string and verifies the truncation boundary is safe or intentionally defined at the str-length level.

**`sanitize_filename` only-dots input — behavior not asserted.**
The function strips leading/trailing dots (`sanitized.strip("_.")`, line 85). If the input is `"..."` or `"....."`, after stripping all characters become empty, and the fallback `"transcript"` should fire. There is no test for a dots-only input. `test_only_illegal_chars_falls_back` passes `'<>:"/\\|?*'`, which exercises the illegal-chars path but not the dots path.

**Router behavior when `request.urls` contains only whitespace strings — partially covered, but error message path untested.**
`test_returns_400_for_empty_urls` sends `["   ", "   "]`, which correctly hits the HTTP 400 branch. However, in the router handler (`routers/transcript.py` line 87`) the `detail` string falls through to `"No valid URLs provided."` when `errors` is empty. This is the only way to reach that specific message. The test asserts the status code but does not assert the detail string, so the `"No valid URLs provided."` branch could silently regress to any other message without test failure.

**`language` field accepts any string — unusual values untested.**
`TranscriptRequest.language` is typed `str` with no further validation. There is no test for edge cases: empty string `""`, a whitespace string `"  "`, or a nonsense value like `"zz-ZZ"`. Whether these are silently passed to the transcript API (and would cause a `NoTranscriptFound`) or should be rejected at the schema level is undefined. One test for `language=""` sent to the router would lock in the current behavior.

**`CORS` — `expose_headers: ["Content-Disposition"]` not verified.**
`main.py` line 30 adds `Content-Disposition` to `expose_headers`. There is no test that makes a cross-origin preflight or actual request and asserts that `Content-Disposition` is present in the `Access-Control-Expose-Headers` response header. The `TestClient` does not simulate browser CORS enforcement, but a test could at least assert the header value is present on actual responses.

**`sanitize_filename` with a name that starts/ends with dots (not underscores) — not tested.**
`test_strips_leading_trailing_underscores_and_dots` only uses `"___name___"` (underscores only). The `strip("_.")` call also handles leading dots (relevant for Unix hidden-file prevention). A name like `"..my_file.."` is not tested.

---

## 5. Test-File vs. Code-Module Alignment

Two functions were refactored into dedicated modules but their tests were not relocated:

- `build_zip` now lives in `app/services/zip_builder.py`, but `TestBuildZip` is in `tests/test_transcript_service.py`. Future TDD work on `zip_builder.py` should add a `tests/test_zip_builder.py` file alongside it.
- `format_transcript` (and its private helper `_format_time`) now lives in `app/services/transcript_format.py`, but `TestFormatTranscript` is in `tests/test_transcript_service.py`. Future TDD work on `transcript_format.py` should add a `tests/test_transcript_format.py` file.

The existing tests still import from the correct final modules (`from app.services.transcript_format import format_transcript`, `from app.services.zip_builder import build_zip`), so this is a discoverability and locality issue, not a correctness bug.

---

## 6. Suggested Next Tests (Priority Order)

1. **Filename dedup loop (`_1`, `_2` suffix).** Submit two identical raw video IDs in a batch request and assert the ZIP contains two distinct entries (e.g., `dQw4w9WgXcQ.txt` and `dQw4w9WgXcQ_1.txt`). This is the only branching logic in the router handler with zero coverage, and a regression here would silently drop a transcript with no HTTP error.

2. **`GET /health` endpoint.** Assert HTTP 200 and `{"status": "ok"}` from the `TestClient`. Takes one test, adds coverage of app startup and router registration, and is a prerequisite for any CI liveness check.

3. **`parse_video_id` for `m.youtube.com` and `music.youtube.com`.** Add two tests in `TestWatchUrl` (or a new `TestMobileUrl` class): one for `m.youtube.com/watch?v=ID` and one for `music.youtube.com/watch?v=ID`. These hostnames are explicitly in the code but untested — any future refactor of the hostname normalisation would not be caught.

4. **`parse_video_id` `/embed/` invalid-ID case.** Add a test in `TestEmbedUrl` that sends `https://www.youtube.com/embed/bad` and asserts `ValueError` with the "Unrecognised YouTube URL path" message. Locks in the failure mode for the embed path.

5. **`sanitize_filename` with a dots-only input.** Add `sanitize_filename(".....")` and assert the fallback `"transcript"` is returned. Verifies the `strip("_.")` + empty-check path is exercised for leading/trailing dots specifically.

6. **Router `detail` message for whitespace-only URL list.** Extend `test_returns_400_for_empty_urls` (or add a new test) to assert `resp.json()["detail"] == "No valid URLs provided."`. Currently the status code is tested but the specific message is not pinned, so it can silently change.

7. **`language` field with empty string.** Send `{"urls": ["https://youtu.be/dQw4w9WgXcQ"], "language": ""}` to the router (with a mocked API that raises `NoTranscriptFound`) and assert either HTTP 400 with a sensible detail or, if schema-level rejection is desired, HTTP 422. This locks in the current behavior and surfaces whether an empty language code should be rejected at the Pydantic layer.

8. **`format_transcript` with a segment missing the `"start"` key.** The code uses `segment.get("start", 0)`, so a segment dict with no `"start"` key should default to 0 seconds. No test currently asserts this fallback. Add `[{"text": "Hello"}]` as input with `include_timestamps=True` and assert `"[00:00] Hello"`.

9. **`build_zip` with a filename containing non-ASCII characters.** The existing unicode test checks content encoding; a complementary test with a non-ASCII filename (e.g., `"日本語.txt"`) would verify that ZIP entry names are also handled correctly by the `zipfile` module under the current Python version.

10. **New test files for relocated modules.** As a TDD hygiene step, create `tests/test_transcript_format.py` and `tests/test_zip_builder.py` as empty modules (or migrate the existing classes into them). This unblocks writing new tests for those modules in the correct location without confusion about which service file a test belongs to.
