import json
from pathlib import Path
from typing import Any, Dict, Optional


def write_manifest(path: str | Path, payload: Dict[str, Any]) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return str(p)


def safe_relpath(base: Path, target: Optional[str | Path]) -> Optional[str]:
    if target is None:
        return None
    t = Path(target)
    try:
        return str(t.relative_to(base))
    except Exception:
        return str(t)
