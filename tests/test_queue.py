import unittest
from engine.coordinator import CoordinationError
from engine.queue import list_queued, build_dispatch_packet


def task(task_id, status):
    return {
        "task_id": task_id, "title": "Queue test", "objective": "Verify dispatch queue behavior",
        "permissions": ["read-only"], "constraints": ["No external actions"],
        "deliverables": ["Handoff packet"], "acceptance_criteria": ["Packet preserves task ID"],
        "owner": "coordinator", "status": status, "protocol_version": "1.0",
        "assigned_agent": "explorer"
    }


class QueueTests(unittest.TestCase):
    def test_only_queued_tasks_are_listed(self):
        result = list_queued({"tasks": [task("OPS-002", "draft"), task("OPS-001", "queued")]})
        self.assertEqual([item["task_id"] for item in result], ["OPS-001"])

    def test_queue_is_sorted_by_task_id(self):
        result = list_queued({"tasks": [task("OPS-003", "queued"), task("OPS-001", "queued")]})
        self.assertEqual([item["task_id"] for item in result], ["OPS-001", "OPS-003"])

    def test_packet_preserves_constraints_and_permissions(self):
        packet = build_dispatch_packet(task("OPS-001", "queued"))
        self.assertEqual(packet["permissions"], ["read-only"])
        self.assertEqual(packet["constraints"], ["No external actions"])
        self.assertEqual(packet["dispatch_state"], "prepared_not_sent")

    def test_non_queued_task_cannot_be_dispatched(self):
        with self.assertRaises(CoordinationError):
            build_dispatch_packet(task("OPS-001", "draft"))

    def test_invalid_registry_task_blocks_queue(self):
        invalid = task("bad id", "queued")
        with self.assertRaises(CoordinationError):
            list_queued({"tasks": [invalid]})


if __name__ == "__main__":
    unittest.main()
