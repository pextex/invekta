import { useState } from "react";
import { errorText } from "../../lib/api";
import { useCrmQuery, useCrmRequest } from "../../lib/crmQuery";
import { formatTimestamp, type Company } from "./types";
import WorkEditor from "./WorkEditor";
import {
  kindLabel,
  statusLabel,
  type WorkEvent,
  type WorkKind,
  type WorkPage,
  type WorkRecord,
  type WorkSummary,
} from "./workTypes";

const fieldLabels: Record<string, string> = {
  company_id: "Kompanija",
  assignee_id: "Odgovorna osoba",
  opportunity_id: "Prilika",
  title: "Naziv",
  notes: "Beleške",
  status: "Status",
  priority: "Prioritet",
  due_at: "Rok",
  remind_at: "Podsetnik",
  completed_at: "Završeno",
  scheduled_at: "Zakazano",
  occurred_at: "Izvršeno",
  outcome: "Ishod",
  kind: "Vrsta",
  archived_at: "Arhivirano",
};
function historyValue(field: string, value: unknown) {
  if (value === null || value === undefined) return "—";
  const text = String(value);
  if (field.endsWith("_at")) return formatTimestamp(text);
  if (field === "status") return statusLabel[text] ?? text;
  if (field === "kind") return kindLabel[text] ?? text;
  if (field === "priority")
    return (
      (
        { low: "Nizak", normal: "Normalan", high: "Visok" } as Record<
          string,
          string
        >
      )[text] ?? text
    );
  return text;
}

export default function WorkBoard({
  unit,
  kind,
  companies,
  companyId,
}: {
  unit: number;
  kind: WorkKind;
  companies: Company[];
  companyId?: number;
}) {
  const [editor, setEditor] = useState<WorkRecord | "new" | null>(null),
    [status, setStatus] = useState(""),
    [offset, setOffset] = useState(0);
  const [filterCompany, setFilterCompany] = useState(companyId ?? 0),
    [assignee, setAssignee] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const people = useCrmQuery<WorkSummary>(unit, "/work/summary");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [selectedHistory, setSelectedHistory] = useState<WorkRecord | null>(null);
  const base = `/${kind}`,
    query = useCrmQuery<WorkPage>(
      unit,
      `${base}?limit=50&offset=${offset}&include_archived=${includeArchived}${filterCompany ? "&company_id=" + filterCompany : ""}${assignee ? "&assignee_id=" + assignee : ""}${status ? "&status=" + status : ""}`,
    );
  const history = useCrmQuery<WorkEvent[]>(
    unit,
    `${base}/${selectedHistory?.id ?? 0}/history`,
    !!selectedHistory,
  );
  const request = useCrmRequest(unit),
    task = kind === "tasks";
  async function archive(row: WorkRecord) {
    setBusy(true);
    setError("");
    try {
      await request(
        `${base}/${row.id}${row.archived_at ? "/restore" : ""}?version=${row.version}`,
        {
          method: row.archived_at ? "POST" : "DELETE",
        },
      );
      setOffset(0);
    } catch (error) {
      setError(errorText(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="section-heading">
        <div>
          <h2>
            {task ? "Zadaci komercijalista" : "Pozivi, sastanci i aktivnosti"}
          </h2>
          <p>Trajni zapisi sa odgovornom osobom i istorijom promena.</p>
        </div>
        <button
          className="primary-button"
          disabled={busy || !!editor || !companies.length}
          onClick={() => {
            setEditor("new");
            setError("");
          }}
        >
          {task ? "Novi zadatak" : "Nova aktivnost"}
        </button>
      </div>
      <div className="button-row">
        <label>
          <input
            type="checkbox"
            checked={includeArchived}
            onChange={(event) => {
              setIncludeArchived(event.target.checked);
              setOffset(0);
            }}
          />{" "}
          Prikaži i arhivirane
        </label>
        {!companyId && (
          <label>
            Kompanija u listi
            <select
              aria-label="Kompanija u listi"
              value={filterCompany}
              onChange={(event) => {
                setFilterCompany(Number(event.target.value));
                setOffset(0);
              }}
            >
              <option value={0}>Sve dostupne</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.name}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          Odgovorna osoba u listi
          <select
            aria-label="Odgovorna osoba u listi"
            value={assignee}
            onChange={(event) => {
              setAssignee(event.target.value);
              setOffset(0);
            }}
          >
            <option value="">Sve dostupne</option>
            {people.data?.assignee_results.map((person) => (
              <option key={person.assignee_id} value={person.assignee_id}>
                {person.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Filter statusa
          <select
            aria-label={task ? "Filter zadataka" : "Filter aktivnosti"}
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setOffset(0);
            }}
          >
            <option value="">Svi statusi</option>
            {(task
              ? ["open", "doing", "done", "cancelled"]
              : ["planned", "done", "cancelled"]
            ).map((value) => (
              <option key={value} value={value}>
                {statusLabel[value]}
              </option>
            ))}
          </select>
        </label>
        <button
          className="secondary-button"
          disabled={query.isFetching}
          onClick={() => query.refetch()}
        >
          Osveži obaveze
        </button>
      </div>
      {(error || query.error) && (
        <p className="error-message" role="alert">
          {error || errorText(query.error)}
        </p>
      )}
      {editor && (
        <WorkEditor
          key={editor === "new" ? "new" : editor.id}
          unit={unit}
          kind={kind}
          companies={companies}
          companyId={companyId}
          record={editor === "new" ? undefined : editor}
          onClose={() => {
            setEditor(null);
            setOffset(0);
          }}
        />
      )}
      <section className="panel">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>{task ? "Zadatak" : "Aktivnost"}</th>
                <th>Kompanija / prilika</th>
                <th>Odgovorna osoba</th>
                <th>Vreme</th>
                <th>Status</th>
                <th>Akcije</th>
              </tr>
            </thead>
            <tbody>
              {query.data?.items.map((row) => (
                <tr key={row.id} data-work-id={row.id}>
                  <td>
                    <strong>{row.title}</strong>
                    <small>
                      {row.kind
                        ? kindLabel[row.kind]
                        : (
                            {
                              high: "Visok prioritet",
                              normal: "Normalan prioritet",
                              low: "Nizak prioritet",
                            } as Record<string, string>
                          )[row.priority ?? "normal"]}
                    </small>
                    {row.outcome && <small>{row.outcome}</small>}
                  </td>
                  <td>
                    {row.company_name}
                    <small>
                      {row.opportunity_title || "Bez povezane prilike"}
                    </small>
                  </td>
                  <td>{row.assignee_name}</td>
                  <td>
                    {formatTimestamp(
                      (task
                        ? row.due_at
                        : row.status === "done"
                          ? row.occurred_at
                          : row.scheduled_at) || row.created_at,
                    )}
                    {row.remind_at && (
                      <small>Podsetnik: {formatTimestamp(row.remind_at)}</small>
                    )}
                  </td>
                  <td>
                    {row.archived_at ? "Arhiviran" : statusLabel[row.status]}
                  </td>
                  <td>
                    <div className="button-row">
                      <button
                        className="text-button"
                        disabled={busy || !!editor || !!row.archived_at}
                        onClick={() => {
                          setEditor(row);
                          setError("");
                        }}
                      >
                        Izmeni obavezu
                      </button>
                      <button
                        className="text-button"
                        disabled={busy}
                        onClick={() => setSelectedHistory(row)}
                      >
                        Istorija obaveze
                      </button>
                      <button
                        className="text-button"
                        disabled={busy || !!editor}
                        onClick={() => archive(row)}
                      >
                        {row.archived_at ? "Vrati iz arhive" : "Arhiviraj"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {query.isPending ? (
          <p className="empty">Učitavanje obaveza…</p>
        ) : (
          query.data?.total === 0 && (
            <p className="empty">Nema obaveza za odabrani prikaz.</p>
          )
        )}
        <div className="panel-actions">
          <span>{query.data?.total ?? 0} zapisa</span>
          <button
            className="secondary-button"
            disabled={busy || !offset}
            onClick={() => setOffset(Math.max(0, offset - 50))}
          >
            Prethodna
          </button>
          <button
            className="secondary-button"
            disabled={
              busy ||
              query.isFetching ||
              offset + 50 >= (query.data?.total ?? 0)
            }
            onClick={() => setOffset(offset + 50)}
          >
            Sledeća
          </button>
        </div>
      </section>
      {selectedHistory && (
        <section className="panel history-panel">
          <div className="panel-heading">
            <h2>Istorija obaveze · {selectedHistory.title}</h2>
            <button
              className="text-button"
              onClick={() => setSelectedHistory(null)}
            >
              Zatvori istoriju
            </button>
          </div>
          {history.error && (
            <p className="error-message" role="alert">
              {errorText(history.error)}
            </p>
          )}
          {history.data?.map((event) => (
            <div className="history-row" key={event.id}>
              <strong>
                {
                  (
                    {
                      created: "Kreiranje",
                      updated: "Izmena",
                      archived: "Arhiviranje",
                      restored: "Vraćanje iz arhive",
                    } as Record<string, string>
                  )[event.action]
                }{" "}
                · {event.actor_name}
              </strong>
              <small>{formatTimestamp(event.changed_at)}</small>
              <div>
                {Object.entries(event.display_changes ?? event.changes).map(
                  ([field, change]) => (
                    <small key={field}>
                      {fieldLabels[field] ?? field}:{" "}
                      {historyValue(field, change.from)} →{" "}
                      {historyValue(field, change.to)}
                    </small>
                  ),
                )}
              </div>
            </div>
          ))}
        </section>
      )}
    </>
  );
}
