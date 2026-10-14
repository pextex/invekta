import Targets from "./features/crm/Targets";
import { businessTypeLabel, businessTypesFor, type BusinessType } from "./features/crm/businessTypes";
import TasksCalendar from "./features/crm/TasksCalendar";
import { loadDemoTasks } from "./features/crm/taskCalendar";
import Reports from "./features/crm/Reports";
import { loadDemoActivity, saveDemoActivity } from "./lib/demoActivity";
import { stageLabel } from "./features/crm/types";
import DailyWelcome, { dailyRecommendations } from "./components/DailyWelcome";
import AiAssistant from "./features/crm/AiAssistant";
import {
  organizations,
  organizationName,
  type OrganizationCode,
} from "./organizations";
import {
  loadDemoStages,
  saveDemoStages,
  readDemoPage,
  writeDemoPage,
} from "./lib/demoPipeline";
import { useStageDragDrop } from "./features/crm/useStageDragDrop";
import { type OpportunityStage } from "./features/crm/types";
import { isCrmRoute } from "./lib/routes";
import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  GripVertical,
  Plus,
  Search,
  Sparkles,
  FileText,
} from "lucide-react";
import Workspace from "./Workspace";
import Shell from "./Shell";
import { selectCompanies, money, stages, type Unit } from "./demo";

type Scope = Unit | "all";
export default function App() {
  const [live, setLive] = useState(() => isCrmRoute());
  const [entry, setEntry] = useState(
    () => !window.location.hash.startsWith("#demo"),
  );
  const [unit, setUnit] = useState<Scope>(() => {
    const code = new URLSearchParams(window.location.hash.split("?")[1]).get(
      "organization",
    );
    return organizations.find((org) => org.code === code)?.code ?? "LUU";
  });
  const [page, setPage] = useState(readDemoPage);
  const [activity, setActivity] = useState(loadDemoActivity);
  const [demoTypes, setDemoTypes] = useState<Record<number, BusinessType>>(() => {
    try { const raw = JSON.parse(localStorage.getItem("crm-demo-business-types-v1") ?? "{}");
      return Object.fromEntries(Object.entries(raw).filter(([_, value]) => ["sale", "contracted", "leasing", "rental"].includes(String(value)))) as Record<number, BusinessType>;
    } catch { return {}; }
  });
  const [stageOverrides, setStageOverrides] = useState(loadDemoStages);
  const [stageMessage, setStageMessage] = useState("");
  const [search, setSearch] = useState("");
  const [, setTaskReload] = useState(0);
  useEffect(() => {
    const update = () => setTaskReload(v => v + 1);
    window.addEventListener("crm-demo-tasks", update);
    return () => window.removeEventListener("crm-demo-tasks", update);
  }, []);
  useEffect(() => {
    const onHash = () => {
      setLive(isCrmRoute());
      setEntry(!window.location.hash.startsWith("#demo"));
      if (!isCrmRoute()) setPage(readDemoPage());
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const rows = selectCompanies(unit, search).map((c) => ({
    ...c,
    business_type: demoTypes[c.id] ?? (businessTypesFor(c.unit).length === 1 ? businessTypesFor(c.unit)[0] : null),
    stage: stageOverrides[c.id] ?? c.stage,
  }));
  const all = selectCompanies(unit).map((c) => ({
    ...c,
    business_type: demoTypes[c.id] ?? (businessTypesFor(c.unit).length === 1 ? businessTypesFor(c.unit)[0] : null),
    stage: stageOverrides[c.id] ?? c.stage,
  }));
  const open = all.filter(
    (c) => c.stage !== "Dobijeno" && c.stage !== "Izgubljeno",
  );
  const total = open.reduce((sum, c) => sum + c.value, 0);
  function moveDemo(item: (typeof all)[number], stage: OpportunityStage) {
    if (item.stage === stage) return;
    if (stage === "Dobijeno" && !item.business_type) { setStageMessage("Izaberite vrstu posla pre realizacije: prodaja, lizing ili najam."); return; }
    const next = { ...stageOverrides, [item.id]: stage };
    setStageOverrides(next);
    const events = [...activity, { id: (activity.at(-1)?.id ?? 0) + 1, changed_at: new Date().toISOString(), company_name: item.name, opportunity_id: item.id, title: item.name, business_type: item.business_type, amount: String(item.value), from_stage: item.stage, to_stage: stage, actor_name: "Demo korisnik", changes: null }];
    setActivity(events);
    const savedHistory = saveDemoActivity(events);
    setStageMessage(
      saveDemoStages(next) && savedHistory
        ? "Demo status je sačuvan u ovom browseru. Ne upisuje se u CRM bazu."
        : "Status je promenjen za ovaj prikaz. Browser ne dozvoljava lokalno čuvanje.",
    );
  }
  const drag = useStageDragDrop(all, false, moveDemo);
  const tasks = (
    unit === "all" ? organizations.map((org) => org.code) : [unit]
  ).flatMap((u) => loadDemoTasks(u).map(task => ({ ...task, unit: u })));
  const openCount = tasks.filter(t => t.status === "planned").length;
  function connect() {
    window.location.hash = unit === "all" ? "crm" : "crm?organization=" + unit;
    setLive(true);
  }
  function navigate(next: string) {
    setPage(next);
    writeDemoPage(next, unit);
    setSearch("");
  }
  const metrics = [
    {
      label: "Kompanije u bazi",
      value: String(all.length),
      note: "U odabranom demo prikazu",
    },
    {
      label: "Otvorene prilike",
      value: String(open.length),
      note: "Bez realizovanih i nerealizovanih poslova",
    },
    {
      label: "Vrednost otvorenih prilika",
      value: money(total),
      note: "Potencijalna vrednost · nije prihod",
    },
    {
      label: "Aktivni zadaci",
      value: String(openCount),
      note: "Planirane demo aktivnosti",
    },
  ];
  const metricCards = (
    <div className="metrics">
      {metrics.map((m) => (
        <article className="metric" key={m.label}>
          <div className="metric-label">{m.label}</div>
          <strong>{m.value}</strong>
          <small>● {m.note}</small>
        </article>
      ))}
    </div>
  );
  const taskPanel = (
    <section className="panel"><div className="panel-heading"><h2>Planirani zadaci</h2></div>
      {tasks.filter(t => t.status === "planned").slice(0, 3).map(task => <div className="task" key={`${task.unit}-${task.id}`}><span><strong>{task.title}</strong><small>{task.unit} · {task.due_date}{task.due_time ? ` · ${task.due_time.slice(0, 5)}` : ""}</small></span></div>)}
      {!openCount && <p className="empty">Nema planiranih demo zadataka. Dodajte prvi u kalendaru.</p>}
      <div className="panel-actions"><button className="secondary-button" onClick={() => navigate("Zadaci")}>Otvori kalendar zadataka →</button></div>
    </section>
  );
  const table = (
    <section className="panel">
      <div className="panel-heading">
        <h2>Kompanije i kontakti</h2>
        <span className="tag">{rows.length} demo zapisa</span>
      </div>
      <label className="search">
        <Search size={17} />
        <input
          aria-label="Pretraga kompanija"
          placeholder="Pretraži naziv, grad ili delatnost"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </label>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Kompanija</th>
              <th>Delatnost</th>
              <th>Modul</th>
              <th>Komercijalista</th>
              <th>Faza</th>
              <th>Vrednost prilike</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.id}>
                <td>
                  <strong>{c.name}</strong>
                  <small>{c.city} · Demo zapis</small>
                </td>
                <td>{c.sector}</td>
                <td>
                  <span className="tag">{organizationName(c.unit)}</span>
                </td>
                <td>
                  {c.owner}
                  <small>Demo korisnik</small>
                </td>
                <td>
                  <span className={"stage stage-" + c.stage}>{stageLabel(c.stage)}</span>
                </td>
                <td>{money(c.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && (
          <p className="empty">Nema kompanija za ovu pretragu.</p>
        )}
      </div>
    </section>
  );
  const funnel = (
    <section className="panel">
      <div className="panel-heading">
        <h2>Prodajni levak</h2>
      </div>
      <div className="bars">
        {stages.map((stage) => {
          const count = all.filter((c) => c.stage === stage).length;
          return (
            <div className="bar-row" key={stage}>
              <div>
                <span>{stageLabel(stage)}</span>
                <strong>{count}</strong>
              </div>
              <div className="bar-track">
                <div
                  style={{
                    width: `${all.length ? (count / all.length) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <div className="panel-actions">
        <button
          className="secondary-button"
          onClick={() => navigate("Prodajni levak")}
        >
          Otvori prodajni levak →
        </button>
      </div>
    </section>
  );
  if (live || entry)
    return (
      <Workspace
        onBack={() => {
          window.location.hash = "demo/dashboard";
          setLive(false);
          setEntry(false);
        }}
        onDemo={(code: OrganizationCode) => {
          setUnit(code);
          setLive(false);
          setEntry(false);
          setPage("Početna tabla");
          setSearch("");
          writeDemoPage("Početna tabla", code);
        }}
      />
    );
  const placeholder =
    page === "Ponude"
      ? {
          icon: FileText,
          title: "Ponude za LUU, Invektu i Cenobots",
          text: "Kreiranje ponuda, obračun stavki i PDF izvoz dolaze u narednoj fazi.",
        }
      : null;
  return (
    <Shell
      organization={unit === "all" ? undefined : unit}
      page={page}
      onPage={navigate}
      search={search}
      onSearch={(value) => {
        setSearch(value);
        if (value.trim()) {
          setPage("Kompanije");
          writeDemoPage("Kompanije", unit);
        }
      }}
      onLogout={() => {
        window.location.hash = "";
        setEntry(true);
        setSearch("");
      }}
      user="Demo korisnik"
      role="Razvojni pregled"
      onConnect={connect}
    >
      {!["AI asistent", "Zadaci", "Izveštaji", "Targeti"].includes(page) && (
        <div className="page-heading">
          <div>
            <h1>
              {page === "Početna tabla"
                ? "Dobrodošli u vaš CRM!"
                : page === "Kompanije"
                  ? "Kompanije i kontakti"
                  : page}
            </h1>
            <p>
              {page === "Početna tabla"
                ? "Pregled prodaje, prilika i aktivnosti vašeg tima."
                : page === "Kompanije"
                  ? "Centralna baza kupaca i potencijalnih klijenata."
                  : "LUU × Invekta × Cenobots · zajednički prodajni prostor."}
            </p>
          </div>
          {["Početna tabla", "Kompanije"].includes(page) && (
            <button className="primary-button" onClick={connect}>
              <Plus size={16} />
              Dodaj kompaniju
            </button>
          )}
        </div>
      )}
      {page === "Početna tabla" && (
        <DailyWelcome
          name="Demo korisnik"
          recommendations={dailyRecommendations(
            Object.fromEntries(
              stages.map((stage) => [
                stage,
                all.filter((c) => c.stage === stage).length,
              ]),
            ),
            all.length,
          )}
          onNavigate={navigate}
        />
      )}
      <div className="demo-notice">
        Demo prikaz — svi klijenti i iznosi su izmišljeni. Za unos i trajno
        čuvanje otvorite povezani CRM i prijavite se.
      </div>
      {page === "Početna tabla" && (
        <>
          {metricCards}
          <div className="dashboard-grid">
            {funnel}
            {taskPanel}
          </div>
        </>
      )}
      {page === "Kompanije" && table}
      {page === "Prodajni levak" && (
        <>
          <p className="section-hint">
            Prevucite karticu u drugu kolonu ili izaberite status na kartici. Na
            telefonu koristite izbor statusa. Demo promene čuvaju se samo u ovom
            browseru.
          </p>
          {stageMessage && (
            <p className="success-message" role="status">
              {stageMessage}
            </p>
          )}
          <div className="kanban live-kanban">
            {stages.map((stage) => (
              <section
                {...drag.columnProps(stage)}
                data-stage={stage}
                className={
                  "kanban-column" + (drag.over === stage ? " drop-target" : "")
                }
                key={stage}
              >
                <h2>
                  {stageLabel(stage)}
                  <span>{all.filter((c) => c.stage === stage).length}</span>
                </h2>
                {all
                  .filter((c) => c.stage === stage)
                  .map((c) => (
                    <article
                      {...drag.cardProps(c)}
                      className={
                        "deal draggable-deal" +
                        (drag.dragged === c.id ? " dragging" : "")
                      }
                      data-demo-id={c.id}
                      key={c.id}
                    >
                      <h3>
                        <GripVertical
                          size={14}
                          className="drag-grip"
                          aria-hidden="true"
                        />
                        {c.name}
                      </h3>
                      <small>
                        {c.unit} · {c.city}
                      </small>
                      <strong>{money(c.value)}</strong>
                      {c.unit === "CENOBOTS" && <label className="stage-control">Vrsta posla
                        <select value={c.business_type ?? ""} onChange={e => {
                          const next = { ...demoTypes, [c.id]: e.target.value as BusinessType }; setDemoTypes(next);
                          try { localStorage.setItem("crm-demo-business-types-v1", JSON.stringify(next)); }
                          catch { setStageMessage("Vrsta posla važi samo tokom ovog prikaza; browser ne dozvoljava čuvanje."); }
                        }}><option value="" disabled>Izaberite vrstu posla</option>{businessTypesFor(c.unit).map(type => <option key={type} value={type}>{businessTypeLabel(type)}</option>)}</select>
                      </label>}
                      <label className="stage-control">
                        Status
                        <select
                          aria-label={"Status demo prilike " + c.name}
                          value={c.stage}
                          onChange={(e) =>
                            moveDemo(c, e.target.value as OpportunityStage)
                          }
                        >
                          {stages.map((s) => (
                            <option key={s} value={s}>{stageLabel(s)}</option>
                          ))}
                        </select>
                      </label>
                      <div>{c.owner} · Demo korisnik</div>
                    </article>
                  ))}
              </section>
            ))}
          </div>
        </>
      )}
      {page === "Targeti" && <Targets key={unit} unit={0} demo={{ organization: unit, events: activity, opportunities: all.map(c => ({ id: c.id, stage: c.stage, business_type: c.business_type })) }} />}
      {page === "Zadaci" && <TasksCalendar key={unit} unit={0} organization={unit} companies={all} />}
      {page === "Izveštaji" && <Reports key={unit} unit={0} demoItems={activity.filter(row => all.some(c => c.id === row.opportunity_id))} />}
      {page === "AI asistent" && (
        <AiAssistant
          key={unit}
          unit={0}
          organization={organizationName(unit)}
          demo
          companies={all.map((c) => ({
            id: c.id,
            name: c.name,
            address: null,
            pib: null,
            city: c.city,
            sector: c.sector,
            business_unit_id: 0,
            owner_id: 0,
            is_demo: true,
          }))}
        />
      )}
      {placeholder && (
        <section className="panel placeholder">
          <placeholder.icon size={36} />
          <h2>{placeholder.title}</h2>
          <p>{placeholder.text}</p>
          <span className="tag gray">Planirano · još nije implementirano</span>
        </section>
      )}
      <footer>
        LUU × INVEKTA × CENOBOTS <span>Demo podaci · Nema pristupa stvarnom CRM-u</span>
      </footer>
    </Shell>
  );
}
