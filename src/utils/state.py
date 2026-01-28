import json
from pathlib import Path
from typing import Any, Dict, Optional


def load_manifest(path: str | Path) -> Optional[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def find_existing_video_dir(output_root: str | Path, video_id: str) -> Optional[Path]:
    """Search for an existing per-video manifest.json containing video_id.

    This is a pragmatic dedupe mechanism that doesn't require a central index.
    """
    root = Path(output_root)
    if not root.exists():
        return None

    # Search within downloads tree. We expect manifests inside .../videos/<title>_<id>/manifest.json
    for manifest_path in root.rglob("manifest.json"):
        md = load_manifest(manifest_path)
        if not md:
            continue
        if md.get("video_id") == video_id:
            return manifest_path.parent
    return None
