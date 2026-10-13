import { organizations, type OrganizationCode } from "./organizations";
import { type CSSProperties, type ReactNode } from "react";
import {
  LayoutDashboard,
  Building2,
  Columns3,
  ListTodo,
  Sparkles,
  Settings,
  Search,
  UsersRound,
  FileText,
  ChartNoAxesCombined,
  UserRound,
  ArrowUpRight,
  LogOut,
} from "lucide-react";

export const navigation = [
  { title: "Početna tabla", icon: LayoutDashboard },
  { title: "Novi klijenti", icon: UsersRound },
  { title: "Kompanije", icon: Building2 },
  { title: "Prodajni levak", icon: Columns3 },
  { title: "Ponude", icon: FileText },
  { title: "Zadaci", icon: ListTodo },
  { title: "Izveštaji", icon: ChartNoAxesCombined },
  { title: "AI asistent", icon: Sparkles },
];
type Props = {
  organization?: OrganizationCode;
  page: string;
  onPage: (page: string) => void;
  search?: string;
  onSearch?: (value: string) => void;
  user: string;
  role: string;
  connected?: boolean;
  busy?: boolean;
  onConnect?: () => void;
  onBack?: () => void;
  onLogout?: () => void;
  children: ReactNode;
};
export default function Shell({
  organization,
  page,
  onPage,
  search = "",
  onSearch,
  user,
  role,
  connected = false,
  busy = false,
  onConnect,
  onBack,
  onLogout,
  children,
}: Props) {
  function navigate(next: string) {
    onPage(next);
  }
  const brand = organizations.find((org) => org.code === organization);
  return (
    <div className="app" data-organization={brand?.code} style={brand ? ({ "--blue": brand.accent, "--nav": brand.nav, "--bg": brand.background } as CSSProperties) : undefined}>
      <aside className="sidebar">
        <a
          className="brand"
          href={connected ? "#crm" : "#demo"}
          onClick={(e) => {
            e.preventDefault();
            navigate(connected ? "Kompanije" : "Početna tabla");
          }}
          aria-label={`${brand?.name ?? "CRM"}, početna stranica`}
        >
          <div>{brand ? <img className="brand-logo" src={brand.logo} alt={brand.name + " logo"} /> : "CRM"}<small className="workspace-brand-label">Prodajni CRM</small></div>
        </a>
        <div className="navigation-area">
          <nav aria-label="Glavna navigacija">
            {navigation.map(({ title, icon: Icon }) => (
              <button
                key={title}
                disabled={busy}
                aria-current={page === title ? "page" : undefined}
                className={page === title ? "active" : ""}
                onClick={() => navigate(title)}
              >
                <Icon size={16} />
                {title}
              </button>
            ))}
          </nav>
          {connected && (
            <nav className="settings-nav" aria-label="Podešavanja">
              <button
                className={page === "Podešavanja" ? "active" : ""}
                onClick={() => navigate("Podešavanja")}
              >
                <Settings size={16} />
                Podešavanja
              </button>
            </nav>
          )}
        </div>
        <div className="sidebar-status">
          <span>● {connected ? "Razvojni CRM" : "Demo režim"}</span>
          <small>
            {connected
              ? "Pristup prema vašim ovlašćenjima"
              : "Bez stvarnih podataka klijenata"}
          </small>
          {onBack && <button onClick={onBack}>← Demo pregled</button>}
        </div>
      </aside>
      <main>
        <header className="topbar">
          <label className="global-search">
            <Search size={16} />
            <input
              disabled={busy || !onSearch}
              aria-label="Globalna pretraga kompanija"
              placeholder="Pretraži kompanije i delatnosti…"
              value={search}
              onChange={(e) => onSearch?.(e.target.value)}
            />
          </label>
          <div className="header-controls">
            <span
              className={
                connected ? "demo-badge connected-badge" : "demo-badge"
              }
            >
              {connected ? "RAZVOJ" : "DEMO"}
            </span>
            <div className="header-user">
              <UserRound size={16} />
              <div>
                {user}
                <strong>{role}</strong>
              </div>
            </div>
            {onConnect && (
              <button
                className="primary-button connect-button"
                onClick={onConnect}
              >
                Otvori povezani CRM <ArrowUpRight size={14} />
              </button>
            )}
            {onBack && (
              <button className="mobile-back text-button" onClick={onBack}>
                Demo pregled
              </button>
            )}
            {onLogout && (
              <button
                className="logout-button"
                disabled={busy}
                onClick={onLogout}
                aria-label="Odjava"
              >
                <LogOut size={18} />
              </button>
            )}
          </div>
        </header>
        <div className="content">{children}</div>
      </main>
    </div>
  );
}
