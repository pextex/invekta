// Offline templates use no API, credentials or language model.
export function prepareLocalMessage(input: {
  company: string;
  organization: string;
  mode: string;
  goal: string;
  tone: string;
  language: string;
}) {
  const en = input.language === "en";
  const subjectByGoal: Record<string, string> = en
    ? {
        meeting: `Meeting proposal · ${input.company}`,
        introduction: `Introduction · ${input.organization}`,
        information: `Additional information · ${input.company}`,
      }
    : {
        meeting: `Predlog sastanka · ${input.company}`,
        introduction: `Predstavljanje · ${input.organization}`,
        information: `Dodatne informacije · ${input.company}`,
      };
  const bodyByGoal: Record<string, string> = en
    ? {
        meeting:
          "Would you be available for a short meeting? Please suggest a convenient time so we can discuss your needs and next steps.",
        introduction: `I am contacting you on behalf of ${input.organization}. We would like to learn more about your needs and explore opportunities to work together.`,
        information:
          "Could you share more information about your requirements, scope and preferred timeline?",
      }
    : {
        meeting:
          "Da li biste bili dostupni za kratak sastanak? Molim Vas da predložite termin koji Vam odgovara kako bismo razgovarali o Vašim potrebama i narednim koracima.",
        introduction: `Javljam Vam se u ime kompanije ${input.organization}. Želeli bismo da saznamo više o Vašim potrebama i razmotrimo mogućnosti za saradnju.`,
        information:
          "Molim Vas da nam pošaljete više informacija o Vašim potrebama, obimu i željenim rokovima.",
      };
  let subject = subjectByGoal[input.goal] ?? subjectByGoal.meeting;
  let body = bodyByGoal[input.goal] ?? bodyByGoal.meeting;
  if (input.mode === "reply") {
    subject = `${en ? "Response to your inquiry" : "Odgovor na upit"} · ${input.company}`;
    body =
      (en
        ? "Thank you for your message.\n\n[Add answers to the client's questions here.]"
        : "Hvala Vam na poruci.\n\n[Ovde dopunite odgovore na pitanja klijenta.]") +
      "\n\n" +
      body;
  } else if (input.mode === "follow_up") {
    subject = `${en ? "Next steps" : "Naredni koraci"} · ${input.company}`;
    body =
      (en
        ? "Are there any updates or additional questions regarding our potential cooperation?"
        : "Da li imate novih informacija ili dodatnih pitanja u vezi sa mogućom saradnjom?") +
      "\n\n" +
      body;
  }
  if (input.tone === "concise")
    body = body
      .split("\n\n")
      .slice(0, input.mode === "reply" ? 2 : 1)
      .join("\n\n");
  const friendly = input.tone === "friendly";
  return {
    subject: subject.slice(0, 200),
    body: `${en ? (friendly ? "Hello," : "Dear Sir or Madam,") : friendly ? "Zdravo," : "Poštovani,"}\n\n${body}\n\n${en ? "Kind regards," : "Srdačan pozdrav,"}\n[${en ? "Your name" : "Vaše ime"}]\n${input.organization}`,
  };
}
