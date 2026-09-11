from __future__ import annotations

import argparse
import http.server
import json
import os
import socketserver
import threading
import time
from pathlib import Path

from src.automation.agent import AutomationAgent, EscalationRequired
from src.automation.artifacts import ArtifactStore
from src.automation.replay import ReplayEngine
from src.automation.policy import SafetyPolicy

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
EVIDENCE_DIR = ROOT / "evidence"
DEMO_DIR = ROOT / "demo_app"
DEMO_PORT = 8001

socketserver.TCPServer.allow_reuse_address = True


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DEMO_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:
        return


def start_demo_server(port: int = DEMO_PORT) -> None:
    httpd = socketserver.TCPServer(("127.0.0.1", port), QuietHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    print(f"Demo app running at http://127.0.0.1:{port}")
    return httpd


def run_demo(member_id: str) -> None:
    artifact_store = ArtifactStore(ARTIFACTS_DIR)
    agent = AutomationAgent(artifact_store, EVIDENCE_DIR, SafetyPolicy())
    server = start_demo_server(DEMO_PORT)
    try:
        result = agent.run(
            goal=f"Find the account summary for member {member_id} and confirm an active status.",
            target_url=f"http://127.0.0.1:{DEMO_PORT}",
            member_id=member_id,
        )
        print(json.dumps({"status": "success", "artifact": result["artifact_path"], "outputs": result["outputs"]}, indent=2))
    except EscalationRequired as exc:
        print(json.dumps({"status": "escalated", "reason": exc.reason, "context": exc.context}, indent=2))
    finally:
        server.shutdown()
        server.server_close()


def run_replay(artifact_path: str, member_id: str) -> None:
    store = ArtifactStore(ARTIFACTS_DIR)
    engine = ReplayEngine(store)
    server = start_demo_server(DEMO_PORT)
    try:
        result = engine.replay(artifact_path, {"member_id": member_id}, f"http://127.0.0.1:{DEMO_PORT}")
        print(json.dumps(result.model_dump(), indent=2))
    finally:
        server.shutdown()
        server.server_close()


def run_handoff_demo(member_id: str) -> None:
    artifact_store = ArtifactStore(ARTIFACTS_DIR)
    agent = AutomationAgent(artifact_store, EVIDENCE_DIR, SafetyPolicy())
    server = start_demo_server(DEMO_PORT)
    try:
        print("Simulating a stuck state; human operator is asked to approve the next step.")
        for _ in range(2):
            try:
                result = agent.run(
                    goal=f"Find the account summary for member {member_id} and confirm an active status.",
                    target_url=f"http://127.0.0.1:{DEMO_PORT}",
                    member_id=member_id,
                )
                print(json.dumps({"status": "success", "outputs": result["outputs"]}, indent=2))
                return
            except EscalationRequired as exc:
                print(json.dumps({"status": "escalated", "reason": exc.reason, "context": exc.context}, indent=2))
                print("Human resumed the run manually. Continuing...")
                time.sleep(1)
        print("No successful manual handoff completed in this demo.")
    finally:
        server.shutdown()
        server.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Computer-use automation demo")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Run an end-to-end goal-driven automation flow.")
    demo.add_argument("--member-id", required=True)

    replay = subparsers.add_parser("replay", help="Replay an existing artifact.")
    replay.add_argument("--artifact", required=True)
    replay.add_argument("--member-id", required=True)

    handoff = subparsers.add_parser("handoff", help="Demonstrate human escalation and resume flow.")
    handoff.add_argument("--member-id", required=True)
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    if args.command == "demo":
        run_demo(args.member_id)
    elif args.command == "replay":
        run_replay(args.artifact, args.member_id)
    elif args.command == "handoff":
        run_handoff_demo(args.member_id)
