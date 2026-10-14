import DailyWelcome, {
  dailyRecommendations,
} from "../../components/DailyWelcome";
import { RefreshCw } from "lucide-react";
import { errorText } from "../../lib/api";
import {
  formatAmount,
  opportunityStages,
  metricQuery,
  type Summary,
  type MetricFilters,
  type Unit,
} from "./types";
import { useCrmQuery } from "../../lib/crmQuery";
import MetricsFilters from "./MetricsFilters";
import WorkOverview from "./WorkOverview";
import Reports, { Results } from "./Reports";
export default function Dashboard({
  unit,
  onPipeline,
  userName,
  onNavigate,
  filters,
  onFilters,
  units,
  onUnit,
  reports = false,
}: {
  unit: number;
  filters: MetricFilters;
  onFilters: (filters: MetricFilters) => void;
  units: Unit[];
  onUnit: (unit: number) => void;
  reports?: boolean;
  onPipeline: () => void;
  userName: string;
  onNavigate: (page: string) => void;
}) {
  const query = useCrmQuery<Summary>(unit, `/summary?${metricQuery(filters)}`);
  const data = query.data,
    loading = query.isPending;
  const error = query.error ? errorText(query.error) : "";
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{reports ? "Izveštaji prodaje" : "Vaš prodajni pregled"}</h1>
          <p>Pokazatelji iz baze, ograničeni vašim pravima pristupa.</p>
        </div>
        <button
          className="secondary-button"
          disabled={query.isFetching}
          onClick={() => query.refetch()}
        >
          <RefreshCw size={15} />
          Osveži
        </button>
      </div>
      <MetricsFilters
        filters={filters}
        onChange={onFilters}
        units={units}
        unit={unit}
        onUnit={onUnit}
        owners={data?.owners ?? []}
      />
      {!reports && (
        <DailyWelcome
          name={userName}
          recommendations={
            data ? dailyRecommendations(data.stages, data.company_count) : []
          }
          onNavigate={onNavigate}
          loading={loading}
        />
      )}
      <WorkOverview
        unit={unit}
        filters={reports ? filters : undefined}
        onNavigate={onNavigate}
        reports={reports}
      />
      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {loading ? (
        <p className="empty">Učitavanje pokazatelja…</p>
      ) : (
        !error &&
        data && (
          <>
            <div className="metrics">
              {[
                {
                  label: "Kompanije u bazi",
                  value: String(data.company_count),
                  note: `${data.contact_count} kontakt osoba`,
                },
                {
                  label: "Otvorene prilike",
                  value: String(data.open_count),
                  note: "Bez dobijenih i izgubljenih poslova",
                },
                {
                  label: "Vrednost otvorenih prilika",
                  value: formatAmount(data.open_value),
                  note: "Potencijalna vrednost, nije prihod",
                },
                {
                  label: "Izgubljene prilike",
                  value: String(data.lost_count),
                  note: formatAmount(data.lost_value),
                },
                {
                  label: "Kontakt osobe",
                  value: String(data.contact_count),
                  note: "Ukupan dostupan broj",
                },
                {
                  label: "Dobijeni poslovi",
                  value: formatAmount(data.won_value),
                  note: `${data.won_count} dobijenih prilika · nije fakturisani prihod`,
                },
              ].map((item) => (
                <article className="metric" key={item.label}>
                  <div className="metric-label">{item.label}</div>
                  <strong>{item.value}</strong>
                  <small>● {item.note}</small>
                </article>
              ))}
            </div>
            {reports ? (
              <Reports data={data} />
            ) : (
              <section className="panel">
                <div className="panel-heading">
                  <h2>Prodajni levak</h2>
                  <span className="tag">{data.opportunity_count} prilika</span>
                </div>
                <div className="bars">
                  {opportunityStages.map((stage) => (
                    <div className="bar-row" key={stage}>
                      <div>
                        <span>{stage}</span>
                        <strong>{data.stages[stage]}</strong>
                      </div>
                      <div className="bar-track">
                        <div
                          style={{
                            width: `${data.opportunity_count ? (data.stages[stage] / data.opportunity_count) * 100 : 0}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="panel-actions">
                  <button className="secondary-button" onClick={onPipeline}>
                    Otvori prodajni levak →
                  </button>
                </div>
                <p className="panel-note">
                  Ovo su podaci iz razvojne baze. Demo zapisi ulaze u
                  pokazatelje i nisu stvarni poslovni rezultati. Svi agregati
                  koriste kompletnu dostupnu listu prilika, ne samo učitane
                  kartice.
                </p>
              </section>
            )}
            {!reports && (
              <Results
                title="Rezultati komercijalista"
                items={data.sales_results}
              />
            )}
          </>
        )
      )}
    </>
  );
}
