import catalog from "../../../shared/message_catalog.json";
export type Personalization = {
  topic: string;
  offering: string;
  need: string;
  meeting_time: string;
  reply_text: string;
  greeting: string;
  sender_name: string;
  sender_title: string;
  sender_phone: string;
  sender_email: string;
};
export const blankPersonalization = (): Personalization => ({
  topic: "",
  offering: "",
  need: "",
  meeting_time: "",
  reply_text: "",
  greeting: "",
  sender_name: "",
  sender_title: "",
  sender_phone: "",
  sender_email: "",
});
export function prepareLocalMessage(input: {
  company: string;
  organization: string;
  mode: string;
  goal: string;
  tone: string;
  language: string;
  instructions?: string;
  personalization?: Personalization;
}) {
  const en = input.language === "en",
    c = catalog[en ? "en" : "sr"],
    p = input.personalization ?? blankPersonalization();
  const values: Record<string, string> = {
    company: input.company,
    organization: input.organization,
    topic: p.topic || c.defaultTopic,
    offering: p.offering,
    need: p.need,
    meetingTime: p.meeting_time,
    details: input.instructions?.trim() ?? "",
  };
  const render = (text: string) =>
    text.replace(/\{(\w+)\}/g, (_, key: string) => values[key] ?? "");
  const goal =
    input.goal in c.subjects
      ? (input.goal as keyof typeof c.subjects)
      : "meeting";
  let subject: string, paragraphs: string[];
  if (input.mode === "reply") {
    subject = c.replySubject;
    paragraphs = [c.replyOpening, p.reply_text || c.replyPlaceholder];
  } else if (input.mode === "follow_up") {
    subject = c.followSubject;
    paragraphs = [c.followOpening];
  } else {
    subject = c.subjects[goal];
    paragraphs = [
      goal === "meeting"
        ? c.meetingOpening
        : goal === "information"
          ? c.informationOpening
          : goal === "proposal"
            ? c.proposalOpening
            : c.opening,
    ];
  }
  if (p.offering) paragraphs.push(c.offer);
  if (p.need) paragraphs.push(c.needs);
  if (values.details) paragraphs.push(c.details);
  paragraphs.push(
    goal === "meeting"
      ? p.meeting_time
        ? c.meetingCta
        : c.meetingCtaDefault
      : goal === "information"
        ? c.informationCta
        : goal === "proposal"
          ? c.proposalCta
          : c.introductionCta,
  );
  if (input.tone !== "concise") paragraphs.push(c.thanks);
  const signature = [
    p.sender_name || c.namePlaceholder,
    p.sender_title,
    input.organization,
    p.sender_phone,
    p.sender_email,
  ]
    .filter(Boolean)
    .join("\n");
  return {
    subject: render(subject).slice(0, 200),
    body: `${p.greeting || (en ? "Dear team," : "Poštovani,")}\n\n${paragraphs.map(render).join("\n\n")}\n\n${input.tone === "friendly" ? c.friendlyClosing : c.closing}\n${signature}`,
  };
}
