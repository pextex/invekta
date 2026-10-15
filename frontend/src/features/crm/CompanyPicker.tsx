import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { api, errorText } from "../../lib/api";
import type { Company } from "./types";

export default function CompanyPicker({ unit, value, options, selectedName, disabled = false, onChange }: {
  unit: number; value: number; options: Company[]; selectedName?: string; disabled?: boolean; onChange: (id: number) => void;
}) {
  const id = useId();
  const root = useRef<HTMLDivElement>(null);
  const [text, setText] = useState(() => options.find(c => c.id === value)?.name ?? selectedName ?? "");
  const [rows, setRows] = useState<Company[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState(-1);
  useEffect(() => {
    if (value > 0) { const name = options.find(c => c.id === value)?.name ?? selectedName; if (name) setText(name); }
  }, [value, selectedName, options]);
  useEffect(() => {
    if (!open || disabled) return;
    const controller = new AbortController(); setLoading(true); setRows([]); setError(""); setActive(-1);
    const timer = window.setTimeout(() => {
      api<Company[]>(`/units/${unit}/companies?${new URLSearchParams({ search: value ? "" : text.trim() })}`, { signal: controller.signal })
        .then(data => { setRows(data.slice(0, 20)); })
        .catch(e => { if (!controller.signal.aborted) setError(errorText(e)); })
        .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }, 180);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [unit, text, open, disabled, value]);
  function select(company: Company) { setText(company.name); setOpen(false); setActive(-1); onChange(company.id); }
  function keyboard(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") { setOpen(false); setActive(-1); }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault(); setOpen(true);
      if (!rows.length) { setActive(-1); return; }
      setActive(index => event.key === "ArrowDown" ? Math.min(rows.length - 1, index + 1) : Math.max(0, index - 1));
    }
    if (event.key === "Enter" && open && active >= 0 && rows[active]) { event.preventDefault(); select(rows[active]); }
  }
  return <div className="company-picker" ref={root} onBlur={event => { if (!root.current?.contains(event.relatedTarget as Node)) setOpen(false); }}>
    <label htmlFor={id}>Kompanija</label>
    <input id={id} role="combobox" aria-label="Kompanija prilike" aria-autocomplete="list" aria-expanded={open} aria-controls={`${id}-list`} aria-activedescendant={open && active >= 0 ? `${id}-${active}` : undefined}
      autoComplete="off" required disabled={disabled} value={text} placeholder="Kucajte naziv, grad ili PIB kompanije…"
      onFocus={() => { if (!disabled) setOpen(true); }} onKeyDown={keyboard}
      onChange={event => { setText(event.target.value); onChange(0); setOpen(true); }} />
    {open && !disabled && <div className="company-picker-menu">
      {loading ? <p role="status">Pretraživanje…</p> : error ? <p role="alert">{error}</p> : !rows.length ? <p>Nema kompanija za unetu pretragu.</p> : null}
      <div role="listbox" id={`${id}-list`} aria-label="Rezultati pretrage kompanija">
        {rows.map((company, index) => <button type="button" role="option" id={`${id}-${index}`} aria-selected={value === company.id} key={company.id} className={index === active ? "active" : ""}
          onMouseDown={event => event.preventDefault()} onClick={() => select(company)}><strong>{company.name}</strong><small>{company.city}{company.pib ? ` · PIB ${company.pib}` : ""}</small></button>)}
      </div>
      {rows.length === 20 && <small>Prikazano prvih 20 rezultata. Dopunite pretragu.</small>}
    </div>}
    {!disabled && value === 0 && text.trim() && !open && <small className="company-picker-hint">Izaberite kompaniju iz rezultata pre čuvanja.</small>}
  </div>;
}
