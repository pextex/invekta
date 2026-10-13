import { blankPersonalization, type Personalization } from "./messageTemplates";
export type MessageDraft = {
  id: number;
  company_id: number;
  mode: string;
  subject: string;
  body: string;
  recipient: string | null;
  model: string;
  version: number;
  created_at: string;
  updated_at: string;
};
export type Composer = {
  company: number;
  mode: string;
  tone: string;
  language: string;
  instructions: string;
  incoming: string;
  goal: string;
  personalization: Personalization;
};
export type AssistantState = {
  compose: Composer;
  draft: MessageDraft | null;
  savedDraft: MessageDraft | null;
  dirty: boolean;
  items: MessageDraft[];
};
const key = (organization: string) =>
  `crm_assistant_v1_${encodeURIComponent(organization)}`;
const choices = (value: unknown, list: string[], fallback: string) =>
  typeof value === "string" && list.includes(value) ? value : fallback;
const text = (value: unknown, limit: number) =>
  typeof value === "string" ? value.slice(0, limit) : "";
const record = (value: unknown): Record<string, unknown> =>
  value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
export function parseAssistant(
  raw: string | null,
  ids: number[],
): AssistantState | null {
  try {
    const root = record(JSON.parse(raw ?? "null"));
    if (root.schema !== 1) return null;
    const allowed = new Set(ids),
      c = record(root.compose),
      p = record(c.personalization),
      personalization = blankPersonalization();
    const limits = {
      topic: 120,
      offering: 600,
      need: 600,
      meeting_time: 120,
      reply_text: 4000,
      greeting: 150,
      sender_name: 150,
      sender_title: 150,
      sender_phone: 80,
      sender_email: 254,
    };
    for (const name of Object.keys(
      personalization,
    ) as (keyof Personalization)[])
      personalization[name] = text(p[name], limits[name]);
    const parseDraft = (value: unknown): MessageDraft | null => {
      const d = record(value);
      if (
        !Number.isSafeInteger(d.id) ||
        Number(d.id) <= 0 ||
        !allowed.has(Number(d.company_id)) ||
        !Number.isSafeInteger(d.version) ||
        Number(d.version) < 1 ||
        typeof d.subject !== "string" ||
        !d.subject.trim() ||
        typeof d.body !== "string" ||
        !d.body.trim() ||
        !Number.isFinite(Date.parse(String(d.created_at))) ||
        !Number.isFinite(Date.parse(String(d.updated_at)))
      )
        return null;
      return {
        id: Number(d.id),
        company_id: Number(d.company_id),
        version: Number(d.version),
        mode: choices(d.mode, ["email", "reply", "follow_up"], "email"),
        subject: text(d.subject, 200),
        body: text(d.body, 20000),
        recipient:
          typeof d.recipient === "string" ? text(d.recipient, 254) : null,
        model: "local-templates-demo",
        created_at: String(d.created_at),
        updated_at: String(d.updated_at),
      };
    };
    const items = Array.isArray(root.items)
      ? root.items
          .slice(0, 30)
          .map(parseDraft)
          .filter((d): d is MessageDraft => !!d)
      : [];
    const draft = parseDraft(root.draft),
      savedDraft = parseDraft(root.savedDraft);
    return {
      compose: {
        company: allowed.has(Number(c.company)) ? Number(c.company) : 0,
        mode: choices(c.mode, ["email", "reply", "follow_up"], "email"),
        goal: choices(
          c.goal,
          ["meeting", "introduction", "information", "proposal"],
          "meeting",
        ),
        tone: choices(
          c.tone,
          ["professional", "friendly", "concise"],
          "professional",
        ),
        language: choices(c.language, ["sr", "en"], "sr"),
        instructions: text(c.instructions, 4000),
        incoming: text(c.incoming, 10000),
        personalization,
      },
      draft,
      savedDraft,
      dirty:
        !!draft &&
        !!savedDraft &&
        draft.id === savedDraft.id &&
        root.dirty === true,
      items: [...new Map(items.map((d) => [d.id, d])).values()],
    };
  } catch {
    return null;
  }
}
export function loadAssistant(organization: string, ids: number[]) {
  try {
    return parseAssistant(window.localStorage.getItem(key(organization)), ids);
  } catch {
    return null;
  }
}
export function saveAssistant(organization: string, state: AssistantState) {
  try {
    window.localStorage.setItem(
      key(organization),
      JSON.stringify({ schema: 1, ...state, items: state.items.slice(0, 30) }),
    );
    return true;
  } catch {
    return false;
  }
}
