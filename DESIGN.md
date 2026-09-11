# Design Notes for the Computer-Use Automation System

## 1. Why this design

This project uses a local demo banking application as a stand-in for a real institution back-office surface. The target is intentionally multi-step and realistic: search for a member, inspect account state, extract status/balance, and decide whether the outcome is a valid business result or a legitimate no-result case.

The overall design follows the assignment’s constraint: build a small but correct vertical slice that touches the real core requirements:

- goal-driven agent loop
- structured reusable artifact
- deterministic replay
- policy guardrails
- evidence capture
- human intervention path

We chose Python + Playwright because it gives a clean way to interact with a real UI, capture DOM state, and perform deterministic replay without forcing dependence on a specific browser framework beyond the actual automation layer.

## 2. Architecture

The system separates concerns into four layers:

1. Surface layer
   - a live UI (here: a local browser app)
   - actions include click, fill, read, wait, navigate

2. Planning layer
   - an LLM-driven planner or a local fallback planner decides the next step
   - the planner observes the page state and chooses actions based on visible page text and selectors

3. Capability layer
   - after a successful run, the system emits a typed artifact describing the flow, inputs, outputs, checkpoint, and policy
   - the artifact is serialized JSON and is reviewable by humans and callable by other agents

4. Runtime layer
   - replay engine executes the saved flow deterministically without LLM decisions
   - guardrails enforce allowed domains/actions
   - evidence logs and screenshots capture what happened when the run failed or stalled

This is a clean seam between:

- how the surface is perceived and acted upon
- what the capability contract says
- how replay executes in production
- when human intervention is required

## 3. Capability artifact design

The saved artifact is intentionally not just a raw step list. It is a typed capability contract with explicit inputs/outputs.

Example fields:

- `capability_id`: stable identifier, e.g. `member_account_summary`
- `goal`: purpose of the flow
- `target_url`: entry point or base route
- `inputs`: typed invocation params, e.g. `member_id`
- `outputs`: expected extracted values, e.g. `member_name`, `account_status`, `account_balance`
- `checkpoint`: the condition proving success, e.g. `#account-status` contains `Active`
- `policy`: rules applied to the run
- `steps`: ordered actions with target selectors, reasoning, and notes
- `metadata`: versioning and surface metadata

This matters because the artifact is a contract: a calling agent can understand what the capability does, what it needs, and what it returns, without needing to inspect raw screen automation internals.

## 4. Deterministic replay strategy

Replay is intentionally not a second LLM run. It is a direct execution of the saved step list against the same surface and it validates the checkpoint before returning outputs.

The replay engine is deterministic because it:

- uses stable CSS selectors for the demo app
- waits for known UI state before asserting success
- checks the checkpoint explicitly instead of assuming a click worked
- distinguishes expected business outcomes from hard failures

This is the production path.

### Result contract

The replay contract is designed around the banking domain reality described in the assignment:

- success: valid member found and summary returned
- business outcome: e.g. `member_account_found`, or a legitimate `no such member`
- recoverable condition: a transient load or known interstitial
- hard failure: unexpected state or permission problem that should stop execution and surface debugging evidence

This is important because “no such member” is not a crash; it is legitimate business output that the caller must know about.

## 5. Safety and policy guardrails

Safety is enforced explicitly in two ways:

- allowlist of domains and actions
- limited risk model for action types

In the project, the policy restricts actions to a known safe subset (`navigate`, `fill`, `click`, `wait`, `read`) and only permits local demo domains. This prevents the agent from wandering outside the approved surface.

We also redact sensitive runtime data before storing outputs or evidence. The project redacts account numbers and balances in the artifact/output layer. This is aligned with the assignment’s requirement to never persist raw sensitive data or secrets in artifacts/logs.

## 6. Evidence and observability

The system records structured logs and captures at least one rich failure signal.

The project stores:

- JSONL log of observations and actions
- screenshot on failure or escalation
- current page snapshot to help debug what the agent saw
- run summary with artifact path and outputs

This is enough to understand why a step failed and what the UI looked like at the time.

## 7. Human-in-the-loop escalation

The assignment expects the system to detect when it is stuck and hand off to a human. This design does not try to build a full co-browsing operator console; instead it creates a real handoff seam that is faithful to the requirement.

The system:

- detects a blocked or dead-end state
- raises an escalation with the goal, current URL, member ID, and screenshot
- preserves the live session context
- records the intervention and the reason for stoppage

This is the minimal but realistic model: automation pauses, a human takes over the same session, and after manual action the run can resume or stop cleanly.

## 8. Heterogeneity and multi-tenant design

The assignment explicitly says we should not build full multi-tenant or desktop support, but the core abstraction must not paint us into a corner.

### Surface abstraction

The key seam is between:

- the physical surface (web page, legacy app, desktop app)
- the execution steps captured in the artifact

The current implementation uses a `TargetRef` and action metadata. That abstraction can generalize beyond web to:

- legacy web apps with more fragile DOMs
- accessibility-tree-based surfaces
- desktop automation with screen coordinates / accessible controls

The artifact stores the action contract and target strategy, not a hard dependency on one UI technology. A different runtime can interpret the same artifact against a different surface as long as the meaning of the step remains the same.

### Multi-tenant reuse

A tenant-specific artifact can be versioned and specialized. The design pattern is:

- base artifact stored as a vendor-neutral capability definition
- tenant overrides for route differences, field labels, and locale variation
- drift detection by comparing selector signatures, page text markers, and success checkpoints

This allows hundreds of tenants to share the same core capability and specialize only the differences that matter. We do not re-record the entire flow per tenant unless the underlying app drifts materially.

## 9. Explicit choices and scope cuts

Chosen technologies:

- Python
- Playwright
- Pydantic models
- local demo banking app
- optional OpenAI API when available, with deterministic local fallback

This keeps the system small and correct while still touching the core assignment requirements.

Deliberate cuts:

- no full real-time co-browsing operator console
- no multi-tenant service architecture
- no desktop automation implementation
- no production deployment / queueing infrastructure

These are intentional because the assignment rewards a correct design and a working end-to-end core, not premature platform plumbing.

## 10. Why this qualifies as a good vertical slice

The project exercises the whole path the assignment cares about:

- a real goal is given
- the agent interacts with a live UI
- the run saves a capability artifact
- the artifact is replayed deterministically
- the program handles both success and failure modes
- a human escalation path exists
- the design is extensible to multi-tenant / heterogenous real-world environments

That is the right shape of a focused engineering submission.
