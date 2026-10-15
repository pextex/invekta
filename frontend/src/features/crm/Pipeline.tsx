import CompanyPicker from "./CompanyPicker";
import { businessTypeLabel, businessTypesFor, type BusinessType } from "./businessTypes";
import { stageLabel } from "./types";
import { useStageDragDrop } from "./useStageDragDrop";
import { useEffect, useState, type FormEvent } from "react";
import { Plus, Save, History, RefreshCw, GripVertical } from "lucide-react";
import { api, errorText } from "../../lib/api";
import {
  opportunityStages,
  formatAmount,
  formatDate,
  formatTimestamp,
  type Company,
  type Opportunity,
  type OpportunityPage,
  type OpportunityStage,
  type StageChange,
} from "./types";
type Fields = {
  business_type: BusinessType | "";
  company_id: number;
  title: string;
  amount: string;
  stage: OpportunityStage;
  expected_close_date: string;
  notes: string;
};
export default function Pipeline({
  unit,
  companies,
  companyId,
  organization = "LUU",
}: {
  unit: number;
  companies: Company[];
  companyId?: number;
  organization?: string;
}) {
  const [items, setItems] = useState<Opportunity[]>([]),
    [total, setTotal] = useState(0),
    [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false);
  const [form, setForm] = useState<Fields | null>(null),
    [editing, setEditing] = useState<Opportunity | null>(null),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const [offset, setOffset] = useState(0),
    [reload, setReload] = useState(0),
    [history, setHistory] = useState<{
      title: string;
      rows: StageChange[];
    } | null>(null);
  const base = `/units/${unit}/opportunities`;
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    if (offset === 0) setItems([]);
    const query = new URLSearchParams({ limit: "100", offset: String(offset) });
    if (companyId) query.set("company_id", String(companyId));
    api<OpportunityPage>(base + "?" + query, { signal: controller.signal })
      .then((data) => {
        setItems((old) => (offset ? [...old, ...data.items] : data.items));
        setTotal(data.total);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(errorText(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [base, companyId, offset, reload]);
  function refresh() {
    setOffset(0);
    setReload((v) => v + 1);
    setHistory(null);
  }
  async function save(e: FormEvent) {
    e.preventDefault();
    if (!form || form.company_id < 1) return;
    setBusy(true);
    setError("");
    const { company_id, ...fields } = form;
    const body = {
      ...fields,
      business_type: fields.business_type || null,
      expected_close_date: form.expected_close_date || null,
      notes: form.notes || null,
      ...(editing ? { version: editing.version } : { company_id }),
    };
    try {
      await api(base + (editing ? "/" + editing.id : ""), {
        method: editing ? "PATCH" : "POST",
        body: JSON.stringify(body),
      });
      setForm(null);
      setMessage("Prodajna prilika je sačuvana.");
      refresh();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function changeStage(item: Opportunity, stage: OpportunityStage) {
    if (busy || loading || form || item.stage === stage) return;
    setBusy(true);
    setError("");
    try {
      const updated = await api<Opportunity>(base + "/" + item.id + "/stage", {
        method: "PATCH",
        body: JSON.stringify({ stage, version: item.version }),
      });
      setItems((old) =>
        old.map((row) => (row.id === updated.id ? updated : row)),
      );
      setMessage("Faza je sačuvana u bazi.");
      setHistory(null);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function showHistory(item: Opportunity) {
    setBusy(true);
    setError("");
    try {
      setHistory({
        title: item.title,
        rows: await api<StageChange[]>(base + "/" + item.id + "/stage-history"),
      });
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  function edit(item: Opportunity) {
    setEditing(item);
    setForm({
      business_type: item.business_type ?? (businessTypesFor(organization).length === 1 ? businessTypesFor(organization)[0] : ""),
      company_id: item.company_id,
      title: item.title,
      amount: item.amount,
      stage: item.stage,
      expected_close_date: item.expected_close_date ?? "",
      notes: item.notes ?? "",
    });
    setMessage("");
  }
  const drag = useStageDragDrop(items, busy || loading || !!form, changeStage);
  return (
    <>
      <div className="section-heading">
        <div>
          <h2>{companyId ? "Prilike kompanije" : "Prodajni levak"}</h2>
          <p>
            Svaka prilika ima svoju vrednost i fazu. Promene se trajno čuvaju.
          </p>
        </div>
        <div className="button-row">
          <button
            className="secondary-button"
            disabled={busy || loading}
            onClick={refresh}
          >
            <RefreshCw size={15} />
            Osveži
          </button>
          <button
            className="primary-button"
            disabled={busy || !companies.length}
            onClick={() => {
              setEditing(null);
              setForm({
                business_type: businessTypesFor(organization)[0],
                company_id: companyId ?? companies[0].id,
                title: "",
                amount: "0",
                stage: "Novi lead",
                expected_close_date: "",
                notes: "",
              });
              setMessage("");
            }}
          >
            <Plus size={16} />
            Nova prilika
          </button>
        </div>
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
      {form && (
        <section className="panel company-form">
          <h2>{editing ? "Izmena prilike" : "Nova prodajna prilika"}</h2>
          <form onSubmit={save}>
            <div className="form-grid">
              <CompanyPicker unit={unit} value={form.company_id} options={companies} selectedName={editing?.company_name}
                disabled={busy || !!editing || !!companyId} onChange={company_id => setForm({ ...form, company_id })} />
              <label>
                Naziv prilike
                <input
                  required
                  minLength={2}
                  maxLength={200}
                  disabled={busy}
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                />
              </label>
              <label>Vrsta posla<select required disabled={busy} value={form.business_type}
                onChange={e => setForm({ ...form, business_type: e.target.value as BusinessType })}>
                <option value="" disabled>Izaberite vrstu posla</option>
                {businessTypesFor(organization).map(type => <option value={type} key={type}>{businessTypeLabel(type)}</option>)}
              </select></label>
              <label>
                Vrednost (RSD)
                <input
                  type="number"
                  min="0"
                  max="999999999999.99"
                  step="0.01"
                  required
                  disabled={busy}
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: e.target.value })}
                />
              </label>
              <label>
                Faza
                <select
                  aria-label="Faza nove prilike"
                  value={form.stage}
                  disabled={busy}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      stage: e.target.value as OpportunityStage,
                    })
                  }
                >
                  {opportunityStages.map((s) => (
                    <option key={s} value={s}>{stageLabel(s)}</option>
                  ))}
                </select>
              </label>
              <label>
                Očekivani datum zatvaranja
                <input
                  type="date"
                  disabled={busy}
                  value={form.expected_close_date}
                  onChange={(e) =>
                    setForm({ ...form, expected_close_date: e.target.value })
                  }
                />
              </label>
              <label>
                Beleška
                <textarea
                  maxLength={2000}
                  disabled={busy}
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                />
              </label>
            </div>
            <p className="section-hint">
              Odgovorna osoba je komercijalista zadužen za kompaniju.
            </p>
            <div className="form-actions">
              <button className="primary-button" disabled={busy || form.company_id < 1}>
                <Save size={16} />
                {busy ? "Čuvanje…" : "Sačuvaj priliku"}
              </button>
              <button
                type="button"
                className="secondary-button"
                disabled={busy}
                onClick={() => setForm(null)}
              >
                Otkaži
              </button>
            </div>
          </form>
        </section>
      )}
      {history && (
        <section className="panel history-panel">
          <div className="panel-heading">
            <h2>Istorija faza · {history.title}</h2>
            <button className="text-button" onClick={() => setHistory(null)}>
              Zatvori
            </button>
          </div>
          {history.rows.length ? (
            history.rows.map((row) => (
              <div className="history-row" key={row.id}>
                <strong>
                  {row.from_stage ? stageLabel(row.from_stage) : "Kreiranje"} → {stageLabel(row.to_stage)}
                </strong>
                <small>
                  {row.actor_name} · {formatTimestamp(row.changed_at)}
                </small>
              </div>
            ))
          ) : (
            <p className="section-hint">
              Nema evidentiranih promena. Početne procene iz stare verzije
              prenete su bez izmišljanja istorije.
            </p>
          )}
        </section>
      )}
      <p className="section-hint">
        Prevucite karticu u drugu kolonu ili promenite fazu izborom na kartici.
        Na telefonu koristite izbor faze. Nova kolona se potvrđuje tek kada baza
        sačuva promenu.
      </p>
      <div className="pipeline-status">
        <span>
          {loading
            ? "Učitavanje…"
            : `Prikazano ${items.length} od ${total} prilika`}
        </span>
        <small>Brojevi u kolonama odnose se na učitane kartice.</small>
      </div>
      <div
        className="kanban live-kanban"
        aria-label="Prodajne prilike po fazama"
      >
        {opportunityStages.map((stage) => (
          <section
            {...drag.columnProps(stage)}
            data-stage={stage}
            className={
              "kanban-column" + (drag.over === stage ? " drop-target" : "")
            }
            key={stage}
          >
            <h2>
              {stageLabel(stage)}
              <span>{items.filter((item) => item.stage === stage).length}</span>
            </h2>
            {items
              .filter((item) => item.stage === stage)
              .map((item) => (
                <article
                  {...drag.cardProps(item)}
                  className={
                    "deal opportunity-card draggable-deal" +
                    (drag.dragged === item.id ? " dragging" : "")
                  }
                  key={item.id}
                  data-opportunity-id={item.id}
                >
                  <h3>
                    <GripVertical
                      size={14}
                      className="drag-grip"
                      aria-hidden="true"
                    />
                    {item.title}
                  </h3>
                  <small>{businessTypeLabel(item.business_type)}</small>
                  <small>
                    {item.company_name}
                    {item.is_demo ? " · DEMO" : ""}
                  </small>
                  <strong>{formatAmount(item.amount)}</strong>
                  <small>
                    {item.owner_name}
                    {item.expected_close_date
                      ? " · " + formatDate(item.expected_close_date)
                      : ""}
                  </small>
                  <label className="stage-control">
                    Faza
                    <select
                      aria-label={"Faza prilike " + item.title}
                      disabled={busy || loading || !!form}
                      value={item.stage}
                      onChange={(e) =>
                        changeStage(item, e.target.value as OpportunityStage)
                      }
                    >
                      {opportunityStages.map((s) => (
                        <option key={s} value={s}>{stageLabel(s)}</option>
                      ))}
                    </select>
                  </label>
                  {item.notes && <p className="deal-note">{item.notes}</p>}
                  <div className="button-row">
                    <button
                      className="text-button"
                      disabled={busy}
                      onClick={() => edit(item)}
                    >
                      Izmeni
                    </button>
                    <button
                      className="text-button"
                      disabled={busy}
                      onClick={() => showHistory(item)}
                    >
                      <History size={13} />
                      Istorija
                    </button>
                  </div>
                </article>
              ))}
          </section>
        ))}
      </div>
      {!loading && !items.length && !error && (
        <p className="empty">
          Još nema prodajnih prilika. Dodajte prvu priliku za kompaniju.
        </p>
      )}
      {items.length < total && (
        <div className="load-more">
          <button
            className="secondary-button"
            disabled={loading || busy}
            onClick={() => setOffset(items.length)}
          >
            Učitaj još prilika
          </button>
        </div>
      )}
    </>
  );
}
