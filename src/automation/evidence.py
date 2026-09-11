from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class EvidenceLogger:
    def __init__(self, evidence_dir: str | Path):
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.log_entries: List[Dict[str, Any]] = []

    def log(self, action: str, details: Dict[str, Any]) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "details": details,
        }
        self.log_entries.append(entry)
        path = self.evidence_dir / "run_log.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

    def capture_screenshot(self, page, name: str) -> str:
        path = self.evidence_dir / f"{name}.png"
        page.screenshot(path=str(path), full_page=True)
        return str(path)

    def save_snapshot(self, page, name: str) -> str:
        snapshot = {
            "url": page.url,
            "title": page.title(),
            "text": page.locator("body").inner_text(),
        }
        path = self.evidence_dir / f"{name}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        return str(path)

    def save_run_summary(self, payload: Dict[str, Any]) -> str:
        path = self.evidence_dir / "run_summary.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return str(path)
