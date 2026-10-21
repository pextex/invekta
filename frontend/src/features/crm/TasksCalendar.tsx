import { useEffect, useRef, useState, type FormEvent } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, Plus, RefreshCw, Save } from "lucide-react";
import { errorText } from "../../lib/api";
import { type CalendarTask, belgradeToday, calendarDays, shiftMonth } from "./taskCalendar";
import { useTaskCalendar } from "./useTaskCalendar";
import CompanyPicker, { type CompanyChoice } from "./CompanyPicker";

type Draft = { title: string; due_date: string; due_time: string; notes: string; company_id: string; company_name?: string };
const displayDate = (date: string, month = false) => new Intl.DateTimeFormat("sr-Latn-RS", month ? { month: "long", year: "numeric", timeZone: "UTC" } : { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" }).format(new Date(`${date}T12:00:00Z`));

export default function TasksCalendar({ unit, companies, organization, hideCompany = false }: { unit: number; companies: CompanyChoice[]; organization?: string; hideCompany?: boolean }) {
  const today = belgradeToday();
  const [month, setMonth] = useState(() => today.slice(0, 7));
  const [selected, setSelected] = useState(today);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [editing, setEditing] = useState<CalendarTask | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const { tasks, loading, error: loadError, warning, save, toggle, refresh } = useTaskCalendar(unit, month, organization);
  useEffect(() => { if (draft) input.current?.focus(); }, [!!draft]);
  const days = calendarDays(month);
  const current = tasks.filter(t => t.due_date.startsWith(month));
  const selectedTasks = tasks.filter(t => t.due_date === selected).sort((a, b) => (a.due_time ?? "99").localeCompare(b.due_time ?? "99") || a.id - b.id);
  function add(date = selected) {
    setEditing(null); setError(""); setMessage("");
    setDraft({ title: "", due_date: date, due_time: "", notes: "", company_id: "" });
  }
  function move(offset: number) {
    const next = shiftMonth(month, offset); setMonth(next); setSelected(`${next}-01`); setMessage("");
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!draft) return;
    setBusy(true); setError("");
    try {
      const companyId = draft.company_id ? Number(draft.company_id) : null;
      await save({ title: draft.title.trim(), due_date: draft.due_date, due_time: draft.due_time || null,
        notes: draft.notes.trim() || null, company_id: companyId }, editing,
        companyId === null ? null : draft.company_name ?? companies.find(c => c.id === companyId)?.name ?? editing?.company_name ?? null);
      setMonth(draft.due_date.slice(0, 7)); setSelected(draft.due_date); setDraft(null);
      setMessage(organization ? "Zadatak je dodat u demo kalendar." : "Zadatak je sačuvan.");
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  async function complete(task: CalendarTask) {
    setBusy(true); setError(""); setMessage("");
    try { await toggle(task); } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <>
    <div className="page-heading"><div><div className="eyebrow">PLAN AKTIVNOSTI</div><h1>Kalendar zadataka</h1><p>Planirajte pozive, sastanke i naredne korake. Vreme je u Beogradu.</p></div>
      <button className="primary-button" disabled={busy || loading || !!draft} onClick={() => add()}><Plus size={16} />Dodaj novi zadatak</button></div>
    {organization && <p className="section-hint">Demo zadaci se čuvaju samo u ovom browseru, zasebno za svaku firmu.</p>}
    {(error || loadError) && <p className="error-message" role="alert">{error || loadError}</p>}
    {warning && <p className="error-message" role="alert">{warning}</p>}
    {message && <p className="success-message" role="status">{message}</p>}
    {draft && <section className="panel task-editor"><h2>{editing ? "Izmena zadatka" : "Novi zadatak"}</h2><form onSubmit={submit}>
      <fieldset disabled={busy}><div className="form-grid">
        <label>Naziv zadatka<input ref={input} required minLength={2} maxLength={200} value={draft.title} onChange={e => setDraft({ ...draft, title: e.target.value })} placeholder="Npr. Pozvati klijenta" /></label>
        {!hideCompany && <CompanyPicker unit={unit} options={companies} value={Number(draft.company_id) || 0}
          selectedName={draft.company_name ?? editing?.company_name ?? undefined} optional local={!!organization}
          label="Kompanija (opciono)" ariaLabel="Kompanija zadatka" disabled={busy}
          onChange={(id, name) => setDraft({ ...draft, company_id: id ? String(id) : "", company_name: name })} />}
        <label>Datum<input type="date" required value={draft.due_date} onChange={e => setDraft({ ...draft, due_date: e.target.value })} /></label>
        <label>Vreme (opciono)<input type="time" value={draft.due_time} onChange={e => setDraft({ ...draft, due_time: e.target.value })} /></label>
      </div><label>Beleška<textarea maxLength={2000} rows={3} value={draft.notes} onChange={e => setDraft({ ...draft, notes: e.target.value })} /></label></fieldset>
      <div className="form-actions"><button type="button" className="secondary-button" disabled={busy} onClick={() => setDraft(null)}>Otkaži</button><button className="primary-button" disabled={busy || draft.title.trim().length < 2}><Save size={16} />{busy ? "Čuvanje…" : "Sačuvaj zadatak"}</button></div>
    </form></section>}
    <div className="task-calendar-layout">
      <section className="panel task-calendar-panel" aria-label="Mesečni kalendar zadataka">
        <div className="task-calendar-toolbar"><h2><CalendarDays size={18} />{displayDate(`${month}-01`, true)}</h2><div>
          <button className="secondary-button" disabled={busy || !!draft} onClick={() => move(-1)} aria-label="Prethodni mesec"><ChevronLeft size={16} /></button>
          <button className="secondary-button" disabled={busy || !!draft} onClick={() => { setMonth(today.slice(0, 7)); setSelected(today); }}>Danas</button>
          <button className="secondary-button" disabled={busy || !!draft} onClick={() => move(1)} aria-label="Sledeći mesec"><ChevronRight size={16} /></button>
        </div></div>
        <p className="task-calendar-summary">{loading ? "Učitavanje…" : `${current.filter(t => t.status === "planned").length} planiranih · ${current.filter(t => t.status === "done").length} završenih u mesecu`}</p>
        <table className="task-calendar-grid"><thead><tr>{["Pon", "Uto", "Sre", "Čet", "Pet", "Sub", "Ned"].map(day => <th key={day} scope="col">{day}</th>)}</tr></thead><tbody>
          {Array.from({ length: 6 }, (_, week) => <tr key={week}>{days.slice(week * 7, week * 7 + 7).map(day => {
            const dayTasks = tasks.filter(t => t.due_date === day); const open = dayTasks.filter(t => t.status === "planned").length;
            return <td key={day}><button disabled={busy || loading || !!draft} aria-pressed={selected === day} aria-current={day === today ? "date" : undefined}
              aria-label={`${displayDate(day)}: ${dayTasks.length} zadataka, ${open} planiranih`}
              className={`task-calendar-day${selected === day ? " selected" : ""}${day === today ? " today" : ""}${!day.startsWith(month) ? " outside" : ""}`}
              onClick={() => { setSelected(day); if (!day.startsWith(month)) setMonth(day.slice(0, 7)); }}>
              <span>{Number(day.slice(-2))}</span>{dayTasks.length > 0 && <><span className="task-day-dots">{open > 0 && <i className="planned" />}{dayTasks.length > open && <i className="done" />}</span><small>{dayTasks.length} zad.</small></>}
            </button></td>;
          })}</tr>)}
        </tbody></table>
        <div className="task-calendar-legend"><span><i className="planned" />Planirano</span><span><i className="done" />Završeno</span></div>
      </section>
      <section className="panel task-day-panel"><div className="panel-heading"><div><h2>Zadaci za dan</h2><p>{displayDate(selected)}</p></div>
        <button className="text-button" aria-label="Osveži zadatke" disabled={busy || loading || !!draft} onClick={refresh}><RefreshCw size={16} /></button></div>
        {loading ? <p className="empty" role="status">Učitavanje zadataka…</p> : loadError ? <p className="empty">Kalendar nije učitan. Pokušajte ponovo pomoću dugmeta za osvežavanje.</p> : !selectedTasks.length ? <div className="task-day-empty"><CalendarDays size={32} /><h3>Dan je slobodan</h3><p>Nema zadataka za izabrani datum.</p><button className="secondary-button" disabled={busy || !!draft} onClick={() => add()}><Plus size={15} />Dodaj zadatak</button></div> : <div className="task-calendar-list">
          {selectedTasks.map(task => <article key={task.id} className={task.status === "done" ? "task-calendar-item completed" : "task-calendar-item"}>
            <div className="task-item-top"><span className="task-item-time">{task.due_time?.slice(0, 5) ?? "Bez vremena"}</span><span className={task.status === "done" ? "tag green" : "tag"}>{task.status === "done" ? "Završeno" : "Planirano"}</span></div>
            <h3>{task.title}</h3><small>{task.company_name ? `${task.company_name} · ` : ""}{task.owner_name}</small>{task.notes && <p className="task-item-notes">{task.notes}</p>}
            <div className="task-item-actions"><label><input type="checkbox" checked={task.status === "done"} disabled={busy || !!draft} onChange={() => complete(task)} />Završeno</label>
              <button className="text-button" disabled={busy || !!draft} onClick={() => { setEditing(task); setError(""); setMessage(""); setDraft({ title: task.title, due_date: task.due_date, due_time: task.due_time?.slice(0, 5) ?? "", notes: task.notes ?? "", company_id: task.company_id ? String(task.company_id) : "" }); }}>Izmeni</button></div>
          </article>)}
        </div>}
      </section>
    </div>
  </>;
}
