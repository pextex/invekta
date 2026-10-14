export type WorkKind = "tasks" | "activities";
export type WorkRecord = {
  id: number;
  business_unit_id: number;
  company_id: number;
  company_name: string;
  opportunity_id: number | null;
  opportunity_title: string | null;
  assignee_id: number;
  assignee_name: string;
  creator_id: number;
  title: string;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  priority?: string;
  notes: string | null;
  version: number;
  status: string;
  remind_at: string | null;
  due_at?: string;
  completed_at?: string | null;
  kind?: "call" | "meeting" | "note";
  scheduled_at?: string | null;
  occurred_at?: string | null;
  outcome?: string | null;
};
export type WorkPage = { items: WorkRecord[]; total: number };
export type WorkSummary = {
  tasks: Record<"open" | "doing" | "done" | "cancelled", number>;
  activities: Record<"planned" | "done" | "cancelled", number>;
  overdue_tasks: number;
  due_today: number;
  activities_today: number;
  overdue_activities: number;
  completed_calls: number;
  completed_meetings: number;
  unread_reminders: number;
  due_tasks: WorkRecord[];
  scheduled_activities: WorkRecord[];
  assignee_results: {
    assignee_id: number;
    name: string;
    open_tasks: number;
    done_tasks: number;
    overdue_tasks: number;
    planned_activities: number;
    completed_calls: number;
    completed_meetings: number;
  }[];
};
export type Reminder = {
  id: number;
  task_id: number | null;
  activity_id: number | null;
  company_id: number;
  title: string;
  company_name: string;
  status: string;
  fire_at: string;
  delivered_at: string | null;
  read_at: string | null;
};
export type WorkEvent = {
  id: number;
  action: string;
  actor_name: string;
  changed_at: string;
  changes: Record<string, { from: unknown; to: unknown }>;
  display_changes?: Record<string, { from: unknown; to: unknown }>;
};
export const statusLabel: Record<string, string> = {
  open: "Otvoren",
  doing: "U toku",
  done: "Završen",
  cancelled: "Otkazan",
  planned: "Zakazan",
};
export const kindLabel: Record<string, string> = {
  call: "Poziv",
  meeting: "Sastanak",
  note: "Beleška",
};
// Datetime inputs use the browser's explicit local timezone; server requires an offset.
export function toLocalInput(value: string | null | undefined) {
  if (!value) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}
export const toInstant = (value: string) =>
  value ? new Date(value).toISOString() : null;
