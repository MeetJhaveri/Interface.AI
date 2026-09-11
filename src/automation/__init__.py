"""Automation package for the computer-use demo."""

from .agent import AutomationAgent
from .policy import SafetyPolicy
from .schemas import CapabilityArtifact

__all__ = ["AutomationAgent", "CapabilityArtifact", "SafetyPolicy"]
