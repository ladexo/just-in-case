"""Approval step: nothing leaves the agent without the user's explicit yes. The agent itself never sends."""
class ApprovalGate:
    def __init__(self):
        self.pending, self.approved, self.log = [], [], []

    def request(self, kind, content, recipients):
        item = {"id": len(self.pending) + len(self.approved) + 1, "kind": kind,
                "content": content, "recipients": list(recipients), "status": "awaiting_user"}
        self.pending.append(item); self.log.append(("requested", item["id"]))
        return item

    def approve(self, item_id, user_confirmed: bool):
        if not user_confirmed:
            raise PermissionError("The user must confirm before anything is shared.")
        item = next(i for i in self.pending if i["id"] == item_id)
        self.pending.remove(item); item["status"] = "approved_for_user_to_send"
        self.approved.append(item); self.log.append(("approved", item_id))
        return item

    def send(self, *_a, **_k):
        raise PermissionError("Just in Case never sends messages. The user sends the approved draft herself.")
