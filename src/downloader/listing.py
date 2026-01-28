import logging
from typing import Any, Dict, List, Optional

import yt_dlp


logger = logging.getLogger(__name__)


def list_entries(url: str, *, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return flat list of entries for a playlist/channel/video URL.

    Uses yt-dlp extract_info(download=False) with extract_flat for speed.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        return []

    # Playlist/channel will have entries.
    if isinstance(info, dict) and info.get("entries"):
        entries = [e for e in info.get("entries") if e]
        if limit is not None:
            entries = entries[:limit]
        out: List[Dict[str, Any]] = []
        for e in entries:
            out.append(
                {
                    "id": e.get("id"),
                    "title": e.get("title"),
                    "url": e.get("url") or e.get("webpage_url"),
                    "webpage_url": e.get("webpage_url"),
                    "duration": e.get("duration"),
                    "upload_date": e.get("upload_date"),
                }
            )
        return out

    # Single video
    return [
        {
            "id": info.get("id"),
            "title": info.get("title"),
            "url": info.get("webpage_url") or url,
            "webpage_url": info.get("webpage_url") or url,
            "duration": info.get("duration"),
            "upload_date": info.get("upload_date"),
        }
    ]
