import { useEffect, useRef, useState, type FormEvent } from "react";
import { X } from "lucide-react";
import { api, errorText } from "../lib/api";
import "./myProfile.css";

type Profile = { name: string; email: string | null; phone: string | null };
export default function MyProfile({ name, demo, onClose }: { name: string; demo: boolean; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [profile, setProfile] = useState<Profile | null>(demo ? { name, email: null, phone: null } : null);
  const [phone, setPhone] = useState("");
  const [current, setCurrent] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const element = dialog.current;
    const previous = document.activeElement;
    element?.showModal();
    return () => { element?.close(); if (previous instanceof HTMLElement) previous.focus(); };
  }, []);
  useEffect(() => {
    if (demo) return;
    const controller = new AbortController();
    api<Profile>("/profile", { signal: controller.signal }).then(next => {
      if (!controller.signal.aborted) { setProfile(next); setPhone(next.phone ?? ""); setError(""); }
    }).catch(e => { if (!controller.signal.aborted) setError(errorText(e)); });
    return () => controller.abort();
  }, [demo, reload]);
  async function savePhone(event: FormEvent) {
    event.preventDefault(); setError(""); setMessage(""); setBusy(true);
    try {
      if (demo) { setMessage("Demo prikaz: broj nije sačuvan na stvarnom nalogu."); return; }
      const next = await api<Profile>("/profile", { method: "PATCH", body: JSON.stringify({ phone: phone.trim() || null }) });
      setProfile(next); setPhone(next.phone ?? ""); setMessage("Broj telefona je sačuvan.");
    } catch (e) { setError(errorText(e)); }
    finally { setBusy(false); }
  }
  async function savePassword(event: FormEvent) {
    event.preventDefault(); setError(""); setMessage("");
    if (password !== confirm) { setError("Nova šifra i potvrda se ne podudaraju."); return; }
    if (password === current) { setError("Nova šifra mora biti različita od trenutne."); return; }
    setBusy(true);
    try {
      await api("/profile/password", { method: "POST", body: JSON.stringify({ current_password: current, new_password: password, confirm_password: confirm }) });
      setCurrent(""); setPassword(""); setConfirm("");
      setMessage("Šifra je promenjena. Ostali uređaji su odjavljeni; ovde ostajete prijavljeni.");
    } catch (e) { setCurrent(""); setPassword(""); setConfirm(""); setError(errorText(e)); }
    finally { setBusy(false); }
  }
  return <dialog ref={dialog} className="my-profile" aria-labelledby="my-profile-title" onCancel={event => { if (busy) event.preventDefault(); else onClose(); }}>
    <header><div><h2 id="my-profile-title">Moj profil</h2><p>Podaci i sigurnost Vašeg naloga</p></div><button className="text-button" aria-label="Zatvori profil" disabled={busy} onClick={onClose}><X size={21} /></button></header>
    <div className="my-profile-content">
      {demo && <p className="demo-notice">Demo profil. Čuvanje podataka i promena šifre dostupni su u prijavljenom CRM-u.</p>}
      {error && <p className="error-message" role="alert">{error}</p>}
      {message && <p className="success-message" role="status">{message}</p>}
      {!profile ? <>{!error ? <p role="status">Učitavanje profila…</p> : <button className="secondary-button" onClick={() => setReload(value => value + 1)}>Pokušaj ponovo</button>}</> : <>
        <div className="profile-identity"><strong>{profile.name}</strong>{profile.email && <span>{profile.email}</span>}</div>
        <form onSubmit={savePhone}><fieldset disabled={busy}><legend>Kontakt telefon</legend><label>Broj telefona<input type="tel" autoComplete="tel" maxLength={40} placeholder="+381 60 123 4567" value={phone} onChange={e => setPhone(e.target.value)} /></label><small>Koristi se i u potpisu AI mejlova. Obrišite polje da uklonite broj.</small><button className="primary-button" disabled={demo}>Sačuvaj telefon</button></fieldset></form>
        <form onSubmit={savePassword}><fieldset disabled={busy || demo}><legend>Promena šifre</legend>
          <label>Trenutna šifra<input type="password" autoComplete="current-password" required maxLength={256} value={current} onChange={e => setCurrent(e.target.value)} /></label>
          <label>Nova šifra<input type="password" autoComplete="new-password" required minLength={12} maxLength={256} value={password} onChange={e => setPassword(e.target.value)} /></label>
          <label>Potvrdite novu šifru<input type="password" autoComplete="new-password" required minLength={12} maxLength={256} value={confirm} onChange={e => setConfirm(e.target.value)} /></label>
          <small>Najmanje 12 znakova. Promena odjavljuje ostale uređaje.</small>
          <button className="primary-button">Promeni šifru</button>
        </fieldset></form>
      </>}
    </div>
  </dialog>;
}
