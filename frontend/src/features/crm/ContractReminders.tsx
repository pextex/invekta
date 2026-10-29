import { useEffect, useState } from "react";
import { api, errorText } from "../../lib/api";
import { formatDate } from "./types";

type Reminder = { company_id: number; company_name: string; contract_expires_on: string; days_remaining: number };
type Reminders = { total: number; items: Reminder[] };
export function contractDeadlineLabel(days: number) {
  return days < 0 ? `Istekao pre ${Math.abs(days)} dana` : days === 0 ? "Ističe danas" : `Ističe za ${days} dana`;
}
export default function ContractReminders({ unit, reload, onOpen }: { unit: number; reload: number; onOpen: (id: number) => void }) {
  const [data, setData] = useState<Reminders | null>(null);
  const [error, setError] = useState("");
  const [offset, setOffset] = useState(0);
  const [tick, setTick] = useState(0);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    const update = () => { if (document.visibilityState !== "hidden") setTick(t => t + 1); };
    const timer = window.setInterval(update, 60000);
    window.addEventListener("focus", update);
    return () => { clearInterval(timer); window.removeEventListener("focus", update); };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    api<Reminders>(`/units/${unit}/contract-reminders?limit=5&offset=${offset}`, { signal: controller.signal })
      .then(result => {
        if (controller.signal.aborted) return;
        if (offset > 0 && offset >= result.total) { setOffset(0); return; }
        setData(result); setError("");
      })
      .catch(e => { if (!controller.signal.aborted) { setData(null); setError(errorText(e)); } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [unit, reload, tick, offset]);
  if (error) return <p role="alert" className="error-message">Podsetnici za ugovore: {error} <button className="text-button" onClick={() => setTick(t => t + 1)}>Pokušaj ponovo</button></p>;
  if (!data?.total) return null;
  return <section className="panel" aria-label="Podsetnici za ugovore" aria-busy={loading}>
    <details>
      <summary><strong>Ugovori koji ističu ili su istekli ({data.total})</strong></summary>
      <p>Podsetnik se prikazuje 30 dana pre isteka i ostaje dok ne ažurirate datum ugovora.</p>
      <div className="today-task-list">{data.items.map(item => <button type="button" className="today-task" key={item.company_id} onClick={() => onOpen(item.company_id)}>
        <span><strong>{item.company_name}</strong><small>{formatDate(item.contract_expires_on)} · {contractDeadlineLabel(item.days_remaining)}</small></span><span>Otvori kompaniju →</span>
      </button>)}</div>
      {data.total > 5 && <div className="form-actions"><button className="secondary-button" disabled={loading || offset === 0} onClick={() => setOffset(n => Math.max(0, n - 5))}>Prethodni ugovori</button><span>{offset + 1}–{Math.min(offset + 5, data.total)} od {data.total}</span><button className="secondary-button" disabled={loading || offset + 5 >= data.total} onClick={() => setOffset(n => n + 5)}>Sledeći ugovori</button></div>}
    </details>
  </section>;
}
