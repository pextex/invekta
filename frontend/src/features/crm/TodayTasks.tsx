import { useEffect, useState } from "react";
import { ArrowRight, CheckCircle2, Clock3 } from "lucide-react";
import { api, errorText } from "../../lib/api";
import { belgradeToday, loadDemoTasks, type CalendarTask, type TaskPage } from "./taskCalendar";

export const todayTasks = (tasks: CalendarTask[], day: string) => tasks.filter(t => t.due_date === day)
  .sort((a, b) => Number(a.status === "done") - Number(b.status === "done") || (a.due_time ?? "99").localeCompare(b.due_time ?? "99") || a.id - b.id);
export default function TodayTasks({ unit, organization, reload = 0, onOpen }: { unit: number; organization?: string; reload?: number; onOpen: () => void }) {
  const [day, setDay] = useState(belgradeToday);
  const [tick, setTick] = useState(0);
  const [tasks, setTasks] = useState<CalendarTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    const update = () => { if (document.visibilityState !== "hidden") { setDay(belgradeToday()); setTick(v => v + 1); } };
    const timer = window.setInterval(update, 60000);
    window.addEventListener("focus", update); window.addEventListener("crm-demo-tasks", update);
    return () => { clearInterval(timer); window.removeEventListener("focus", update); window.removeEventListener("crm-demo-tasks", update); };
  }, []);
  useEffect(() => {
    const controller = new AbortController(); setError(""); setLoading(true); setTasks([]);
    if (organization) { setTasks(todayTasks(loadDemoTasks(organization), day)); setLoading(false); return; }
    async function load() {
      const tasks: CalendarTask[] = [];
      let total = 0;
      do {
        const params = new URLSearchParams({ date_from: day, date_to: day, limit: "200", offset: String(tasks.length) });
        const page = await api<TaskPage>(`/units/${unit}/tasks?${params}`, { signal: controller.signal });
        if (!page.items.length && tasks.length < page.total) throw new Error("Lista zadataka je promenjena. Osvežite prikaz.");
        tasks.push(...page.items); total = page.total;
      } while (tasks.length < total);
      if (!controller.signal.aborted) setTasks(todayTasks(tasks, day));
    }
    load().catch(e => { if (!controller.signal.aborted) setError(errorText(e)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [unit, organization, day, tick, reload]);
  return <div className="today-tasks">
    <div className="today-tasks-heading"><h3>Zadaci za danas</h3><button onClick={onOpen}>Otvori kalendar <ArrowRight size={15} /></button></div>
    {loading ? <p role="status">Učitavanje današnjih zadataka…</p> : error ? <p role="alert">{error}</p> : tasks.length ? <>
      <div className="today-task-list">{tasks.slice(0, 5).map(task => <button onClick={onOpen} className={task.status === "done" ? "today-task done" : "today-task"} key={task.id}>
        {task.status === "done" ? <CheckCircle2 size={17} /> : <Clock3 size={17} />}<span><strong>{task.title}</strong><small>{task.due_time?.slice(0, 5) ?? "Tokom dana"}{task.company_name ? ` · ${task.company_name}` : ""} · {task.owner_name}</small></span><span className="today-task-status">{task.status === "done" ? "Završeno" : "Planirano"}</span>
      </button>)}</div>
      <small>{tasks.filter(t => t.status === "planned").length} planiranih · {tasks.filter(t => t.status === "done").length} završenih{tasks.length > 5 ? ` · prikazano prvih 5 od ${tasks.length}` : ""}</small>
    </> : <p>Nema zadataka za danas. Dodajte novi u kalendaru.</p>}
  </div>;
}
