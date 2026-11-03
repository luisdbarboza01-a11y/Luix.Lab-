"""Validated result intake for the Luix° task protocol.

Stores an agent's structured submission and records a submitted event.
It does not contact agents or decide scientific correctness.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.coordinator import CoordinationError, read_registry, read_events, utc_now
from engine.store import transition_task


REQUIRED = ("task_id", "agent_id", "summary", "actions_taken", "sources",
            "method", "results", "limitations", "blockers", "evidence_refs")


def validate_submission(submission: dict[str, Any]) -> list[str]:
    errors = []
    for key in REQUIRED:
        if key not in submission:
            errors.append(f"missing field: {key}")
    for key in ("task_id", "agent_id", "summary", "method"):
        if key in submission and (not isinstance(submission[key], str) or not submission[key].strip()):
            errors.append(f"{key} must be a non-empty string")
    for key in ("actions_taken", "sources", "results", "limitations", "blockers", "evidence_refs"):
        if key in submission and not isinstance(submission[key], list):
            errors.append(f"{key} must be an array")
    if isinstance(submission.get("evidence_refs"), list) and not submission["evidence_refs"]:
        errors.append("evidence_refs must not be empty")
    return errors


def receive_submission(registry_path: Path, event_path: Path, results_dir: Path,
                       submission: dict[str, Any], channel: str = "result-inbox") -> Path:
    errors = validate_submission(submission)
    if errors:
        raise CoordinationError("; ".join(errors))
    registry = read_registry(registry_path)
    matches = [t for t in registry["tasks"] if isinstance(t, dict)
               and t.get("task_id") == submission["task_id"]]
    if len(matches) != 1:
        raise CoordinationError(f"unknown or duplicate task: {submission['task_id']}")
    task = matches[0]
    if task["status"] != "in_progress":
        raise CoordinationError("only in_progress tasks can submit results")
    if submission["task_id"] in {p.stem for p in results_dir.glob("*.json")}:
        raise CoordinationError("a result already exists for this task; revisions require a separate review process")
    payload = dict(submission)
    payload["received_at_utc"] = utc_now()
    results_dir.mkdir(parents=True, exist_ok=True)
    destination = results_dir / f"{submission['task_id']}.json"
    temp = destination.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(destination)
    try:
        transition_task(registry_path, event_path, submission["task_id"], "submitted",
                        submission["agent_id"], channel,
                        [f"file:{destination.as_posix()}"], "Structured agent result received.")
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return destination
