import { useEffect, useRef, useState } from "react";
import { api, errorText } from "../../lib/api";
import { calendarDays, loadDemoTasks, saveDemoTasks, type CalendarTask, type TaskFields, type TaskPage } from "./taskCalendar";

export function useTaskCalendar(unit: number, month: string, organization?: string) {
  const demoTasks = useRef(organization ? loadDemoTasks(organization) : []);
  const [tasks, setTasks] = useState<CalendarTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setError(""); setLoading(true); setTasks([]);
    if (organization) { setTasks(demoTasks.current); setLoading(false); return; }
    const days = calendarDays(month);
    async function load() {
      const items: CalendarTask[] = [];
      let total = 0;
      do {
        const params = new URLSearchParams({ date_from: days[0], date_to: days[41], limit: "200", offset: String(items.length) });
        const page = await api<TaskPage>(`/units/${unit}/tasks?${params}`, { signal: controller.signal });
        if (!page.items.length && items.length < page.total) throw new Error("Lista zadataka se promenio. Osvežite kalendar.");
        items.push(...page.items); total = page.total;
      } while (items.length < total);
      if (!controller.signal.aborted) setTasks(items);
    }
    load().catch(e => { if (!controller.signal.aborted) setError(errorText(e)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [unit, month, organization, reload]);
  function persist(next: CalendarTask[]) {
    if (!organization) return;
    demoTasks.current = next;
    setTasks(next);
    setWarning(saveDemoTasks(organization, next) ? "" : "Browser ne dozvoljava lokalno čuvanje. Zadaci važe samo dok je ovaj prikaz otvoren.");
  }
  async function save(fields: TaskFields, existing: CalendarTask | null, companyName: string | null) {
    if (organization) {
      const record: CalendarTask = { ...fields, id: existing?.id ?? Math.max(0, ...tasks.map(t => t.id)) + 1,
        owner_id: 0, owner_name: "Demo korisnik", business_unit_id: 0, company_name: companyName,
        status: existing?.status ?? "planned", version: (existing?.version ?? 0) + 1 };
      persist(existing ? tasks.map(t => t.id === existing.id ? record : t) : [...tasks, record]);
    } else {
      await api(`/units/${unit}/tasks${existing ? "/" + existing.id : ""}`, {
        method: existing ? "PATCH" : "POST", body: JSON.stringify(existing ? { ...fields, version: existing.version } : fields),
      });
      setReload(value => value + 1);
    }
  }
  async function toggle(task: CalendarTask) {
    const status = task.status === "done" ? "planned" : "done";
    if (organization) persist(tasks.map(t => t.id === task.id ? { ...t, status, version: t.version + 1 } : t));
    else {
      await api(`/units/${unit}/tasks/${task.id}/status`, { method: "PATCH", body: JSON.stringify({ status, version: task.version }) });
      setReload(value => value + 1);
    }
  }
  return { tasks, loading, error, warning, save, toggle, refresh: () => setReload(v => v + 1) };
}
