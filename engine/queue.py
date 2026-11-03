"""Read-only dispatch queue for tasks already marked queued.

This module prepares handoff packets; it does not contact agents or mark tasks sent.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from engine.coordinator import CoordinationError, REGISTRY, read_registry, validate_task


def list_queued(registry: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = registry.get("tasks", [])
    queued = []
    for task in tasks:
        if not isinstance(task, dict):
            raise CoordinationError("registry contains a non-object task")
        errors = validate_task(task)
        if errors:
            raise CoordinationError(f"{task.get('task_id', 'unknown')}: " + "; ".join(errors))
        if task["status"] == "queued":
            queued.append(task)
    return sorted(queued, key=lambda item: item["task_id"])


def build_dispatch_packet(task: dict[str, Any]) -> dict[str, Any]:
    errors = validate_task(task)
    if errors:
        raise CoordinationError("; ".join(errors))
    if task["status"] != "queued":
        raise CoordinationError("only queued tasks can enter the dispatch queue")
    return {
        "packet_version": "1.0",
        "task_id": task["task_id"],
        "assigned_agent": task.get("assigned_agent"),
        "objective": task["objective"],
        "context": task.get("context", ""),
        "inputs": task.get("inputs", []),
        "permissions": task["permissions"],
        "constraints": task["constraints"],
        "deliverables": task["deliverables"],
        "acceptance_criteria": task["acceptance_criteria"],
        "protocol_version": task["protocol_version"],
        "dispatch_state": "prepared_not_sent",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect queued Luix Lab tasks and prepare handoff packets.")
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--task-id")
    args = parser.parse_args(argv)
    try:
        registry = read_registry(args.registry)
        queued = list_queued(registry)
        if args.task_id:
            queued = [task for task in queued if task["task_id"] == args.task_id]
        packets = [build_dispatch_packet(task) for task in queued]
    except (OSError, json.JSONDecodeError, CoordinationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"queue_count": len(packets), "packets": packets}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
