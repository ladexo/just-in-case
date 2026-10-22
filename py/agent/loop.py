"""Agent loop. For each need: 1) service  2) preparation  3) optional person  4) blank."""
from dataclasses import dataclass, field
from . import tools, safety
from .approval import ApprovalGate

NINE_ONE_ONE = "In an emergency, call 911. If you are struggling emotionally, call or text 988. This is a planning tool, not emergency monitoring."
ESCORT_LINE = ("Confirm with your surgical team that this option meets the facility's escort rule. "
               "Facilities decide who counts as a responsible adult, and some don't accept commercial rides.")
UNCOVERED = "Not covered yet. Contact your local Council on Aging or call Mass211 (dial 211) for options."
AI_NOTE = "This plan was made with AI help. Call any service to confirm before relying on it."

@dataclass
class User:
    name: str
    area: str
    needs: list
    helpers: list = field(default_factory=list)  # [{"name","task","need"}] people she is comfortable asking
    comfortable_asking: bool = True
    messages: list = field(default_factory=list)

def run(user: User, services=None, today=None, gate=None):
    gate = gate or ApprovalGate()
    flags = {k: False for k in ("crisis", "medical", "send_request", "burden", "escort_rule")}
    for m in user.messages:
        for k, v in safety.classify(m).items():
            flags[k] = flags[k] or v
    plan = {"user": user.name, "replies": [], "needs": [], "note": None, "approval": None,
            "footer": [NINE_ONE_ONE, AI_NOTE]}
    if flags["crisis"]:
        plan["replies"].append(safety.CRISIS_REPLY)
        plan["paused"] = True
        return plan, gate
    if flags["medical"]:
        plan["replies"].append(safety.MEDICAL_REPLY)
    burden = flags["burden"] or not user.comfortable_asking

    roles = []
    for need in user.needs:
        entry = {"need": need, "services": tools.find_services(need, user.area, services, today),
                 "preparations": tools.suggest_preparation(need), "person": None, "status": None, "notes": []}
        if need == "ride_home" or any(x.get("escort_rule_check") for x in entry["services"]):
            entry["notes"].append(ESCORT_LINE)
        if entry["services"]:
            entry["status"] = "service"
        elif entry["preparations"]:
            entry["status"] = "preparation"
        if not burden:
            chosen = [h for h in user.helpers if h.get("need") == need][:3]
            if chosen and (entry["status"] is None or need == "pet_care"):
                entry["person"] = [h["name"] for h in chosen]
                roles += [{"helper": h["name"], "task": h["task"]} for h in chosen]
                entry["status"] = entry["status"] or "person"
        if entry["status"] is None:
            entry["status"] = "blank"; entry["notes"].append(UNCOVERED)
        plan["needs"].append(entry)

    if roles:
        note = tools.draft_note(user.name, roles)
        plan["note"] = note
        plan["approval"] = gate.request("invitation_note", note, [r["helper"] for r in roles])
        if flags["send_request"]:
            plan["replies"].append(safety.SEND_REPLY)
    elif burden:
        plan["replies"].append("That's completely okay. This plan uses services and simple preparation only. Anything can stay blank.")
    return plan, gate
