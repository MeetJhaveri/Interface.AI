from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .schemas import CapabilityArtifact


class ArtifactStore:
    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save(self, artifact: CapabilityArtifact) -> str:
        artifact_path = self.root_dir / f"{artifact.capability_id}.json"
        with artifact_path.open("w", encoding="utf-8") as fh:
            json.dump(artifact.model_dump(mode="json"), fh, indent=2, ensure_ascii=False)
        return str(artifact_path)

    def load(self, artifact_path: str | Path) -> CapabilityArtifact:
        path = Path(artifact_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return CapabilityArtifact.model_validate(data)

    def list(self) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for path in sorted(self.root_dir.glob("*.json")):
            result[path.stem] = str(path)
        return result
