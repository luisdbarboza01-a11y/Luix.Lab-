"""Independent acceptance review for submitted task results.

The reviewer must be distinct from the submitting agent. This records a
criteria-based decision; it does not claim scientific truth beyond the evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.coordinator import CoordinationError, read_registry
from engine.store import transition_task


def validate_review(review: dict[str, Any], task: dict[str, Any], submission: dict[str, Any]) -> list[str]:
    errors = []
    for field in ("task_id", "reviewer_id", "decision", "criteria", "evidence_refs", "notes"):
        if field not in review:
            errors.append(f"missing field: {field}")
    if review.get("task_id") != task.get("task_id"):
        errors.append("review task_id does not match task")
    if review.get("reviewer_id") == submission.get("agent_id"):
        errors.append("reviewer must be independent from submitting agent")
    if review.get("decision") not in {"accepted", "rejected"}:
        errors.append("decision must be accepted or rejected")
    criteria = review.get("criteria")
    if not isinstance(criteria, dict):
        errors.append("criteria must be an object mapping criterion text to boolean")
    else:
        expected = set(task.get("acceptance_criteria", []))
        actual = set(criteria)
        if actual != expected:
            errors.append("review criteria must cover every acceptance criterion exactly")
        if any(not isinstance(value, bool) for value in criteria.values()):
            errors.append("every criterion result must be boolean")
        if review.get("decision") == "accepted" and criteria and not all(criteria.values()):
            errors.append("cannot accept while any acceptance criterion is false")
        if review.get("decision") == "rejected" and criteria and all(criteria.values()):
            errors.append("cannot reject when all acceptance criteria pass")
    if not isinstance(review.get("evidence_refs"), list) or not review.get("evidence_refs"):
        errors.append("review evidence_refs must be a non-empty array")
    if not isinstance(review.get("notes"), str):
        errors.append("notes must be a string")
    return errors


def record_review(registry_path: Path, event_path: Path, results_dir: Path,
                  reviews_dir: Path, review: dict[str, Any], channel: str = "independent-review") -> Path:
    registry = read_registry(registry_path)
    matches = [t for t in registry["tasks"] if isinstance(t, dict)
               and t.get("task_id") == review.get("task_id")]
    if len(matches) != 1:
        raise CoordinationError("review references unknown or duplicate task")
    task = matches[0]
    if task["status"] != "submitted":
        raise CoordinationError("only submitted tasks can enter independent review")
    result_path = results_dir / f"{task['task_id']}.json"
    if not result_path.exists():
        raise CoordinationError("submitted result artifact is missing")
    submission = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate_review(review, task, submission)
    if errors:
        raise CoordinationError("; ".join(errors))
    reviews_dir.mkdir(parents=True, exist_ok=True)
    destination = reviews_dir / f"{task['task_id']}.json"
    if destination.exists():
        raise CoordinationError("a review already exists for this task")
    payload = dict(review)
    payload["reviewed_at_utc"] = __import__("engine.coordinator", fromlist=["utc_now"]).utc_now()
    temp = destination.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(destination)
    try:
        transition_task(registry_path, event_path, task["task_id"], "review_started",
                        review["reviewer_id"], channel,
                        [f"file:{result_path.as_posix()}"], "Independent review started.")
        transition_task(registry_path, event_path, task["task_id"], review["decision"],
                        review["reviewer_id"], channel,
                        [f"file:{destination.as_posix()}"], review["notes"])
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return destination
