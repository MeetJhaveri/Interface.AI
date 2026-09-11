from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SafetyPolicy:
    allowed_domains: List[str] = field(default_factory=lambda: ["127.0.0.1", "localhost"])
    allowed_actions: List[str] = field(default_factory=lambda: ["navigate", "fill", "click", "wait", "read"])
    max_steps: int = 12
    require_confirmation_for: List[str] = field(default_factory=lambda: ["delete", "transfer", "freeze", "unlock"])

    def validate_action(self, action_type: str, target: str) -> None:
        if action_type not in self.allowed_actions:
            raise ValueError(f"Action type '{action_type}' is not allowed by policy.")
        if target and any(domain in target for domain in ["example.com", "realbank.com"]):
            raise ValueError(f"Target '{target}' is not allowed by policy.")

    def redact(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            text = value
            if len(text) > 6 and any(ch.isdigit() for ch in text):
                return "[REDACTED]"
            return text
        if isinstance(value, dict):
            return {k: self.redact(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.redact(v) for v in value]
        return value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed_domains": self.allowed_domains,
            "allowed_actions": self.allowed_actions,
            "max_steps": self.max_steps,
            "require_confirmation_for": self.require_confirmation_for,
        }
