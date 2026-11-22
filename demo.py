"""Demo mode: the meeting notes agent steps without an AI key, using simple rules.

It sorts each meeting note into one of the five sections (Decisions, Action items,
Discussion, Blockers, Next steps), finds owners and dates where it can, and lists questions
for anything that is missing. A real AI model (add your key in .streamlit/secrets.toml) does this far better.
"""
from __future__ import annotations

import re

SECTIONS = ["Decisions", "Action items", "Discussion", "Blockers", "Next steps"]

KEYWORDS = {
    "Blockers": ["blocked", "waiting on", "waiting for", "stuck", "cannot", "can't", "no access", "dependency", "impediment", "delay"],
    "Decisions": ["agreed to", "agreed that", "decided to", "decided that", "approved", "consensus", "aligned on", "concluded", "signed off", "decision:"],
    "Action items": ["action item", "todo", "task", "will ", "to follow up", "to deliver", "to fix", "to prepare", "assigned to", "to lead", "to review", "to write", "to test", "to deploy"],
    "Next steps": ["next week", "next sprint", "plan to", "planning", "going to", "schedule", "target date", "upcoming"],
}

DAY_PREFIX = re.compile(r"^\s*(mon|tue|wed|thu|fri|sat|sun)[a-z]*\s*[:\-]\s*", re.I)
NAME_TO = re.compile(r"\b([A-Z][a-z]+)\s+to\s+(?:follow up|prepare|finish|fix|test|review|deliver|lead|run|conduct|update|schedule|coordinate)\b", re.I)
NAME_WILL = re.compile(r"\b([A-Z][a-z]+)\s+(?:will|agreed to)\b", re.I)
NAME_ASSIGNED = re.compile(r"(?:assigned to|owner\s*[:\-])\s*([A-Z][a-z]+)", re.I)
NAME_START = re.compile(r"^([A-Z][a-z]+)\s+(?:is|was|spent|finished|fixed|stuck|raised|working|started|agreed|shared|opened|noted)\b")
DATE = re.compile(r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*|Monday|Tuesday|Wednesday|Thursday|Friday|tomorrow|next week|end of sprint|EOD|this Friday|by Friday|by Wednesday|by Thursday|by Tuesday|by Monday)\b", re.I)


def _clean(line: str) -> str:
    cleaned = DAY_PREFIX.sub("", line).strip()
    cleaned = re.sub(r"^[\s\-\*•\d\.\)]+(?=[A-Za-z])", "", cleaned).strip()
    return cleaned


def _owner(line: str) -> str:
    m = NAME_TO.search(line) or NAME_WILL.search(line) or NAME_ASSIGNED.search(line) or NAME_START.search(line)
    return m.group(1) if m else ""


def demo_analyse(notes: str) -> dict:
    """Return the same structure the AI model returns (see agent.py)."""
    items = []
    for raw in notes.splitlines():
        line = _clean(raw)
        if not line:
            continue
        low = line.lower()
        section = "Discussion"
        for s in ("Blockers", "Decisions", "Action items", "Next steps"):
            if any(w in low for w in KEYWORDS[s]):
                section = s
                break
        d = DATE.search(line)
        impact = "High" if section == "Blockers" else "Medium" if section in ("Decisions", "Action items") else ""
        items.append({
            "section": section,
            "text": line,
            "owner": _owner(line),
            "due": d.group(1) if d else "",
            "impact": impact,
        })

    decisions = [i["text"] for i in items if i["section"] == "Decisions"]
    action_items = [i for i in items if i["section"] == "Action items"]
    blockers = [i for i in items if i["section"] == "Blockers"]

    status = "Red" if len(blockers) >= 2 else "Amber" if (blockers or any(not i["owner"] for i in action_items)) else "Green"

    questions = []
    for i in blockers + action_items:
        if not i["owner"]:
            questions.append(f"Who is responsible for: \"{i['text']}\"?")
        if not i["due"] and i["section"] == "Action items":
            questions.append(f"When is this due: \"{i['text']}\" ({i['owner'] or 'unassigned'})?")

    if not items:
        questions.append("Not enough information: no meeting notes were given.")

    def n(k: int, word: str) -> str:
        return f"{k} {word}" if k == 1 else f"{k} {word}s"

    lead = decisions[0] if decisions else (action_items[0]["text"] if action_items else "Meeting reviewed with no major blockers")
    headline = f"{status}: {lead}."
    status_reason = f"{n(len(decisions), 'decision')} agreed, {n(len(action_items), 'action item')} logged, and {n(len(blockers), 'blocker')} noted."
    summary = f"The meeting produced {n(len(decisions), 'decision')} and {n(len(action_items), 'action item')}. {n(len(blockers), 'blocker')} requires follow-up."

    top_actions = [
        {"action": i["text"], "owner": i["owner"] or "Not known", "why": "Deliverable agreed in meeting"}
        for i in (blockers + action_items)[:5]
    ]

    email_body = [
        "Hi team,",
        "",
        f"Here is the summary of our meeting outcomes (Status: {status}):",
        "",
        "Key Decisions:",
    ]
    if decisions:
        email_body.extend(f"- {d}" for d in decisions[:3])
    else:
        email_body.append("- No formal decisions recorded.")

    email_body.append("\nTop Action Items:")
    if top_actions:
        for a in top_actions[:4]:
            email_body.append(f"- {a['action']} (Owner: {a['owner']})")
    else:
        email_body.append("- No action items recorded.")

    email_body.append("\nPlease review and let the lead know if any owner or date needs adjusting.")

    return {
        "headline": headline,
        "actions": top_actions,
        "decisions": decisions or ["Alignment reached on current progress."],
        "email": "\n".join(email_body),
        "status": status,
        "status_reason": status_reason,
        "summary": summary,
        "items": items,
        "questions": questions[:5],
    }
