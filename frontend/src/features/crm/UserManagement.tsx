import { useEffect, useState, type FormEvent } from "react";
import { api, errorText } from "../../lib/api";
import { organizations, type OrganizationCode } from "../../organizations";

type Grant = { code: OrganizationCode; role: string };
type Profile = { id: number; name: string; email: string | null; active: boolean; is_platform_admin: boolean; version: number; units: Grant[] };
type Draft = { name: string; email: string; password: string; active: boolean; units: Grant[] };
const empty = (): Draft => ({ name: "", email: "", password: "", active: true, units: [] });
const roles = [{ value: "sales", label: "Komercijalista" }, { value: "manager", label: "Menadžer" }, { value: "admin", label: "Administrator firme" }];
export default function UserManagement() {
  const [list, setList] = useState<Profile[]>([]), [total, setTotal] = useState(0), [offset, setOffset] = useState(0);
  const [draft, setDraft] = useState<Draft | null>(null), [editing, setEditing] = useState<Profile | null>(null);
  const [busy, setBusy] = useState(false), [loading, setLoading] = useState(true), [error, setError] = useState(""), [message, setMessage] = useState(""), [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setError("");
    api<{ items: Profile[]; total: number }>(`/admin/users?offset=${offset}&limit=50`, { signal: controller.signal })
      .then(data => { setList(data.items); setTotal(data.total); })
      .catch(e => { if (!controller.signal.aborted) setError(errorText(e)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [offset, revision]);
  function edit(profile: Profile) { setEditing(profile); setDraft({ name: profile.name, email: profile.email ?? "", password: "", active: profile.active, units: profile.units }); setMessage(""); setError(""); }
  async function save(e: FormEvent) {
    e.preventDefault(); if (!draft) return; setBusy(true); setError(""); setMessage("");
    try {
      const body = editing ? { name: draft.name, active: draft.active, units: draft.units, version: editing.version, ...(draft.password ? { password: draft.password } : {}) } : draft;
      await api(`/admin/users${editing ? "/" + editing.id : ""}`, { method: editing ? "PATCH" : "POST", body: JSON.stringify(body) });
      setDraft(null); setEditing(null); setRevision(v => v + 1);
      setMessage(editing ? "Profil je sačuvan. Korisnik treba ponovo da se prijavi." : "Korisnik je kreiran. Može da se prijavi samo u dodeljene firme.");
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <>
    <div className="page-heading"><div><h1>Korisnici i pristup</h1><p>Kreirajte naloge i odredite u kojim firmama mogu da rade.</p></div><button className="primary-button" disabled={busy} onClick={() => { setEditing(null); setDraft(empty()); setError(""); setMessage(""); }}>Novi korisnik</button></div>
    {error && <p className="error-message" role="alert">{error}</p>}
    {message && <p className="success-message" role="status">{message}</p>}
    {draft && <section className="panel"><h2>{editing ? "Uredi korisnika" : "Novi korisnik"}</h2><form onSubmit={save}>
      <div className="form-grid"><label>Ime i prezime<input required maxLength={150} disabled={busy} value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })}/></label><label>Email adresa<input type="email" required={!editing} maxLength={254} disabled={busy || !!editing} value={draft.email} onChange={e => setDraft({ ...draft, email: e.target.value })}/></label><label>{editing ? "Nova lozinka (opciono)" : "Početna lozinka"}<input type="password" autoComplete="new-password" required={!editing} minLength={12} maxLength={256} disabled={busy} value={draft.password} onChange={e => setDraft({ ...draft, password: e.target.value })}/><small>Najmanje 12 znakova.{editing && " Prazno polje zadržava postojeću lozinku."}</small></label></div>
      <fieldset disabled={busy} className="user-access"><legend>Pristup firmama</legend>{organizations.map(org => {
        const grant = draft.units.find(g => g.code === org.code);
        return <div className="user-access-row" key={org.code}><label><input type="checkbox" checked={!!grant} onChange={e => setDraft({ ...draft, units: e.target.checked ? [...draft.units, { code: org.code, role: "sales" }] : draft.units.filter(g => g.code !== org.code) })}/>{org.name}</label>{grant ? <select aria-label={"Uloga za " + org.name} value={grant.role} onChange={e => setDraft({ ...draft, units: draft.units.map(g => g.code === org.code ? { ...g, role: e.target.value } : g) })}>{roles.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}</select> : <span className="tag gray">Bez pristupa</span>}</div>;
      })}</fieldset>
      <label className="user-active"><input type="checkbox" disabled={busy} checked={draft.active} onChange={e => setDraft({ ...draft, active: e.target.checked })}/>Aktivan nalog</label>
      <p className="panel-note">Bez označene firme korisnik ne može da pristupi njenom CRM-u. Administrator firme nema pravo upravljanja nalozima platforme.</p>
      <div className="form-actions"><button className="primary-button" disabled={busy}>{busy ? "Čuvanje…" : "Sačuvaj korisnika"}</button><button type="button" className="secondary-button" disabled={busy} onClick={() => { setDraft(null); setEditing(null); }}>Otkaži</button></div>
    </form></section>}
    <section className="panel"><h2>Korisnici ({total})</h2>{loading ? <p>Učitavanje…</p> : <div className="table-scroll"><table><thead><tr><th>Korisnik</th><th>Status</th><th>Pristup</th><th></th></tr></thead><tbody>{list.map(profile => <tr key={profile.id}><td><strong>{profile.name}</strong><br/>{profile.email ?? "Stariji nalog bez emaila"}</td><td>{profile.active ? "Aktivan" : "Neaktivan"}</td><td>{profile.units.length ? profile.units.map(g => `${organizations.find(o => o.code === g.code)?.name ?? g.code}: ${roles.find(r => r.value === g.role)?.label ?? g.role}`).join(" · ") : "Bez pristupa"}</td><td>{profile.is_platform_admin ? <span className="tag">Administrator platforme</span> : <button className="text-button" disabled={busy} onClick={() => edit(profile)}>Uredi</button>}</td></tr>)}</tbody></table></div>}
      <div className="panel-actions"><button className="secondary-button" disabled={loading || busy || offset === 0} onClick={() => setOffset(v => Math.max(0, v - 50))}>Prethodna</button><button className="secondary-button" disabled={loading || busy || offset + 50 >= total} onClick={() => setOffset(v => v + 50)}>Sledeća</button><button className="secondary-button" disabled={loading || busy} onClick={() => setRevision(v => v + 1)}>Osveži spisak</button></div>
    </section>
  </>;
}
