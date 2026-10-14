import luuLogo from "./assets/luu-logo-web.png";
import invektaLogo from "./assets/invekta-logo-web.png";
import cenobotsLogo from "./assets/cenobots-logo-web.png";
export const organizations = [
  {
    code: "LUU",
    logo: luuLogo,
    name: "LUU",
    initials: "LU",
    website: "https://luu.rs/",
    domain: "luu.rs",
    accent: "#f6d451",
    nav: "#383a3c",
    background: "#faf9f3",
  },
  {
    code: "INVEKTA",
    logo: invektaLogo,
    name: "Invekta",
    initials: "IN",
    website: "https://invekta.rs/",
    domain: "invekta.rs",
    accent: "#34349a",
    nav: "#202464",
    background: "#f3f6fb",
  },
  {
    code: "CENOBOTS",
    logo: cenobotsLogo,
    name: "Cenobots",
    initials: "CB",
    website: "https://cenobots.rs/",
    domain: "cenobots.rs",
    accent: "#22272c",
    nav: "#090d10",
    background: "#f4f5f6",
  },
] as const;
export type OrganizationCode = (typeof organizations)[number]["code"];
export const organizationName = (code: string) =>
  organizations.find((org) => org.code === code)?.name ?? code;
export const isOrganizationCode = (value: unknown): value is OrganizationCode =>
  organizations.some((org) => org.code === value);
