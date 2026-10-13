export const organizations = [
  {
    code: "LUU",
    name: "LUU",
    initials: "LU",
    website: "https://luu.rs/",
    domain: "luu.rs",
    accent: "#14966d",
  },
  {
    code: "INVEKTA",
    name: "Invekta",
    initials: "IN",
    website: "https://invekta.rs/",
    domain: "invekta.rs",
    accent: "#2868e8",
  },
  {
    code: "CENOBOTS",
    name: "Cenobots",
    initials: "CB",
    website: "https://cenobots.rs/",
    domain: "cenobots.rs",
    accent: "#7553d6",
  },
] as const;
export type OrganizationCode = (typeof organizations)[number]["code"];
export const organizationName = (code: string) =>
  organizations.find((org) => org.code === code)?.name ?? code;
export const isOrganizationCode = (value: unknown): value is OrganizationCode =>
  organizations.some((org) => org.code === value);
