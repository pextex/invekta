import { useEffect, useRef, useState, type FormEvent } from "react";
import { BookOpen, Copy, Sparkles } from "lucide-react";
import AiKnowledge from "./AiKnowledge";
import CompanyPicker from "./CompanyPicker";
import { api, errorText } from "../../lib/api";
import { prepareLocalMessage } from "../../lib/messageTemplates";
import type { Company } from "./types";
import "./aiAssistant.css";
import { organizationAiName } from "../../organizations";

type Recipient = { id: number; name: string; position: string | null; email: string };
type Draft = { subject: string; body: string; recipient: string | null; recipients: Recipient[]; model: string };
type RecipientsState = { company: number; items: Recipient[]; loading: boolean; error: string };

export default function AiAssistant({ unit, companies, demo = false, organization = "CRM" }: {
  unit: number; companies: Company[]; demo?: boolean; organization?: string;
}) {
  const assistantName = organizationAiName(organization);
  const [company, setCompany] = useState(0);
  const [companyName, setCompanyName] = useState("");
  const [instructions, setInstructions] = useState("");
  const [draft, setDraft] = useState<Draft | null>(null);
  const [recipients, setRecipients] = useState<RecipientsState>({ company: 0, items: [], loading: false, error: "" });
  const [refreshContacts, setRefreshContacts] = useState(0);
  const [engine, setEngine] = useState<"gemini" | "templates">("templates");
  const [configured, setConfigured] = useState(false);
  const [checking, setChecking] = useState(!demo);
  const [canManageKnowledge, setCanManageKnowledge] = useState(false);
  const [showKnowledge, setShowKnowledge] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const bodyRef = useRef<HTMLTextAreaElement>(null);
  const recipientRef = useRef<HTMLInputElement>(null);
  const generation = useRef<AbortController | null>(null);

  useEffect(() => () => generation.current?.abort(), []);
  useEffect(() => {
    if (demo) return;
    const controller = new AbortController();
    setChecking(true);
    api<{ configured: boolean; engine: "gemini" | "templates"; can_manage_knowledge: boolean }>(
      `/units/${unit}/ai/status`, { signal: controller.signal },
    ).then(data => {
      if (controller.signal.aborted) return;
      setConfigured(data.configured); setEngine(data.engine); setCanManageKnowledge(data.can_manage_knowledge);
    }).catch(e => { if (!controller.signal.aborted) setError(errorText(e)); })
      .finally(() => { if (!controller.signal.aborted) setChecking(false); });
    return () => controller.abort();
  }, [unit, demo]);

  useEffect(() => {
    if (!company || demo) {
      setRecipients({ company, items: [], loading: false, error: "" });
      return;
    }
    const controller = new AbortController();
    setRecipients({ company, items: [], loading: true, error: "" });
    api<Recipient[]>(`/units/${unit}/ai/companies/${company}/recipients`, { signal: controller.signal })
      .then(items => { if (!controller.signal.aborted) setRecipients({ company, items, loading: false, error: "" }); })
      .catch(e => { if (!controller.signal.aborted) setRecipients({ company, items: [], loading: false, error: errorText(e) }); });
    return () => controller.abort();
  }, [unit, company, demo, refreshContacts]);

  const currentRecipients = recipients.company === company ? recipients.items : [];
  const contactsLoading = !demo && company > 0 && (recipients.company !== company || recipients.loading);
  const contactsError = recipients.company === company ? recipients.error : "";
  function chooseCompany(id: number, name?: string) {
    setCompany(id); setCompanyName(name ?? ""); setDraft(null); setError(""); setMessage("");
  }
  async function generate(event: FormEvent) {
    event.preventDefault();
    if (!company || !instructions.trim() || contactsLoading || contactsError) return;
    const controller = new AbortController();
    generation.current = controller;
    setBusy(true); setError(""); setMessage("");
    try {
      let next: Draft;
      if (demo) {
        const text = prepareLocalMessage({ company: companyName, organization, instructions,
          mode: "email", goal: "meeting", tone: "professional", language: "sr" });
        next = { ...text, recipient: null, recipients: [], model: "local-templates-demo" };
      } else {
        next = await api<Draft>(`/units/${unit}/ai/generate`, {
          method: "POST", signal: controller.signal,
          body: JSON.stringify({ company_id: company, instructions: instructions.trim() }),
        });
      }
      if (controller.signal.aborted) return;
      setDraft(next);
      setRecipients({ company, items: next.recipients, loading: false, error: "" });
      setMessage("Mejl je pripremljen. Pregledajte primaoce i tekst pre kopiranja.");
    } catch (e) { if (!controller.signal.aborted) setError(errorText(e)); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }
  async function copy(addressesOnly = false) {
    if (!draft) return;
    if (draft.recipient?.trim() && recipientRef.current && !recipientRef.current.checkValidity()) {
      recipientRef.current.reportValidity();
      setError("Proverite email adrese primalaca. Više adresa odvojite zarezom.");
      return;
    }
    try {
      await navigator.clipboard.writeText(addressesOnly ? draft.recipient ?? "" :
        `${draft.recipient?.trim() ? `Za: ${draft.recipient.trim()}\n` : ""}Predmet: ${draft.subject}\n\n${draft.body}`);
      setMessage(addressesOnly ? "Adrese primalaca su kopirane." : "Mejl je kopiran. Nalepite ga u svoj email program.");
    } catch {
      const field = addressesOnly ? recipientRef.current : bodyRef.current;
      field?.focus(); field?.select();
      setError("Browser nije dozvolio kopiranje. Označeni tekst kopirajte ručno.");
    }
  }
  return <>
    <div className="page-heading">
      <div><h1>{assistantName}</h1><p>Opišite mejl i izaberite kompaniju. Kontakte popunjavamo automatski.</p></div>
      {canManageKnowledge ? <button className="secondary-button" aria-expanded={showKnowledge} aria-controls="ai-brand-settings"
        onClick={() => setShowKnowledge(value => !value)}><BookOpen size={16} /> Znanje brenda</button> : <Sparkles size={28} />}
    </div>
    {error && <p className="error-message" role="alert">{error}</p>}
    {message && <p className="success-message" role="status">{message}</p>}
    {demo ? <p className="demo-notice">Demo koristi lokalni šablon. Automatski kontakti i Gemini AI rade u prijavljenom CRM-u.</p> :
      !checking && !configured ? <p className="demo-notice">{assistantName} još nije povezan. Administrator treba da podesi Gemini ključ na serveru.</p> :
        !checking && engine === "templates" ? <p className="demo-notice">Gemini AI je isključen. Lokalni šablon ne tumači slobodno uputstvo.</p> : null}
    {canManageKnowledge && showKnowledge && <div id="ai-brand-settings">
      <AiKnowledge unit={unit} brand={organization} canManage expanded />
    </div>}
    <div className="ai-grid">
      <section className="panel">
        <h2>Priprema mejla</h2>
        <form onSubmit={generate}>
          <fieldset className="ai-fields" disabled={busy || checking}>
            <label>Šta želite da napišete?
              <textarea aria-label="Uputstvo za mejl" required maxLength={4000} rows={7} value={instructions}
                onChange={event => setInstructions(event.target.value)}
                placeholder="Npr. Napiši kratak mejl na engleskom. Predstavi našu ponudu ovom hotelu i predloži razgovor." />
            </label>
            <CompanyPicker unit={unit} value={company} selectedName={companyName} options={companies} local={demo}
              disabled={busy || checking} label="Kompanija kojoj šaljete mejl" ariaLabel="Kompanija za mejl" onChange={chooseCompany} />
            {company > 0 && <div className="ai-auto-contacts" aria-live="polite">
              {contactsLoading ? <p>Učitavanje kontakata…</p> : contactsError ? <>
                <p className="error-message" role="alert">{contactsError}</p>
                <button type="button" className="text-button" onClick={() => setRefreshContacts(value => value + 1)}>Ponovo učitaj kontakte</button>
              </> : currentRecipients.length ? <>
                <strong>Primaoci iz kompanije</strong>
                <ul>{currentRecipients.map(person => <li key={person.id}><span>{person.name}{person.position ? ` · ${person.position}` : ""}</span><small>{person.email}</small></li>)}</ul>
              </> : <p>{demo ? "Demo nema stvarne kontakte klijenata." : "Kompanija nema kontakt sa unetom ispravnom email adresom. Dodajte kontakt u profilu kompanije ili popunite primaoce u pripremljenom mejlu."}</p>}
            </div>}
            {!demo && engine === "gemini" && configured && <p className="panel-note">Pripremom šaljete zahtev, podatke izabrane kompanije i imena kontakata Gemini servisu. Znanje aktivnog brenda koristi se za tekst mejla.</p>}
            <button className="primary-button" disabled={(!demo && !configured) || !company || !instructions.trim() || contactsLoading || !!contactsError}>
              <Sparkles size={16} /> {busy ? "Pripremanje mejla…" : demo || engine === "templates" ? "Pripremi mejl iz šablona" : "Napiši mejl"}
            </button>
          </fieldset>
        </form>
      </section>
      <section className="panel">
        <h2>Vaš mejl</h2>
        {draft ? <fieldset className="ai-fields" disabled={busy}>
          <label>Primaoci
            <input ref={recipientRef} aria-label="Primaoci" type="email" multiple value={draft.recipient ?? ""}
              onChange={event => setDraft({ ...draft, recipient: event.target.value })} placeholder="Email adrese odvojene zarezom" />
          </label>
          <label>Predmet<input maxLength={200} value={draft.subject} onChange={event => setDraft({ ...draft, subject: event.target.value })} /></label>
          <label>Tekst poruke<textarea ref={bodyRef} aria-label="Tekst poruke" maxLength={20000} rows={16}
            value={draft.body} onChange={event => setDraft({ ...draft, body: event.target.value })} /></label>
          <div className="form-actions">
            <button type="button" className="primary-button" onClick={() => copy()}><Copy size={16} /> Kopiraj mejl</button>
            <button type="button" className="secondary-button" disabled={!draft.recipient?.trim()} onClick={() => copy(true)}>Kopiraj adrese</button>
          </div>
          <p className="panel-note">Primaoce i tekst možete izmeniti. Mejl nije poslat i ne čuva se. Kopirajte ga pre napuštanja ili osvežavanja ekrana.</p>
        </fieldset> : <p className="empty">Ovde će se pojaviti pripremljen mejl sa primaocima iz izabrane kompanije.</p>}
      </section>
    </div>
  </>;
}
