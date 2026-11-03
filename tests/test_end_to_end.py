import json
import tempfile
import unittest
from pathlib import Path

from engine.coordinator import audit, read_events, read_registry
from engine.store import create_task, transition_task
from engine.queue import list_queued, build_dispatch_packet
from engine.receipts import receive_submission
from engine.reviewer import record_review


class FullLifecycleTests(unittest.TestCase):
    def test_task_creation_to_independent_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            registry=root/"tasks"/"registry.json"
            events=root/"logs"/"events.jsonl"
            results=root/"tasks"/"results"
            reviews=root/"tasks"/"reviews"
            registry.parent.mkdir(parents=True); events.parent.mkdir(parents=True)
            registry.write_text(json.dumps({"registry_version":"1.0","tasks":[]}),encoding="utf-8")
            events.write_text("",encoding="utf-8")

            task={"task_id":"SYS-001","title":"End-to-end test",
                  "objective":"Verify complete internal task lifecycle",
                  "permissions":["read-only"],"constraints":["No external actions"],
                  "deliverables":["Structured report"],"acceptance_criteria":["Evidence included","Method documented"],
                  "owner":"coordinator","assigned_agent":"analyst","status":"draft","protocol_version":"1.0"}

            create_task(registry,events,task)
            transition_task(registry,events,"SYS-001","queued","coordinator","test",[],"Queued")
            queued=list_queued(read_registry(registry))
            self.assertEqual(len(queued),1)
            packet=build_dispatch_packet(queued[0])
            self.assertEqual(packet["dispatch_state"],"prepared_not_sent")

            transition_task(registry,events,"SYS-001","sent","coordinator","manual-handoff",["handoff#1"],"Manually handed off")
            transition_task(registry,events,"SYS-001","received","analyst","manual-handoff",["ack#1"],"Agent receipt confirmed")
            transition_task(registry,events,"SYS-001","started","analyst","manual-handoff",["start#1"],"Execution confirmed")

            submission={"task_id":"SYS-001","agent_id":"analyst","summary":"Completed",
                        "actions_taken":["Reviewed input"],"sources":["input#1"],
                        "method":"Documented inspection","results":["Evidence included","Method documented"],
                        "limitations":[],"blockers":[],"evidence_refs":["input#1","output#1"]}
            receive_submission(registry,events,results,submission)

            review={"task_id":"SYS-001","reviewer_id":"auditor","decision":"accepted",
                    "criteria":{"Evidence included":True,"Method documented":True},
                    "evidence_refs":["review#1"],"notes":"Both criteria independently verified."}
            record_review(registry,events,results,reviews,review)

            final_registry=read_registry(registry)
            final_events=read_events(events)
            self.assertEqual(final_registry["tasks"][0]["status"],"accepted")
            self.assertEqual(final_events[-1]["to_status"],"accepted")
            self.assertEqual(audit(final_registry,final_events),[])


if __name__=="__main__": unittest.main()
