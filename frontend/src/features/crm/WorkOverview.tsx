import { useCrmQuery } from "../../lib/crmQuery";
import { errorText } from "../../lib/api";
import { metricQuery, formatTimestamp, type MetricFilters } from "./types";
import type { WorkSummary } from "./workTypes";
export default function WorkOverview({
  unit,
  filters,
  onNavigate,
  reports = false,
}: {
  unit: number;
  filters?: MetricFilters;
  onNavigate: (page: string) => void;
  reports?: boolean;
}) {
  const query = useCrmQuery<WorkSummary>(
      unit,
      `/work/summary${filters ? "?" + metricQuery(filters) : ""}`,
    ),
    data = query.data;
  return (
    <section className="panel work-overview">
      <div className="panel-heading">
        <h2>
          {reports ? "Izveštaj obaveza i aktivnosti" : "Današnje obaveze"}
        </h2>
        <button className="text-button" onClick={() => onNavigate("Zadaci")}>
          Otvori zadatke →
        </button>
      </div>
      {query.error && (
        <p className="error-message" role="alert">
          {errorText(query.error)}
        </p>
      )}
      {query.isPending ? (
        <p className="empty">Učitavanje dnevnih obaveza…</p>
      ) : (
        data && (
          <>
            <div className="work-counts">
              <span>
                Otvoreni zadaci:{" "}
                <strong>{data.tasks.open + data.tasks.doing}</strong>
              </span>
              <span>
                Završeni zadaci: <strong>{data.tasks.done}</strong>
              </span>
              <span>
                Danas dospeva: <strong>{data.due_today}</strong>
              </span>
              <span>
                Zakasneli zadaci: <strong>{data.overdue_tasks}</strong>
              </span>
              <span>
                Aktivnosti danas: <strong>{data.activities_today}</strong>
              </span>
              <span>
                Zakasnele aktivnosti: <strong>{data.overdue_activities}</strong>
              </span>
              <span>
                Izvršeni pozivi: <strong>{data.completed_calls}</strong>
              </span>
              <span>
                Izvršeni sastanci: <strong>{data.completed_meetings}</strong>
              </span>
              <span>
                Novi podsetnici: <strong>{data.unread_reminders}</strong>
              </span>
            </div>
            {reports ? (
              <>
                <p className="section-hint">
                  Period za zadatke prati rok; za završene aktivnosti vreme
                  izvršenja, za zakazane/otkazane vreme zakazivanja.
                  Komercijalista filter prati vlasnika kompanije; redovi
                  prikazuju odgovornu osobu. Podsetnici su lični i nezavisni od
                  perioda.
                </p>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Odgovorna osoba</th>
                        <th>Otvoreni</th>
                        <th>Završeni</th>
                        <th>Zakasneli</th>
                        <th>Zakazane aktivnosti</th>
                        <th>Pozivi</th>
                        <th>Sastanci</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.assignee_results.map((row) => (
                        <tr key={row.assignee_id}>
                          <td>{row.name}</td>
                          <td>{row.open_tasks}</td>
                          <td>{row.done_tasks}</td>
                          <td>{row.overdue_tasks}</td>
                          <td>{row.planned_activities}</td>
                          <td>{row.completed_calls}</td>
                          <td>{row.completed_meetings}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <>
                {[...data.due_tasks, ...data.scheduled_activities].map(
                  (row) => (
                    <div
                      className="history-row"
                      key={(row.kind ? "activity" : "task") + row.id}
                    >
                      <strong>{row.title}</strong>
                      <small>
                        {row.company_name} · {row.assignee_name} ·{" "}
                        {formatTimestamp(row.due_at || row.scheduled_at || "")}
                      </small>
                    </div>
                  ),
                )}
                {!data.due_tasks.length &&
                  !data.scheduled_activities.length && (
                    <p className="empty">
                      Nema današnjih ili zakasnelih obaveza.
                    </p>
                  )}
                <p className="section-hint">
                  Prvih pet zadataka i aktivnosti do kraja dana; kompletna lista
                  je u Zadacima. Prikaz uključuje samo podatke za koje imate
                  pristup.
                </p>
              </>
            )}
          </>
        )
      )}
    </section>
  );
}
