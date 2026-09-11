# Computer-Use Automation System

This project implements a compact computer-use automation system that follows the assignment requirements:

- goal-driven agent loop against a live UI
- structured, typed capability artifact
- deterministic replay engine
- policy guardrails and redaction
- failure evidence and screenshots
- human-in-the-loop escalation
- design notes for multi-tenant and heterogeneous surfaces

## Demo target

The project uses a local demo banking app served from `demo_app/`. It exercises a realistic multi-step flow:

1. Search for a member
2. Open the member details page
3. Read account status/balance
4. Confirm a valid business outcome or a legitimate no-result outcome

## Commands

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

Run the full demo end-to-end:

```bash
python3 main.py demo --member-id 10021
```

Replay a saved artifact:

```bash
python3 main.py replay --artifact artifacts/member_account_summary.json --member-id 10021
```

Run the human handoff demo:

```bash
python3 main.py handoff --member-id 99999
```

## Important notes

- The system uses an optional OpenAI API when `OPENAI_API_KEY` is available.
- If no key is present, it falls back to a deterministic local planner so the app still runs.
- Evidence for failed runs is stored under `evidence/`.
- Replay artifacts are stored under `artifacts/`.
- The demo app is served at `http://127.0.0.1:8001`.

## Design summary

The project keeps a clean seam between:

- surface perception and action
- recorded capability artifact
- replay execution engine
- safety policy
- human escalation

This makes it straightforward to later adapt the same design to a legacy enterprise app or a desktop surface.

## Design write-up

The project design and architecture notes are documented in `DESIGN.md`.

That document covers:

- why the chosen stack works for enterprise UI automation
- how the artifact contract is structured
- replay determinism and checkpointing
- safety guardrails and redaction
- human escalation and handoff strategy
- how the design extends to legacy and multi-tenant systems
