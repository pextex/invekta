export type CalendarTask = {
  id: number; business_unit_id: number; owner_id: number; owner_name: string;
  title: string; due_date: string; due_time: string | null; notes: string | null;
  company_id: number | null; company_name: string | null; status: "planned" | "done"; version: number;
};
export type TaskFields = Pick<CalendarTask, "title" | "due_date" | "due_time" | "notes" | "company_id">;
export type TaskPage = { items: CalendarTask[]; total: number };
export function belgradeToday() {
  const parts = new Intl.DateTimeFormat("en", { timeZone: "Europe/Belgrade", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date());
  const get = (type: string) => parts.find(p => p.type === type)?.value;
  return `${get("year")}-${get("month")}-${get("day")}`;
}
export const dateString = (date: Date) => date.toISOString().slice(0, 10);
export function calendarDays(month: string) {
  const first = new Date(`${month}-01T12:00:00Z`);
  first.setUTCDate(first.getUTCDate() - (first.getUTCDay() + 6) % 7);
  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(first); day.setUTCDate(day.getUTCDate() + index); return dateString(day);
  });
}
export function shiftMonth(month: string, offset: number) {
  const date = new Date(`${month}-01T12:00:00Z`); date.setUTCMonth(date.getUTCMonth() + offset); return dateString(date).slice(0, 7);
}
const storageKey = (organization: string) => `crm-demo-tasks-v1-${organization}`;
export function loadDemoTasks(organization: string): CalendarTask[] {
  try {
    const raw: unknown = JSON.parse(localStorage.getItem(storageKey(organization)) ?? "[]");
    if (!Array.isArray(raw)) return [];
    return raw.filter((t): t is CalendarTask => t && Number.isSafeInteger(t.id) && t.id > 0
      && typeof t.title === "string" && /^\d{4}-\d{2}-\d{2}$/.test(t.due_date)
      && (t.due_time === null || typeof t.due_time === "string")
      && (t.notes === null || typeof t.notes === "string")
      && (t.company_id === null || Number.isSafeInteger(t.company_id))
      && (t.company_name === null || typeof t.company_name === "string")
      && (t.status === "planned" || t.status === "done") && Number.isSafeInteger(t.version));
  } catch { return []; }
}
export function saveDemoTasks(organization: string, tasks: CalendarTask[]) {
  try {
    localStorage.setItem(storageKey(organization), JSON.stringify(tasks));
    window.dispatchEvent(new Event("crm-demo-tasks")); return true;
  } catch { return false; }
}
