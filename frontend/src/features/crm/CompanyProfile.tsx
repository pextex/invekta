import { useEffect, useState } from "react";
import { ArrowLeft, Building2 } from "lucide-react";
import { api, errorText } from "../../lib/api";
import Contacts from "./Contacts";
import Pipeline from "./Pipeline";
import { formatDate, type Company } from "./types";
export default function CompanyProfile({
  unit,
  id,
  onBack,
  organization,
}: {
  organization?: string;
  unit: number;
  id: number;
  onBack: () => void;
}) {
  const [company, setCompany] = useState<Company | null>(null),
    [error, setError] = useState(""),
    [tab, setTab] = useState("contacts");
  useEffect(() => {
    const controller = new AbortController();
    setCompany(null);
    setError("");
    api<Company>(`/units/${unit}/companies/${id}`, {
      signal: controller.signal,
    })
      .then(setCompany)
      .catch((e) => {
        if (!controller.signal.aborted) setError(errorText(e));
      });
    return () => controller.abort();
  }, [unit, id]);
  return (
    <>
      <button className="secondary-button profile-back" onClick={onBack}>
        <ArrowLeft size={15} />
        Sve kompanije
      </button>
      {error ? (
        <p className="error-message" role="alert">
          {error}
        </p>
      ) : !company ? (
        <p className="empty">Učitavanje kompanije…</p>
      ) : (
        <>
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                PROFIL KOMPANIJE
              </div>
              <h1>{company.name}</h1>
              <p>
                {company.city} · {company.sector}
              </p>
              <p>Adresa: {company.address || "Nije uneta"} · PIB: {company.pib || "Nije unet"}
              </p>
            </div>
            <Building2 size={30} />
          </div>
          <section className="panel" aria-label="Ugovor kompanije">
            <h2>Ugovor</h2>
            <p>Datum potpisivanja: {company.contract_signed_on ? formatDate(company.contract_signed_on) : "Nije unet"}</p>
            <p>Datum isteka: {company.contract_expires_on ? formatDate(company.contract_expires_on) : "Nije unet"}</p>
            <small>Datume menjate kroz „Izmeni” na listi kompanija. Podsetnik se prikazuje 30 dana pre isteka.</small>
          </section>
          <div
            className="profile-tabs"
            role="tablist"
            aria-label="Podaci kompanije"
          >
            <button
              role="tab"
              aria-selected={tab === "contacts"}
              aria-controls="profile-contacts"
              id="contacts-tab"
              className={tab === "contacts" ? "active" : ""}
              onClick={() => setTab("contacts")}
            >
              Kontakt osobe
            </button>
            <button
              role="tab"
              aria-selected={tab === "opportunities"}
              aria-controls="profile-opportunities"
              id="opportunities-tab"
              className={tab === "opportunities" ? "active" : ""}
              onClick={() => setTab("opportunities")}
            >
              Prodajne prilike
            </button>
          </div>
          {tab === "contacts" ? (
            <div
              role="tabpanel"
              id="profile-contacts"
              aria-labelledby="contacts-tab"
            >
              <Contacts unit={unit} company={id} />
            </div>
          ) : (
            <div
              role="tabpanel"
              id="profile-opportunities"
              aria-labelledby="opportunities-tab"
            >
              <Pipeline organization={organization} unit={unit} companyId={id} companies={[company]} />
            </div>
          )}
        </>
      )}
    </>
  );
}
