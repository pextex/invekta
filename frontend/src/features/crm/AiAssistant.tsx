import { useEffect, useState, type FormEvent } from "react";
import { Sparkles, Copy, Save } from "lucide-react";
import { api, errorText } from "../../lib/api";
import type { Company, Contact, Opportunity, OpportunityPage } from "./types";

type Draft = {
  id: number;
  company_id: number;
  mode: string;
  subject: string;
  body: string;
  recipient: string | null;
  model: string;
  version: number;
  created_at: string;
  updated_at: string;
};
const modes = [
  { value: "email", label: "Novi email" },
  { value: "reply", label: "Odgovor na poruku" },
  { value: "follow_up", label: "Follow-up" },
];
export default function AiAssistant({
  unit,
  companies,
  demo = false,
}: {
  unit: number;
  companies: Company[];
  demo?: boolean;
}) {
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
  const [configured, setConfigured] = useState(false),
    [checking, setChecking] = useState(!demo),
    [contextLoading, setContextLoading] = useState(false),
    [contextError, setContextError] = useState("");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const [draft, setDraft] = useState<Draft | null>(null),
    [savedDraft, setSavedDraft] = useState<Draft | null>(null),
    [dirty, setDirty] = useState(false),
    [items, setItems] = useState<Draft[]>([]),
    [total, setTotal] = useState(0),
    [offset, setOffset] = useState(0),
    [reload, setReload] = useState(0),
    [listLoading, setListLoading] = useState(!demo);
  useEffect(() => {
    if (demo) return;
    const controller = new AbortController();
    setChecking(true);
    api<{ configured: boolean }>(`/units/${unit}/ai/status`, {
      signal: controller.signal,
    })
      .then((data) => setConfigured(data.configured))
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
      const next = await api<Draft>(`/units/${unit}/ai/drafts`, {
        method: "POST",
        body: JSON.stringify({
          company_id: company,
          contact_id: contact || null,
          opportunity_id: opportunity || null,
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
        "AI nacrt je pripremljen i sačuvan. Pregledajte ga pre upotrebe.",
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
      setError(
        "Browser nije dozvolio kopiranje. Označite i kopirajte tekst ručno.",
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
          <h1>AI asistent</h1>
          <p>Pripremite email, odgovor ili follow-up za izabranog klijenta.</p>
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
          Ovo je pregled AI asistenta. Generisanje i čuvanje nacrta rade u
          povezanom CRM-u uz podešen AI servis.
        </p>
      ) : (
        !checking &&
        !configured && (
          <p className="demo-notice">
            AI servis još nije povezan. Administrator treba da podesi AI ključ.
            Sačuvani nacrti ostaju dostupni za pregled i izmene.
          </p>
        )
      )}
      <div className="ai-grid">
        <section className="panel">
          <h2>Priprema poruke</h2>
          <form onSubmit={generate}>
            <fieldset className="ai-fields" disabled={busy || checking}>
              <label>
                Kompanija
                <select
                  aria-label="Kompanija"
                  required
                  value={company || ""}
                  onChange={(e) => setCompany(Number(e.target.value))}
                >
                  <option value="">Izaberite klijenta</option>
                  {companies.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </label>
              {contextError && (
                <p className="error-message" role="alert">
                  {contextError}
                </p>
              )}
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
                        {o.title} · {o.stage}
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
                Šta želite da poruka postigne?
                <textarea
                  required
                  minLength={3}
                  maxLength={4000}
                  rows={5}
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="Npr. predloži kratak sastanak sledeće nedelje i pitaj koje su potrebe klijenta."
                />
              </label>
              <p className="panel-note">
                AI dobija instrukcije i podatke izabrane kompanije, kontakta i
                prilike. Pregledajte činjenice i dopunite mesta označena sa
                [dopuniti].
              </p>
              <button
                className="primary-button"
                disabled={
                  demo ||
                  !configured ||
                  !company ||
                  contextLoading ||
                  !!contextError ||
                  dirty
                }
              >
                {busy ? "Pripremanje nacrta…" : "Pripremi AI nacrt"}
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
                  {dirty ? "Imate nesačuvane izmene." : "Nacrt je sačuvan."}{" "}
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
        {listLoading ? (
          <p>Učitavanje…</p>
        ) : items.length ? (
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
                {items.map((item) => (
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
          <p className="empty">Još nema sačuvanih nacrta.</p>
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
