import { useEffect, useState } from "react";
import { CalendarDays, ArrowRight } from "lucide-react";
import type { OpportunityStage } from "../features/crm/types";
export function dailyRecommendations(
  stages: Partial<Record<OpportunityStage, number>>,
  companyCount: number,
) {
  const items: { label: string; page: string }[] = [];
  if (stages["Novi lead"])
    items.push({
      label: `Kontaktirajte nove leadove (${stages["Novi lead"]}).`,
      page: "Prodajni levak",
    });
  if (stages["Ponuda"])
    items.push({
      label: `Proverite odgovor klijenata na ponude (${stages["Ponuda"]}).`,
      page: "Prodajni levak",
    });
  if (stages["Pregovori"])
    items.push({
      label: `Dogovorite naredni korak za prilike u pregovorima (${stages["Pregovori"]}).`,
      page: "Prodajni levak",
    });
  if (stages["Kontaktiran"] || stages["Sastanak"])
    items.push({
      label: "Pripremite sledeći sastanak i poruku klijentu.",
      page: "AI asistent",
    });
  if (items.length < 3)
    items.push({
      label: companyCount
        ? "Proverite i dopunite podatke kontakt osoba."
        : "Dodajte prvu kompaniju i njene kontakte.",
      page: "Kompanije",
    });
  if (items.length < 3)
    items.push({
      label: "Pripremite profesionalnu poruku za sledeći kontakt.",
      page: "AI asistent",
    });
  return items.slice(0, 3);
}
export default function DailyWelcome({
  name,
  recommendations,
  onNavigate,
  loading = false,
}: {
  name: string;
  recommendations: { label: string; page: string }[];
  onNavigate: (page: string) => void;
  loading?: boolean;
}) {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 60000);
    return () => window.clearInterval(timer);
  }, []);
  const date = new Intl.DateTimeFormat("sr-Latn-RS", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Europe/Belgrade",
  }).format(now);
  return (
    <section
      className="daily-welcome"
      aria-label="Dobrodošlica i predlog za danas"
    >
      <div className="daily-welcome-heading">
        <div>
          <div className="daily-date">
            <CalendarDays size={17} />
            {date}
          </div>
          <h2>Dobro došli, {name}!</h2>
          <p>Predlog za danas, prema trenutnom stanju prodaje.</p>
        </div>
      </div>
      <div className="daily-actions">
        {loading ? (
          <p>Pripremam pregled…</p>
        ) : recommendations.length ? (
          recommendations.map((item) => (
            <button key={item.label} onClick={() => onNavigate(item.page)}>
              {item.label}
              <ArrowRight size={17} />
            </button>
          ))
        ) : (
          <p>Preporuke će biti dostupne kada se učitaju podaci.</p>
        )}
      </div>
      <small>
        Ovo su predloženi koraci, a ne zadaci sa dodeljenim rokovima.
      </small>
    </section>
  );
}
