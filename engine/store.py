"""Task and event write operations for the Luix° coordination engine.

Writes are local to the checked-out project. No network or agent messaging.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from engine.coordinator import (
    EVENT_TO_STATUS, EVENT_ID_RE, TASK_ID_RE, TRANSITIONS,
    CoordinationError, audit, read_events, read_registry, utc_now,
)

def _next_event_id(events: list[dict[str, Any]]) -> str:
    nums = [int(m.group(1)) for e in events
            if isinstance(e.get("event_id"), str)
            and (m := re.fullmatch(r"EVT-([0-9]+)", e["event_id"]))]
    return f"EVT-{max(nums, default=0) + 1:06d}"

def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)

def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")
        stream.flush()

def create_task(registry_path: Path, event_path: Path, task: dict[str, Any],
                actor_id: str = "coordinator", channel: str = "local-engine") -> dict[str, Any]:
    registry = read_registry(registry_path)
    events = read_events(event_path)
    errors = []
    from engine.coordinator import validate_task
    errors.extend(validate_task(task))
    if errors:
        raise CoordinationError("; ".join(errors))
    if any(t.get("task_id") == task["task_id"] for t in registry["tasks"] if isinstance(t, dict)):
        raise CoordinationError(f"duplicate task_id: {task['task_id']}")
    if task["status"] != "draft":
        raise CoordinationError("new tasks must start in draft")
    event = {
        "event_id": _next_event_id(events), "timestamp_utc": utc_now(),
        "task_id": task["task_id"], "event_type": "task_created",
        "from_status": "draft", "to_status": "draft",
        "actor_id": actor_id, "channel": channel,
        "evidence_refs": [f"registry:{task['task_id']}"],
        "details": "Task registered locally; this does not mean it was sent to an agent."
    }
    # Append the audit event first; if registry write fails, audit will expose mismatch.
    _append_jsonl(event_path, event)
    registry["tasks"].append(task)
    _write_json(registry_path, registry)
    return event

def transition_task(registry_path: Path, event_path: Path, task_id: str,
                    event_type: str, actor_id: str, channel: str,
                    evidence_refs: list[str], details: str = "") -> dict[str, Any]:
    if event_type not in EVENT_TO_STATUS:
        raise CoordinationError(f"unknown event_type: {event_type}")
    registry = read_registry(registry_path)
    events = read_events(event_path)
    matches = [t for t in registry["tasks"] if isinstance(t, dict) and t.get("task_id") == task_id]
    if len(matches) != 1:
        raise CoordinationError(f"expected exactly one task {task_id}; found {len(matches)}")
    task = matches[0]
    current = task["status"]
    target = EVENT_TO_STATUS[event_type]
    if target not in TRANSITIONS.get(current, set()):
        raise CoordinationError(f"illegal transition {current} -> {target}")
    if target in {"sent", "received", "in_progress", "submitted", "accepted", "rejected"}:
        if not evidence_refs or not any(isinstance(x, str) and x.strip() for x in evidence_refs):
            raise CoordinationError(f"evidence required for transition to {target}")
    event = {
        "event_id": _next_event_id(events), "timestamp_utc": utc_now(),
        "task_id": task_id, "event_type": event_type,
        "from_status": current, "to_status": target,
        "actor_id": actor_id, "channel": channel,
        "evidence_refs": evidence_refs, "details": details,
    }
    # Append event before updating the registry; discrepancies remain detectable by audit.
    _append_jsonl(event_path, event)
    task["status"] = target
    _write_json(registry_path, registry)
    return event
