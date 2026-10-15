import AiKnowledge from "./AiKnowledge";
import CompanyPicker from "./CompanyPicker";
import "./aiAssistant.css";
import { stageLabel } from "./types";
import {
  loadAssistant,
  saveAssistant,
  type AssistantState,
  type MessageDraft,
} from "../../lib/assistantStorage";
import {
  prepareLocalMessage,
  blankPersonalization,
} from "../../lib/messageTemplates";
import { useEffect, useState, useRef, type FormEvent } from "react";
import { Sparkles, Copy, Save } from "lucide-react";
import { api, errorText } from "../../lib/api";
import type { Company, Contact, Opportunity, OpportunityPage } from "./types";

type Draft = MessageDraft;
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
  const [initial] = useState(() =>
    demo
      ? loadAssistant(
          organization,
          companies.map((c) => c.id),
        )
      : null,
  );
  const [localSaveFailed, setLocalSaveFailed] = useState(false);
  const [draftSearch, setDraftSearch] = useState("");
  const bodyRef = useRef<HTMLTextAreaElement>(null);
  const [company, setCompany] = useState(initial?.compose.company ?? 0),
    [contact, setContact] = useState(0),
    [opportunity, setOpportunity] = useState(0);
  const [contacts, setContacts] = useState<Contact[]>([]),
    [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [mode, setMode] = useState(initial?.compose.mode ?? "email"),
    [tone, setTone] = useState(initial?.compose.tone ?? "professional"),
    [language, setLanguage] = useState(initial?.compose.language ?? "sr"),
    [instructions, setInstructions] = useState(
      initial?.compose.instructions ?? "",
    ),
    [incoming, setIncoming] = useState(initial?.compose.incoming ?? "");
  const [personalization, setPersonalization] = useState(
    initial?.compose.personalization ?? blankPersonalization(),
  );
  const [goal, setGoal] = useState(initial?.compose.goal ?? "meeting");
  const [engine, setEngine] = useState<"groq" | "templates">("templates");
  const [canManageKnowledge, setCanManageKnowledge] = useState(false);
  const [configured, setConfigured] = useState(false),
    [checking, setChecking] = useState(!demo),
    [contextLoading, setContextLoading] = useState(false),
    [contextError, setContextError] = useState("");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const [draft, setDraft] = useState<Draft | null>(initial?.draft ?? null),
    [savedDraft, setSavedDraft] = useState<Draft | null>(
      initial?.savedDraft ?? null,
    ),
    [dirty, setDirty] = useState(initial?.dirty ?? false),
    [items, setItems] = useState<Draft[]>(initial?.items ?? []),
    [total, setTotal] = useState(initial?.items.length ?? 0),
    [offset, setOffset] = useState(0),
    [reload, setReload] = useState(0),
    [listLoading, setListLoading] = useState(!demo);
  const snapshot: AssistantState = {
    compose: {
      company,
      mode,
      tone,
      language,
      instructions,
      incoming,
      goal,
      personalization,
    },
    draft,
    savedDraft,
    dirty,
    items,
  };
  const snapshotRef = useRef(snapshot);
  snapshotRef.current = snapshot;
  useEffect(() => {
    if (!demo) return;
    const timer = window.setTimeout(
      () =>
        setLocalSaveFailed(!saveAssistant(organization, snapshotRef.current)),
      300,
    );
    return () => window.clearTimeout(timer);
  }, [
    demo,
    organization,
    company,
    mode,
    tone,
    language,
    instructions,
    incoming,
    goal,
    personalization,
    draft,
    savedDraft,
    dirty,
    items,
  ]);
  useEffect(() => {
    if (!demo) return;
    const persist = () => {
      saveAssistant(organization, snapshotRef.current);
    };
    window.addEventListener("beforeunload", persist);
    return () => {
      window.removeEventListener("beforeunload", persist);
      persist();
    };
  }, [demo, organization]);
  const visibleItems = items.filter((item) =>
    (
      item.subject +
      " " +
      item.body +
      " " +
      (companies.find((c) => c.id === item.company_id)?.name ?? "")
    )
      .toLocaleLowerCase("sr-RS")
      .includes(draftSearch.toLocaleLowerCase("sr-RS")),
  );
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
  }, [unit, demo, reload]);
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
  useEffect(() => {
    if (demo) return;
    const controller = new AbortController();
    setListLoading(true);
    api<{ items: Draft[]; total: number }>(
      `/units/${unit}/ai/drafts?offset=${offset}&limit=20`,
      { signal: controller.signal },
    )
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(errorText(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setListLoading(false);
      });
    return () => controller.abort();
  }, [unit, offset, reload, demo]);
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
        const now = new Date().toISOString();
        const next: Draft = {
          ...text,
          id: Date.now(),
          company_id: company,
          mode,
          recipient: null,
          model: "local-templates-demo",
          version: 1,
          created_at: now,
          updated_at: now,
        };
        setDraft(next);
        setSavedDraft(next);
        setDirty(false);
        setItems((previous) => [next, ...previous].slice(0, 30));
        setTotal((previous) => Math.min(30, previous + 1));
        setMessage(
          "Nacrt je pripremljen. Pregledajte tekst, izmenite ga i kopirajte.",
        );
        return;
      }
      const next = await api<Draft>(`/units/${unit}/ai/drafts`, {
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
      setSavedDraft(next);
      setDirty(false);
      setOffset(0);
      setReload((v) => v + 1);
      setMessage(
        next.model === "local-templates"
          ? "Nacrt iz šablona je sačuvan. Pregledajte ga pre upotrebe."
          : "Invekta AI je pripremio i sačuvao nacrt. Pregledajte ga pre upotrebe.",
      );
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function save(e: FormEvent) {
    e.preventDefault();
    if (!draft) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (demo) {
        const next = {
          ...draft,
          version: draft.version + 1,
          updated_at: new Date().toISOString(),
        };
        setDraft(next);
        setSavedDraft(next);
        setItems((previous) =>
          previous.map((item) => (item.id === next.id ? next : item)),
        );
        setDirty(false);
        setMessage("Izmene su sačuvane za ovaj browser.");
        return;
      }
      const next = await api<Draft>(`/units/${unit}/ai/drafts/${draft.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          subject: draft.subject,
          body: draft.body,
          recipient: draft.recipient || null,
          version: draft.version,
        }),
      });
      setDraft(next);
      setSavedDraft(next);
      setDirty(false);
      setReload((v) => v + 1);
      setMessage("Izmene nacrta su sačuvane.");
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
      setMessage("Nacrt je kopiran. Nalepite ga u svoj email program.");
    } catch {
      bodyRef.current?.focus();
      bodyRef.current?.select();
      setError(
        "Browser nije dozvolio kopiranje. Označite tekst poruke i kopirajte ga ručno.",
      );
    }
  }
  function open(item: Draft) {
    if (dirty) {
      setError("Sačuvajte ili odbacite izmene pre otvaranja drugog nacrta.");
      return;
    }
    setDraft(item);
    setSavedDraft(item);
    setDirty(false);
    setMessage("");
    setError("");
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
          Demo koristi lokalne šablone, bez Groq-a i tumačenja slobodnih uputstava. Nacrti i potpis pamte se u ovom
          browseru zasebno za svaku firmu (poslednjih 30 nacrta). Nisu u CRM
          bazi.
        </p>
      ) : (
        !checking &&
        !configured && (
          <p className="demo-notice">
            Invekta AI još nije povezan. Administrator treba da podesi Groq ključ na serveru.
            Sačuvani nacrti ostaju dostupni za pregled i izmene.
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
      {demo && localSaveFailed && (
        <p className="error-message" role="alert">
          Browser ne dozvoljava lokalno čuvanje ili nema dovoljno prostora.
          Kopirajte tekst pre zatvaranja.
        </p>
      )}
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
                  !!contextError ||
                  dirty
                }
              >
                {busy ? "Pripremanje nacrta…" : demo || engine === "templates" ? "Pripremi nacrt iz šablona" : "Napiši mejl · Invekta AI"}
                <Sparkles size={16} />
              </button>
              {dirty && (
                <p className="panel-note">
                  Sačuvajte ili odbacite izmene trenutnog nacrta pre novog
                  generisanja.
                </p>
              )}
            </fieldset>
          </form>
        </section>
        <section className="panel">
          <h2>Nacrt poruke</h2>
          {draft ? (
            <form onSubmit={save}>
              <fieldset className="ai-fields" disabled={busy}>
                <label>
                  Primalac
                  <input
                    type="email"
                    maxLength={254}
                    value={draft.recipient ?? ""}
                    onChange={(e) => {
                      setDraft({ ...draft, recipient: e.target.value });
                      setDirty(true);
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
                      setDirty(true);
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
                      setDirty(true);
                    }}
                  />
                </label>
                <div className="form-actions">
                  <button className="primary-button" disabled={!dirty}>
                    <Save size={16} />
                    Sačuvaj izmene
                  </button>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={copy}
                  >
                    <Copy size={16} />
                    Kopiraj nacrt
                  </button>
                  {dirty && (
                    <button
                      type="button"
                      className="text-button"
                      onClick={() => {
                        if (savedDraft) {
                          setDraft(savedDraft);
                          setDirty(false);
                          setError("");
                        }
                      }}
                    >
                      Odbaci izmene
                    </button>
                  )}
                </div>
                <p className="panel-note">
                  {dirty
                    ? "Imate nesačuvane izmene."
                    : demo
                      ? "Nacrt se pamti u ovom browseru."
                      : "Nacrt je sačuvan."}{" "}
                  Email nije poslat.
                </p>
              </fieldset>
            </form>
          ) : (
            <p className="empty">
              Pripremite novi nacrt ili otvorite ranije sačuvanu poruku.
            </p>
          )}
        </section>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <h2>Moji sačuvani nacrti ({total})</h2>
          <button
            className="secondary-button"
            disabled={busy || listLoading || demo}
            onClick={() => setReload((v) => v + 1)}
          >
            Osveži
          </button>
        </div>
        <label className="search">
          Pretraži prikazane nacrte
          <input
            aria-label="Pretraži sačuvane nacrte"
            value={draftSearch}
            onChange={(e) => setDraftSearch(e.target.value)}
            placeholder="Predmet, kompanija ili tekst poruke"
          />
        </label>
        {listLoading ? (
          <p>Učitavanje…</p>
        ) : visibleItems.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Predmet</th>
                  <th>Kompanija</th>
                  <th>Vrsta</th>
                  <th>Sačuvano</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {visibleItems.map((item) => (
                  <tr key={item.id}>
                    <td>{item.subject}</td>
                    <td>
                      {companies.find((c) => c.id === item.company_id)?.name ??
                        "Kompanija #" + item.company_id}
                    </td>
                    <td>{modes.find((m) => m.value === item.mode)?.label}</td>
                    <td>{new Date(item.updated_at).toLocaleString("sr-RS")}</td>
                    <td>
                      <button
                        className="text-button"
                        disabled={busy}
                        onClick={() => open(item)}
                      >
                        Otvori
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="empty">
            {draftSearch
              ? "Nema nacrta za ovu pretragu."
              : "Još nema sačuvanih nacrta."}
          </p>
        )}
        <div className="panel-actions">
          <button
            className="secondary-button"
            disabled={demo || busy || listLoading || offset === 0}
            onClick={() => setOffset((v) => Math.max(0, v - 20))}
          >
            Prethodna
          </button>
          <button
            className="secondary-button"
            disabled={demo || busy || listLoading || offset + 20 >= total}
            onClick={() => setOffset((v) => v + 20)}
          >
            Sledeća
          </button>
        </div>
      </section>
    </>
  );
}
