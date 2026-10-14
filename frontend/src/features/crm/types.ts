export type Unit = { id: number; code: string; role: string };
export type User = { name: string; units: Unit[]; is_platform_admin: boolean };
export type Company = {
  id: number;
  business_unit_id: number;
  owner_id: number;
  name: string;
  address: string | null;
  pib: string | null;
  city: string;
  sector: string;
  is_demo: boolean;
};
export type ContactForm = { name: string; position: string; phone: string; email: string };
export type CompanyForm = { name: string; address: string; pib: string; city: string; sector: string; contacts?: ContactForm[] };
export type Contact = {
  id: number;
  company_id: number;
  business_unit_id: number;
  name: string;
  position: string | null;
  email: string | null;
  phone: string | null;
  is_demo: boolean;
};
export const opportunityStages = [
  "Novi lead",
  "Kontaktiran",
  "Sastanak",
  "Ponuda",
  "Pregovori",
  "Dobijeno",
  "Izgubljeno",
] as const;
export type OpportunityStage = (typeof opportunityStages)[number];
export type Opportunity = {
  id: number;
  company_id: number;
  company_name: string;
  business_unit_id: number;
  owner_name: string;
  title: string;
  amount: string;
  stage: OpportunityStage;
  expected_close_date: string | null;
  notes: string | null;
  is_demo: boolean;
  version: number;
  updated_at: string;
};
export type OpportunityPage = { items: Opportunity[]; total: number };
export type StageChange = {
  id: number;
  from_stage: string | null;
  to_stage: string;
  actor_name: string;
  changed_at: string;
};
export type Summary = {
  company_count: number;
  contact_count: number;
  opportunity_count: number;
  open_count: number;
  open_value: string;
  won_count: number;
  won_value: string;
  stages: Record<OpportunityStage, number>;
};
export const formatAmount = (value: string | number) =>
  new Intl.NumberFormat("sr-RS", {
    style: "currency",
    currency: "RSD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(Number(value));
export const formatDate = (value: string) =>
  new Intl.DateTimeFormat("sr-RS", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value + "T12:00:00"));
export const formatTimestamp = (value: string) =>
  new Intl.DateTimeFormat("sr-RS", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "Europe/Belgrade",
  }).format(new Date(value));

export function stageLabel(stage: string): string {
  if (stage === "Dobijeno") return "Realizovano";
  if (stage === "Izgubljeno") return "Nije realizovano";
  return stage;
}
