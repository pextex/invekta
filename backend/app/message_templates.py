"""Professional local templates, shared wording with the offline frontend."""

import json
import re
from pathlib import Path
from .ai_provider import GeneratedDraft

CATALOG = json.loads(
    (Path(__file__).resolve().parents[2] / "shared/message_catalog.json").read_text()
)


def generate(context: dict) -> GeneratedDraft:
    en = context.get("language") == "en"
    catalog = CATALOG["en" if en else "sr"]
    personal = context.get("personalization") or {}
    sender = context["sender"]
    contact = context.get("contact") or {}
    opportunity = context.get("opportunity") or {}
    topic = personal.get("topic") or opportunity.get("title") or catalog["defaultTopic"]
    values = {
        "company": context["company"]["name"],
        "organization": sender["organization"],
        "topic": topic,
        "offering": personal.get("offering", ""),
        "need": personal.get("need", ""),
        "meetingTime": personal.get("meeting_time", ""),
        "details": context.get("instructions", "").strip(),
    }

    def render(text):
        return re.sub(r"\{(\w+)\}", lambda match: values.get(match[1], ""), text)

    goal = context.get("goal", "meeting")
    if goal not in catalog["subjects"]:
        goal = "meeting"  # Local templates cannot infer a goal from free-form text.
    mode = context["mode"]
    concise = context.get("tone") == "concise"
    if mode == "reply":
        subject = render(catalog["replySubject"])
        paragraphs = [
            catalog["replyOpening"],
            personal.get("reply_text") or catalog["replyPlaceholder"],
        ]
    elif mode == "follow_up":
        subject = render(catalog["followSubject"])
        paragraphs = [catalog["followOpening"]]
    else:
        subject = render(catalog["subjects"][goal])
        opening = {
            "meeting": "meetingOpening",
            "information": "informationOpening",
            "proposal": "proposalOpening",
        }.get(goal, "opening")
        paragraphs = [catalog[opening]]
    for field, key in [
        ("offering", "offer"),
        ("need", "needs"),
        ("details", "details"),
    ]:
        if values[field]:
            paragraphs.append(catalog[key])
    cta = (
        "meetingCta"
        if goal == "meeting" and values["meetingTime"]
        else "meetingCtaDefault"
        if goal == "meeting"
        else goal + "Cta"
    )
    paragraphs.append(catalog[cta])
    if not concise:
        paragraphs.append(catalog["thanks"])
    greeting = personal.get("greeting") or (
        f"Dear {contact['name']},"
        if en and contact.get("name")
        else "Dear team,"
        if en
        else "Poštovani,"
    )
    closing = (
        catalog["friendlyClosing"]
        if context.get("tone") == "friendly"
        else catalog["closing"]
    )
    signature = [
        personal.get("sender_name") or sender.get("name") or catalog["namePlaceholder"],
        personal.get("sender_title"),
        sender["organization"],
        personal.get("sender_phone"),
        personal.get("sender_email"),
    ]
    body = (
        greeting
        + "\n\n"
        + "\n\n".join(render(p) for p in paragraphs)
        + "\n\n"
        + closing
        + "\n"
        + "\n".join(s for s in signature if s)
    )
    return GeneratedDraft(subject=subject[:200], body=body)
