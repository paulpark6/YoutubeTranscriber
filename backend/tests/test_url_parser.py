"""
Unit tests for backend/app/services/url_parser.py
"""

import pytest

from app.services.url_parser import parse_video_id

# A well-known valid video ID to use across tests
VALID_ID = "dQw4w9WgXcQ"


class TestRawVideoId:
    def test_accepts_11_char_alphanumeric(self):
        assert parse_video_id(VALID_ID) == VALID_ID

    def test_accepts_id_with_hyphen(self):
        video_id = "abc-def_ghi"  # 11 chars, contains - and _
        assert parse_video_id(video_id) == video_id

    def test_rejects_10_char_string(self):
        with pytest.raises(ValueError, match="Not a recognised YouTube URL"):
            parse_video_id("dQw4w9WgXc")  # 10 chars

    def test_rejects_12_char_string(self):
        with pytest.raises(ValueError, match="Not a recognised YouTube URL"):
            parse_video_id("dQw4w9WgXcQQ")  # 12 chars

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError, match="must not be empty"):
            parse_video_id("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValueError, match="must not be empty"):
            parse_video_id("   ")


class TestWatchUrl:
    def test_standard_watch_url(self):
        assert parse_video_id(f"https://www.youtube.com/watch?v={VALID_ID}") == VALID_ID

    def test_watch_url_without_www(self):
        assert parse_video_id(f"https://youtube.com/watch?v={VALID_ID}") == VALID_ID

    def test_watch_url_with_extra_params(self):
        url = f"https://www.youtube.com/watch?v={VALID_ID}&t=30s&list=PLxyz"
        assert parse_video_id(url) == VALID_ID

    def test_watch_url_missing_v_param(self):
        with pytest.raises(ValueError, match="Missing or invalid 'v' query parameter"):
            parse_video_id("https://www.youtube.com/watch?list=PLxyz")

    def test_watch_url_invalid_v_param(self):
        with pytest.raises(ValueError, match="Missing or invalid 'v' query parameter"):
            parse_video_id("https://www.youtube.com/watch?v=tooshort")


class TestShortenedUrl:
    def test_youtu_be_url(self):
        assert parse_video_id(f"https://youtu.be/{VALID_ID}") == VALID_ID

    def test_youtu_be_url_with_params(self):
        url = f"https://youtu.be/{VALID_ID}?t=42"
        assert parse_video_id(url) == VALID_ID

    def test_youtu_be_invalid_id(self):
        with pytest.raises(ValueError, match="youtu.be URL"):
            parse_video_id("https://youtu.be/bad")


class TestShortsUrl:
    def test_shorts_url(self):
        assert parse_video_id(f"https://www.youtube.com/shorts/{VALID_ID}") == VALID_ID

    def test_shorts_url_without_www(self):
        assert parse_video_id(f"https://youtube.com/shorts/{VALID_ID}") == VALID_ID

    def test_shorts_url_invalid_id(self):
        with pytest.raises(ValueError, match="Shorts URL"):
            parse_video_id("https://www.youtube.com/shorts/toolong_id_here!")


class TestEmbedUrl:
    def test_embed_url(self):
        assert parse_video_id(f"https://www.youtube.com/embed/{VALID_ID}") == VALID_ID


class TestInvalidUrls:
    def test_non_youtube_domain(self):
        with pytest.raises(ValueError, match="Not a recognised YouTube URL"):
            parse_video_id("https://vimeo.com/123456789")

    def test_completely_random_string(self):
        with pytest.raises(ValueError):
            parse_video_id("not_a_url_at_all_and_not_11")

    def test_whitespace_is_stripped_before_parsing(self):
        assert parse_video_id(f"  {VALID_ID}  ") == VALID_ID

    def test_youtube_channel_url(self):
        with pytest.raises(ValueError):
            parse_video_id("https://www.youtube.com/channel/UCxxxxxx")
