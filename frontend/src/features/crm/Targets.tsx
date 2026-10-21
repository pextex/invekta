import TeamBonus from "./TeamBonus";
import { useEffect, useState, type FormEvent } from "react";
import { RefreshCw, Save, Target } from "lucide-react";
import { api, errorText } from "../../lib/api";
import { formatAmount } from "./types";
import { belgradeToday } from "./taskCalendar";
import { businessTypeLabel } from "./businessTypes";
import { demoTargets, loadDemoGoals, saveDemoGoals, type DemoTargetContext } from "./targetsDemo";

export type TargetProgress = { category: string; target_amount: string | null; achieved_amount: string; achieved_count: number; version: number | null };
export type TargetPerson = { user_id: number; user_name: string; targets: TargetProgress[] };
export type TargetsData = { month: string; categories: string[]; can_manage: boolean; salespeople: TargetPerson[] };
export const targetPercent = (goal: string | null, achieved: string) => goal !== null && Number(goal) > 0 ? Math.round(Number(achieved) / Number(goal) * 100) : null;

export default function Targets({ unit, demo }: { unit: number; demo?: DemoTargetContext }) {
  const [month, setMonth] = useState(() => belgradeToday().slice(0, 7));
  const [data, setData] = useState<TargetsData | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [bonusReload, setBonusReload] = useState(0);
  const [reload, setReload] = useState(0);
  const [editing, setEditing] = useState<TargetPerson | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError("");
    if (!month) { setLoading(false); return; }
    if (demo) { setData(demoTargets(month, demo, loadDemoGoals(demo.organization, month))); setLoading(false); return; }
    setLoading(true);
    api<TargetsData>(`/units/${unit}/targets?${new URLSearchParams({ month })}`, { signal: controller.signal })
      .then(setData).catch(e => { if (!controller.signal.aborted) setError(errorText(e)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [unit, month, reload, demo]);
  async function save(event: FormEvent) {
    event.preventDefault(); if (!editing || !data) return;
    setBusy(true); setError(""); setMessage("");
    try {
      if (demo) {
        const goals = Object.fromEntries(editing.targets.map(row => [row.category, draft[row.category]]));
        const stored = saveDemoGoals(demo.organization, month, goals);
        setData(demoTargets(month, demo, goals));
        setMessage(stored ? "Demo target je sačuvan u ovom browseru." : "Browser ne dozvoljava čuvanje; demo target važi samo tokom ovog prikaza.");
      } else {
        setData(await api<TargetsData>(`/units/${unit}/targets`, { method: "PUT", body: JSON.stringify({
          month, user_id: editing.user_id, targets: editing.targets.map(row => ({ category: row.category, target_amount: draft[row.category], version: row.version })),
        }) }));
        setMessage("Mesečni target je sačuvan.");
      }
      setEditing(null);
      setBonusReload(v => v + 1);
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <>
    <div className="page-heading"><div><div className="eyebrow">CILJEVI I OSTVARENJE</div><h1>Mesečni targeti</h1><p>Cilj po komercijalisti, za svaku vrstu posla.</p></div><button className="secondary-button" disabled={loading || busy || !!editing || !month} onClick={() => setReload(v => v + 1)}><RefreshCw size={15} />Osveži</button></div>
    <div className="report-toolbar"><Target size={17} /><label className="target-month">Mesec<input type="month" required value={month} disabled={busy} onChange={e => { setMonth(e.target.value); setEditing(null); setMessage(""); }} /></label><span className="report-timezone">Vrednosti u RSD · vreme u Beogradu</span></div>
    {demo && <p className="section-hint">Demo cilj se čuva samo u ovom browseru. Ostvarenje prati demo prilike koje ste označili kao realizovane.</p>}
    {error && <p className="error-message" role="alert">{error}</p>}{message && <p className="success-message" role="status">{message}</p>}
    {!month ? <p className="empty">Izaberite mesec.</p> : loading ? <p className="empty" role="status">Učitavanje targeta…</p> : data && <>
      {!data.salespeople.length && <p className="empty">Nema aktivnih komercijalista u ovoj firmi. Pristup i uloge uređuje administrator.</p>}
      {data.salespeople.length > 0 && <h2>{demo || !data.can_manage ? "Ovo je vaš target" : "Pojedinačni targeti"}</h2>}
      {data.salespeople.map(person => <section className="panel target-person" key={person.user_id}>
        <div className="panel-heading"><h2>{person.user_name}</h2>{data.can_manage && <button className="secondary-button" disabled={busy || !!editing} onClick={() => { setEditing(person); setDraft(Object.fromEntries(person.targets.map(t => [t.category, t.target_amount ?? "0"]))); setMessage(""); }}>Postavi target</button>}</div>
        {editing?.user_id === person.user_id ? <form className="target-form" onSubmit={save}>
          <div className="target-cards">{person.targets.map(row => <label key={row.category}>{businessTypeLabel(row.category)} — mesečni cilj (RSD)<input required type="number" min="0" max="999999999999.99" step="0.01" disabled={busy} value={draft[row.category]} onChange={e => setDraft({ ...draft, [row.category]: e.target.value })} /></label>)}</div>
          <div className="form-actions"><button type="button" className="secondary-button" disabled={busy} onClick={() => setEditing(null)}>Otkaži</button><button className="primary-button" disabled={busy}><Save size={15} />{busy ? "Čuvanje…" : "Sačuvaj target"}</button></div>
        </form> : <div className="target-cards">{person.targets.map(row => {
          const percent = targetPercent(row.target_amount, row.achieved_amount);
          return <article className="target-card" key={row.category}><div className="target-card-heading"><span>{businessTypeLabel(row.category)}</span><strong>{percent === null ? "Bez targeta" : `${percent}%`}</strong></div>
            <strong className="target-achieved">{formatAmount(row.achieved_amount)}</strong><p>ostvareno · {row.achieved_count} realizovanih poslova</p>
            <div className="target-progress" role="progressbar" aria-label={`${person.user_name} — ${businessTypeLabel(row.category)}`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.min(100, percent ?? 0)} aria-valuetext={percent === null ? "Target nije postavljen" : `${percent}% ostvarenja`}><div style={{ width: `${Math.min(100, percent ?? 0)}%` }} /></div>
            <div className="target-card-footer"><span>Cilj: {row.target_amount !== null && Number(row.target_amount) > 0 ? formatAmount(row.target_amount) : "nije postavljen"}</span><span>{percent === null ? "" : percent >= 100 ? "Cilj ostvaren" : `Preostalo: ${formatAmount(Math.max(0, Number(row.target_amount) - Number(row.achieved_amount)))}`}</span></div>
          </article>;
        })}</div>}
      </section>)}
      <p className="panel-note target-explanation">Ostvarenje se računa po poslednjem prelasku trenutno realizovane prilike u status Realizovano, prema datumu tog događaja. Jedna prilika se broji jednom. Koristi se vrednost i vrsta posla pri realizaciji; to nije fakturisan prihod. Starije prilike bez zabeležene realizacije ili istorijske vrednosti nisu uključene. Realizovane marketing porudžbine računaju se po potvrđenom datumu realizacije i vrsti posla; ispravka iznosa porudžbine osvežava ostvarenje u tom mesecu.</p>
    </>}
    {data && <TeamBonus unit={unit} month={month} reload={reload + bonusReload} demo={demo && data ? {
      organization: demo.organization,
      individualTotal: data.salespeople.flatMap(person => person.targets).reduce((sum, row) => sum + Number(row.target_amount ?? 0), 0).toFixed(2),
      achieved: data.salespeople.flatMap(person => person.targets).reduce((sum, row) => sum + Number(row.achieved_amount), 0).toFixed(2),
      achievedCount: data.salespeople.flatMap(person => person.targets).reduce((sum, row) => sum + row.achieved_count, 0),
    } : undefined} />}
  </>;
}
