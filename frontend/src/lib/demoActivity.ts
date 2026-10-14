import type { Change } from "../features/crm/Reports";
const KEY = "invekta-demo-pipeline-history-v1";
export function loadDemoActivity(): Change[] {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(KEY) ?? "[]");
    if (!Array.isArray(value)) return [];
    return value.filter(row => row && typeof row.id === "number" && typeof row.opportunity_id === "number"
      && typeof row.changed_at === "string" && Number.isFinite(Date.parse(row.changed_at))
      && typeof row.company_name === "string" && typeof row.title === "string"
      && typeof row.to_stage === "string" && typeof row.from_stage === "string"
      && typeof row.amount === "string" && typeof row.actor_name === "string" && row.changes === null);
  } catch { return []; }
}
export function saveDemoActivity(rows: Change[]): boolean {
  try { localStorage.setItem(KEY, JSON.stringify(rows)); return true; }
  catch { return false; }
}
