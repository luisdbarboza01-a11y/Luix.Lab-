"""Luix° AI Network coordination engine v1.

Standard-library-only validation and event replay. This module does not send
messages to agents or execute external actions; it validates recorded evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tasks" / "registry.json"
EVENT_LOG = ROOT / "logs" / "events.jsonl"

STATUSES = {
    "draft", "queued", "sent", "received", "in_progress", "blocked",
    "submitted", "under_review", "accepted", "rejected", "cancelled"
}
EVENT_TO_STATUS = {
    "task_created": "draft",
    "queued": "queued",
    "sent": "sent",
    "received": "received",
    "started": "in_progress",
    "blocked": "blocked",
    "submitted": "submitted",
    "review_started": "under_review",
    "accepted": "accepted",
    "rejected": "rejected",
    "cancelled": "cancelled",
}
TRANSITIONS = {
    "draft": {"queued", "cancelled"},
    "queued": {"sent", "cancelled"},
    "sent": {"received", "blocked", "cancelled"},
    "received": {"in_progress", "blocked", "cancelled"},
    "in_progress": {"submitted", "blocked", "cancelled"},
    "blocked": {"queued", "cancelled"},
    "submitted": {"under_review", "blocked"},
    "under_review": {"accepted", "rejected", "blocked"},
    "rejected": {"queued", "cancelled"},
    "accepted": set(),
    "cancelled": set(),
}
TASK_ID_RE = re.compile(r"^[A-Z]{2,8}-[0-9]{3,6}$")
EVENT_ID_RE = re.compile(r"^EVT-[0-9]{6,}$")


class CoordinationError(Exception):
    """Raised when a requested state change violates the protocol."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_registry(path: Path = REGISTRY) -> dict[str, Any]:
    if not path.exists():
        return {"registry_version": "1.0", "tasks": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        raise CoordinationError("Registry must be an object with a tasks array.")
    return data


def read_events(path: Path = EVENT_LOG) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CoordinationError(f"Invalid JSON in event log line {line_no}: {exc}") from exc
        if not isinstance(event, dict):
            raise CoordinationError(f"Event log line {line_no} must be a JSON object.")
        events.append(event)
    return events


def validate_task(task: dict[str, Any]) -> list[str]:
    errors = []
    required = ("task_id", "title", "objective", "permissions", "constraints",
                "deliverables", "acceptance_criteria", "owner", "status", "protocol_version")
    for field in required:
        if field not in task:
            errors.append(f"missing required field: {field}")
    task_id = task.get("task_id")
    if task_id is not None and (not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id)):
        errors.append("task_id must match PREFIX-000")
    if task.get("status") not in STATUSES:
        errors.append("invalid task status")
    for field in ("permissions", "constraints", "deliverables", "acceptance_criteria"):
        if field in task and not isinstance(task[field], list):
            errors.append(f"{field} must be an array")
    if task.get("protocol_version") != "1.0":
        errors.append("protocol_version must be 1.0")
    return errors


def validate_event(event: dict[str, Any]) -> list[str]:
    errors = []
    for field in ("event_id", "timestamp_utc", "task_id", "event_type",
                  "actor_id", "channel", "evidence_refs", "details"):
        if field not in event:
            errors.append(f"missing event field: {field}")
    if "event_id" in event and (not isinstance(event["event_id"], str)
                                or not EVENT_ID_RE.fullmatch(event["event_id"])):
        errors.append("event_id must match EVT-000000")
    if event.get("task_id") and (not isinstance(event["task_id"], str)
                                 or not TASK_ID_RE.fullmatch(event["task_id"])):
        errors.append("invalid event task_id")
    if event.get("event_type") not in EVENT_TO_STATUS:
        errors.append("invalid event_type")
    if "evidence_refs" in event and not isinstance(event["evidence_refs"], list):
        errors.append("evidence_refs must be an array")
    try:
        datetime.fromisoformat(str(event.get("timestamp_utc", "")).replace("Z", "+00:00"))
    except ValueError:
        errors.append("timestamp_utc must be ISO-8601")
    return errors


def _evidence_sufficient(event: dict[str, Any]) -> bool:
    """Conservative evidence gate for externally meaningful transitions."""
    target = EVENT_TO_STATUS.get(event.get("event_type"))
    refs = event.get("evidence_refs")
    if target in {"sent", "received", "in_progress", "submitted", "accepted", "rejected"}:
        return isinstance(refs, list) and any(isinstance(x, str) and x.strip() for x in refs)
    return True


def audit(registry: dict[str, Any], events: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    tasks = registry.get("tasks", [])
    by_id: dict[str, dict[str, Any]] = {}
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            issues.append(f"registry task #{index + 1} is not an object")
            continue
        for error in validate_task(task):
            issues.append(f"{task.get('task_id', f'task#{index + 1}')}: {error}")
        task_id = task.get("task_id")
        if task_id in by_id:
            issues.append(f"duplicate task_id: {task_id}")
        else:
            by_id[task_id] = task

    seen_event_ids = set()
    current: dict[str, str] = {}
    for index, event in enumerate(events):
        label = event.get("event_id", f"event#{index + 1}") if isinstance(event, dict) else f"event#{index + 1}"
        if not isinstance(event, dict):
            issues.append(f"{label}: event is not an object")
            continue
        for error in validate_event(event):
            issues.append(f"{label}: {error}")
        event_id = event.get("event_id")
        if event_id in seen_event_ids:
            issues.append(f"duplicate event_id: {event_id}")
        seen_event_ids.add(event_id)
        task_id = event.get("task_id")
        if task_id not in by_id:
            issues.append(f"{label}: references unknown task_id {task_id}")
            continue
        if not _evidence_sufficient(event):
            issues.append(f"{label}: evidence required for transition to {EVENT_TO_STATUS.get(event.get('event_type'))}")
        target = EVENT_TO_STATUS.get(event.get("event_type"))
        if target is None:
            continue
        prior = current.get(task_id, "draft")
        declared_from = event.get("from_status")
        declared_to = event.get("to_status", target)
        if declared_from != prior:
            issues.append(f"{label}: from_status {declared_from!r} does not match replayed status {prior!r}")
        if declared_to != target:
            issues.append(f"{label}: to_status must be {target!r}")
        if target not in TRANSITIONS.get(prior, set()) and not (prior == "draft" and target == "draft" and event.get("event_type") == "task_created"):
            issues.append(f"{label}: illegal transition {prior} -> {target}")
        else:
            current[task_id] = target

    for task_id, task in by_id.items():
        replayed = current.get(task_id, "draft")
        if task.get("status") != replayed:
            issues.append(f"{task_id}: registry status {task.get('status')!r} differs from event replay {replayed!r}")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Luix AI Network task registry and event log.")
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--events", type=Path, default=EVENT_LOG)
    args = parser.parse_args(argv)
    try:
        registry = read_registry(args.registry)
        events = read_events(args.events)
        issues = audit(registry, events)
    except (OSError, json.JSONDecodeError, CoordinationError) as exc:
        print(f"ERROR: {exc}")
        return 2
    if issues:
        print(f"AUDIT FAILED: {len(issues)} issue(s)")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(f"AUDIT PASSED: {len(registry.get('tasks', []))} task(s), {len(events)} event(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
