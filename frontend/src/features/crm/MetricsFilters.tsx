import type { MetricFilters, Summary, Unit } from "./types";
import { organizationName } from "../../organizations";
export default function MetricsFilters({
  filters,
  onChange,
  units,
  unit,
  onUnit,
  owners,
}: {
  filters: MetricFilters;
  onChange: (filters: MetricFilters) => void;
  units: Unit[];
  unit: number;
  onUnit: (unit: number) => void;
  owners: Summary["owners"];
}) {
  return (
    <section
      className="panel metrics-filters"
      aria-label="Filteri prodajnog pregleda"
    >
      <div className="form-grid">
        <label>
          Poslovna jedinica
          <select
            aria-label="Poslovna jedinica izveštaja"
            value={unit}
            onChange={(e) => onUnit(Number(e.target.value))}
          >
            {units.map((u) => (
              <option key={u.id} value={u.id}>
                {organizationName(u.code)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Prilike kreirane od
          <input
            type="date"
            aria-label="Prilike kreirane od"
            value={filters.start_date}
            max={filters.end_date || undefined}
            onChange={(e) =>
              onChange({ ...filters, start_date: e.target.value })
            }
          />
        </label>
        <label>
          Prilike kreirane do
          <input
            type="date"
            aria-label="Prilike kreirane do"
            value={filters.end_date}
            min={filters.start_date || undefined}
            onChange={(e) => onChange({ ...filters, end_date: e.target.value })}
          />
        </label>
        <label>
          Komercijalista
          <select
            aria-label="Komercijalista izveštaja"
            value={filters.owner_id}
            onChange={(e) => onChange({ ...filters, owner_id: e.target.value })}
          >
            <option value="">Svi dostupni</option>
            {owners.map((owner) => (
              <option key={owner.id} value={owner.id}>
                {owner.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="section-hint">
        Period bira prilike prema datumu kreiranja; iznosi i faze prikazuju
        njihovo sadašnje stanje. Kompanije i kontakti su ukupan dostupan broj,
        nezavisno od perioda.
      </p>
    </section>
  );
}
