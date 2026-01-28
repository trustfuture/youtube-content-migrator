from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


def summarize_results(results: List[Any]) -> Dict[str, Any]:
    """Create a compact summary from the heterogeneous results list.

    `results` contains dict entries (single video) and also dicts for playlist/channel dry-runs.
    """
    flat: List[Dict[str, Any]] = [r for r in results if isinstance(r, dict)]

    counts = Counter()
    reasons = Counter()
    errors = Counter()

    for r in flat:
        if r.get("dry_run"):
            counts["dry_run"] += 1
        if r.get("skipped"):
            counts["skipped"] += 1
            reasons[r.get("reason") or "unknown"] += 1
        if r.get("success") is True:
            counts["success"] += 1
        if r.get("success") is False:
            counts["failed"] += 1
            errors[r.get("error") or "unknown"] += 1

    return {
        "counts": dict(counts),
        "skip_reasons": dict(reasons),
        "top_errors": errors.most_common(10),
        "total": len(flat),
    }
