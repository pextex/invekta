import Workspace from "./Workspace";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Building2,
  Columns3,
  ListTodo,
  Sparkles,
  Settings,
  ArrowUpRight,
  Search,
  Menu,
  X,
  ChevronRight,
  FlaskConical,
  Package,
  BriefcaseBusiness,
} from "lucide-react";
import { selectCompanies, money, stages, type Unit } from "./demo";
const navigation = [
  { title: "Pregled", icon: LayoutDashboard },
  { title: "Kompanije", icon: Building2 },
  { title: "Prodajni levak", icon: Columns3 },
  { title: "Zadaci", icon: ListTodo },
  { title: "Poslovni modul", icon: BriefcaseBusiness },
  { title: "AI asistent", icon: Sparkles },
  { title: "Podešavanja", icon: Settings },
];
export default function App() {
  const [live, setLive] = useState(() => window.location.hash === "#crm");
  useEffect(() => {
    const onHash = () => setLive(window.location.hash === "#crm");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const [unit, setUnit] = useState<Unit>("LUU");
  const [page, setPage] = useState("Pregled");
  const [search, setSearch] = useState("");
  const [mobile, setMobile] = useState(false);
  const [done, setDone] = useState<string[]>([]);
  const rows = selectCompanies(unit, search);
  const all = selectCompanies(unit);
  const total = all.reduce((sum, c) => sum + c.value, 0);
  const tasks =
    unit === "LUU"
      ? [
          "Pozvati Demo Hotel Dunav",
          "Proveriti potrebe Demo Studija Javor",
          "Pripremiti sledeći sastanak",
        ]
      : [
          "Dogovoriti obilazak Demo Poslovnog centra",
          "Kontaktirati Demo Park Sever",
          "Pripremiti pregled usluga",
        ];
  const taskPanel = (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Sledeće aktivnosti</h2>
          <p>Demonstracioni zadaci · promene važe tokom ovog prikaza</p>
        </div>
        <ListTodo size={20} />
      </div>
      {tasks.map((task, i) => (
        <label className="task" key={task}>
          <input
            type="checkbox"
            checked={done.includes(task)}
            onChange={() =>
              setDone(
                done.includes(task)
                  ? done.filter((t) => t !== task)
                  : [...done, task],
              )
            }
          />
          <span className={done.includes(task) ? "completed" : ""}>
            {task}
            <small>
              {i === 0 ? "Danas" : "Sledeće nedelje"} · Demo korisnik
            </small>
          </span>
          <span className="tag">{i === 0 ? "Prioritet" : "Planirano"}</span>
        </label>
      ))}
    </section>
  );
  const table = (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Aktivne kompanije</h2>
          <p>Primeri zapisa za modul {unit}</p>
        </div>
        <span className="tag">{rows.length} zapisa</span>
      </div>
      <label className="search">
        <Search size={18} />
        <input
          aria-label="Pretraga kompanija"
          placeholder="Pretraži kompanije, grad ili delatnost…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </label>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Kompanija</th>
              <th>Odgovorna osoba</th>
              <th>Faza</th>
              <th>Vrednost prilike</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.id}>
                <td>
                  <strong>{c.name}</strong>
                  <small>
                    {c.city} · {c.sector}
                  </small>
                </td>
                <td>
                  {c.owner} <small>Demo korisnik</small>
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
  if (live)
    return (
      <Workspace
        onBack={() => {
          window.location.hash = "demo";
          setLive(false);
        }}
      />
    );
  return (
    <div className="app">
      <aside className={mobile ? "sidebar open" : "sidebar"}>
        <a
          href="#"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            setPage("Pregled");
            setMobile(false);
          }}
        >
          <span className="brand-mark">L×I</span>
          <span>
            LUU × INVEKTA<small>SALES WORKSPACE</small>
          </span>
        </a>
        <button
          className="close-mobile"
          onClick={() => setMobile(false)}
          aria-label="Zatvori meni"
        >
          <X />
        </button>
        <div className="unit-label">POSLOVNA JEDINICA</div>
        <div className="unit-switch">
          {(["LUU", "INVEKTA"] as Unit[]).map((u) => (
            <button
              aria-pressed={unit === u}
              className={unit === u ? "selected" : ""}
              key={u}
              onClick={() => {
                setUnit(u);
                setSearch("");
              }}
            >
              {u}
            </button>
          ))}
        </div>
        <div className="nav-label">RADNI PROSTOR</div>
        <nav>
          {navigation.map(({ title, icon: Icon }) => (
            <button
              key={title}
              className={page === title ? "active" : ""}
              onClick={() => {
                setPage(title);
                setSearch("");
                setMobile(false);
              }}
            >
              <Icon size={19} />
              {title}
              {page === title && <ChevronRight size={15} />}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <Sparkles size={22} />
          <strong>Prodaja sa jasnim fokusom.</strong>
          <p>Jedna platforma. Dva poslovna modula.</p>
          <span>FAZA 1 · DEMO</span>
        </div>
        <div className="profile">
          <span className="avatar">DK</span>
          <div>
            Demo korisnik<small>Razvojni pregled</small>
          </div>
        </div>
      </aside>
      {mobile && (
        <button
          className="backdrop"
          aria-label="Zatvori navigaciju"
          onClick={() => setMobile(false)}
        />
      )}
      <main>
        <header>
          <div className="breadcrumb">
            <button
              className="mobile-menu"
              onClick={() => setMobile(true)}
              aria-label="Otvori meni"
            >
              <Menu />
            </button>
            <span>Radni prostor</span>
            <ChevronRight size={14} />
            <strong>{unit}</strong>
          </div>
          <button
            className="primary-button"
            onClick={() => {
              window.location.hash = "crm";
              setLive(true);
            }}
          >
            Otvori povezani CRM <ArrowUpRight size={15} />
          </button>
        </header>
        <div className="content">
          <div className="demo-notice">
            <FlaskConical size={18} />
            <span>
              Demo okruženje — svi prikazani klijenti i iznosi su izmišljeni.
              Ovaj demo ne čuva izmene. Za prijavu i trajnu bazu otvorite
              povezani CRM.
            </span>
          </div>
          <div className="page-heading">
            <div>
              <div className="eyebrow">{unit} / PRODAJNI TIM</div>
              <h1>{page === "Pregled" ? "Vaš prodajni pregled" : page}</h1>
              <p>
                {page === "Pregled"
                  ? "Sve važne prilike i aktivnosti, na jednom mestu."
                  : "Zajednički CRM, prilagođen vašem poslovanju."}
              </p>
            </div>
            <span className="heading-badge">
              {unit === "LUU" ? "Proizvodi i oprema" : "Facility management"}
            </span>
          </div>
          {page === "Pregled" && (
            <>
              <div className="metrics">
                {[
                  {
                    label: "Aktivne kompanije",
                    value: String(all.length),
                    note: "U odabranoj poslovnoj jedinici",
                    icon: Building2,
                  },
                  {
                    label: "Otvorene prilike",
                    value: String(all.length),
                    note: "Demonstracioni prodajni levak",
                    icon: Columns3,
                  },
                  {
                    label: "Vrednost prilika",
                    value: money(total),
                    note: "Potencijalna vrednost · nije prihod",
                    icon: ArrowUpRight,
                  },
                  {
                    label: "Otvoreni zadaci",
                    value: String(
                      tasks.filter((t) => !done.includes(t)).length,
                    ),
                    note: "Planirane prodajne aktivnosti",
                    icon: ListTodo,
                  },
                ].map(({ label, value, note, icon: Icon }) => (
                  <article className="metric" key={label}>
                    <div>
                      {label}
                      <Icon size={20} />
                    </div>
                    <strong>{value}</strong>
                    <small>{note}</small>
                  </article>
                ))}
              </div>
              <div className="dashboard-grid">
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Prodajni levak</h2>
                      <p>Raspodela potencijalne vrednosti po fazama</p>
                    </div>
                    <button
                      className="text-button"
                      onClick={() => setPage("Prodajni levak")}
                    >
                      Otvori levak <ArrowUpRight size={16} />
                    </button>
                  </div>
                  <div className="bars">
                    {stages.map((stage, i) => {
                      const value = all
                        .filter((c) => c.stage === stage)
                        .reduce((sum, c) => sum + c.value, 0);
                      return (
                        <div className="bar-row" key={stage}>
                          <div>
                            <span>{stage}</span>
                            <strong>{money(value)}</strong>
                          </div>
                          <div className="bar-track">
                            <div
                              style={{
                                width: `${(value / total) * 100}%`,
                                background: ["#a8c6b5", "#568d7a", "#254e47"][
                                  i
                                ],
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="panel-footer">
                    3 otvorene prilike <span>Demo podaci</span>
                  </div>
                </section>
                {taskPanel}
              </div>
              {table}
            </>
          )}
          {page === "Kompanije" && table}
          {page === "Prodajni levak" && (
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
                        <span className="eyebrow">DEMO PRILIKA</span>
                        <h3>{c.name}</h3>
                        <p>
                          {c.sector} · {c.city}
                        </p>
                        <strong>{money(c.value)}</strong>
                        <div>{c.owner} · Demo korisnik</div>
                      </article>
                    ))}
                </section>
              ))}
            </div>
          )}
          {page === "Zadaci" && taskPanel}
          {page === "Poslovni modul" && (
            <section className="panel placeholder">
              <Package size={36} />
              <h2>
                {unit === "LUU"
                  ? "LUU — proizvodi i potrošnja"
                  : "INVEKTA — usluge i objekti"}
              </h2>
              <p>
                {unit === "LUU"
                  ? "Katalog proizvoda, cenovnici, ponude i kalkulator potrošnje planirani su za fazu 3."
                  : "Usluge, poslovni objekti, tenderi i ugovori planirani su za fazu 3."}
              </p>
              <span className="tag">Planirano · još nije implementirano</span>
            </section>
          )}
          {page === "AI asistent" && (
            <section className="panel placeholder">
              <Sparkles size={36} />
              <h2>Vaš budući prodajni asistent</h2>
              <p>
                Pretraga leadova, proverljivi izvori i nacrti prodajnih poruka
                dolaze u fazi 5. Trenutno nema AI poziva niti slanja poruka.
              </p>
              <span className="tag">Planirano · još nije implementirano</span>
            </section>
          )}
          {page === "Podešavanja" && (
            <section className="panel placeholder">
              <Settings size={36} />
              <h2>Pristup i poslovne jedinice</h2>
              <p>
                Ovaj prikaz nema autentifikaciju. Izbor modula služi
                demonstraciji interfejsa. Backend kontrola pristupa biće uvedena
                pre unosa stvarnih podataka.
              </p>
              <span className="tag">Sledeći korak · autentifikacija</span>
            </section>
          )}
          <footer>
            LUU × INVEKTA <span>Osnova CRM platforme · Verzija 0.1</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
