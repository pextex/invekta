import type { CSSProperties, ReactNode } from "react";
import { ArrowRight, LockKeyhole, Building2 } from "lucide-react";
import {
  organizations,
  organizationName,
  type OrganizationCode,
} from "../organizations";
type Props = {
  selected: OrganizationCode | null;
  onSelect: (code: OrganizationCode) => void;
  busy?: boolean;
  error?: string;
  children: ReactNode;
};
export default function OrganizationPortal({
  selected,
  onSelect,
  busy = false,
  error,
  children,
}: Props) {
  return (
    <main className="organization-portal">
      <div className="portal-content">
        <div className="portal-brand">
          <span>LUU</span>
          <i>×</i>
          <span>Invekta</span>
          <i>×</i>
          <span className="cenobots-wordmark">Cenobots</span>
          <small>SALES CRM</small>
        </div>
        <div className="portal-heading">
          <span className="eyebrow">
            ZAJEDNIČKA PLATFORMA · ODVOJENI POSLOVNI PODACI
          </span>
          <h1>Izaberite kompaniju</h1>
          <p>Prijavite se u poslovni prostor u kojem želite da radite.</p>
        </div>
        <div className="organization-grid">
          {organizations.map((org) => (
            <button
              type="button"
              key={org.code}
              aria-label={"Izaberi " + org.name}
              aria-pressed={selected === org.code}
              data-organization={org.code}
              className={
                "organization-card" + (selected === org.code ? " selected" : "")
              }
              disabled={busy}
              onClick={() => onSelect(org.code)}
              style={{ "--org-accent": org.accent } as CSSProperties}
            >
              <span className="organization-mark"><img className="company-logo" src={org.logo} alt={org.name + " logo"} /></span>
              <span className="organization-copy">
                <strong>{org.name}</strong>
                <small>{org.domain}</small>
              </span>
              <ArrowRight size={19} />
              <span className="organization-description">
                Kompanije, kontakti i prodajne prilike.
              </span>
              <span className="organization-select-label">
                {selected === org.code
                  ? "Izabrana kompanija"
                  : "Izaberi poslovni prostor"}
              </span>
            </button>
          ))}
        </div>
        {error && (
          <p className="error-message portal-error" role="alert">
            {error}
          </p>
        )}
        {selected ? (
          <section className="portal-login panel">
            <div className="portal-login-heading">
              <LockKeyhole size={24} />
              <div>
                <h2>Prijava · {organizationName(selected)}</h2>
                <p>
                  Koristite svoj korisnički nalog. Pristup proverava server.
                </p>
              </div>
            </div>
            {children}
          </section>
        ) : (
          <div className="portal-selection-hint">
            <Building2 size={19} />
            Izaberite LUU, Invekta ili Cenobots da biste nastavili.
          </div>
        )}
        <p className="portal-footer">
          Razvojna verzija · koristite samo testne podatke.
        </p>
      </div>
    </main>
  );
}
