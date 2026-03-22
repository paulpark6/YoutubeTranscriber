from youtube_transcript_api import YouTubeTranscriptApi

# Get user inputs
video_id = input("Enter the YouTube video ID: ")
filename = input("Enter the output filename (without extension): ")
if not filename.endswith(".txt"):
    filename += ".txt"

def format_time(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

try:
    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id=video_id)
    
    lines = []
    for item in transcript:
        ts = format_time(item.start)
        lines.append(f"[{ts}] {item.text}")
    
    full_text = "\n".join(lines)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    print(f"Saved to {filename}")
except Exception as e:
    print("Error:", e)