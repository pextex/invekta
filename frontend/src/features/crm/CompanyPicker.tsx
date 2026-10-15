import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { api, errorText } from "../../lib/api";
import type { Company } from "./types";

export type CompanyChoice = Pick<Company, "id" | "name"> & Partial<Pick<Company, "city" | "pib">>;

export default function CompanyPicker({ unit, value, options, selectedName, disabled = false, optional = false,
  local = false, label = "Kompanija", ariaLabel = "Kompanija prilike", onChange }: {
  unit: number; value: number; options: CompanyChoice[]; selectedName?: string; disabled?: boolean;
  optional?: boolean; local?: boolean; label?: string; ariaLabel?: string; onChange: (id: number, name?: string) => void;
}) {
  const id = useId();
  const root = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const [text, setText] = useState(() => options.find(c => c.id === value)?.name ?? selectedName ?? "");
  const [rows, setRows] = useState<CompanyChoice[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState(-1);
  useEffect(() => {
    if (value > 0) { const name = options.find(c => c.id === value)?.name ?? selectedName; if (name) setText(name); }
  }, [value, selectedName, options]);
  useEffect(() => {
    input.current?.setCustomValidity(text.trim() && value === 0 ? "Izaberite kompaniju iz rezultata pre čuvanja." : "");
  }, [text, value]);
  useEffect(() => {
    if (!open || disabled) return;
    const controller = new AbortController(); setLoading(true); setRows([]); setError(""); setActive(-1);
    const timer = window.setTimeout(() => {
      if (local) {
        const query = value ? "" : text.trim().toLocaleLowerCase("sr-Latn-RS");
        setRows(options.filter(company => [company.name, company.city, company.pib].some(field => field?.toLocaleLowerCase("sr-Latn-RS").includes(query))).slice(0, 20));
        setLoading(false); return;
      }
      api<Company[]>(`/units/${unit}/companies?${new URLSearchParams({ search: value ? "" : text.trim() })}`, { signal: controller.signal })
        .then(data => { if (!controller.signal.aborted) setRows(data.slice(0, 20)); })
        .catch(e => { if (!controller.signal.aborted) setError(errorText(e)); })
        .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }, 180);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [unit, text, open, disabled, value, local, options]);
  function select(company: CompanyChoice) { setText(company.name); setOpen(false); setActive(-1); onChange(company.id, company.name); }
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
    <label htmlFor={id}>{label}</label>
    <input ref={input} id={id} role="combobox" aria-label={ariaLabel} aria-autocomplete="list" aria-expanded={open} aria-controls={`${id}-list`} aria-activedescendant={open && active >= 0 ? `${id}-${active}` : undefined}
      autoComplete="off" required={!optional} maxLength={200} disabled={disabled} value={text} placeholder="Kucajte naziv, grad ili PIB kompanije…"
      onFocus={() => { if (!disabled) setOpen(true); }} onKeyDown={keyboard}
      onChange={event => { setText(event.target.value); onChange(0); setOpen(true); }} />
    {open && !disabled && <div className="company-picker-menu">
      {loading ? <p role="status">Pretraživanje…</p> : error ? <p role="alert">{error}</p> : !rows.length ? <p>Nema kompanija za unetu pretragu.</p> : null}
      <div role="listbox" id={`${id}-list`} aria-label="Rezultati pretrage kompanija">
        {rows.map((company, index) => <button type="button" role="option" id={`${id}-${index}`} aria-selected={value === company.id} key={company.id} className={index === active ? "active" : ""}
          onMouseDown={event => event.preventDefault()} onClick={() => select(company)}><strong>{company.name}</strong><small>{[company.city, company.pib ? `PIB ${company.pib}` : null].filter(Boolean).join(" · ")}</small></button>)}
      </div>
      {rows.length === 20 && <small>Prikazano prvih 20 rezultata. Dopunite pretragu.</small>}
    </div>}
    {!disabled && value === 0 && text.trim() && !open && <small className="company-picker-hint">Izaberite kompaniju iz rezultata pre čuvanja.</small>}
    {optional && (value > 0 || text.trim()) && <button type="button" className="text-button" disabled={disabled} onClick={() => {
      setText(""); setActive(-1); onChange(0); input.current?.focus(); setOpen(false);
    }}>Bez kompanije</button>}
  </div>;
}
