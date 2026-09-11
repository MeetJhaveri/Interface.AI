from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TargetRef(BaseModel):
    strategy: Literal["css", "xpath", "text", "role"]
    value: str
    description: str


class ActionStep(BaseModel):
    step_id: str
    action_type: Literal["navigate", "fill", "click", "wait", "read"]
    target: TargetRef
    value: Optional[str] = None
    expected_text: Optional[str] = None
    notes: str = ""


class CapabilityArtifact(BaseModel):
    schema_version: str = "1.0"
    capability_id: str
    goal: str
    target_url: str
    inputs: Dict[str, str] = Field(default_factory=dict)
    outputs: Dict[str, str] = Field(default_factory=dict)
    checkpoint: Dict[str, Any] = Field(default_factory=dict)
    policy: Dict[str, Any] = Field(default_factory=dict)
    steps: List[ActionStep] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReplayResult(BaseModel):
    success: bool
    status: str
    outputs: Dict[str, Any] = Field(default_factory=dict)
    business_outcome: Optional[str] = None
    error: Optional[str] = None
    evidence_path: Optional[str] = None
