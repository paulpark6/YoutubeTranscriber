 Two things to plan here. Let me handle them in order.                                                                           

  ---                                                                                                                             
  1. Rip out the old tests + global URL fixtures
                                                                                                                                  
  Confirmed approach for the test refactor:
                                                                                                                                  
  - Define one global table at the top of test_url_parser.py (or a fixture module) — REAL_URLS for success cases, INVALID_URLS for
   rejection cases.                                                                                                               
  - Delete the existing classes that template VALID_ID (TestRawVideoId, TestWatchUrl, TestShortenedUrl, TestShortsUrl,            
  TestEmbedUrl, TestInvalidUrls).                                                                                                 
  - Replace them with parametrized tests reading from the global tables.
  - One row in INVALID_URLS for the scheme-less youtu.be/<id> case → fails red → drives the implementation change.                
                                                                                                                                  
  Two small calls I want you to confirm before I write anything:                                                                  
                                                                                                                                  
  - (a) Where should the global tables live? Two options:                                                                         
    - Inline at top of test_url_parser.py — one file, easy to read.
    - In a new tests/fixtures/url_samples.py — reusable later if router tests want the same data.                                 
    - My rec: inline in test_url_parser.py. You said "url parser only for this round" and reusing them later is a 30-second move. 
  - (b) Existing rejection cases (e.g., 10/12-char strings, empty string, vimeo URL, channel URL) — keep them in the new          
  INVALID_URLS table, right? Some of those are useful regression tests. I'll preserve all of them; just confirming nothing gets   
  dropped.                                                                                                                        

# answer 1:
global tables should live inside the file test_url_parser.py on top of the code stating that its global variable.

For existing rejection cases, keep them in new invalidurl table. preserve them.
  ---             

  # answer 2: 
  yea tyhis markdown file is good.
  ---                                                                                                                             
  Title: Feature: Playlist URL support — fetch transcripts for every video in a playlist
                                                                                                                                  
  Body:
                                                                                                                                  
  ## Summary      
  When a user pastes a YouTube playlist URL (e.g. `https://www.youtube.com/playlist?list=PLxyz`), expand it into the full ordered
  list of video IDs and produce a transcript for each, named in playlist order: `1_<videoid>.txt`, `2_<videoid>.txt`, ...         
   
  ## Motivation                                                                                                                   
  Today `parse_video_id` rejects playlist URLs with `ValueError: Unrecognised YouTube URL path`. Users with a playlist they want
  bulk-transcribed have to copy-paste each video URL individually. Supporting playlists directly is a high-value feature for      
  educators, podcasters, and researchers.
                                                                                                                                  
  ## Open design questions

  ### 1. How do we resolve a playlist URL → list of video IDs?                                                                    
  The current dependency `youtube-transcript-api` does NOT support playlists. We must pick:
                                                                                                                                  
  - **Option A: YouTube Data API v3** (official)
    - Pros: reliable, documented, widely used.                                                                                    
    - Cons: requires Google Cloud project, API key, quota management (10,000 units/day default), `.env` secret. New dependency:   
  `google-api-python-client`.                                                                                                     
  - **Option B: HTML scraping**                                                                                                   
    - Pros: no API key, no quota.                                                                                                 
    - Cons: fragile (breaks on YouTube markup changes), arguably against ToS, no guarantee of full playlist for >100 videos       
  (lazy-loaded).                                                                                                                  
  - **Option C: `yt-dlp`**                                                                                                        
    - Pros: no API key, robust, handles edge cases.                                                                               
    - Cons: ~10MB dependency, slower (subprocess invocation), cumbersome to deploy.                                               
                                                                                                                                  
  **Decision needed before implementation.**                                                                                      
                                                                                                                                  
  ### 2. Filename policy                                                                                                          
  Proposed: `<index>_<videoid>.txt` where index is the 1-based position in the playlist (e.g. `1_dQw4w9WgXcQ.txt`).
  - Index zero-padded? (`01_xxx.txt` for playlists of 10–99, `001_xxx.txt` for 100+?)                                             
  - How does this interact with the existing `_1`, `_2` dedup-suffix rule for repeated names? Need to make sure                   
  `1_dQw4w9WgXcQ.txt` and `1_dQw4w9WgXcQ_1.txt` can't both occur (they would if the same video appears twice in a playlist —      
  possible in real playlists).                                                                                                    
                                                                                                                                  
  ### 3. UX / safety                                                                                                              
  - A playlist of 100 videos = ~100 sequential API calls = several minutes of latency. Need at least one of:
    - Confirmation step in the frontend ("This playlist has 47 videos. Continue?") before submission.                             
    - Hard cap (e.g. 50 videos max) with a clear error.                                                                           
    - Streaming progress (more work — probably v2).                                                                               
  - What if the playlist is unlisted/private? (Resolution layer will fail — error message needs to be actionable.)                
  - What if 3 of 47 videos have transcripts disabled? (Existing per-URL error model handles this; just need to make sure          
  `_errors.txt` lists them with their playlist-position context.)                                                                 
                                                                                                                                  
  ### 4. Schema / API surface                                                                                                     
  - Does `TranscriptRequest.urls` accept playlist URLs alongside video URLs in the same request, or are they a separate field?
  - Does the frontend need a new "playlist mode" UI, or is auto-detection from the URL enough?                                    
                                                                                                                                  
  ## Acceptance criteria                                                                                                          
  - [ ] Pasting `https://www.youtube.com/playlist?list=PLxyz` (any host variant) produces a ZIP containing one `.txt` per video in
   the playlist.                                                                                                                  
  - [ ] Files are named in playlist order: `1_<videoid>.txt`, `2_<videoid>.txt`, ...
  - [ ] If any video in the playlist fails (no transcript, deleted, etc.), it appears in `_errors.txt` with its playlist position,
   and the rest still succeed.                                                                                                    
  - [ ] If the playlist itself is invalid/unavailable, the request fails with HTTP 400 and a clear error message.
  - [ ] Tests cover: success case, partial-failure case, invalid-playlist case, empty-playlist case, single-video-in-playlist     
  case.                                                                                                                           
                                                                                                                                  
  ## Out of scope (for v1)                                                                                                        
  - Mixed video + playlist URLs in the same request (defer to v2).
  - Live progress updates during playlist transcription (defer to v2).                                                            
  - Caching or deduping playlist contents across requests.                                                                        
                                                                                                                                  
  ## Related                                                                                                                      
  - `backend/app/services/url_parser.py` — needs a new branch for playlist URLs.
  - `backend/app/routers/transcript.py` — orchestrator needs to handle "one input → many videos."                                 
  - `frontend/src/components/TranscriptForm.tsx` — needs UX for playlist confirmation/progress.                                   
  - Refactor step B3 (`pick_filename`) — playlist filename policy should land in this helper.                                     
                                                                                                                                  
  ## Labels (suggested)                                                                                                           
  `enhancement`, `needs-design`, `backend`, `frontend`                                                                            
                                                                                                                                  
  ---
  What I need from you to proceed                                                                                                 
                                                                                                                                  
  Three quick yes/no answers, then I'll execute:
                                                                                                                                  
  - ☐ Test fixtures location: inline in test_url_parser.py (rec) or new tests/fixtures/url_samples.py?                            
  - ☐ Preserve existing rejection cases (10-char, 12-char, vimeo, channel URLs) in the new INVALID_URLS table? (rec: yes)         
  - ☐ Playlist issue file location: repo root as feature-playlist-support.md (rec) or invoke project-planner to write into        
  mdfiles/?                                                                                                                       
                                                                                                                                  
  Also: do you want me to prepare a gh issue create command alongside the file, so you can run it to push the issue to GitHub     
  directly? (Requires gh auth status to be logged in — you can check that yourself with ! gh auth status.)
                          