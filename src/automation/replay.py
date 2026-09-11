from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from playwright.sync_api import Page, sync_playwright

from .artifacts import ArtifactStore
from .schemas import CapabilityArtifact, ReplayResult


class ReplayEngine:
    def __init__(self, artifact_store: ArtifactStore):
        self.artifact_store = artifact_store

    def replay(self, artifact_path: str | Path, input_values: Dict[str, Any], target_url: str) -> ReplayResult:
        artifact = self.artifact_store.load(artifact_path)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            page.goto(target_url, wait_until="networkidle")
            for step in artifact.steps:
                selector = step.target.value
                action_type = step.action_type
                if action_type == "fill":
                    value = input_values.get(step.value or "", step.value or "")
                    page.locator(selector).fill(str(value))
                elif action_type == "click":
                    page.locator(selector).click(timeout=8000)
                elif action_type == "wait":
                    page.wait_for_timeout(300)
                elif action_type == "read":
                    page.locator(selector).inner_text()
                elif action_type == "navigate":
                    page.goto(step.value or target_url, wait_until="networkidle")
                else:
                    raise ValueError(f"Unsupported replay action: {action_type}")

            checkpoint = artifact.checkpoint
            observed = page.locator(checkpoint.get("selector", "body")).inner_text()
            success = checkpoint.get("expected", "active").lower() in observed.lower()
            if not success:
                return ReplayResult(
                    success=False,
                    status="checkpoint_failed",
                    error=f"Expected '{checkpoint.get('expected')}' but observed '{observed[:150]}'.",
                )

            outputs = {
                "member_name": page.locator("#member-name").inner_text() if page.locator("#member-name").count() else "",
                "account_status": page.locator("#account-status").inner_text() if page.locator("#account-status").count() else "",
                "account_balance": page.locator("#account-balance").inner_text() if page.locator("#account-balance").count() else "",
            }
            return ReplayResult(success=True, status="success", outputs=outputs, business_outcome="member_account_found")
