import { describe, it, expect, vi, afterEach } from "vitest";
import {
  parseAssistant,
  loadAssistant,
  saveAssistant,
  type AssistantState,
} from "./assistantStorage";
import { blankPersonalization } from "./messageTemplates";
const draft = {
  id: 1,
  company_id: 11,
  mode: "email",
  subject: "Ponuda",
  body: "Privatan demo tekst",
  recipient: null,
  model: "local-templates-demo",
  version: 1,
  created_at: "2026-10-13T08:00:00Z",
  updated_at: "2026-10-13T08:00:00Z",
};
const state: AssistantState = {
  compose: {
    company: 11,
    mode: "email",
    tone: "professional",
    language: "sr",
    instructions: "",
    incoming: "",
    goal: "meeting",
    personalization: blankPersonalization(),
  },
  draft,
  savedDraft: draft,
  dirty: false,
  items: [draft],
};
afterEach(() => vi.unstubAllGlobals());
describe("local assistant storage", () => {
  it("restores unsaved edits and rejects drafts for another company scope", () => {
    const parsed = parseAssistant(
      JSON.stringify({
        schema: 1,
        ...state,
        draft: { ...draft, body: "Unsaved change" },
        dirty: true,
        items: [draft, { ...draft, id: 2, company_id: 99 }],
      }),
      [11],
    );
    expect(parsed?.draft?.body).toBe("Unsaved change");
    expect(parsed?.dirty).toBe(true);
    expect(parsed?.savedDraft?.body).toBe(draft.body);
    expect(parsed?.items).toHaveLength(1);
    expect(
      parseAssistant(JSON.stringify({ schema: 1, ...state }), [99])?.draft,
    ).toBeNull();
    expect(parseAssistant("broken json", [11])).toBeNull();
  });
  it("isolates organizations and handles blocked storage", () => {
    const values = new Map<string, string>();
    vi.stubGlobal("window", {
      localStorage: {
        getItem: (key: string) => values.get(key) ?? null,
        setItem: (key: string, value: string) => values.set(key, value),
      },
    });
    expect(saveAssistant("LUU", state)).toBe(true);
    expect(loadAssistant("Invekta", [11])).toBeNull();
    expect(loadAssistant("LUU", [11])?.draft?.subject).toBe("Ponuda");
    vi.stubGlobal("window", {
      localStorage: {
        getItem: () => {
          throw new Error("denied");
        },
        setItem: () => {
          throw new Error("quota");
        },
      },
    });
    expect(loadAssistant("LUU", [11])).toBeNull();
    expect(saveAssistant("LUU", state)).toBe(false);
  });
});
