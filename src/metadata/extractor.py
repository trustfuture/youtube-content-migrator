import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yt_dlp


class MetadataExtractor:
    """Extract and persist YouTube metadata without downloading media."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_video_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(url, download=False)
            if not info:
                return None
            return self._normalize_info(info)
        except Exception as e:
            self.logger.error(f"Failed to extract metadata for {url}: {e}")
            return None

    def batch_extract_metadata(self, urls: List[str], output_dir: str) -> List[Dict[str, Any]]:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        results: List[Dict[str, Any]] = []
        for url in urls:
            md = self.extract_video_metadata(url)
            if not md:
                results.append({"success": False, "url": url, "error": "metadata-extract-failed"})
                continue
            path = self.save_metadata(md, output_dir)
            results.append({"success": True, "url": url, "path": path, "metadata": md})
        return results

    def save_metadata(self, metadata: Dict[str, Any], output_dir: str, fmt: str = "json") -> str:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        video_id = metadata.get("id") or "unknown_id"
        base = out / f"{video_id}_metadata"

        if fmt == "csv":
            path = f"{base}.csv"
            self._write_csv(metadata, path)
            return path

        path = f"{base}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        return path

    def _write_csv(self, metadata: Dict[str, Any], path: str) -> None:
        # Flatten 1-level for a simple CSV export.
        row: Dict[str, Any] = {}
        for k, v in metadata.items():
            if isinstance(v, (dict, list)):
                continue
            row[k] = v

        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            w.writeheader()
            w.writerow(row)

    def _normalize_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        # Keep this intentionally small/stable as a contract.
        return {
            "id": info.get("id"),
            "title": info.get("title"),
            "description": info.get("description"),
            "uploader": info.get("uploader"),
            "uploader_id": info.get("uploader_id"),
            "channel": info.get("channel"),
            "channel_id": info.get("channel_id"),
            "upload_date": info.get("upload_date"),
            "timestamp": info.get("timestamp"),
            "duration": info.get("duration"),
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "comment_count": info.get("comment_count"),
            "tags": info.get("tags"),
            "categories": info.get("categories"),
            "webpage_url": info.get("webpage_url"),
        }
