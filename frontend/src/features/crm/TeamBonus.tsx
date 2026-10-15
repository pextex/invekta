import { useEffect, useState, type FormEvent } from "react";
import { Gift, Save, Trophy } from "lucide-react";
import { api, errorText } from "../../lib/api";
import { formatAmount } from "./types";

type Bonus = { month: string; target_amount: string | null; reward_note: string | null; version: number | null; can_manage: boolean;
  individual_targets_total: string; achieved_amount: string; my_achieved_amount: string; salespeople_count: number; achieved_count: number; unlocked: boolean };
export type DemoBonus = { organization: string; individualTotal: string; achieved: string; achievedCount: number };
function readDemo(demo: DemoBonus, month: string): Bonus {
  let goal: { target_amount: string; reward_note: string } | null = null;
  try {
    const value = JSON.parse(localStorage.getItem(`crm-demo-team-bonus-v1-${demo.organization}-${month}`) ?? "null");
    if (value && typeof value.target_amount === "string" && /^\d{1,12}(\.\d{1,2})?$/.test(value.target_amount) && typeof value.reward_note === "string") goal = value;
  } catch { /* Demo remains usable without local storage. */ }
  return { month, target_amount: goal?.target_amount ?? null, reward_note: goal?.reward_note ?? null, version: null,
    can_manage: true, individual_targets_total: demo.individualTotal, achieved_amount: demo.achieved, my_achieved_amount: demo.achieved,
    salespeople_count: 1, achieved_count: demo.achievedCount, unlocked: !!goal && Number(goal.target_amount) > 0 && Number(demo.achieved) >= Number(goal.target_amount) };
}
export default function TeamBonus({ unit, month, reload, demo }: { unit: number; month: string; reload: number; demo?: DemoBonus }) {
  const [data, setData] = useState<Bonus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  useEffect(() => {
    const controller = new AbortController(); setError(""); setData(null); setEditing(false); setMessage("");
    if (!month) { setLoading(false); return; }
    if (demo) { setData(readDemo(demo, month)); setLoading(false); return; }
    setLoading(true);
    api<Bonus>(`/units/${unit}/team-bonus?${new URLSearchParams({ month })}`, { signal: controller.signal })
      .then(setData).catch(e => { if (!controller.signal.aborted) setError(errorText(e)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [unit, month, reload, demo]);
  async function save(event: FormEvent) {
    event.preventDefault(); if (!data) return;
    setBusy(true); setError(""); setMessage("");
    try {
      if (demo) {
        let stored = true;
        try { localStorage.setItem(`crm-demo-team-bonus-v1-${demo.organization}-${month}`, JSON.stringify({ target_amount: amount, reward_note: note })); } catch { stored = false; }
        setData({ ...data, target_amount: amount, reward_note: note, unlocked: Number(amount) > 0 && Number(data.achieved_amount) >= Number(amount) });
        setMessage(stored ? "Demo kolektivni cilj je sačuvan u ovom browseru." : "Browser ne dozvoljava čuvanje. Cilj važi samo tokom ovog prikaza.");
      } else {
        setData(await api<Bonus>(`/units/${unit}/team-bonus`, { method: "PUT", body: JSON.stringify({ month, target_amount: amount, reward_note: note.trim() || null, version: data.version }) }));
        setMessage("Kolektivni cilj i opis bonusa su sačuvani.");
      }
      setEditing(false);
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  if (!month) return null;
  const percent = data?.target_amount && Number(data.target_amount) > 0 ? Math.round(Number(data.achieved_amount) / Number(data.target_amount) * 100) : null;
  return <section className="panel team-bonus">
    <div className="panel-heading"><h2><Gift size={19} />Kolektivni bonus za tim</h2>{data?.can_manage && <button className="secondary-button" disabled={loading || busy || editing} onClick={() => { setAmount(data.target_amount ?? "0"); setNote(data.reward_note ?? ""); setEditing(true); setMessage(""); }}>Postavi kolektivni cilj</button>}</div>
    {error && <p className="error-message" role="alert">{error}</p>}{message && <p className="success-message" role="status">{message}</p>}
    {loading ? <p className="empty" role="status">Učitavanje kolektivnog cilja…</p> : data && <>
      {editing ? <form onSubmit={save} className="team-bonus-form"><div className="form-grid"><label>Kolektivni mesečni cilj (RSD)<input type="number" min="0" max="999999999999.99" step="0.01" required disabled={busy} value={amount} onChange={e => setAmount(e.target.value)} /></label><label>Opis bonusa za ceo tim (opciono)<textarea maxLength={1000} rows={3} disabled={busy} value={note} onChange={e => setNote(e.target.value)} /></label></div><div className="form-actions"><button type="button" className="secondary-button" disabled={busy} onClick={() => setEditing(false)}>Otkaži</button><button className="primary-button" disabled={busy}><Save size={15} />{busy ? "Čuvanje…" : "Sačuvaj kolektivni cilj"}</button></div></form> : <div className="team-bonus-body">
        <div className="team-bonus-progress"><span className={data.unlocked ? "tag green" : "tag"}>{data.unlocked ? <><Trophy size={13} /> Kolektivni cilj ostvaren</> : percent === null ? "Cilj nije postavljen" : "Tim napreduje ka cilju"}</span><strong>{formatAmount(data.achieved_amount)}</strong><p>realizacija tima od {data.salespeople_count} komercijalista · {data.achieved_count} realizovanih poslova</p>
          <div className="target-progress" role="progressbar" aria-label="Ostvarenje kolektivnog cilja" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.min(100, percent ?? 0)} aria-valuetext={percent === null ? "Cilj nije postavljen" : `${percent}%`}><div style={{ width: `${Math.min(100, percent ?? 0)}%` }} /></div><small>{percent === null ? "Administrator postavlja kolektivni cilj za izabrani mesec." : `${percent}% od cilja ${formatAmount(data.target_amount ?? "0")}`}</small>
        </div>
        <div className="team-bonus-details"><p><span>Zbir pojedinačnih targeta</span><strong>{formatAmount(data.individual_targets_total)}</strong></p><p><span>Vaš doprinos realizaciji</span><strong>{formatAmount(data.my_achieved_amount)}</strong></p><div className="team-reward"><strong>Zajednički bonus</strong><p>{data.reward_note || "Opis bonusa još nije unet."}</p></div></div>
      </div>}
      <p className="panel-note">Zajednički cilj i zbirno ostvarenje vide svi komercijalisti ovog brenda. Pojedinačni targeti sabiraju se za tim, a napredak prati realizovane poslove. Prikaz ne predstavlja obračun ili potvrdu isplate bonusa.</p>
    </>}
  </section>;
}
