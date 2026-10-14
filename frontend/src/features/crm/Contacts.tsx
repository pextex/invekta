import { useState, type FormEvent } from "react";
import { Plus, Save } from "lucide-react";
import { errorText } from "../../lib/api";
import { useCrmQuery, useCrmRequest } from "../../lib/crmQuery";
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
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState<Fields | null>(null),
    [editing, setEditing] = useState<number | null>(null);
  const [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const base = `/companies/${company}/contacts`;
  const query = useCrmQuery<Contact[]>(unit, base);
  const items = query.error ? [] : (query.data ?? []),
    loading = query.isPending;
  const request = useCrmRequest(unit);
  async function save(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setBusy(true);
    setError("");
    try {
      await request(base + (editing ? "/" + editing : ""), {
        method: editing ? "PATCH" : "POST",
        body: JSON.stringify(form),
      });
      setForm(null);
      setMessage("Kontakt je sačuvan.");
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
      {(error || query.error) && (
        <p className="error-message" role="alert">
          {error || errorText(query.error)}
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
                        {c.is_demo ? " · DEMO" : ""}
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
