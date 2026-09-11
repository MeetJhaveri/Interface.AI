from __future__ import annotations

import json
import os
from typing import Any, Dict, List

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv() -> bool:
        return False

load_dotenv()

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key and OpenAI else None

    def plan(self, goal: str, page_state: Dict[str, Any], member_id: str) -> Dict[str, Any]:
        if self.client is not None:
            return self._call_openai(goal, page_state, member_id)
        return self._fallback_plan(goal, page_state, member_id)

    def _call_openai(self, goal: str, page_state: Dict[str, Any], member_id: str) -> Dict[str, Any]:
        prompt = (
            "You are an automation planner for a banking member lookup workflow. "
            "Return valid JSON only. The JSON must be an object with a top-level 'actions' array. "
            "Each action must use keys exactly: action, selector, value. "
            "Allowed actions: fill, click, wait, read. "
            "Use these CSS selectors whenever possible: #member-id, #search-button, #member-name, #account-status, #account-balance, #account-number. "
            "For a member lookup, first fill #member-id, then click #search-button, then read the result fields. "
            f"Goal: {goal}. Member ID: {member_id}. Page state: {json.dumps(page_state, ensure_ascii=False)[:4000]}"
        )
        completion = self.client.responses.create(
            model="gpt-4o-mini",
            input=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = completion.output_text.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raw = raw.split("```json", 1)[-1].split("```", 1)[0].strip()
            return json.loads(raw)

    def _fallback_plan(self, goal: str, page_state: Dict[str, Any], member_id: str) -> Dict[str, Any]:
        url = page_state.get("url", "")
        text = (page_state.get("text", "") or "").lower()

        if "member-directory" in url or "member-id" in text or "search for a member" in text:
            return {
                "actions": [
                    {"action": "fill", "selector": "#member-id", "value": member_id},
                    {"action": "click", "selector": "#search-button", "value": None},
                ]
            }

        if "member-name" in text or "account-status" in text or "ava nguyen" in text or "marcus hill" in text or "priya patel" in text:
            return {
                "actions": [
                    {"action": "read", "selector": "#member-name", "value": None},
                    {"action": "read", "selector": "#account-status", "value": None},
                    {"action": "read", "selector": "#account-balance", "value": None},
                ]
            }

        if "member-details" in url or "account summary" in text or "member name" in text:
            return {
                "actions": [
                    {"action": "read", "selector": "#member-name", "value": None},
                    {"action": "read", "selector": "#account-status", "value": None},
                    {"action": "read", "selector": "#account-balance", "value": None},
                ]
            }

        return {
            "actions": [
                {"action": "wait", "selector": "body", "value": None},
                {"action": "read", "selector": "#member-id", "value": None},
            ]
        }
