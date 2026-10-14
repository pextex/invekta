import { useState } from "react";
import { errorText } from "../../lib/api";
import { useCrmQuery, useCrmRequest } from "../../lib/crmQuery";
import { formatTimestamp } from "./types";
import type { Reminder } from "./workTypes";
export default function ReminderInbox({
  unit,
  companyId,
}: {
  unit: number;
  companyId?: number;
}) {
  const [offset, setOffset] = useState(0),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const query = useCrmQuery<{ items: Reminder[]; total: number }>(
      unit,
      `/reminders?offset=${offset}&limit=50${companyId ? "&company_id=" + companyId : ""}`,
    ),
    request = useCrmRequest(unit);
  async function read(id: number) {
    setBusy(true);
    setError("");
    try {
      await request(`/reminders/${id}/read`, { method: "PATCH", body: "{}" });
    } catch (error) {
      setError(errorText(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Moji podsetnici</h2>
        <button
          className="secondary-button"
          disabled={query.isFetching}
          onClick={() => query.refetch()}
        >
          Osveži podsetnike
        </button>
      </div>
      <p className="section-hint">Samo vaši podsetnici u ovoj jedinici.</p>
      {(error || query.error) && (
        <p className="error-message" role="alert">
          {error || errorText(query.error)}
        </p>
      )}
      {query.data?.items.map((row) => (
        <div className="history-row" key={row.id}>
          <strong>{row.title}</strong>
          <small>
            {row.company_name} · {formatTimestamp(row.fire_at)} ·{" "}
            {row.status === "pending"
              ? "Na čekanju"
              : row.read_at
                ? "Pročitan"
                : "NOV PODSETNIK"}
          </small>
          {row.status === "delivered" && !row.read_at && (
            <button
              className="text-button"
              disabled={busy}
              onClick={() => read(row.id)}
            >
              Označi kao pročitan
            </button>
          )}
        </div>
      ))}
      {query.data?.total === 0 && (
        <p className="empty">Nema vaših podsetnika.</p>
      )}
      <div className="panel-actions">
        <button
          className="secondary-button"
          disabled={!offset}
          onClick={() => setOffset(Math.max(0, offset - 50))}
        >
          Prethodna
        </button>
        <button
          className="secondary-button"
          disabled={query.isFetching || offset + 50 >= (query.data?.total ?? 0)}
          onClick={() => setOffset(offset + 50)}
        >
          Sledeća
        </button>
      </div>
    </section>
  );
}
