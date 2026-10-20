import { useEffect, useState, type FormEvent } from "react";
import { Plus, Save } from "lucide-react";
import { api, errorText } from "../../lib/api";
import type { Contact } from "./types";
type Fields = { name: string; position: string; email: string; phone: string };
const blank: Fields = { name: "", position: "", email: "", phone: "" };
export default function Contacts({
  unit,
  company,
}: {
  unit: number;
  company: number;
}) {
  const [items, setItems] = useState<Contact[]>([]),
    [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false);
  const [form, setForm] = useState<Fields | null>(null),
    [editing, setEditing] = useState<number | null>(null);
  const [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [reload, setReload] = useState(0);
  const base = `/units/${unit}/companies/${company}/contacts`;
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    api<Contact[]>(base, { signal: controller.signal })
      .then(setItems)
      .catch((e) => {
        if (!controller.signal.aborted) setError(errorText(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [base, reload]);
  async function save(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setBusy(true);
    setError("");
    try {
      await api(base + (editing ? "/" + editing : ""), {
        method: editing ? "PATCH" : "POST",
        body: JSON.stringify(form),
      });
      setForm(null);
      setMessage("Kontakt je sačuvan.");
      setReload((v) => v + 1);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="section-heading">
        <div>
          <h2>Kontakt osobe</h2>
          <p>Kontakti ove kompanije u izabranoj poslovnoj jedinici.</p>
        </div>
        <button
          className="primary-button"
          disabled={busy || loading}
          onClick={() => {
            setForm({ ...blank });
            setEditing(null);
            setMessage("");
          }}
        >
          <Plus size={16} />
          Novi kontakt
        </button>
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
      {form && (
        <section className="panel company-form">
          <h2>{editing ? "Izmena kontakta" : "Novi kontakt"}</h2>
          <form onSubmit={save}>
            <div className="form-grid">
              {(["name", "position", "email", "phone"] as const).map((key) => (
                <label key={key}>
                  {
                    {
                      name: "Ime i prezime",
                      position: "Pozicija",
                      email: "E-mail",
                      phone: "Telefon",
                    }[key]
                  }
                  <input
                    required={key === "name"}
                    type={
                      key === "email"
                        ? "email"
                        : key === "phone"
                          ? "tel"
                          : "text"
                    }
                    minLength={key === "name" ? 2 : undefined}
                    maxLength={
                      { name: 150, position: 100, email: 254, phone: 40 }[key]
                    }
                    disabled={busy}
                    value={form[key]}
                    onChange={(e) =>
                      setForm({ ...form, [key]: e.target.value })
                    }
                  />
                </label>
              ))}
            </div>
            <div className="form-actions">
              <button className="primary-button" disabled={busy}>
                <Save size={16} />
                {busy ? "Čuvanje…" : "Sačuvaj kontakt"}
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
        <div className="table-scroll">
          {loading ? (
            <p className="empty">Učitavanje kontakata…</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Kontakt</th>
                  <th>E-mail</th>
                  <th>Telefon</th>
                  <th>Akcija</th>
                </tr>
              </thead>
              <tbody>
                {items.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <strong>{c.name}</strong>
                      <small>
                        {c.position || "Pozicija nije uneta"}

                      </small>
                    </td>
                    <td>{c.email || "—"}</td>
                    <td>{c.phone || "—"}</td>
                    <td>
                      <button
                        className="text-button"
                        disabled={busy}
                        onClick={() => {
                          setEditing(c.id);
                          setForm({
                            name: c.name,
                            position: c.position ?? "",
                            email: c.email ?? "",
                            phone: c.phone ?? "",
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
          )}
          {!loading && !error && !items.length && (
            <p className="empty">
              Još nema kontakt osoba. Dodajte prvi kontakt.
            </p>
          )}
        </div>
      </section>
    </>
  );
}
