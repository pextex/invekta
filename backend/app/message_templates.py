"""Local message templates: no model, HTTP requests or API billing."""

from .ai_provider import GeneratedDraft


def generate(context: dict) -> GeneratedDraft:
    company = context["company"]["name"]
    sender = context["sender"]
    contact = context.get("contact") or {}
    opportunity = context.get("opportunity") or {}
    name = contact.get("name")
    title = opportunity.get("title")
    goal = context.get("goal", "meeting")
    mode = context["mode"]
    english = context["language"] == "en"
    tone = context["tone"]
    if english:
        greeting = (
            f"Hello {name},"
            if name and tone == "friendly"
            else f"Dear {name},"
            if name
            else "Hello,"
            if tone == "friendly"
            else "Dear Sir or Madam,"
        )
        subjects = {
            "meeting": f"Meeting proposal · {company}",
            "introduction": f"Introduction · {sender['organization']}",
            "information": f"Additional information · {company}",
        }
        messages = {
            "meeting": "Would you be available for a short meeting? Please suggest a convenient time so we can discuss your needs and next steps.",
            "introduction": f"I am contacting you on behalf of {sender['organization']}. We would like to learn more about your needs and explore opportunities to work together.",
            "information": "Could you share more information about your requirements, scope and preferred timeline? This will help us prepare a relevant proposal.",
        }
        subject = subjects[goal]
        main = messages[goal]
        if mode == "reply":
            subject = f"Response to your inquiry · {company}"
            main = (
                "Thank you for your message.\n\n[Add answers to the client's questions here.]\n\n"
                + main
            )
        elif mode == "follow_up":
            subject = f"Next steps · {company}"
            main = (
                "I would like to check whether there are any updates or additional questions regarding our potential cooperation.\n\n"
                + main
            )
        if title:
            main += f"\n\nRegarding: {title}."
        closing = "Best regards," if tone == "friendly" else "Kind regards,"
    else:
        greeting = (
            f"Zdravo {name},"
            if name and tone == "friendly"
            else f"Poštovani/a {name},"
            if name
            else "Zdravo,"
            if tone == "friendly"
            else "Poštovani,"
        )
        subjects = {
            "meeting": f"Predlog sastanka · {company}",
            "introduction": f"Predstavljanje · {sender['organization']}",
            "information": f"Dodatne informacije · {company}",
        }
        messages = {
            "meeting": "Da li biste bili dostupni za kratak sastanak? Molim Vas da predložite termin koji Vam odgovara kako bismo razgovarali o Vašim potrebama i narednim koracima.",
            "introduction": f"Javljam Vam se u ime kompanije {sender['organization']}. Želeli bismo da saznamo više o Vašim potrebama i razmotrimo mogućnosti za saradnju.",
            "information": "Molim Vas da nam pošaljete više informacija o Vašim potrebama, obimu i željenim rokovima kako bismo pripremili odgovarajući predlog.",
        }
        subject = subjects[goal]
        main = messages[goal]
        if mode == "reply":
            subject = f"Odgovor na upit · {company}"
            main = (
                "Hvala Vam na poruci.\n\n[Ovde dopunite odgovore na pitanja klijenta.]\n\n"
                + main
            )
        elif mode == "follow_up":
            subject = f"Naredni koraci · {company}"
            main = (
                "Želeo bih da proverim da li imate novih informacija ili dodatnih pitanja u vezi sa mogućom saradnjom.\n\n"
                + main
            )
        if title:
            main += f"\n\nTema: {title}."
        closing = "Srdačan pozdrav," if tone == "friendly" else "S poštovanjem,"
    if tone == "concise":
        main = (
            main.split("\n\n")[0]
            if mode != "reply"
            else (
                "Thank you for your message.\n\n[Add your reply here.]"
                if english
                else "Hvala na poruci.\n\n[Dopunite odgovor ovde.]"
            )
        )
    return GeneratedDraft(
        subject=subject[:200],
        body=f"{greeting}\n\n{main}\n\n{closing}\n{sender['name']}\n{sender['organization']}",
    )
