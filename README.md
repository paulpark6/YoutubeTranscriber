# YouTube Transcription Tool

A simple Python script that fetches the transcript of a YouTube video and saves it to a `.txt` file with timestamps.

Uses the community library [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) by [jdepoix](https://github.com/jdepoix).

---

## Setup

**1. Create and activate a virtual environment (recommended)**

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

---

## Usage

Run the script:

```bash
python transcribe.py
```

You will be prompted for two inputs:

1. **YouTube video ID** — the part after `?v=` in a YouTube URL.
2. **Output filename** — name of the `.txt` file to save the transcript to (no extension needed).

### Example

For the video `https://www.youtube.com/watch?v=zijbzxinWng`, the video ID is `zijbzxinWng`.

```
Enter the YouTube video ID: zijbzxinWng
Enter the output filename (without extension): my_transcript
Saved to my_transcript.txt
```

The output file will look like:

```
[00:00] Welcome to the video.
[00:05] Today we're going to talk about...
[01:23] Let's dive in.
...
```

---

## Notes

- The video must have captions/transcripts available (auto-generated or manual). If not, the script will print an error.
- No YouTube API key is required.
- The transcript is saved in UTF-8 encoding.
