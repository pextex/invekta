import { isOrganizationCode } from "../organizations";
const pages: Record<string, string> = {
  companies: "Kompanije",
  orders: "Porudžbine",
  pipeline: "Prodajni levak",
  dashboard: "Početna tabla",
  leads: "Kompanije",
  quotes: "Ponude",
  tasks: "Zadaci",
  reports: "Izveštaji",
  targets: "Targeti",
  ai: "Invekta AI",
  history: "Hronologija promena - log",
  settings: "Podešavanja",
};
export const isCrmRoute = () => /^#crm(?:[/?]|$)/.test(window.location.hash);
export function readRoute() {
  const [path, query = ""] = window.location.hash.slice(1).split("?");
  const params = new URLSearchParams(query);
  const positive = (value: string | null) => {
    const n = Number(value);
    return Number.isSafeInteger(n) && n > 0 ? n : undefined;
  };
  return {
    page: pages[path.split("/")[1]] ?? "Kompanije",
    organization: isOrganizationCode(params.get("organization"))
      ? (params.get(
          "organization",
        ) as import("../organizations").OrganizationCode)
      : undefined,
    unit: positive(params.get("unit")),
    company: positive(params.get("company")),
  };
}
export function writeRoute(
  page: string,
  unit: number,
  company?: number,
  replace = false,
) {
  const code =
    Object.entries(pages).find(([, title]) => title === page)?.[0] ??
    "companies";
  const params = new URLSearchParams({ unit: String(unit) });
  if (company) params.set("company", String(company));
  const hash = `#crm/${code}?${params}`;
  if (replace) window.history.replaceState(null, "", hash);
  else window.location.hash = hash;
}
