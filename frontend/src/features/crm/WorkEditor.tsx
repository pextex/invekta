import { useState, type FormEvent } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { api, errorText } from "../../lib/api";
import { crmKey, useCrmQuery, useCrmRequest } from "../../lib/crmQuery";
import type { Company, OpportunityPage } from "./types";
import {
  kindLabel,
  statusLabel,
  toInstant,
  toLocalInput,
  type WorkKind,
  type WorkRecord,
} from "./workTypes";

export default function WorkEditor({
  unit,
  kind,
  companies,
  companyId,
  record,
  onClose,
}: {
  unit: number;
  kind: WorkKind;
  companies: Company[];
  companyId?: number;
  record?: WorkRecord;
  onClose: () => void;
}) {
  const task = kind === "tasks";
  const [fields, setFields] = useState({
    company_id: record?.company_id ?? companyId ?? companies[0]?.id ?? 0,
    assignee_id: record?.assignee_id ?? 0,
    opportunity_id: String(record?.opportunity_id ?? ""),
    title: record?.title ?? "",
    notes: record?.notes ?? "",
    status: record?.status ?? (task ? "open" : "planned"),
    priority: record?.priority ?? "normal",
    date:
      toLocalInput(task ? record?.due_at : record?.scheduled_at) ||
      toLocalInput(new Date(Date.now() + 3600_000).toISOString()),
    occurred: toLocalInput(record?.occurred_at),
    remind: toLocalInput(record?.remind_at),
    kind: record?.kind ?? "call",
    outcome: record?.outcome ?? "",
  });
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const request = useCrmRequest(unit);
  const people = useCrmQuery<{ id: number; name: string }[]>(
    unit,
    `/work/assignees?company_id=${fields.company_id}`,
    !!fields.company_id,
  );
  const assignee = fields.assignee_id || people.data?.[0]?.id || 0;
  const opportunities = useInfiniteQuery({
    queryKey: crmKey(
      unit,
      `/work-opportunity-choices?company_id=${fields.company_id}`,
    ),
    enabled: !!fields.company_id,
    initialPageParam: 0,
    queryFn: ({ pageParam, signal }) =>
      api<OpportunityPage>(
        `/units/${unit}/opportunities?company_id=${fields.company_id}&offset=${pageParam}&limit=200`,
        { signal },
      ),
    getNextPageParam: (last, pages) => {
      const loaded = pages.reduce(
        (count, page) => count + page.items.length,
        0,
      );
      return loaded < last.total ? loaded : undefined;
    },
  });
  const choices = opportunities.error
    ? []
    : (opportunities.data?.pages.flatMap((page) => page.items) ?? []);
  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const common = {
      company_id: fields.company_id,
      assignee_id: assignee,
      opportunity_id: fields.opportunity_id
        ? Number(fields.opportunity_id)
        : null,
      title: fields.title,
      notes: fields.notes || null,
      status: fields.status,
      remind_at: toInstant(fields.remind),
      ...(record ? { version: record.version } : {}),
    };
    const body = task
      ? { ...common, priority: fields.priority, due_at: toInstant(fields.date) }
      : {
          ...common,
          kind: fields.kind,
          scheduled_at: toInstant(fields.date),
          occurred_at:
            fields.status === "done" ? toInstant(fields.occurred) : null,
          outcome: fields.outcome || null,
        };
    try {
      await request(`/${kind}${record ? "/" + record.id : ""}`, {
        method: record ? "PATCH" : "POST",
        body: JSON.stringify(body),
      });
      onClose();
    } catch (error) {
      setError(errorText(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel company-form">
      <h2>
        {record ? "Izmena" : "Nova obaveza"} · {task ? "Zadatak" : "Aktivnost"}
      </h2>
      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {(people.error || opportunities.error) && (
        <p className="error-message" role="alert">
          {errorText(people.error || opportunities.error)}
        </p>
      )}
      <form onSubmit={save}>
        <div className="form-grid">
          <label>
            Kompanija obaveze
            <select
              required
              aria-label="Kompanija obaveze"
              value={fields.company_id}
              disabled={busy || !!record || !!companyId}
              onChange={(event) =>
                setFields({
                  ...fields,
                  company_id: Number(event.target.value),
                  assignee_id: 0,
                  opportunity_id: "",
                })
              }
            >
              <option value={0}>Izaberite kompaniju</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.name}
                </option>
              ))}
              {record &&
                !companies.some(
                  (company) => company.id === record.company_id,
                ) && (
                  <option value={record.company_id}>
                    {record.company_name}
                  </option>
                )}
            </select>
          </label>
          <label>
            Odgovorna osoba
            <select
              required
              aria-label="Odgovorna osoba"
              value={assignee || ""}
              disabled={busy || people.isPending}
              onChange={(event) =>
                setFields({
                  ...fields,
                  assignee_id: Number(event.target.value),
                })
              }
            >
              <option value="">Izaberite osobu</option>
              {people.data?.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Prodajna prilika
            <select
              aria-label="Prodajna prilika obaveze"
              value={fields.opportunity_id}
              disabled={busy}
              onChange={(event) =>
                setFields({ ...fields, opportunity_id: event.target.value })
              }
            >
              <option value="">Bez povezane prilike</option>
              {choices.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.title}
                </option>
              ))}
              {record?.opportunity_id &&
                !choices.some((row) => row.id === record.opportunity_id) && (
                  <option value={record.opportunity_id}>
                    {record.opportunity_title}
                  </option>
                )}
            </select>
            {opportunities.hasNextPage && (
              <button
                type="button"
                className="text-button"
                disabled={opportunities.isFetching}
                onClick={() => opportunities.fetchNextPage()}
              >
                Učitaj još prilika
              </button>
            )}
          </label>
          <label>
            Naziv obaveze
            <input
              required
              minLength={2}
              maxLength={200}
              value={fields.title}
              disabled={busy}
              onChange={(event) =>
                setFields({ ...fields, title: event.target.value })
              }
            />
          </label>
          <label>
            Status obaveze
            <select
              value={fields.status}
              disabled={busy}
              onChange={(event) =>
                setFields({ ...fields, status: event.target.value })
              }
            >
              {(task
                ? ["open", "doing", "done", "cancelled"]
                : ["planned", "done", "cancelled"]
              ).map((status) => (
                <option key={status} value={status}>
                  {statusLabel[status]}
                </option>
              ))}
            </select>
          </label>
          {task ? (
            <label>
              Prioritet
              <select
                value={fields.priority}
                disabled={busy}
                onChange={(event) =>
                  setFields({ ...fields, priority: event.target.value })
                }
              >
                <option value="low">Nizak</option>
                <option value="normal">Normalan</option>
                <option value="high">Visok</option>
              </select>
            </label>
          ) : (
            <label>
              Vrsta aktivnosti
              <select
                value={fields.kind}
                disabled={busy}
                onChange={(event) =>
                  setFields({
                    ...fields,
                    kind: event.target.value as "call" | "meeting" | "note",
                  })
                }
              >
                {Object.entries(kindLabel).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          )}
          <label>
            {task ? "Rok zadatka" : "Zakazano vreme"}
            <input
              aria-label={task ? "Rok zadatka" : "Zakazano vreme"}
              type="datetime-local"
              required={task || fields.status === "planned"}
              value={fields.date}
              disabled={busy}
              onChange={(event) =>
                setFields({ ...fields, date: event.target.value })
              }
            />
          </label>
          <label>
            Vreme podsetnika
            <input
              type="datetime-local"
              value={fields.remind}
              max={fields.date || undefined}
              disabled={busy}
              onChange={(event) =>
                setFields({ ...fields, remind: event.target.value })
              }
            />
          </label>
          {!task && fields.status === "done" && (
            <label>
              Vreme izvršenja
              <input
                type="datetime-local"
                value={fields.occurred}
                disabled={busy}
                onChange={(event) =>
                  setFields({ ...fields, occurred: event.target.value })
                }
              />
            </label>
          )}
          <label>
            Beleške obaveze
            <textarea
              maxLength={4000}
              value={fields.notes}
              disabled={busy}
              onChange={(event) =>
                setFields({ ...fields, notes: event.target.value })
              }
            />
          </label>
          {!task && (
            <label>
              Ishod aktivnosti
              <textarea
                maxLength={4000}
                value={fields.outcome}
                disabled={busy}
                onChange={(event) =>
                  setFields({ ...fields, outcome: event.target.value })
                }
              />
            </label>
          )}
        </div>
        <p className="section-hint">
          Unos vremena koristi zonu preglednika (
          {Intl.DateTimeFormat().resolvedOptions().timeZone}); prikaz je
          Europe/Belgrade. Podsetnici su obaveštenja u aplikaciji. Prazno vreme
          izvršenja završene aktivnosti znači sada.
        </p>
        <div className="form-actions">
          <button
            className="primary-button"
            disabled={
              busy || !assignee || !!people.error || !!opportunities.error
            }
          >
            {busy ? "Čuvanje…" : "Sačuvaj obavezu"}
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={busy}
            onClick={onClose}
          >
            Otkaži obavezu
          </button>
        </div>
      </form>
    </section>
  );
}
