import DailyWelcome, {
  dailyRecommendations,
} from "../../components/DailyWelcome";
import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { api, errorText } from "../../lib/api";
import { formatAmount, opportunityStages, type Summary } from "./types";
export default function Dashboard({
  unit,
  onPipeline,
  userName,
  onNavigate,
}: {
  unit: number;
  onPipeline: () => void;
  userName: string;
  onNavigate: (page: string) => void;
}) {
  const [data, setData] = useState<Summary | null>(null),
    [error, setError] = useState(""),
    [reload, setReload] = useState(0),
    [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setData(null);
    api<Summary>(`/units/${unit}/summary`, { signal: controller.signal })
      .then(setData)
      .catch((e) => {
        if (!controller.signal.aborted) setError(errorText(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [unit, reload]);
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Vaš prodajni pregled</h1>
          <p>Pokazatelji iz baze, ograničeni vašim pravima pristupa.</p>
        </div>
        <button
          className="secondary-button"
          disabled={loading}
          onClick={() => setReload((v) => v + 1)}
        >
          <RefreshCw size={15} />
          Osveži
        </button>
      </div>
      <DailyWelcome
        name={userName}
        recommendations={
          data ? dailyRecommendations(data.stages, data.company_count) : []
        }
        onNavigate={onNavigate}
        loading={loading}
      />
      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {loading ? (
        <p className="empty">Učitavanje pokazatelja…</p>
      ) : (
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
                  label: "Dobijeni poslovi",
                  value: formatAmount(data.won_value),
                  note: `${data.won_count} dobijenih prilika`,
                },
              ].map((item) => (
                <article className="metric" key={item.label}>
                  <div className="metric-label">{item.label}</div>
                  <strong>{item.value}</strong>
                  <small>● {item.note}</small>
                </article>
              ))}
            </div>
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
                Ovo su podaci iz razvojne baze. Demo zapisi ulaze u pokazatelje
                i nisu stvarni poslovni rezultati.
              </p>
            </section>
          </>
        )
      )}
    </>
  );
}
