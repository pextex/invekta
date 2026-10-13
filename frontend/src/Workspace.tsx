import { useEffect, useState } from "react";
import { ArrowLeft, Building2, LogOut, Plus, Save, Search } from "lucide-react";
import { money } from "./demo";

type Unit = { id: number; code: string; role: string };
type User = { name: string; units: Unit[] };
type Company = {
  id: number;
  business_unit_id: number;
  name: string;
  city: string;
  sector: string;
  stage: string;
  potential_value: string;
  is_demo: boolean;
};
type Form = {
  name: string;
  city: string;
  sector: string;
  stage: string;
  potential_value: string;
};
const blank: Form = {
  name: "",
  city: "",
  sector: "",
  stage: "Kontakt",
  potential_value: "0",
};
async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch("/api" + path, {
    credentials: "same-origin",
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Proverite uneta polja i pokušajte ponovo.",
    );
  return data as T;
}
export default function Workspace({ onBack }: { onBack: () => void }) {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [unit, setUnit] = useState(0);
  const [rows, setRows] = useState<Company[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [reload, setReload] = useState(0);
  const [form, setForm] = useState<Form | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  function acceptUser(next: User) {
    setUser(next);
    setUnit(next.units[0]?.id ?? 0);
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
        if (!controller.signal.aborted) setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [user, unit, search, reload]);
  async function login(e: React.FormEvent) {
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
      setError(e instanceof Error ? e.message : "Backend nije dostupan.");
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
    } catch (e) {
      setError(e instanceof Error ? e.message : "Odjava nije uspela.");
    } finally {
      setBusy(false);
    }
  }
  async function save(e: React.FormEvent) {
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
      setEditing(null);
      setMessage("Kompanija je sačuvana u PostgreSQL bazi.");
      setReload((v) => v + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Čuvanje nije uspelo.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="workspace">
      <header>
        <button className="text-button" onClick={onBack}>
          <ArrowLeft size={18} /> Demo pregled
        </button>
        <strong>LUU × INVEKTA · CRM</strong>
        {user && (
          <button className="text-button" disabled={busy} onClick={logout}>
            <LogOut size={16} /> Odjava
          </button>
        )}
      </header>
      <div className="workspace-content">
        <div className="demo-notice">
          Razvojni CRM · trajna baza i kontrola pristupa su uključeni. Koristite
          samo testne podatke dok ne završimo produkcionu pripremu.
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
        ) : (
          <>
            <div className="page-heading">
              <div>
                <div className="eyebrow">DOBRO DOŠLI · {user.name}</div>
                <h1>Kompanije</h1>
                <p>Zapisi dostupni prema vašoj poslovnoj jedinici i ulozi.</p>
              </div>
              <button
                className="primary-button"
                disabled={!unit || loading || busy}
                onClick={() => {
                  setForm({ ...blank });
                  setEditing(null);
                  setMessage("");
                }}
              >
                <Plus size={17} /> Nova kompanija
              </button>
            </div>
            <div className="workspace-tools">
              <label>
                Poslovna jedinica
                <select
                  aria-label="Poslovna jedinica"
                  value={unit}
                  disabled={busy}
                  onChange={(e) => {
                    setUnit(Number(e.target.value));
                    setForm(null);
                    setMessage("");
                  }}
                >
                  {user.units.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.code} ·{" "}
                      {u.role === "sales"
                        ? "Komercijalista"
                        : u.role === "manager"
                          ? "Menadžer"
                          : "Administrator"}
                    </option>
                  ))}
                </select>
              </label>
              <label className="search">
                <Search size={18} />
                <input
                  placeholder="Pretraži naziv, grad, delatnost…"
                  aria-label="Pretraga sačuvanih kompanija"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </label>
            </div>
            {user.units.length === 0 && (
              <p className="empty">
                Nije vam dodeljena poslovna jedinica. Obratite se
                administratoru.
              </p>
            )}
            {form && (
              <section className="panel company-form">
                <h2>{editing ? "Izmena kompanije" : "Nova kompanija"}</h2>
                <form onSubmit={save}>
                  <div className="form-grid">
                    {(
                      ["name", "city", "sector", "potential_value"] as const
                    ).map((key) => (
                      <label key={key}>
                        {
                          {
                            name: "Naziv kompanije",
                            city: "Grad",
                            sector: "Delatnost",
                            potential_value: "Potencijalna vrednost (RSD)",
                          }[key]
                        }
                        <input
                          required
                          disabled={busy}
                          type={key === "potential_value" ? "number" : "text"}
                          min={key === "potential_value" ? 0 : undefined}
                          step={key === "potential_value" ? "0.01" : undefined}
                          minLength={key === "potential_value" ? undefined : 2}
                          maxLength={
                            key === "name"
                              ? 200
                              : key === "potential_value"
                                ? undefined
                                : 100
                          }
                          value={form[key]}
                          onChange={(e) =>
                            setForm({ ...form, [key]: e.target.value })
                          }
                        />
                      </label>
                    ))}
                    <label>
                      Faza
                      <select
                        aria-label="Faza"
                        disabled={busy}
                        value={form.stage}
                        onChange={(e) =>
                          setForm({ ...form, stage: e.target.value })
                        }
                      >
                        {["Kontakt", "Ponuda", "Pregovori"].map((s) => (
                          <option key={s}>{s}</option>
                        ))}
                      </select>
                    </label>
                  </div>
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
                        <th>Faza</th>
                        <th>Potencijalna vrednost</th>
                        <th>Izmena</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((c) => (
                        <tr key={c.id}>
                          <td>
                            <strong>{c.name}</strong>
                            <small>
                              {c.city} · {c.sector}
                              {c.is_demo ? " · DEMO" : ""}
                            </small>
                          </td>
                          <td>
                            <span className={"stage stage-" + c.stage}>
                              {c.stage}
                            </span>
                          </td>
                          <td>{money(Number(c.potential_value))}</td>
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
                                  stage: c.stage,
                                  potential_value: c.potential_value,
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
                      Nema kompanija za prikaz. Dodajte prvu kompaniju ili
                      promenite pretragu.
                    </p>
                  )}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}
