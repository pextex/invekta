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
  ListTodo,
  Plus,
  Search,
  Sparkles,
  FileText,
  ChartNoAxesCombined,
  UsersRound,
} from "lucide-react";
import Workspace from "./Workspace";
import Shell from "./Shell";
import { selectCompanies, money, stages, type Unit } from "./demo";

type Scope = Unit | "all";
const demoTasks = {
  CENOBOTS: [
    "Pozvati Demo partnera Alfa",
    "Pripremiti ponudu za Demo partnera Beta",
    "Dogovoriti sastanak sa Demo partnerom Gama",
  ],
  LUU: [
    "Pozvati Demo Hotel Dunav",
    "Proveriti potrebe Demo Studija Javor",
    "Pripremiti sledeći sastanak",
  ],
  INVEKTA: [
    "Dogovoriti obilazak Demo Poslovnog centra",
    "Kontaktirati Demo Park Sever",
    "Pripremiti pregled usluga",
  ],
};
export default function App() {
  const [live, setLive] = useState(() => isCrmRoute());
  const [entry, setEntry] = useState(
    () => !window.location.hash.startsWith("#demo"),
  );
  const [unit, setUnit] = useState<Scope>("all");
  const [page, setPage] = useState(readDemoPage);
  const [stageOverrides, setStageOverrides] = useState(loadDemoStages);
  const [stageMessage, setStageMessage] = useState("");
  const [search, setSearch] = useState("");
  const [done, setDone] = useState<string[]>([]);
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
    stage: stageOverrides[c.id] ?? c.stage,
  }));
  const all = selectCompanies(unit).map((c) => ({
    ...c,
    stage: stageOverrides[c.id] ?? c.stage,
  }));
  const open = all.filter(
    (c) => c.stage !== "Dobijeno" && c.stage !== "Izgubljeno",
  );
  const total = open.reduce((sum, c) => sum + c.value, 0);
  function moveDemo(item: (typeof all)[number], stage: OpportunityStage) {
    if (item.stage === stage) return;
    const next = { ...stageOverrides, [item.id]: stage };
    setStageOverrides(next);
    setStageMessage(
      saveDemoStages(next)
        ? "Demo status je sačuvan u ovom browseru. Ne upisuje se u CRM bazu."
        : "Status je promenjen za ovaj prikaz. Browser ne dozvoljava lokalno čuvanje.",
    );
  }
  const drag = useStageDragDrop(all, false, moveDemo);
  const tasks = (
    unit === "all" ? organizations.map((org) => org.code) : [unit]
  ).flatMap((u) => demoTasks[u].map((title) => ({ title, unit: u })));
  const openCount = tasks.filter((t) => !done.includes(t.title)).length;
  function connect() {
    window.location.hash = unit === "all" ? "crm" : "crm?organization=" + unit;
    setLive(true);
  }
  function navigate(next: string) {
    setPage(next);
    writeDemoPage(next);
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
      note: "Bez dobijenih i izgubljenih poslova",
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
    <section className="panel">
      <div className="panel-heading">
        <h2>Aktivnosti tima</h2>
      </div>
      <div className="task-list">
        {(page === "Početna tabla" ? tasks.slice(0, 3) : tasks).map(
          (task, i) => (
            <label className="task" key={task.title}>
              <input
                type="checkbox"
                checked={done.includes(task.title)}
                onChange={() =>
                  setDone(
                    done.includes(task.title)
                      ? done.filter((t) => t !== task.title)
                      : [...done, task.title],
                  )
                }
              />
              <span className={done.includes(task.title) ? "completed" : ""}>
                <strong>{task.title}</strong>
                <small>
                  {task.unit} · {i % 3 === 0 ? "Danas" : "Sledeće nedelje"} ·
                  Demo korisnik
                </small>
              </span>
              <span className={done.includes(task.title) ? "tag green" : "tag"}>
                {done.includes(task.title) ? "Završeno" : "Planirano"}
              </span>
            </label>
          ),
        )}
      </div>
      {page === "Početna tabla" && (
        <div className="panel-actions">
          <button
            className="secondary-button"
            onClick={() => navigate("Zadaci")}
          >
            Svi zadaci →
          </button>
        </div>
      )}
      <p className="panel-note">
        Demo zadaci · resetuju se osvežavanjem stranice.
      </p>
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
                  <span className={"stage stage-" + c.stage}>{c.stage}</span>
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
                <span>{stage}</span>
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
          navigate("Početna tabla");
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
      : page === "AI asistent"
        ? {
            icon: Sparkles,
            title: "AI Sales Assistant",
            text: "Pretraga leadova, proverljivi izvori i predlozi poruka dolaze kasnije. U ovoj verziji nema AI poziva niti slanja poruka.",
          }
        : null;
  return (
    <Shell
      page={page}
      onPage={navigate}
      search={search}
      onSearch={(value) => {
        setSearch(value);
        if (value.trim()) {
          setPage("Kompanije");
          writeDemoPage("Kompanije");
        }
      }}
      unit={unit}
      units={[
        { value: "all", label: "Sve demo kompanije" },
        { value: "LUU", label: "LUU" },
        { value: "INVEKTA", label: "Invekta" },
        { value: "CENOBOTS", label: "Cenobots" },
      ]}
      onUnit={(value) => {
        setUnit(value as Scope);
        setSearch("");
      }}
      user="Demo korisnik"
      role="Razvojni pregled"
      onConnect={connect}
    >
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
        {["Početna tabla", "Kompanije", "Novi klijenti"].includes(page) && (
          <button className="primary-button" onClick={connect}>
            <Plus size={16} />
            {page === "Početna tabla" ? "Novi klijent" : "Dodaj kompaniju"}
          </button>
        )}
      </div>
      {page === "Početna tabla" && (
        <div className="sales-banner">
          <div>
            <h2>Jedna platforma. Tri prodajna tima.</h2>
            <p>
              Od pronalaženja klijenata do ponude, ugovora i ponovljene prodaje.
            </p>
          </div>
          <ArrowUpRight size={40} />
        </div>
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
      {page === "Novi klijenti" && (
        <>
          <section className="panel feature-note">
            <UsersRound size={23} />
            <div>
              <h2>Potencijalni klijenti</h2>
              <p>
                Ovo su demo kompanije. Automatsko pronalaženje i kvalifikacija
                novih leadova još nisu povezani.
              </p>
            </div>
          </section>
          {table}
        </>
      )}
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
                  {stage}
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
                            <option key={s}>{s}</option>
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
      {page === "Zadaci" && taskPanel}
      {page === "Izveštaji" && (
        <>
          {metricCards}
          <div className="dashboard-grid">
            {funnel}
            <section className="panel">
              <div className="panel-heading">
                <h2>Vrednost po fazama</h2>
                <ChartNoAxesCombined size={20} />
              </div>
              <div className="bars">
                {stages.map((stage) => (
                  <div className="bar-row" key={stage}>
                    <div>
                      <span>{stage}</span>
                      <strong>
                        {money(
                          all
                            .filter((c) => c.stage === stage)
                            .reduce((s, c) => s + c.value, 0),
                        )}
                      </strong>
                    </div>
                  </div>
                ))}
              </div>
              <p className="panel-note">
                Izveštaj iz demo zapisa, bez stvarnih prodajnih rezultata.
              </p>
            </section>
          </div>
        </>
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
        LUU × INVEKTA × CENOBOTS <span>Razvojna verzija 0.4 · Demo podaci</span>
      </footer>
    </Shell>
  );
}
