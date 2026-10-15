import { useEffect, useState, type FormEvent } from "react";
import { BookOpen, Save } from "lucide-react";
import { api, errorText } from "../../lib/api";

type Knowledge = { content: string; version: number | null; updated_at: string | null };
export default function AiKnowledge({ unit, brand, canManage }: { unit: number; brand: string; canManage: boolean }) {
  const [saved, setSaved] = useState<Knowledge | null>(null);
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(""); setMessage("");
    api<Knowledge>(`/units/${unit}/ai/knowledge`, { signal: controller.signal })
      .then(data => { if (!controller.signal.aborted) { setSaved(data); setContent(data.content); } })
      .catch(e => { if (!controller.signal.aborted) setError(errorText(e)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [unit, reload]);
  async function save(event: FormEvent) {
    event.preventDefault(); if (!saved) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const next = await api<Knowledge>(`/units/${unit}/ai/knowledge`, {
        method: "PUT", body: JSON.stringify({ content, version: saved.version }),
      });
      setSaved(next); setContent(next.content); setMessage("Znanje je sačuvano. Koristiće se za sledeće AI nacrte.");
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <section className="panel ai-knowledge">
    <details>
      <summary><BookOpen size={18} /> Znanje brenda · {brand} <span>{loading ? "Učitavanje…" : saved?.content.trim() ? "Dodato" : "Nije dodato"}</span></summary>
      <p className="panel-note">Odobrene informacije o proizvodima, uslugama, prednostima i uslovima ovog brenda. Administrator ih dopunjava; AI ih koristi pri pisanju mejla. Ne unosite lozinke niti privatne podatke klijenata.</p>
      {error && <p className="error-message" role="alert">{error}</p>}
      {message && <p className="success-message" role="status">{message}</p>}
      {canManage ? <form onSubmit={save}>
        <label>Odobreno znanje brenda
          <textarea aria-label="Odobreno znanje brenda" rows={9} maxLength={12000} value={content} disabled={loading || busy || !saved}
            onChange={event => setContent(event.target.value)} placeholder="Predstavljanje firme, proizvodi/usluge, ciljni kupci, prednosti, odobreni uslovi i zvanični izvori…" />
        </label>
        <p className="panel-note">{content.length.toLocaleString("sr-RS")} / 12.000 znakova. Unesite samo proverene činjenice. Prazno polje uklanja prethodno znanje.</p>
        <div className="form-actions">
          <button className="primary-button" disabled={busy || loading || !saved || saved.content === content}><Save size={16} /> {busy ? "Čuvanje…" : "Sačuvaj znanje"}</button>
          <button type="button" className="secondary-button" disabled={loading || busy} onClick={() => setReload(v => v + 1)}>Ponovo učitaj sačuvano</button>
        </div>
      </form> : <div className="ai-knowledge-text">{loading ? "Učitavanje…" : saved?.content || "Administrator još nije dodao znanje. Navedite potrebne činjenice u uputstvu za mejl."}</div>}
      {!canManage && error && <button className="secondary-button" onClick={() => setReload(v => v + 1)}>Pokušaj ponovo</button>}
    </details>
  </section>;
}
