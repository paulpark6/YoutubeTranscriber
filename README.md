# YouTube Transcription Tool

A web app that downloads YouTube transcripts as `.txt` files. Paste one or more YouTube URLs, choose a language, toggle timestamps, and download.

Built with **FastAPI** (backend) and **React + Vite** (frontend).

---

## Prerequisites

- Python 3.10+
- Node.js 18+

---

## Setup

### Backend

```bash
# From the project root
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

pip install -r backend/requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

---

## Running the app

You need two terminals running at the same time.

**Terminal 1 — Backend**

```bash
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend**

```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

---

## Usage

1. Paste one or more YouTube URLs into the text area (one per line)
2. Optionally enter a custom filename for each export, if you want.
3. Choose a language (default: English)
4. Toggle timestamps on or off (default: on)
5. Click **Download Transcript**

Single URL → downloads a `.txt` file
Multiple URLs → downloads a `.zip` containing one `.txt` per video

### Supported URL formats

```
https://www.youtube.com/watch?v=zijbzxinWng
https://youtu.be/zijbzxinWng
https://www.youtube.com/shorts/zijbzxinWng
https://www.youtube.com/embed/zijbzxinWng
zijbzxinWng   (raw 11-character video ID)
```

The `youtube.com` host also accepts the `m.youtube.com` (mobile) and `music.youtube.com` variants for any of the path-based formats above.

---

## Running tests

**Backend**

```bash
source venv/bin/activate
cd backend
python -m pytest tests/ -v
```

**Frontend**

```bash
cd frontend
npm run test
```

---

## Notes

- The video must have captions available (auto-generated or manual). If not, an error is shown.
- No YouTube API key is required.
- All transcripts are UTF-8 encoded.
- The original command-line script is still available at `transcribe.py`.
