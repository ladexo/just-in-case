"""Checks run on every user message before planning."""
import re
CRISIS = re.compile(r"no one would (notice|care)|want to die|kill myself|end it all|(nobody|no one) would( \w+)? miss|(don'?t|do not) see the point|no reason to (live|go on)|better off without me", re.I)
MEDICAL = re.compile(r"(stop|skip|take|change).{0,30}(medication|medicine|pill|dose|blood thinner)", re.I)
SEND = re.compile(r"\b(text|email|e-mail|message|call|send|tell|notify|contact|reach out to|let)\b.{0,30}\b(friends?|them|her|him|family|neighbou?rs?|dana|marcy|everyone|people|know)\b|\bsend (it|this|the note)\b", re.I)
BURDEN = re.compile(r"(don'?t|do not) want to (bother|burden)|be a burden|bother anyone", re.I)
ESCORT = re.compile(r"responsible adult|escort|someone to (drive|take) me home", re.I)

CRISIS_REPLY = ("I'm really sorry you're feeling this way. You matter. Please reach out to someone you trust today. "
                "You can call or text 988 (Suicide & Crisis Lifeline) any time. Your local police non-emergency line can "
                "do a wellness check. If you're in danger, call 911. We can set the plan aside, and I'm here when you want to come back.")
MEDICAL_REPLY = "I can't give medical advice. Please ask your surgical or care team about your medications before the procedure."
SEND_REPLY = "I can't send messages for you, but I've written the draft below so you can send it yourself."

def classify(text):
    return {"crisis": bool(CRISIS.search(text)), "medical": bool(MEDICAL.search(text)),
            "send_request": bool(SEND.search(text)), "burden": bool(BURDEN.search(text)),
            "escort_rule": bool(ESCORT.search(text))}
