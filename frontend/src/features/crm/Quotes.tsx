import { useEffect, useRef, useState, type FormEvent } from "react";
import { Download, FileText, Search, Upload } from "lucide-react";
import { api, errorText } from "../../lib/api";
import { documentAccept, documentSize, downloadDocument, uploadDocument, validateDocument, type DocumentPage, type SalesDocument } from "./salesDocuments";
import "./quotes.css";

const pageSize = 20;
export default function Quotes({ unit = 0, canUpload = false, demo = false }: { unit?: number; canUpload?: boolean; demo?: boolean }) {
  const [documents, setDocuments] = useState<DocumentPage>({ items: [], total: 0 });
  const [loading, setLoading] = useState(!demo), [busy, setBusy] = useState(false);
  const [search, setSearch] = useState(""), [offset, setOffset] = useState(0), [reload, setReload] = useState(0);
  const [open, setOpen] = useState(false), [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null), [downloading, setDownloading] = useState<number | null>(null);
  const [error, setError] = useState(""), [message, setMessage] = useState("");
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (demo || !unit) return;
    const controller = new AbortController();
    setLoading(true); setError("");
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams({ search: search.trim(), limit: String(pageSize), offset: String(offset) });
      api<DocumentPage>(`/units/${unit}/sales-documents?${params}`, { signal: controller.signal })
        .then(setDocuments)
        .catch(e => { if (!controller.signal.aborted) { setDocuments({ items: [], total: 0 }); setError(errorText(e)); } })
        .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }, 180);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [unit, demo, search, offset, reload]);
  useEffect(() => { if (open) input.current?.focus(); }, [open]);
  async function upload(event: FormEvent) {
    event.preventDefault();
    if (!file || demo || !canUpload) return;
    const invalid = validateDocument(file);
    if (invalid) { setError(invalid); return; }
    setBusy(true); setError(""); setMessage("");
    try {
      await uploadDocument(unit, file, title);
      setFile(null); setTitle(""); setOpen(false); setOffset(0); setSearch(""); setReload(v => v + 1);
      setMessage("Fajl je sačuvan i dostupan korisnicima ovog brenda.");
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  async function download(record: SalesDocument) {
    if (downloading !== null || demo) return;
    setDownloading(record.id); setError("");
    try {
      const blob = await downloadDocument(unit, record);
      const url = URL.createObjectURL(blob), link = document.createElement("a");
      link.href = url; link.download = record.filename; document.body.append(link); link.click(); link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) { setError(errorText(e)); } finally { setDownloading(null); }
  }
  return <>
    <div className="page-heading"><div><div className="eyebrow">DOKUMENTACIJA ZA PRODAJU</div><h1>Ponude</h1><p>PDF ponude, katalozi i drugi fajlovi dostupni timu ovog brenda.</p></div>
      {canUpload && !demo && <button className="primary-button" disabled={busy} onClick={() => { setOpen(true); setError(""); setMessage(""); }}><Upload size={17} />Dodaj fajl</button>}</div>
    <p className="section-hint">{demo ? "Dodavanje i preuzimanje fajlova dostupno je u povezanom CRM-u posle prijave." : canUpload ? "Kao administrator možete dodavati fajlove. Svi korisnici sa pristupom ovom brendu mogu da ih preuzmu." : "Dokumente dodaje administrator. Dostupne fajlove možete preuzeti."}</p>
    {error && <p className="error-message" role="alert">{error}</p>}
    {message && <p className="success-message" role="status">{message}</p>}
    {open && canUpload && !demo && <section className="panel sales-document-editor"><h2>Dodaj prodajni dokument</h2><form onSubmit={upload}><fieldset disabled={busy}>
      <label>Naziv dokumenta (opciono)<input ref={input} maxLength={200} value={title} onChange={e => setTitle(e.target.value)} placeholder="Npr. Ponuda za prodaju opreme" /></label>
      <label className="sales-document-file">Izaberi fajl<input type="file" required accept={documentAccept} onChange={e => { const next = e.target.files?.[0] ?? null; setFile(next); setError(next ? validateDocument(next) ?? "" : ""); }} /></label>
      <p className="section-hint">PDF, Word, Excel, PNG ili JPG · najviše 10 MB po fajlu.</p>
      {file && <p className="sales-document-selected"><FileText size={18} /><span>{file.name} · {documentSize(file.size)}</span></p>}
      </fieldset><div className="form-actions"><button type="button" className="secondary-button" disabled={busy} onClick={() => { setOpen(false); setFile(null); setTitle(""); }}>Otkaži</button><button className="primary-button" disabled={busy || !file || !!validateDocument(file)}><Upload size={16} />{busy ? "Slanje fajla…" : "Sačuvaj fajl"}</button></div></form></section>}
    <section className="panel"><div className="sales-document-toolbar"><h2>Prodajni fajlovi {loading ? "" : `(${documents.total})`}</h2><label className="sales-document-search"><Search size={17} /><span className="sr-only">Pretraga fajlova</span><input type="search" aria-label="Pretraga fajlova" placeholder="Pretraži naziv ili ime fajla…" maxLength={200} disabled={demo} value={search} onChange={e => { setSearch(e.target.value); setOffset(0); }} /></label></div>
      {loading ? <p className="empty" role="status">Učitavanje fajlova…</p> : !documents.items.length ? <div className="sales-document-empty"><FileText size={35} /><h3>{search.trim() ? "Nema rezultata pretrage" : "Još nema dodatih fajlova"}</h3><p>{search.trim() ? "Pokušajte sa drugim nazivom." : "Ovde će se pojaviti ponude i prodajni dokumenti koje administrator doda za vaš tim."}</p></div> : <div className="sales-document-grid">{documents.items.map(record => <article className="sales-document-card" key={record.id}>
        <div className="sales-document-type"><FileText size={24} /><span>{record.filename.split(".").pop()?.toUpperCase()}</span></div><div className="sales-document-details"><h3>{record.title}</h3><p>{record.filename}</p><small>{documentSize(record.size_bytes)} · {new Intl.DateTimeFormat("sr-Latn-RS", { dateStyle: "medium", timeZone: "Europe/Belgrade" }).format(new Date(record.created_at))}</small><small>Dodao/la: {record.uploaded_by_name}</small></div>
        <button className="secondary-button" aria-label={`Preuzmi ${record.filename}`} disabled={downloading !== null} onClick={() => download(record)}><Download size={16} />{downloading === record.id ? "Preuzimanje…" : "Preuzmi"}</button></article>)}</div>}
      {documents.total > pageSize && <div className="pagination"><button className="secondary-button" disabled={loading || offset === 0} onClick={() => setOffset(v => Math.max(0, v - pageSize))}>Prethodna</button><span>{offset + 1}–{Math.min(offset + pageSize, documents.total)} od {documents.total}</span><button className="secondary-button" disabled={loading || offset + pageSize >= documents.total} onClick={() => setOffset(v => v + pageSize)}>Sledeća</button></div>}
    </section>
  </>;
}
