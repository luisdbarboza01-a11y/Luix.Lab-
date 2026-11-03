import json
import tempfile
import unittest
from pathlib import Path

from engine.coordinator import CoordinationError, read_registry, read_events
from engine.store import create_task, transition_task
from engine.receipts import receive_submission, validate_submission


def make_task():
    return {"task_id":"EXP-901","title":"Receipt test","objective":"Test receiving structured agent results",
            "permissions":["read-only"],"constraints":["No external actions"],
            "deliverables":["JSON result"],"acceptance_criteria":["Contains evidence"],
            "owner":"coordinator","status":"draft","protocol_version":"1.0"}


def make_submission():
    return {"task_id":"EXP-901","agent_id":"explorer","summary":"Completed scoped review",
            "actions_taken":["Read supplied document"],"sources":["docs/input.md"],
            "method":"Manual review","results":["Finding A"],"limitations":[],
            "blockers":[],"evidence_refs":["docs/input.md#L1-L10"]}


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.registry = self.root/"tasks"/"registry.json"
        self.events = self.root/"logs"/"events.jsonl"
        self.results = self.root/"tasks"/"results"
        self.registry.parent.mkdir(parents=True)
        self.events.parent.mkdir(parents=True)
        self.registry.write_text(json.dumps({"registry_version":"1.0","tasks":[]}), encoding="utf-8")
        self.events.write_text("", encoding="utf-8")
        create_task(self.registry,self.events,make_task())
        transition_task(self.registry,self.events,"EXP-901","queued","coordinator","test",[],"Queued")
        transition_task(self.registry,self.events,"EXP-901","sent","coordinator","test",["dispatch#1"],"Sent evidence")
        transition_task(self.registry,self.events,"EXP-901","received","explorer","test",["receipt#1"],"Receipt evidence")
        transition_task(self.registry,self.events,"EXP-901","started","explorer","test",["start#1"],"Start evidence")

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_submission_is_saved_and_status_submitted(self):
        path=receive_submission(self.registry,self.events,self.results,make_submission())
        self.assertTrue(path.exists())
        self.assertEqual(read_registry(self.registry)["tasks"][0]["status"],"submitted")
        self.assertEqual(read_events(self.events)[-1]["event_type"],"submitted")

    def test_missing_evidence_is_rejected(self):
        data=make_submission(); data["evidence_refs"]=[]
        with self.assertRaises(CoordinationError):
            receive_submission(self.registry,self.events,self.results,data)

    def test_unknown_task_is_rejected(self):
        data=make_submission(); data["task_id"]="EXP-902"
        with self.assertRaises(CoordinationError):
            receive_submission(self.registry,self.events,self.results,data)

    def test_duplicate_submission_is_rejected(self):
        receive_submission(self.registry,self.events,self.results,make_submission())
        with self.assertRaises(CoordinationError):
            receive_submission(self.registry,self.events,self.results,make_submission())

    def test_task_not_in_progress_is_rejected(self):
        data=make_submission()
        # revert fixture to queued status in both registry and event history is unnecessary:
        # use an independent draft task record to assert state gate.
        registry=read_registry(self.registry)
        registry["tasks"][0]["status"]="draft"
        self.registry.write_text(json.dumps(registry),encoding="utf-8")
        with self.assertRaises(CoordinationError):
            receive_submission(self.registry,self.events,self.results,data)


if __name__ == "__main__":
    unittest.main()
