import { companies } from "../demo";
import {
  opportunityStages,
  type OpportunityStage,
} from "../features/crm/types";
export const demoStageKey = "luu_invekta_demo_stages_v1";
export type DemoStages = Record<number, OpportunityStage>;
export function parseDemoStages(raw: string | null): DemoStages {
  try {
    const value: unknown = JSON.parse(raw ?? "{}");
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    const result: DemoStages = {};
    for (const company of companies) {
      const stage = (value as Record<string, unknown>)[company.id];
      if (
        typeof stage === "string" &&
        opportunityStages.includes(stage as OpportunityStage)
      )
        result[company.id] = stage as OpportunityStage;
    }
    return result;
  } catch {
    return {};
  }
}
export function loadDemoStages(): DemoStages {
  try {
    return parseDemoStages(window.localStorage.getItem(demoStageKey));
  } catch {
    return {};
  }
}
export function saveDemoStages(stages: DemoStages): boolean {
  try {
    window.localStorage.setItem(demoStageKey, JSON.stringify(stages));
    return true;
  } catch {
    return false;
  }
}
const demoPages: Record<string, string> = {
  dashboard: "Početna tabla",
  companies: "Kompanije",
  leads: "Kompanije",
  pipeline: "Prodajni levak",
  quotes: "Ponude",
  tasks: "Zadaci",
  reports: "Izveštaji",
  targets: "Targeti",
  ai: "AI asistent",
};
export const readDemoPage = () =>
  demoPages[window.location.hash.split("?")[0].split("/")[1]] ?? "Početna tabla";
export function writeDemoPage(page: string, organization?: string) {
  const key =
    Object.entries(demoPages).find(([, title]) => title === page)?.[0] ??
    "dashboard";
  window.location.hash = "#demo/" + key + (organization ? "?organization=" + encodeURIComponent(organization) : "");
}
