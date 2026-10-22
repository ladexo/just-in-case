"""The three tools. Every service the agent mentions comes from services.json by ID; nothing is invented."""
import json, datetime
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "services.json"
STALE_DAYS = 365

PREPARATIONS = {
    "spare_key": "Put a spare key in a lockbox. Keep the code on your paper card only, never in an app.",
    "emergency_kit": "Stock an emergency kit: water, flashlight, batteries, 3 days of medicine, phone charger.",
    "pet_care": "Write down your pet's food, amount and feeding times, and leave it with the pet supplies.",
    "power_outage": "Ask your utility about its program for customers with medical needs.",
}

def load_services(path=DATA):
    d = json.loads(Path(path).read_text())
    rows = d["services"] if isinstance(d, dict) else d
    default_date = d.get("verified_on", "1970-01-01") if isinstance(d, dict) else "1970-01-01"
    out = []
    for r in rows:
        needs = r.get("needs", r.get("need", []))
        areas = r.get("areas", r.get("area", []))
        out.append({**r, "needs": [needs] if isinstance(needs, str) else needs,
                    "areas": [areas] if isinstance(areas, str) else (areas or []),
                    "last_verified": r.get("last_verified", default_date)})
    return out

def _area_ok(user_area, areas):
    wide = ("massachusetts", "customers", "service area")
    return not areas or any(w in a.lower() for a in areas for w in wide) or any(user_area.lower() in a.lower() or a.lower() in user_area.lower() for a in areas)

def find_services(need, area, services=None, today=None):
    """Tool 1: return matching services for a need, free first, with waitlist/stale flags."""
    services = services if services is not None else load_services()
    today = today or datetime.date.today()
    aliases = {"power_outage": {"power_outage", "utility_medical"}, "ride_home": {"ride_home", "procedure_escort"}}
    wanted = aliases.get(need, {need})
    out = []
    for s in services:
        if not wanted & set(s["needs"]) or not _area_ok(area, s["areas"]):
            continue
        verified = datetime.date.fromisoformat(s["last_verified"])
        stale = (today - verified).days > STALE_DAYS
        wl = s.get("waitlist", False)
        out.append({"id": s["id"], "name": s["name"], "phone": s.get("phone"), "url": s.get("url", ""),
                    "cost": s.get("cost", "unknown"), "waitlist": wl is True, "stale": stale,
                    "escort_rule_check": s.get("escort_rule_check", False),
                    "call_to_confirm": wl is not False or stale or not s.get("phone")})
    order = {"free": 0, "low": 1, "paid": 2}
    out.sort(key=lambda r: (order.get(r["cost"], 3), r["waitlist"], r["stale"], not r["phone"]))
    return out

def suggest_preparation(need):
    """Tool 2: map a need to simple preparations."""
    mapping = {"ride_home": [], "pet_care": ["pet_care", "spare_key"], "home_access": ["spare_key"],
               "power_outage": ["power_outage", "emergency_kit"], "fall": ["emergency_kit", "spare_key"]}
    return [PREPARATIONS[k] for k in mapping.get(need, [])]

def draft_note(user_name, roles):
    """Tool 3: draft ONE warm note for the user to review and send herself. Never sends."""
    lines = [f"Hi {', '.join(r['helper'] for r in roles)},", "",
             f"I'm putting together a small 'just in case' plan. If you're able to, I'd be grateful for help with one small thing:"]
    lines += [f"- {r['helper']}: {r['task']}" for r in roles]
    lines += ["", "Only say yes if it suits you. No reply needed if it doesn't, and I won't follow up.", "", f"Thank you, {user_name}"]
    return "\n".join(lines)
