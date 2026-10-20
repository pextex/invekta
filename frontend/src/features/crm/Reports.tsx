import { useEffect, useState } from "react";
import { CalendarDays, RefreshCw } from "lucide-react";
import { api, errorText } from "../../lib/api";
import { formatAmount, formatTimestamp, opportunityStages, stageLabel } from "./types";

export type Change = {
  owner_id?: number; owner_name?: string;
  business_type?: string | null;
  id: number; changed_at: string; company_name: string; opportunity_id: number;
  title: string; amount: string | null; from_stage: string | null; to_stage: string;
  actor_name: string; changes: Record<string, { before: string | null; after: string | null }> | null;
};
type ReportOwner = { user_id: number; user_name: string; total: number; created_count: number; stage_change_count: number; edit_count: number; realized_count: number; unrealized_count: number };
type SalesReport = {
  people: { id: number; name: string }[]; owners: ReportOwner[];
  total: number; opportunity_count: number; created_count: number;
  stage_change_count: number; edit_count: number; realized_count: number;
  unrealized_count: number; stage_counts: Record<string, number>; items: Change[];
};
export function reportPeriod(mode: "day" | "month", value: string) {
  if (mode === "day") return { from: value, to: value };
  const [year, month] = value.split("-").map(Number);
  const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate();
  return { from: `${value}-01`, to: `${value}-${lastDay}` };
}
function dateInBelgrade(date: Date) {
  const parts = new Intl.DateTimeFormat("en", {
    timeZone: "Europe/Belgrade", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(date);
  const part = (name: string) => parts.find(p => p.type === name)?.value;
  return `${part("year")}-${part("month")}-${part("day")}`;
}
const today = () => dateInBelgrade(new Date());
export function summarizeChanges(items: Change[], offset = 0): SalesReport {
  items = items.filter(row => row.from_stage === null || row.from_stage !== row.to_stage);
  const owners = new Map<number, ReportOwner>();
  for (const row of items) {
    const id = row.owner_id ?? 0;
    const person = owners.get(id) ?? { user_id: id, user_name: row.owner_name ?? row.actor_name, total: 0, created_count: 0, stage_change_count: 0, edit_count: 0, realized_count: 0, unrealized_count: 0 };
    person.total++; person[row.from_stage === null ? "created_count" : row.from_stage === row.to_stage ? "edit_count" : "stage_change_count"]++;
    if (row.from_stage !== row.to_stage && row.to_stage === "Dobijeno") person.realized_count++;
    if (row.from_stage !== row.to_stage && row.to_stage === "Izgubljeno") person.unrealized_count++;
    owners.set(id, person);
  }
  return {
    people: [...owners.values()].map(p => ({ id: p.user_id, name: p.user_name })), owners: [...owners.values()],
    total: items.length, opportunity_count: new Set(items.map(row => row.opportunity_id)).size,
    created_count: items.filter(row => row.from_stage === null).length,
    stage_change_count: items.filter(row => row.from_stage !== null && row.from_stage !== row.to_stage).length,
    edit_count: items.filter(row => row.from_stage === row.to_stage).length,
    realized_count: items.filter(row => row.to_stage === "Dobijeno" && row.from_stage !== row.to_stage).length,
    unrealized_count: items.filter(row => row.to_stage === "Izgubljeno" && row.from_stage !== row.to_stage).length,
    stage_counts: Object.fromEntries(opportunityStages.map(stage => [stage, items.filter(row => row.to_stage === stage && row.from_stage !== row.to_stage).length])),
    items: items.slice(offset, offset + 50),
  };
}
export default function Reports({ unit, role, demoItems, historyOnly = false }: { unit: number; role?: string; demoItems?: Change[]; historyOnly?: boolean }) {
  const allowed = !historyOnly || role === "manager" || role === "admin";
  const [mode, setMode] = useState<"day" | "month">("day");
  const [day, setDay] = useState(today);
  const [month, setMonth] = useState(() => today().slice(0, 7));
  const [ownerId, setOwnerId] = useState("");
  const [people, setPeople] = useState<{id: number; name: string}[]>([]);
  const [data, setData] = useState<SalesReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const [offset, setOffset] = useState(0);
  const value = mode === "day" ? day : month;
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError("");
    if (!allowed || !value) { setLoading(false); return; }
    setLoading(true);
    const period = reportPeriod(mode, value);
    if (demoItems) {
      setPeople(summarizeChanges(demoItems).people);
      const selected = demoItems.filter(row => {
        const day = dateInBelgrade(new Date(row.changed_at));
        return day >= period.from && day <= period.to && (!ownerId || String(row.owner_id ?? 0) === ownerId);
      }).sort((a, b) => b.changed_at.localeCompare(a.changed_at) || b.id - a.id);
      setData(summarizeChanges(selected, offset)); setLoading(false); return;
    }
    const params = new URLSearchParams({ date_from: period.from, date_to: period.to, include_demo: "false", limit: "50", offset: String(offset) });
    if (historyOnly) params.set("include_history", "true");
    if (ownerId) params.set("owner_id", ownerId);
    api<SalesReport>(`/units/${unit}/reports?${params}`, { signal: controller.signal })
      .then(data => { setData(data); setPeople(data.people); })
      .catch(e => { if (!controller.signal.aborted) setError(errorText(e)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [unit, mode, value, reload, offset, demoItems, ownerId, historyOnly, allowed]);

  if (!allowed) return <p className="error-message" role="alert">Hronologija promena je dostupna samo menadžerima i administratorima.</p>;
  return <>
    <div className="page-heading">
      <div><div className="eyebrow">AKTIVNOSTI U PRODAJNOM LEVKU</div><h1>{historyOnly ? "Hronologija promena - log" : "Izveštaji"}</h1>
        <p>{role === "sales" ? "Nove prilike i promene statusa za vaše kompanije." : "Nove prilike i promene statusa u prodajnom levku vaše firme."}</p></div>
      <button className="secondary-button" disabled={loading || !value} onClick={() => { setOffset(0); setReload(v => v + 1); }}><RefreshCw size={15} />Osveži</button>
    </div>
    <div className="report-toolbar">
      <div className="report-period-toggle" role="group" aria-label="Period izveštaja">
        {(["day", "month"] as const).map(option => <button key={option} type="button" aria-pressed={mode === option}
          className={mode === option ? "active" : ""} onClick={() => { setMode(option); setOffset(0); }}>{option === "day" ? "Dnevno" : "Mesečno"}</button>)}
      </div>
      <label className="report-date"><CalendarDays size={16} /><span className="report-sr-only">{mode === "day" ? "Izaberite dan" : "Izaberite mesec"}</span>
        {mode === "day" ? <input type="date" required value={day} onChange={e => { setDay(e.target.value); setOffset(0); }} /> : <input type="month" required value={month} onChange={e => { setMonth(e.target.value); setOffset(0); }} />}</label>
      {role !== "sales" && <label className="report-owner-filter">Komercijalista<select aria-label="Komercijalista" value={ownerId} disabled={loading} onChange={e => { setOwnerId(e.target.value); setOffset(0); }}><option value="">Svi komercijalisti</option>{people.map(person => <option key={person.id} value={person.id}>{person.name}</option>)}</select></label>}
      <span className="report-timezone">Vreme u Beogradu</span>
    </div>
    {demoItems && <p className="section-hint">Demo istorija se beleži u ovom browseru od prve promene statusa. Nema veze sa CRM bazom.</p>}
    {error && <p className="error-message" role="alert">{error}</p>}
    {!value ? <p className="empty">Izaberite {mode === "day" ? "datum" : "mesec"} za pregled.</p> : loading ? <p className="empty" role="status">Učitavanje izveštaja…</p> : data && <>
      {!historyOnly && <>
      <div className="metrics report-metrics">
        {[
          { label: "Nove prilike", value: data.created_count, note: "Kreirane u periodu" },
          { label: "Promene statusa", value: data.stage_change_count, note: "Prelazak iz jedne faze u drugu" },
          { label: "Realizovano", value: data.realized_count, note: "Prelasci u status Realizovano" },
          { label: "Nije realizovano", value: data.unrealized_count, note: "Prelasci u status Nije realizovano" },
        ].map(item => <article className="metric" key={item.label}><div className="metric-label">{item.label}</div><strong>{item.value}</strong><small>{item.note}</small></article>)}
      </div>
      <div className="report-charts">
        <section className="panel report-chart">
          <div className="report-chart-heading"><div><h2>Kretanje kroz levak</h2><p>Broj ulazaka u svaki status u izabranom periodu</p></div><span className="tag">{data.created_count + data.stage_change_count} događaja</span></div>
          <div className="report-stage-bars" role="img" aria-label={opportunityStages.map(stage => `${stageLabel(stage)}: ${data.stage_counts[stage] ?? 0}`).join(", ")}>
            {opportunityStages.map(stage => {
              const count = data.stage_counts[stage] ?? 0;
              const max = Math.max(1, ...Object.values(data.stage_counts));
              return <div className="report-stage-row" key={stage}><span>{stageLabel(stage)}</span><div className="report-stage-track"><div className={stage === "Dobijeno" ? "realized" : stage === "Izgubljeno" ? "unrealized" : ""} style={{ width: `${count / max * 100}%` }} /></div><strong>{count}</strong></div>;
            })}
          </div>
          {!data.created_count && !data.stage_change_count && <p className="report-chart-note">Nema ulazaka u statuse u ovom periodu.</p>}
        </section>
        <section className="panel report-chart">
          <div className="report-chart-heading"><div><h2>Vrste aktivnosti</h2><p>Nove prilike i promene statusa u periodu</p></div></div>
          <div className="report-activity-chart">
            <div className="report-donut" role="img" aria-label={`Nove prilike: ${data.created_count}, promene statusa: ${data.stage_change_count}`}
              style={{ background: data.total ? `conic-gradient(#2563eb 0 ${data.created_count / data.total * 100}%, #14b8a6 ${data.created_count / data.total * 100}% 100%)` : "#e8edf3" }}>
              <div><strong>{data.total}</strong><span>promena</span></div>
            </div>
            <div className="report-chart-legend">
              {[{ label: "Nove prilike", count: data.created_count, color: "#2563eb" }, { label: "Promene statusa", count: data.stage_change_count, color: "#14b8a6" }].map(item =>
                <div key={item.label}><span className="report-legend-dot" style={{ background: item.color }} /><span>{item.label}</span><strong>{item.count}</strong><small>{data.total ? Math.round(item.count / data.total * 100) : 0}%</small></div>)}
            </div>
          </div>
        </section>
      </div>
      {role !== "sales" && <section className="panel report-salespeople"><div className="panel-heading"><h2>Izveštaj po komercijalisti</h2></div><div className="table-scroll"><table><thead><tr><th>Komercijalista</th><th>Nove prilike</th><th>Promene statusa</th><th>Realizovano</th><th>Nije realizovano</th></tr></thead><tbody>{data.owners.map(person => <tr key={person.user_id}><td><strong>{person.user_name}</strong></td><td>{person.created_count}</td><td>{person.stage_change_count}</td><td>{person.realized_count}</td><td>{person.unrealized_count}</td></tr>)}</tbody></table>{!data.owners.length && <p className="empty">Nema promena za izabrani period.</p>}</div><p className="panel-note">Pregled se pripisuje komercijalisti koji vodi kompaniju. U istoriji se posebno vidi korisnik koji je izvršio promenu.</p></section>}
      </>}
      {historyOnly && <section className="panel">
        <div className="panel-heading"><h2>Hronologija promena - log</h2><span className="tag">Najnovije prvo</span></div>
        {!data.total ? <p className="empty">Nema zabeleženih promena u izabranom periodu. Izaberite drugi period.</p> : <>
          <div className="table-scroll"><table className="report-history"><thead><tr><th>Vreme</th><th>Kompanija / prilika</th><th>Komercijalista</th><th>Promena</th><th>Vrednost pri promeni</th><th>Korisnik</th></tr></thead><tbody>
            {data.items.map(row => <tr key={row.id}>
              <td>{formatTimestamp(row.changed_at)}</td>
              <td><strong>{row.company_name}</strong><small>{row.title}</small></td>
              <td>{row.owner_name ?? row.actor_name}</td>
              <td><strong>{row.from_stage === null ? "Nova prilika" : "Promena statusa"}</strong>
                <small>{row.from_stage ? stageLabel(row.from_stage) : "Kreiranje"} → {stageLabel(row.to_stage)}</small>
              </td>
              <td>{row.amount === null ? "Nije zabeležena" : formatAmount(row.amount)}</td>
              <td>{row.actor_name}</td>
            </tr>)}
          </tbody></table></div>
          <div className="form-actions report-pagination">
            <button className="secondary-button" disabled={!offset} onClick={() => setOffset(v => Math.max(0, v - 50))}>Prethodna</button>
            <span>{offset + 1}–{Math.min(offset + 50, data.total)} od {data.total} promena</span>
            <button className="secondary-button" disabled={offset + 50 >= data.total} onClick={() => setOffset(v => v + 50)}>Sledeća</button>
          </div>
        </>}
        <p className="panel-note">Prikazuju se kreiranje prilika i promene statusa u izabranom periodu. Jedna prilika može imati više promena statusa tokom istog perioda.</p>
      </section>}
    </>}
  </>;
}
