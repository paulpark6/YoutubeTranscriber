"""
In-memory ZIP archive builder.
"""

import io
import zipfile


def build_zip(files: dict[str, str]) -> bytes:
    """
    Build a ZIP archive in memory from a mapping of filename to text content.

    Args:
        files: Dict mapping filenames (including extension) to their text content.

    Returns:
        Raw ZIP file bytes ready to be sent as an HTTP response body.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, content in files.items():
            zf.writestr(filename, content.encode("utf-8"))
    buffer.seek(0)
    return buffer.read()
