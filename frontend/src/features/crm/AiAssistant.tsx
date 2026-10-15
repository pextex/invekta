import AiKnowledge from "./AiKnowledge";
import CompanyPicker from "./CompanyPicker";
import "./aiAssistant.css";
import { stageLabel } from "./types";
import {
  prepareLocalMessage,
  blankPersonalization,
} from "../../lib/messageTemplates";
import { useEffect, useState, useRef, type FormEvent } from "react";
import { Sparkles, Copy } from "lucide-react";
import { api, errorText } from "../../lib/api";
import type { Company, Contact, Opportunity, OpportunityPage } from "./types";

type Draft = { subject: string; body: string; recipient: string | null; model: string };
const modes = [
  { value: "email", label: "Novi email" },
  { value: "reply", label: "Odgovor na poruku" },
  { value: "follow_up", label: "Follow-up" },
];
export default function AiAssistant({
  unit,
  companies,
  demo = false,
  organization = "CRM",
}: {
  unit: number;
  companies: Company[];
  demo?: boolean;
  organization?: string;
}) {
  const bodyRef = useRef<HTMLTextAreaElement>(null);
  const [company, setCompany] = useState(0),
    [contact, setContact] = useState(0),
    [opportunity, setOpportunity] = useState(0);
  const [contacts, setContacts] = useState<Contact[]>([]),
    [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [mode, setMode] = useState("email"),
    [tone, setTone] = useState("professional"),
    [language, setLanguage] = useState("sr"),
    [instructions, setInstructions] = useState(""),
    [incoming, setIncoming] = useState("");
  const [personalization, setPersonalization] = useState(
    blankPersonalization(),
  );
  const [goal, setGoal] = useState("meeting");
  const [engine, setEngine] = useState<"groq" | "templates">("templates");
  const [canManageKnowledge, setCanManageKnowledge] = useState(false);
  const [configured, setConfigured] = useState(false),
    [checking, setChecking] = useState(!demo),
    [contextLoading, setContextLoading] = useState(false),
    [contextError, setContextError] = useState("");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const [draft, setDraft] = useState<Draft | null>(null);
  useEffect(() => {
    if (demo) return;
    const controller = new AbortController();
    setChecking(true);
    api<{ configured: boolean; engine: "groq" | "templates"; can_manage_knowledge: boolean }>(
      `/units/${unit}/ai/status`,
      {
        signal: controller.signal,
      },
    )
      .then((data) => {
        if (controller.signal.aborted) return;
        setConfigured(data.configured);
        setEngine(data.engine);
        setCanManageKnowledge(data.can_manage_knowledge);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(errorText(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setChecking(false);
      });
    return () => controller.abort();
  }, [unit, demo]);
  useEffect(() => {
    setContacts([]);
    setOpportunities([]);
    setContact(0);
    setOpportunity(0);
    setContextError("");
    if (!company || demo) {
      setContextLoading(false);
      return;
    }
    const controller = new AbortController();
    setContextLoading(true);
    Promise.all([
      api<Contact[]>(`/units/${unit}/companies/${company}/contacts`, {
        signal: controller.signal,
      }),
      api<OpportunityPage>(
        `/units/${unit}/opportunities?company_id=${company}&limit=100`,
        { signal: controller.signal },
      ),
    ])
      .then(([c, o]) => {
        setContacts(c);
        setOpportunities(o.items);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setContextError(errorText(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setContextLoading(false);
      });
    return () => controller.abort();
  }, [unit, company, demo]);
  async function generate(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (demo) {
        const selected = companies.find((c) => c.id === company);
        if (!selected) throw new Error("Izaberite kompaniju.");
        const text = prepareLocalMessage({
          company: selected.name,
          organization,
          instructions,
          personalization,
          mode,
          goal,
          tone,
          language,
        });
        const next: Draft = {
          ...text,
          recipient: null,
          model: "local-templates-demo",
        };
        setDraft(next);
        setMessage(
          "Nacrt je pripremljen. Pregledajte tekst, izmenite ga i kopirajte.",
        );
        return;
      }
      const next = await api<Draft>(`/units/${unit}/ai/generate`, {
        method: "POST",
        body: JSON.stringify({
          company_id: company,
          contact_id: contact || null,
          opportunity_id: opportunity || null,
          goal,
          personalization,
          mode,
          tone,
          language,
          instructions,
          incoming_message: mode === "reply" ? incoming : "",
        }),
      });
      setDraft(next);
      setMessage(
        next.model === "local-templates"
          ? "Poruka iz šablona je pripremljena. Pregledajte je i kopirajte."
          : "Invekta AI je pripremio mejl. Pregledajte ga i kopirajte.",
      );
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function copy() {
    if (!draft) return;
    try {
      await navigator.clipboard.writeText(
        `Predmet: ${draft.subject}\n\n${draft.body}`,
      );
      setMessage("Mejl je kopiran. Nalepite ga u svoj email program.");
    } catch {
      bodyRef.current?.focus();
      bodyRef.current?.select();
      setError(
        "Browser nije dozvolio kopiranje. Označite tekst poruke i kopirajte ga ručno.",
      );
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Invekta AI</h1>
          <p>Vaš prodajni asistent za mejlove, odgovore klijentima i follow-up poruke.</p>
        </div>
        <Sparkles size={30} />
      </div>
      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {message && (
        <p className="success-message" role="status">
          {message}
        </p>
      )}
      {demo ? (
        <p className="demo-notice">
          Demo koristi lokalne šablone, bez Groq-a i tumačenja slobodnih uputstava.
          Poruka je dostupna samo na ovom ekranu dok ga ne zatvorite ili osvežite.
        </p>
      ) : (
        !checking &&
        !configured && (
          <p className="demo-notice">
            Invekta AI još nije povezan. Administrator treba da podesi Groq ključ na serveru.
          </p>
        )
      )}
      {!demo && !checking && engine === "templates" && <p className="demo-notice">
        Groq AI je isključen. Dostupni su lokalni šabloni koji ne tumače slobodna uputstva ni pitanja klijenta.
      </p>}
      {!demo && !checking && engine === "groq" && configured && <p className="demo-notice">
        GroqCloud · Besplatan paket ima ograničenja korišćenja. Klikom na pripremu šaljete uputstvo,
        odabrane podatke klijenta i znanje ovog brenda Groq servisu. Proverite nacrt pre slanja.
      </p>}
      {!demo && <AiKnowledge key={unit} unit={unit} brand={organization} canManage={canManageKnowledge} />}
      <div className="ai-grid">
        <section className="panel">
          <h2>Priprema poruke</h2>
          <form onSubmit={generate}>
            <fieldset className="ai-fields" disabled={busy || checking}>
              <div className="ai-compose-intro">
                <label>
                  Za šta treba da napišem mejl?
                  <textarea aria-label="Uputstvo za mejl" maxLength={4000} rows={5} value={instructions}
                    onChange={event => setInstructions(event.target.value)}
                    placeholder="Npr. Napiši kratak uvodni mejl direktoru hotela. Predstavi našu ponudu i predloži sastanak sledeće nedelje." />
                </label>
                <div className="ai-example-actions">
                  {[
                    ["Prvi kontakt", "Napiši kratak uvodni mejl klijentu. Predstavi našu ponudu na osnovu odobrenog znanja brenda i predloži razgovor."],
                    ["Podsetnik na ponudu", "Napiši ljubazan follow-up u vezi sa ponudom. Pitaj da li su potrebna pojašnjenja i predloži sledeći korak."],
                    ["Dogovor za sastanak", "Napiši profesionalan mejl kojim predlažemo kratak sastanak o potrebama klijenta i mogućoj saradnji."],
                  ].map(([label, text]) => <button type="button" className="secondary-button" key={label} onClick={() => setInstructions(text)}>{label}</button>)}
                </div>
              </div>
              <CompanyPicker unit={unit} value={company} options={companies} local={demo} disabled={busy || checking}
                label="Kompanija klijenta" ariaLabel="Kompanija za mejl" onChange={setCompany} />
              {contextError && (
                <p className="error-message" role="alert">
                  {contextError}
                </p>
              )}
              <details className="ai-options" open={mode === "reply" || undefined}>
                <summary>Kontakt, ton, jezik i dodatni podaci</summary>
                <div className="ai-fields">
                  <div className="form-grid">
                    <label>
                      Kontakt
                      <select
                        aria-label="Kontakt"
                        value={contact}
                        disabled={contextLoading}
                        onChange={(e) => setContact(Number(e.target.value))}
                      >
                        <option value={0}>Bez izabranog kontakta</option>
                        {contacts.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                            {c.email ? " · " + c.email : ""}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Prodajna prilika
                      <select
                        aria-label="Prodajna prilika"
                        value={opportunity}
                        disabled={contextLoading}
                        onChange={(e) => setOpportunity(Number(e.target.value))}
                      >
                        <option value={0}>Bez izabrane prilike</option>
                        {opportunities.map((o) => (
                          <option key={o.id} value={o.id}>
                            {o.title} · {stageLabel(o.stage)}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <div className="form-grid">
                    <label>
                      Vrsta poruke
                      <select
                        aria-label="Vrsta poruke"
                        value={mode}
                        onChange={(e) => setMode(e.target.value)}
                      >
                        {modes.map((m) => (
                          <option key={m.value} value={m.value}>
                            {m.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Ton
                      <select
                        aria-label="Ton"
                        value={tone}
                        onChange={(e) => setTone(e.target.value)}
                      >
                        <option value="professional">Profesionalan</option>
                        <option value="friendly">Prijateljski</option>
                        <option value="concise">Kratak i direktan</option>
                      </select>
                    </label>
                    <label>
                      Jezik
                      <select
                        aria-label="Jezik"
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                      >
                        <option value="sr">Srpski</option>
                        <option value="en">Engleski</option>
                      </select>
                    </label>
                  </div>
                  {mode === "reply" && (
                    <label>
                      Primljena poruka
                      <textarea
                        required
                        maxLength={10000}
                        rows={6}
                        value={incoming}
                        onChange={(e) => setIncoming(e.target.value)}
                        placeholder="Nalepite poruku na koju želite da odgovorite…"
                      />
                    </label>
                  )}
                  <label>
                    Cilj poruke
                    <select
                      aria-label="Cilj poruke"
                      value={goal}
                      onChange={(e) => setGoal(e.target.value)}
                    >
                      <option value="meeting">Zakazivanje sastanka</option>
                      <option value="introduction">
                        Prvi kontakt i predstavljanje
                      </option>
                      <option value="proposal">
                        Predstavljanje predloga saradnje
                      </option>
                      <option value="information">
                        Traženje dodatnih informacija
                      </option>
                    </select>
                  </label>
                  <div className="form-grid">
                    {(
                      [
                        ["topic", "Tema razgovora / predmet saradnje", 120],
                        ["offering", "Šta nudimo klijentu", 600],
                        ["need", "Potrebe klijenta / fokus razgovora", 600],
                        ["meeting_time", "Predlog termina (opciono)", 120],
                        ["greeting", "Oslovljavanje (opciono)", 150],
                        ["sender_name", "Vaše ime i prezime", 150],
                        ["sender_title", "Vaša pozicija", 150],
                        ["sender_phone", "Telefon za potpis", 80],
                        ["sender_email", "Email za potpis", 254],
                      ] as const
                    ).map(([key, label, limit]) => (
                      <label key={key}>
                        {label}
                        <input
                          maxLength={limit}
                          value={personalization[key]}
                          onChange={(e) =>
                            setPersonalization({
                              ...personalization,
                              [key]: e.target.value,
                            })
                          }
                        />
                      </label>
                    ))}
                  </div>
                  {mode === "reply" && (
                    <label>
                      Konkretan odgovor klijentu
                      <textarea
                        maxLength={4000}
                        rows={5}
                        value={personalization.reply_text}
                        onChange={(e) =>
                          setPersonalization({
                            ...personalization,
                            reply_text: e.target.value,
                          })
                        }
                        placeholder="Unesite informacije kojima odgovarate na pitanja klijenta."
                      />
                    </label>
                  )}
                </div>
              </details>
              <p className="panel-note">
                {demo || engine === "templates"
                  ? "Šablon koristi odabranu kompaniju i uneta polja; ne tumači uputstvo niti koristi znanje brenda."
                  : "Nacrt koristi odabrani kontekst i znanje izabranog brenda."} Ako podatak nedostaje,
                dopunite mesta označena sa [dopuniti]. Mejl šaljete sami nakon pregleda.
              </p>
              <button
                className="primary-button"
                disabled={
                  (!demo && !configured) ||
                  !company ||
                  contextLoading ||
                  !!contextError
                }
              >
                {busy ? "Pripremanje nacrta…" : demo || engine === "templates" ? "Pripremi nacrt iz šablona" : "Napiši mejl · Invekta AI"}
                <Sparkles size={16} />
              </button>
            </fieldset>
          </form>
        </section>
        <section className="panel">
          <h2>Vaš mejl</h2>
          {draft ? (
            <div>
              <fieldset className="ai-fields" disabled={busy}>
                <label>
                  Primalac
                  <input
                    type="email"
                    maxLength={254}
                    value={draft.recipient ?? ""}
                    onChange={(e) => {
                      setDraft({ ...draft, recipient: e.target.value });
                    }}
                  />
                </label>
                <label>
                  Predmet
                  <input
                    required
                    maxLength={200}
                    value={draft.subject}
                    onChange={(e) => {
                      setDraft({ ...draft, subject: e.target.value });
                    }}
                  />
                </label>
                <label>
                  Tekst poruke
                  <textarea
                    ref={bodyRef}
                    aria-label="Tekst poruke"
                    required
                    maxLength={20000}
                    rows={16}
                    value={draft.body}
                    onChange={(e) => {
                      setDraft({ ...draft, body: e.target.value });
                    }}
                  />
                </label>
                <div className="form-actions">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={copy}
                  >
                    <Copy size={16} />
                    Kopiraj mejl
                  </button>
                </div>
                <p className="panel-note">
                  Poruka se ne čuva. Kopirajte je pre napuštanja ili osvežavanja ekrana. Email nije poslat.
                </p>
              </fieldset>
            </div>
          ) : (
            <p className="empty">
              Opišite kakav mejl želite i izaberite kompaniju. Ovde će se pojaviti tekst za pregled i kopiranje.
            </p>
          )}
        </section>
      </div>
    </>
  );
}
