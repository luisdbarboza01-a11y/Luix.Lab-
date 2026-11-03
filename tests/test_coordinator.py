import json
import tempfile
import unittest
from pathlib import Path

from engine.coordinator import audit, read_events, read_registry, validate_event, validate_task


def task(status="draft"):
    return {
        "task_id": "TST-001",
        "title": "Test task",
        "objective": "Verify event replay",
        "permissions": [],
        "constraints": ["No external actions"],
        "deliverables": ["Audit result"],
        "acceptance_criteria": ["Status matches replay"],
        "owner": "coordinator",
        "status": status,
        "protocol_version": "1.0",
    }


def event(event_id, event_type, before, after, evidence=None):
    return {
        "event_id": event_id,
        "timestamp_utc": "2026-11-03T12:00:00Z",
        "task_id": "TST-001",
        "event_type": event_type,
        "from_status": before,
        "to_status": after,
        "actor_id": "test-runner",
        "channel": "unit-test",
        "evidence_refs": evidence or [],
        "details": "Controlled test event",
    }


class CoordinatorTests(unittest.TestCase):
    def test_valid_task(self):
        self.assertEqual(validate_task(task()), [])

    def test_invalid_task_id(self):
        bad = task()
        bad["task_id"] = "bad id"
        self.assertTrue(validate_task(bad))

    def test_valid_event(self):
        self.assertEqual(validate_event(event("EVT-000001", "queued", "draft", "queued")), [])

    def test_task_rejects_blank_owner_and_non_string_permissions(self):
        bad = task()
        bad["owner"] = "  "
        bad["permissions"] = ["read-only", 7]
        self.assertTrue(any("owner must be a non-empty string" in e for e in validate_task(bad)))
        self.assertTrue(any("permissions must contain only non-empty strings" in e for e in validate_task(bad)))

    def test_task_rejects_duplicate_acceptance_criteria(self):
        bad = task()
        bad["acceptance_criteria"] = ["same", "same"]
        self.assertTrue(any("must not contain duplicates" in e for e in validate_task(bad)))

    def test_event_rejects_timezone_free_timestamp(self):
        bad = event("EVT-000001", "queued", "draft", "queued")
        bad["timestamp_utc"] = "2026-11-03T12:00:00"
        self.assertTrue(any("must include a timezone" in e for e in validate_event(bad)))

    def test_event_rejects_blank_evidence_reference(self):
        bad = event("EVT-000001", "sent", "queued", "sent", ["  "])
        self.assertTrue(any("evidence_refs must contain only non-empty strings" in e for e in validate_event(bad)))

    def test_valid_transition_replay(self):
        events = [event("EVT-000001", "queued", "draft", "queued")]
        self.assertEqual(audit({"tasks": [task("queued")]}, events), [])

    def test_sent_without_evidence_fails(self):
        events = [
            event("EVT-000001", "queued", "draft", "queued"),
            event("EVT-000002", "sent", "queued", "sent"),
        ]
        issues = audit({"tasks": [task("sent")]}, events)
        self.assertTrue(any("evidence required" in issue for issue in issues))

    def test_illegal_transition_fails(self):
        events = [event("EVT-000001", "accepted", "draft", "accepted", ["review.md"])]
        issues = audit({"tasks": [task("accepted")]}, events)
        self.assertTrue(any("illegal transition" in issue for issue in issues))

    def test_duplicate_task_id_fails(self):
        issues = audit({"tasks": [task(), task()]}, [])
        self.assertTrue(any("duplicate task_id" in issue for issue in issues))

    def test_registry_must_match_event_replay(self):
        events = [event("EVT-000001", "queued", "draft", "queued")]
        issues = audit({"tasks": [task("draft")]}, events)
        self.assertTrue(any("differs from event replay" in issue for issue in issues))

    def test_duplicate_event_id_fails(self):
        ev = event("EVT-000001", "queued", "draft", "queued")
        issues = audit({"tasks": [task("queued")]}, [ev, ev])
        self.assertTrue(any("duplicate event_id" in issue for issue in issues))

    def test_readers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "registry.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")
            (root / "events.jsonl").write_text("", encoding="utf-8")
            self.assertEqual(read_registry(root / "registry.json")["tasks"], [])
            self.assertEqual(read_events(root / "events.jsonl"), [])


    def test_complete_task_lifecycle(self):
        events = [
            event("EVT-000001", "task_created", "draft", "draft"),
            event("EVT-000002", "queued", "draft", "queued"),
            event("EVT-000003", "sent", "queued", "sent", ["message-log#1"]),
            event("EVT-000004", "received", "sent", "received", ["agent-reply#1"]),
            event("EVT-000005", "started", "received", "in_progress", ["agent-reply#1"]),
            event("EVT-000006", "submitted", "in_progress", "submitted", ["delivery#1"]),
            event("EVT-000007", "review_started", "submitted", "under_review"),
            event("EVT-000008", "accepted", "under_review", "accepted", ["review#1"]),
        ]
        self.assertEqual(audit({"tasks": [task("accepted")]}, events), [])

    def test_complete_lifecycle_rejects_missing_receipt_evidence(self):
        events = [
            event("EVT-000001", "queued", "draft", "queued"),
            event("EVT-000002", "sent", "queued", "sent", ["message-log#1"]),
            event("EVT-000003", "received", "sent", "received"),
        ]
        issues = audit({"tasks": [task("received")]}, events)
        self.assertTrue(any("evidence required" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
