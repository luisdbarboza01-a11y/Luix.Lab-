import json
import tempfile
import unittest
from pathlib import Path

from engine.coordinator import audit, CoordinationError, read_events, read_registry
from engine.store import create_task, transition_task


def make_task(task_id="OPS-001"):
    return {
        "task_id": task_id, "title": "Operational test", "objective": "Test task/event writes",
        "permissions": [], "constraints": ["No external actions"],
        "deliverables": ["Recorded status"], "acceptance_criteria": ["Audit passes"],
        "owner": "coordinator", "status": "draft", "protocol_version": "1.0"
    }


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.registry = self.root / "tasks" / "registry.json"
        self.events = self.root / "logs" / "events.jsonl"
        self.registry.parent.mkdir(parents=True)
        self.events.parent.mkdir(parents=True)
        self.registry.write_text(json.dumps({"registry_version": "1.0", "tasks": []}), encoding="utf-8")
        self.events.write_text("", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_task_records_event_and_registry(self):
        create_task(self.registry, self.events, make_task())
        self.assertEqual(read_registry(self.registry)["tasks"][0]["status"], "draft")
        self.assertEqual(len(read_events(self.events)), 1)
        self.assertEqual(audit(read_registry(self.registry), read_events(self.events)), [])

    def test_duplicate_task_is_rejected(self):
        create_task(self.registry, self.events, make_task())
        with self.assertRaises(CoordinationError):
            create_task(self.registry, self.events, make_task())

    def test_transition_updates_both_records(self):
        create_task(self.registry, self.events, make_task())
        transition_task(self.registry, self.events, "OPS-001", "queued",
                        "coordinator", "unit-test", [], "Queued for dispatch")
        transition_task(self.registry, self.events, "OPS-001", "sent",
                        "coordinator", "unit-test", ["dispatch-log#1"], "Dispatch evidence")
        self.assertEqual(read_registry(self.registry)["tasks"][0]["status"], "sent")
        self.assertEqual(audit(read_registry(self.registry), read_events(self.events)), [])

    def test_sent_without_evidence_is_rejected_without_mutation(self):
        create_task(self.registry, self.events, make_task())
        transition_task(self.registry, self.events, "OPS-001", "queued",
                        "coordinator", "unit-test", [], "Queued")
        before = len(read_events(self.events))
        with self.assertRaises(CoordinationError):
            transition_task(self.registry, self.events, "OPS-001", "sent",
                            "coordinator", "unit-test", [], "No evidence")
        self.assertEqual(len(read_events(self.events)), before)

    def test_illegal_transition_is_rejected(self):
        create_task(self.registry, self.events, make_task())
        with self.assertRaises(CoordinationError):
            transition_task(self.registry, self.events, "OPS-001", "accepted",
                            "coordinator", "unit-test", ["review#1"], "Illegal jump")


if __name__ == "__main__":
    unittest.main()
