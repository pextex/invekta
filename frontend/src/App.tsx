import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  ListTodo,
  Plus,
  Search,
  Sparkles,
  FileText,
  Package,
  BriefcaseBusiness,
  ChartNoAxesCombined,
  UsersRound,
} from "lucide-react";
import Workspace from "./Workspace";
import Shell from "./Shell";
import { selectCompanies, money, stages, type Unit } from "./demo";

type Scope = Unit | "all";
const demoTasks = {
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
  const [live, setLive] = useState(() => window.location.hash === "#crm");
  const [unit, setUnit] = useState<Scope>("all");
  const [page, setPage] = useState("Početna tabla");
  const [search, setSearch] = useState("");
  const [done, setDone] = useState<string[]>([]);
  useEffect(() => {
    const onHash = () => setLive(window.location.hash === "#crm");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const rows = selectCompanies(unit, search);
  const all = selectCompanies(unit);
  const total = all.reduce((sum, c) => sum + c.value, 0);
  const tasks = (
    unit === "all" ? (["LUU", "INVEKTA"] as Unit[]) : [unit]
  ).flatMap((u) => demoTasks[u].map((title) => ({ title, unit: u })));
  const openCount = tasks.filter((t) => !done.includes(t.title)).length;
  function connect() {
    window.location.hash = "crm";
    setLive(true);
  }
  function navigate(next: string) {
    setPage(next);
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
      value: String(all.length),
      note: "U demonstracionom procesu",
    },
    {
      label: "Vrednost prilika",
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
                  <span className="tag">
                    {c.unit === "LUU" ? "LUU" : "Invekta"}
                  </span>
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
  if (live)
    return (
      <Workspace
        onBack={() => {
          window.location.hash = "demo";
          setLive(false);
        }}
      />
    );
  const placeholder =
    page === "Ponude"
      ? {
          icon: FileText,
          title: "Ponude za LUU i Invektu",
          text: "Kreiranje ponuda, obračun stavki i PDF izvoz dolaze u narednoj fazi.",
        }
      : page === "AI asistent"
        ? {
            icon: Sparkles,
            title: "AI Sales Assistant",
            text: "Pretraga leadova, proverljivi izvori i predlozi poruka dolaze kasnije. U ovoj verziji nema AI poziva niti slanja poruka.",
          }
        : page === "LUU proizvodi"
          ? {
              icon: Package,
              title: "LUU — katalog proizvoda",
              text: "Proizvodi, cenovnici i kalkulator potrošnje biće povezani sa bazom u fazi poslovnih modula.",
            }
          : page === "Invekta usluge"
            ? {
                icon: BriefcaseBusiness,
                title: "Invekta — katalog usluga",
                text: "Usluge, poslovni objekti, tenderi i ugovori planirani su za fazu poslovnih modula.",
              }
            : null;
  return (
    <Shell
      page={page}
      onPage={navigate}
      search={search}
      onSearch={(value) => {
        setSearch(value);
        if (value.trim()) setPage("Kompanije");
      }}
      unit={unit}
      units={[
        { value: "all", label: "Sve demo kompanije" },
        { value: "LUU", label: "LUU" },
        { value: "INVEKTA", label: "Invekta" },
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
                : "LUU × Invekta · zajednički prodajni prostor."}
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
            <h2>Jedna platforma. Dva prodajna tima.</h2>
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
            Demonstracioni prikaz trenutnih faza. Zasebne prodajne prilike i
            njihovo upravljanje slede u narednom koraku.
          </p>
          <div className="kanban">
            {stages.map((stage) => (
              <section className="kanban-column" key={stage}>
                <h2>
                  {stage}
                  <span>{all.filter((c) => c.stage === stage).length}</span>
                </h2>
                {all
                  .filter((c) => c.stage === stage)
                  .map((c) => (
                    <article className="deal" key={c.id}>
                      <h3>{c.name}</h3>
                      <small>
                        {c.unit} · {c.city}
                      </small>
                      <strong>{money(c.value)}</strong>
                      <span className={"stage stage-" + stage}>{stage}</span>
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
        LUU × INVEKTA <span>Razvojna verzija 0.2 · Demo podaci</span>
      </footer>
    </Shell>
  );
}
