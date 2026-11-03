import json
import tempfile
import unittest
from pathlib import Path

from engine.coordinator import CoordinationError, read_registry, read_events
from engine.store import create_task, transition_task
from engine.receipts import receive_submission
from engine.reviewer import record_review, validate_review


def task():
    return {"task_id":"AUD-901","title":"Review test","objective":"Test independent review",
            "permissions":["read-only"],"constraints":["No external actions"],
            "deliverables":["Structured result"],"acceptance_criteria":["Criterion A","Criterion B"],
            "owner":"coordinator","status":"draft","protocol_version":"1.0"}


def submission():
    return {"task_id":"AUD-901","agent_id":"analyst","summary":"Result",
            "actions_taken":["Reviewed"],"sources":["source#1"],"method":"Inspection",
            "results":["A","B"],"limitations":[],"blockers":[],"evidence_refs":["source#1"]}


def review(decision="accepted", reviewer="auditor", criteria=None):
    return {"task_id":"AUD-901","reviewer_id":reviewer,"decision":decision,
            "criteria":criteria or {"Criterion A":True,"Criterion B":True},
            "evidence_refs":["review#1"],"notes":"Independent criteria check."}


class ReviewerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.registry=self.root/"tasks"/"registry.json"
        self.events=self.root/"logs"/"events.jsonl"
        self.results=self.root/"tasks"/"results"
        self.reviews=self.root/"tasks"/"reviews"
        self.registry.parent.mkdir(parents=True); self.events.parent.mkdir(parents=True)
        self.registry.write_text(json.dumps({"registry_version":"1.0","tasks":[]}),encoding="utf-8")
        self.events.write_text("",encoding="utf-8")
        create_task(self.registry,self.events,task())
        for event, actor, refs in [
            ("queued","coordinator",[]),("sent","coordinator",["dispatch#1"]),
            ("received","analyst",["receipt#1"]),("started","analyst",["start#1"])
        ]:
            transition_task(self.registry,self.events,"AUD-901",event,actor,"test",refs,event)
        receive_submission(self.registry,self.events,self.results,submission())

    def tearDown(self): self.tmp.cleanup()

    def test_independent_acceptance_updates_status(self):
        path=record_review(self.registry,self.events,self.results,self.reviews,review())
        self.assertTrue(path.exists())
        self.assertEqual(read_registry(self.registry)["tasks"][0]["status"],"accepted")
        self.assertEqual(read_events(self.events)[-1]["event_type"],"accepted")

    def test_submitter_cannot_review_own_work(self):
        with self.assertRaises(CoordinationError):
            record_review(self.registry,self.events,self.results,self.reviews,review(reviewer="analyst"))

    def test_acceptance_requires_all_criteria(self):
        bad=review(criteria={"Criterion A":True,"Criterion B":False})
        with self.assertRaises(CoordinationError):
            record_review(self.registry,self.events,self.results,self.reviews,bad)

    def test_review_must_cover_all_criteria(self):
        bad=review(criteria={"Criterion A":True})
        with self.assertRaises(CoordinationError):
            record_review(self.registry,self.events,self.results,self.reviews,bad)

    def test_rejection_requires_failed_criterion(self):
        bad=review(decision="rejected")
        with self.assertRaises(CoordinationError):
            record_review(self.registry,self.events,self.results,self.reviews,bad)


if __name__=="__main__": unittest.main()
