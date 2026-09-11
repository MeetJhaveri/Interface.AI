from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from playwright.sync_api import Browser, Page, sync_playwright

from .artifacts import ArtifactStore
from .evidence import EvidenceLogger
from .llm_client import LLMClient
from .policy import SafetyPolicy
from .schemas import ActionStep, CapabilityArtifact, ReplayResult, TargetRef


class EscalationRequired(RuntimeError):
    def __init__(self, reason: str, context: Dict[str, Any]):
        super().__init__(reason)
        self.reason = reason
        self.context = context


class AutomationAgent:
    def __init__(self, artifact_store: ArtifactStore, evidence_dir: str | Path, policy: SafetyPolicy | None = None):
        self.artifact_store = artifact_store
        self.evidence = EvidenceLogger(evidence_dir)
        self.policy = policy or SafetyPolicy()
        self.llm = LLMClient()

    def run(self, goal: str, target_url: str, member_id: str) -> Dict[str, Any]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            page.goto(target_url, wait_until="networkidle")
            self.evidence.log("launch", {"url": target_url, "goal": goal})

            step_log: List[ActionStep] = []
            outputs: Dict[str, Any] = {}
            for step_index in range(self.policy.max_steps):
                page_state = self._page_state(page)
                self.evidence.log("observe", {"url": page.url, "summary": page_state.get("text", "")[:800]})
                plan = self.llm.plan(goal, page_state, member_id)
                actions = plan.get("actions", [])
                if not actions:
                    raise RuntimeError("Planner returned no actions.")

                for action in actions:
                    action_type = action.get("action")
                    selector = self._normalize_selector(action.get("selector") or action.get("target"))
                    if selector is None and action.get("value") is not None:
                        selector = "body"
                    self.policy.validate_action(action_type, selector or target_url)
                    try:
                        self._execute_action(page, {**action, "selector": selector})
                    except Exception as exc:
                        screenshot = self.evidence.capture_screenshot(page, f"failure_{step_index}")
                        self.evidence.save_snapshot(page, f"debug_{step_index}")
                        raise EscalationRequired(
                            reason=str(exc),
                            context={
                                "goal": goal,
                                "url": page.url,
                                "screenshot": screenshot,
                                "step_index": step_index,
                                "action": action,
                            },
                        ) from exc

                    step_log.append(
                        ActionStep(
                            step_id=f"step-{len(step_log)+1}",
                            action_type=action_type,
                            target=TargetRef(
                                strategy="css",
                                value=selector or "body",
                                description=f"Automation step for {goal}",
                            ),
                            value=str(action.get("value")) if action.get("value") is not None else None,
                            expected_text=action.get("expected_text"),
                            notes=f"Planner action generated for goal '{goal}'.",
                        )
                    )

                    if action_type == "read":
                        outputs.update(self._read_fields(page))

                if page.locator("#member-name").count() or page.locator("#account-status").count():
                    outputs.update(self._read_fields(page))
                    break

                if "member-name" in page.locator("body").inner_text() or page.url.endswith("/details"):
                    outputs.update(self._read_fields(page))
                    break

            if outputs:
                self.evidence.log("success", {"outputs": self.policy.redact(outputs)})
            else:
                self.evidence.log("incomplete", {"page_url": page.url})
                screenshot = self.evidence.capture_screenshot(page, "escalation_state")
                self.evidence.save_snapshot(page, "escalation_state")
                raise EscalationRequired(
                    reason="Automation reached a dead end without a valid member result.",
                    context={
                        "goal": goal,
                        "target_url": target_url,
                        "member_id": member_id,
                        "current_url": page.url,
                        "screenshot": screenshot,
                    },
                )

            artifact = CapabilityArtifact(
                capability_id="member_account_summary",
                goal=goal,
                target_url=target_url,
                inputs={"member_id": member_id},
                outputs=self.policy.redact(outputs),
                checkpoint={"type": "text", "selector": "#account-status", "expected": "active"},
                policy=self.policy.to_dict(),
                steps=step_log,
                metadata={
                    "run_id": f"run-{len(step_log)}",
                    "surface": "local_demo_banking_app",
                    "status": "success" if outputs else "incomplete",
                },
            )
            artifact_path = self.artifact_store.save(artifact)
            self.evidence.save_run_summary({"artifact_path": artifact_path, "outputs": self.policy.redact(outputs)})
            browser.close()
            return {"artifact_path": artifact_path, "outputs": self.policy.redact(outputs), "run_log": self.evidence.log_entries}

    def _page_state(self, page: Page) -> Dict[str, Any]:
        body_text = page.locator("body").inner_text()
        return {
            "url": page.url,
            "title": page.title(),
            "text": body_text[:5000],
            "member_id": page.locator("#member-id").input_value() if page.locator("#member-id").count() else "",
        }

    def _execute_action(self, page: Page, action: Dict[str, Any]) -> None:
        action_type = action.get("action")
        selector = action.get("selector")

        if action_type == "navigate":
            page.goto(action.get("value") or page.url, wait_until="networkidle")
            return
        if action_type == "fill":
            page.locator(selector).fill(action.get("value") or "")
            return
        if action_type == "click":
            page.locator(selector).click(timeout=8000)
            return
        if action_type == "wait":
            page.wait_for_timeout(400)
            return
        if action_type == "read":
            page.locator(selector).inner_text()
            return
        raise ValueError(f"Unknown action type {action_type!r}")

    def _read_fields(self, page: Page) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for selector in ["#member-name", "#account-status", "#account-balance", "#account-number"]:
            if page.locator(selector).count():
                text = page.locator(selector).inner_text().strip()
                if text:
                    data[selector.removeprefix("#")] = text
        return data

    def _normalize_selector(self, selector: str | None) -> str | None:
        if selector is None:
            return None
        mapping = {
            "search_member_input": "#member-id",
            "member_id_input": "#member-id",
            " member-id ": "#member-id",
            "search_button": "#search-button",
            "search-button": "#search-button",
            "member_name": "#member-name",
            "account_status": "#account-status",
            "account_balance": "#account-balance",
            "account_number": "#account-number",
        }
        return mapping.get(selector.strip(), selector)


def _recover_from_handoff(page: Page, previous_url: str) -> None:
    page.goto(previous_url, wait_until="networkidle")
