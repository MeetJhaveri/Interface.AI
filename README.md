# Interface.AI — Computer-Use Automation System

A compact computer-use automation system designed around the core requirements of the assignment: goal-driven UI automation, structured capability artifacts, deterministic replay, safety policies, evidence capture, and human escalation.

## Objective

This project demonstrates an end-to-end automation workflow for a banking-style member lookup system. The system:

- accepts a user goal and target surface
- observes the live UI state
- decides the next action using an LLM-assisted planner
- interacts with a real browser surface
- records the successful run as a typed, reviewable capability artifact
- replays the artifact deterministically without invoking the LLM
- detects failure states and captures evidence
- escalates to a human operator when the run becomes blocked or unsafe

## Architecture

The implementation is organized into a small, focused set of layers:

- Surface layer: browser automation against a local demo application
- Planning layer: LLM-backed decision-making with a deterministic fallback
- Capability layer: typed artifact schema for reusable workflows
- Replay layer: production path for saved capabilities
- Safety layer: guardrails, allowlisting, and redaction
- Evidence layer: logs, screenshots, and run snapshots
- Handoff layer: human intervention and resume flow

## Features

- Goal-driven agent loop
- Structured capability artifact
- Deterministic replay engine
- Policy guardrails
- Redaction of sensitive values
- Failure evidence capture
- Human-in-the-loop escalation
- Design notes for extensibility to multi-tenant and heterogeneous surfaces

## Project Structure

- `main.py` — command-line entry point
- `src/automation/` — automation, replay, artifact, policy, evidence logic
- `demo_app/` — local mock banking app used as the automated target
- `artifacts/` — saved capability artifacts
- `evidence/` — execution logs and screenshots
- `DESIGN.md` — architecture and design rationale
- `.env.example` — template for environment configuration

## Setup

### Prerequisites

- Python 3.10+
- Playwright browser dependencies

### Install dependencies

```bash
cd /Users/diyashah/Desktop/Project
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

### Environment configuration

Create a local `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Do not commit the real `.env` file. Use `.env.example` as the safe template.

## Usage

### End-to-end demo

```bash
python3 main.py demo --member-id 10021
```

### Replay a saved artifact

```bash
python3 main.py replay --artifact artifacts/member_account_summary.json --member-id 10021
```

### Human escalation demo

```bash
python3 main.py handoff --member-id 99999
```

## Notes

- The demo app runs locally at `http://127.0.0.1:8001`
- The implementation is intentionally scoped as a focused vertical slice rather than a broad platform build
- The design and extensibility rationale are documented in `DESIGN.md`

## Public Repository

https://github.com/MeetJhaveri/Interface.AI
