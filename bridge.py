# Thin glue only: builds agent.loop.User from the form, calls the REAL run(), returns JSON. No planning logic here.
import json
from agent.loop import User, run
_gate = None
def plan_json(form_json):
    global _gate
    f = json.loads(form_json)
    needs = ["ride_home"] + (["pet_care"] if f.get("pet") else []) + ["home_access"]
    friends = [x.strip() for x in f.get("friends", "").split(",") if x.strip()]
    pet = f.get("pet") or "my pet"
    tasks = [f"Feed {pet} twice a day while I'm in the hospital", f"Be my backup to feed {pet} if {friends[0] if friends else 'my first helper'} can't"]
    helpers = [{"name": n, "task": tasks[min(i, 1)], "need": "pet_care"} for i, n in enumerate(friends[:3])] if f.get("pet") else []
    msgs = []
    if f.get("escort"): msgs.append("My surgical team needs a responsible adult.")
    if f.get("message"): msgs.append(f["message"])
    user = User(name=f.get("name") or "Friend", area="Boston", needs=needs, helpers=helpers,
                comfortable_asking=not f.get("burden"), messages=msgs)
    plan, _gate = run(user)
    return json.dumps(plan)
def approve_json(item_id):
    item = _gate.approve(int(item_id), user_confirmed=True)
    try:
        _gate.send(item)
        refusal = None
    except PermissionError as e:
        refusal = str(e)
    return json.dumps({"item": item, "send_refused": refusal})
