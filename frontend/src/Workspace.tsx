import Targets from "./features/crm/Targets";
import Quotes from "./features/crm/Quotes";
import TasksCalendar from "./features/crm/TasksCalendar";
import Reports from "./features/crm/Reports";
import AiAssistant from "./features/crm/AiAssistant";
import UserManagement from "./features/crm/UserManagement";
import OrganizationPortal from "./components/OrganizationPortal";
import {
  organizationName,
  isOrganizationCode,
  type OrganizationCode,
} from "./organizations";
import { useEffect, useState, type FormEvent } from "react";
import { Building2, Plus, Save } from "lucide-react";
import Shell from "./Shell";
import { api, errorText } from "./lib/api";
import { isCrmRoute, readRoute, writeRoute } from "./lib/routes";
import CompanyProfile from "./features/crm/CompanyProfile";
import Pipeline from "./features/crm/Pipeline";
import Dashboard from "./features/crm/Dashboard";
import type { User, Company, CompanyForm } from "./features/crm/types";
const blank: CompanyForm = { name: "", address: "", pib: "", city: "", sector: "", contacts: [{ name: "", position: "", phone: "", email: "" }] };
export default function Workspace({
  onDemo,
}: {
  onBack?: () => void;
  onDemo?: (code: OrganizationCode) => void;
}) {
  const [loginChoice, setLoginChoice] = useState<OrganizationCode | null>(
    () => readRoute().organization ?? null,
  );
  const [page, setPage] = useState(() => readRoute().page),
    [selectedCompany, setSelectedCompany] = useState(() => readRoute().company);
  const [user, setUser] = useState<User | null>(null),
    [checking, setChecking] = useState(true);
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [unit, setUnit] = useState(0);
  const [rows, setRows] = useState<Company[]>([]),
    [search, setSearch] = useState(""),
    [error, setError] = useState("");
  const [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(false),
    [reload, setReload] = useState(0);
  const [form, setForm] = useState<CompanyForm | null>(null),
    [editing, setEditing] = useState<number | null>(null),
    [message, setMessage] = useState("");
  function acceptUser(next: User, choice?: OrganizationCode) {
    const desired = readRoute().unit;
    const selectedCode = choice ?? readRoute().organization;
    const selected = selectedCode
      ? next.units.find((u) => u.code === selectedCode)
      : undefined;
    if (selectedCode && !selected)
      throw new Error(
        "Nemate pristup izabranoj kompaniji. Obratite se administratoru.",
      );
    const nextUnit =
      selected?.id ??
      next.units.find((u) => u.id === desired)?.id ??
      next.units[0]?.id ??
      0;
    setUser(next);
    setUnit(nextUnit);
    writeRoute(page, nextUnit, selectedCompany, true);
  }
  function navigate(next: string, company?: number) {
    if (busy) return;
    setPage(next);
    setSelectedCompany(company);
    setForm(null);
    setMessage("");
    setSearch("");
    setError("");
    writeRoute(next, unit, company);
  }
  useEffect(() => {
    if (!isCrmRoute()) {
      setChecking(false);
      return;
    }
    let active = true;
    api<User>("/auth/me")
      .then((next) => {
        if (active) acceptUser(next);
      })
      .catch(() => {})
      .finally(() => {
        if (active) setChecking(false);
      });
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    function onHash() {
      const route = readRoute();
      setPage(route.page);
      setSelectedCompany(route.company);
      setForm(null);
      if (user && route.unit && route.unit !== unit)
        writeRoute(route.page, unit, undefined, true);
    }
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [user, unit]);
  useEffect(() => {
    if (!user || !unit) return;
    const controller = new AbortController();
    setLoading(true);
    setRows([]);
    setError("");
    api<Company[]>(
      `/units/${unit}/companies?search=${encodeURIComponent(search)}`,
      { signal: controller.signal },
    )
      .then(setRows)
      .catch((e) => {
        if (!controller.signal.aborted) setError(errorText(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [user, unit, search, reload]);
  async function login(e: FormEvent) {
    e.preventDefault();
    if (!loginChoice) return;
    setBusy(true);
    setError("");
    try {
      await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          business_unit_code: loginChoice,
        }),
      });
      acceptUser(await api<User>("/auth/me"), loginChoice);
      setPassword("");
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function logout() {
    setBusy(true);
    setError("");
    try {
      await api("/auth/logout", { method: "POST", body: "{}" });
      const currentCode = user?.units.find((u) => u.id === unit)?.code;
      if (isOrganizationCode(currentCode)) setLoginChoice(currentCode);
      setPassword("");
      setUser(null);
      setRows([]);
      setForm(null);
      setMessage("");
      setSelectedCompany(undefined);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function save(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setBusy(true);
    setError("");
    try {
      await api(`/units/${unit}/companies${editing ? "/" + editing : ""}`, {
        method: editing ? "PATCH" : "POST",
        body: JSON.stringify({ ...form, address: form.address || null, pib: form.pib || null }),
      });
      setForm(null);
      setMessage("Kompanija je sačuvana u CRM bazi.");
      setReload((v) => v + 1);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  const roleName = (role: string) =>
    role === "sales"
      ? "Komercijalista"
      : role === "manager"
        ? "Menadžer prodaje"
        : "Administrator";
  const activeRole = user?.units.find((u) => u.id === unit)?.role;
  const canViewHistory = user?.is_platform_admin || activeRole === "manager" || activeRole === "admin";
  const supported = [
    "Kompanije",
    "Početna tabla",
    "Izveštaji",
    "Prodajni levak",
  ].includes(page);
  if (checking)
    return (
      <main className="portal-loading">
        <p>Provera sesije…</p>
      </main>
    );
  if (!user)
    return (
      <OrganizationPortal
        selected={loginChoice}
        onSelect={(code) => {
          setLoginChoice(code);
          setError("");
        }}
        busy={busy}
        error={error}
      >
        <form onSubmit={login}>
          <label>
            Email adresa
            <input
              required
              maxLength={254}
              type="email"
              autoComplete="username"
              disabled={busy}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label>
            Lozinka
            <input
              required
              maxLength={256}
              type="password"
              autoComplete="current-password"
              disabled={busy}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button
            className="primary-button"
            disabled={busy || window.location.protocol === "file:"}
          >
            {busy
              ? "Prijavljivanje…"
              : "Prijavi se u " + organizationName(loginChoice ?? "")}
          </button>
        </form>
        {onDemo && <div className="portal-demo-entry">
          <span>
            {window.location.protocol === "file:"
              ? "Preuzeti HTML nema povezan server za prijavu."
              : "Želite samo da pogledate demo?"}
          </span>
          <button
            type="button"
            className="secondary-button"
            disabled={busy || !loginChoice}
            onClick={() => {
              if (loginChoice) onDemo(loginChoice);
            }}
          >
            Pogledaj demo bez prijave
          </button>
          <small>Izmišljeni podaci · nema pristupa stvarnom CRM-u.</small>
        </div>}
      </OrganizationPortal>
    );
  return (
    <Shell
      canViewHistory={canViewHistory}
      organization={
        user?.units.find((u) => u.id === unit)?.code as
          | OrganizationCode
          | undefined
      }
      page={user ? page : "Prijava"}
      onPage={(next) => {
        if (user) navigate(next);
      }}
      search={search}
      onSearch={
        user
          ? (value) => {
              setSearch(value);
              setPage("Kompanije");
              setSelectedCompany(undefined);
              setForm(null);
              writeRoute("Kompanije", unit, undefined, true);
            }
          : undefined
      }
      user={user?.name ?? "Gost"}
      role={activeRole ? roleName(activeRole) : "Prijavite se za pristup"}
      connected
      canManageUsers={user.is_platform_admin}
      busy={busy}
      onLogout={user ? logout : undefined}
    >
      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {message && (
        <p className="success-message" role="status">
          {message}
        </p>
      )}
      {!unit ? (
        <p className="empty">
          Nije vam dodeljena poslovna jedinica. Obratite se administratoru.
        </p>
      ) : selectedCompany && page === "Kompanije" ? (
        <CompanyProfile
          key={`${unit}-${selectedCompany}`}
          unit={unit}
          organization={user.units.find(u => u.id === unit)?.code}
          id={selectedCompany}
          onBack={() => navigate("Kompanije")}
        />
      ) : page === "Prodajni levak" ? (
        <>
          <div className="page-heading">
            <div>
              <h1>Prodajne prilike</h1>
              <p>Pregled procesa od prvog kontakta do odluke klijenta.</p>
            </div>
          </div>
          <Pipeline organization={user.units.find(u => u.id === unit)?.code} key={unit} unit={unit} companies={rows} canViewHistory={canViewHistory} />
          <p className="section-hint">
            Izbor kompanije nudi najviše 200 kompanija iz odabrane jedinice. Za
            ostale otvorite profil kompanije preko pretrage.
          </p>
        </>
      ) : page === "Targeti" ? (
        <Targets key={unit} unit={unit} />
      ) : page === "Ponude" ? (
        <Quotes key={unit} unit={unit} canUpload={user.is_platform_admin || activeRole === "admin"} />
      ) : page === "Zadaci" ? (
        <TasksCalendar key={unit} unit={unit} companies={rows} />
      ) : page === "Izveštaji" ? (
        <Reports key={unit} unit={unit} role={activeRole} />
      ) : page === "Hronologija promena - log" ? (
        canViewHistory ? <Reports key={`history-${unit}`} unit={unit} role="manager" historyOnly /> : <p className="error-message" role="alert">Hronologija promena je dostupna samo menadžerima i administratorima.</p>
      ) : page === "Početna tabla" ? (
        <Dashboard
          userName={user.name}
          onNavigate={navigate}
          key={unit}
          unit={unit}
          onPipeline={() => navigate("Prodajni levak")}
        />
      ) : page === "Invekta AI" ? (
        <AiAssistant key={unit} unit={unit} companies={rows} organization={user.units.find(item => item.id === unit)?.code ?? "CRM"} />
      ) : page === "Podešavanja" && user.is_platform_admin ? (
        <UserManagement />
      ) : !supported ? (
        <>
          <div className="page-heading">
            <h1>{page}</h1>
          </div>
          <section className="panel placeholder">
            <Building2 size={36} />
            <h2>Ovaj ekran je u pripremi</h2>
            <p>
              Kompanije, kontakti, prodajni levak i osnovni pokazatelji su
              dostupni. Ostali moduli slede u narednim fazama.
            </p>
            <button
              className="primary-button"
              onClick={() => navigate("Kompanije")}
            >
              Otvori kompanije
            </button>
          </section>
        </>
      ) : (
        <>
          <div className="page-heading">
            <div>
              <div className="eyebrow">DOBRO DOŠLI · {user.name}</div>
              <h1>Kompanije i kontakti</h1>
              <p>Otvorite profil kompanije za kontakte i prodajne prilike.</p>
            </div>
            <button
              className="primary-button"
              disabled={loading || busy}
              onClick={() => {
                setForm({ ...blank });
                setEditing(null);
                setMessage("");
              }}
            >
              <Plus size={17} />
              Nova kompanija
            </button>
          </div>
          {form && (
            <section className="panel company-form">
              <h2>{editing ? "Izmena kompanije" : "Nova kompanija"}</h2>
              <form onSubmit={save}>
                <div className="form-grid">
                  {(["name", "address", "pib", "city", "sector"] as const).map((key) => (
                    <label key={key}>
                      {
                        {
                          name: "Naziv kompanije",
                          address: "Adresa",
                          pib: "PIB",
                          city: "Grad",
                          sector: "Delatnost",
                        }[key]
                      }
                      <input
                        required
                        disabled={busy}
                        minLength={key === "pib" ? 9 : 2}
                        pattern={key === "pib" ? "[0-9]{9}" : undefined}
                        inputMode={key === "pib" ? "numeric" : undefined}
                        maxLength={key === "pib" ? 9 : key === "address" ? 300 : key === "name" ? 200 : 100}
                        value={form[key]}
                        onChange={(e) =>
                          setForm({ ...form, [key]: e.target.value })
                        }
                      />
                    </label>
                  ))}
                </div>
                {!editing && <>
                  <h3>Kontakt osobe</h3>
                  {form.contacts?.map((contact, index) => (
                    <fieldset key={index} disabled={busy}>
                      <legend>Kontakt osoba {index + 1}</legend>
                      <div className="form-grid">
                        {(["name", "position", "phone", "email"] as const).map(key => (
                          <label key={key}>
                            {{ name: "Ime i prezime", position: "Funkcija", phone: "Broj telefona", email: "Email" }[key]}
                            <input required type={key === "email" ? "email" : key === "phone" ? "tel" : "text"}
                              maxLength={{ name: 150, position: 100, phone: 40, email: 254 }[key]}
                              minLength={key === "name" ? 2 : 1} value={contact[key]}
                              onChange={e => setForm({ ...form, contacts: form.contacts?.map((c, i) => i === index ? { ...c, [key]: e.target.value } : c) })} />
                          </label>
                        ))}
                      </div>
                      {(form.contacts?.length ?? 0) > 1 && <button type="button" className="text-button"
                        onClick={() => setForm({ ...form, contacts: form.contacts?.filter((_, i) => i !== index) })}>Ukloni kontakt</button>}
                    </fieldset>
                  ))}
                  <button type="button" className="secondary-button" disabled={busy || (form.contacts?.length ?? 0) >= 50}
                    onClick={() => setForm({ ...form, contacts: [...(form.contacts ?? []), { name: "", position: "", phone: "", email: "" }] })}>Dodaj kontakt osobu</button>
                </>}
                {editing && <p className="section-hint">Kontakt osobe menjate u profilu kompanije.</p>}
                <p className="section-hint">
                  Vrednost i fazu prodaje sada unosite kroz zasebne prilike u
                  profilu kompanije.
                </p>
                <div className="form-actions">
                  <button className="primary-button" disabled={busy}>
                    <Save size={16} />
                    {busy ? "Čuvanje…" : "Sačuvaj"}
                  </button>
                  <button
                    type="button"
                    className="secondary-button"
                    disabled={busy}
                    onClick={() => setForm(null)}
                  >
                    Otkaži
                  </button>
                </div>
              </form>
            </section>
          )}
          <section className="panel">
            <div className="panel-heading">
              <h2>Sačuvane kompanije</h2>
              <span className="tag">{rows.length} zapisa · najviše 200</span>
            </div>
            {loading ? (
              <p className="empty">Učitavanje…</p>
            ) : (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Kompanija</th>
                      <th>Delatnost</th>
                      <th>Kontakti i prilike</th>
                      <th>Izmena</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((c) => (
                      <tr key={c.id}>
                        <td>
                          <strong>{c.name}</strong>
                          <small>
                            {c.city}
                          </small>
                        </td>
                        <td>{c.sector}</td>
                        <td>
                          <button
                            className="text-button"
                            onClick={() => navigate("Kompanije", c.id)}
                          >
                            Otvori profil →
                          </button>
                        </td>
                        <td>
                          <button
                            className="text-button"
                            disabled={busy}
                            onClick={() => {
                              setEditing(c.id);
                              setForm({
                                name: c.name,
                                address: c.address ?? "",
                                pib: c.pib ?? "",
                                city: c.city,
                                sector: c.sector,
                              });
                              setMessage("");
                            }}
                          >
                            Izmeni
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {rows.length === 0 && !error && (
                  <p className="empty">
                    Nema kompanija za prikaz. Dodajte prvu ili promenite
                    pretragu.
                  </p>
                )}
              </div>
            )}
          </section>
        </>
      )}
    </Shell>
  );
}
