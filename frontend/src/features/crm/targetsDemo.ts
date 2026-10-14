import type { TargetsData } from "./Targets";
import type { Change } from "./Reports";
import { businessTypesFor } from "./businessTypes";
export type DemoTargetContext = { organization: string; events: Change[]; opportunities: { id: number; stage: string; business_type: string | null }[] };
const key = (organization: string, month: string) => `crm-demo-targets-v1-${organization}-${month}`;
export function loadDemoGoals(organization: string, month: string): Record<string, string> {
  try {
    const raw: unknown = JSON.parse(localStorage.getItem(key(organization, month)) ?? "{}");
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) return {};
    return Object.fromEntries(Object.entries(raw).filter(([_, value]) => typeof value === "string" && /^\d{1,12}(\.\d{1,2})?$/.test(value)));
  } catch { return {}; }
}
export function saveDemoGoals(organization: string, month: string, goals: Record<string, string>) {
  try { localStorage.setItem(key(organization, month), JSON.stringify(goals)); return true; } catch { return false; }
}
export function demoTargets(month: string, context: DemoTargetContext, goals: Record<string, string>): TargetsData {
  const categories = businessTypesFor(context.organization);
  const results: Record<string, { value: number; count: number }> = {};
  for (const opportunity of context.opportunities.filter(o => o.stage === "Dobijeno")) {
    const event = context.events.filter(e => e.opportunity_id === opportunity.id && e.to_stage === "Dobijeno" && e.from_stage !== e.to_stage).sort((a, b) => b.id - a.id)[0];
    if (!event || event.amount === null) continue;
    const parts = new Intl.DateTimeFormat("en", { timeZone: "Europe/Belgrade", year: "numeric", month: "2-digit" }).formatToParts(new Date(event.changed_at));
    const period = `${parts.find(p => p.type === "year")?.value}-${parts.find(p => p.type === "month")?.value}`;
    if (period !== month) continue;
    const type = event.business_type ?? opportunity.business_type;
    if (!type || !categories.includes(type as typeof categories[number])) continue;
    const row = results[type] ??= { value: 0, count: 0 }; row.value += Number(event.amount); row.count++;
  }
  return { month, categories, can_manage: true, salespeople: [{ user_id: 1, user_name: "Demo komercijalista", targets: categories.map(category => ({
    category, target_amount: goals[category] ?? null, achieved_amount: (results[category]?.value ?? 0).toFixed(2), achieved_count: results[category]?.count ?? 0, version: null,
  })) }] };
}
