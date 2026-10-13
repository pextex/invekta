import { useEffect, useState, type FormEvent } from "react";
import { Building2, Plus, Save } from "lucide-react";
import Shell from "./Shell";
import { api, errorText } from "./lib/api";
import { readRoute, writeRoute } from "./lib/routes";
import CompanyProfile from "./features/crm/CompanyProfile";
import Pipeline from "./features/crm/Pipeline";
import Dashboard from "./features/crm/Dashboard";
import type { User, Company, CompanyForm } from "./features/crm/types";
const blank: CompanyForm = { name: "", city: "", sector: "" };
export default function Workspace({ onBack }: { onBack: () => void }) {
  const [page, setPage] = useState(() => readRoute().page),
    [selectedCompany, setSelectedCompany] = useState(() => readRoute().company);
  const [user, setUser] = useState<User | null>(null),
    [checking, setChecking] = useState(true);
  const [username, setUsername] = useState(""),
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
  function acceptUser(next: User) {
    const desired = readRoute().unit;
    const nextUnit =
      next.units.find((u) => u.id === desired)?.id ?? next.units[0]?.id ?? 0;
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
      if (user?.units.some((u) => u.id === route.unit)) setUnit(route.unit!);
    }
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [user]);
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
    setBusy(true);
    setError("");
    try {
      await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      acceptUser(await api<User>("/auth/me"));
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
        body: JSON.stringify(form),
      });
      setForm(null);
      setMessage("Kompanija je sačuvana u PostgreSQL bazi.");
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
  const supported = [
    "Kompanije",
    "Novi klijenti",
    "Početna tabla",
    "Izveštaji",
    "Prodajni levak",
  ].includes(page);
  return (
    <Shell
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
      unit={String(unit)}
      units={
        user?.units.map((u) => ({
          value: String(u.id),
          label: u.code + " · " + roleName(u.role),
        })) ?? []
      }
      onUnit={
        user
          ? (value) => {
              const id = Number(value);
              setUnit(id);
              setSelectedCompany(undefined);
              setForm(null);
              setSearch("");
              setMessage("");
              writeRoute(page, id);
            }
          : undefined
      }
      user={user?.name ?? "Gost"}
      role={activeRole ? roleName(activeRole) : "Prijavite se za pristup"}
      connected
      busy={busy}
      onBack={onBack}
      onLogout={user ? logout : undefined}
    >
      <div className="demo-notice">
        Razvojni CRM · trajna baza i kontrola pristupa su uključeni. Koristite
        samo testne podatke do završetka produkcione pripreme.
      </div>
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
      {checking ? (
        <p className="empty">Provera sesije…</p>
      ) : !user ? (
        <section className="panel login-panel">
          <Building2 size={32} />
          <h1>Prijava u CRM</h1>
          <p>
            Nalog kreira administrator razvojnog okruženja. Demo prikaz možete
            otvoriti bez prijave.
          </p>
          <form onSubmit={login}>
            <label>
              Korisničko ime
              <input
                required
                maxLength={100}
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </label>
            <label>
              Lozinka
              <input
                required
                maxLength={256}
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            <button className="primary-button" disabled={busy}>
              {busy ? "Prijavljivanje…" : "Prijavi se"}
            </button>
          </form>
        </section>
      ) : !unit ? (
        <p className="empty">
          Nije vam dodeljena poslovna jedinica. Obratite se administratoru.
        </p>
      ) : selectedCompany && page === "Kompanije" ? (
        <CompanyProfile
          key={`${unit}-${selectedCompany}`}
          unit={unit}
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
          <Pipeline key={unit} unit={unit} companies={rows} />
          <p className="section-hint">
            Izbor kompanije nudi najviše 200 kompanija iz odabrane jedinice. Za
            ostale otvorite profil kompanije preko pretrage.
          </p>
        </>
      ) : page === "Početna tabla" || page === "Izveštaji" ? (
        <Dashboard
          key={unit}
          unit={unit}
          onPipeline={() => navigate("Prodajni levak")}
        />
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
              <h1>
                {page === "Novi klijenti"
                  ? "Novi klijenti"
                  : "Kompanije i kontakti"}
              </h1>
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
          {page === "Novi klijenti" && (
            <p className="section-hint">
              Ručni unos novih klijenata. Automatsko pronalaženje i AI
              kvalifikacija još nisu uključeni.
            </p>
          )}
          {form && (
            <section className="panel company-form">
              <h2>{editing ? "Izmena kompanije" : "Nova kompanija"}</h2>
              <form onSubmit={save}>
                <div className="form-grid">
                  {(["name", "city", "sector"] as const).map((key) => (
                    <label key={key}>
                      {
                        {
                          name: "Naziv kompanije",
                          city: "Grad",
                          sector: "Delatnost",
                        }[key]
                      }
                      <input
                        required
                        disabled={busy}
                        minLength={2}
                        maxLength={key === "name" ? 200 : 100}
                        value={form[key]}
                        onChange={(e) =>
                          setForm({ ...form, [key]: e.target.value })
                        }
                      />
                    </label>
                  ))}
                </div>
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
                            {c.is_demo ? " · DEMO" : ""}
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
