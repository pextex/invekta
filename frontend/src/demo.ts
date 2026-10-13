export type Unit = "LUU" | "INVEKTA";
export type Company = {
  id: number;
  name: string;
  city: string;
  sector: string;
  owner: string;
  value: number;
  stage: string;
  unit: Unit;
};
export const companies: Company[] = [
  {
    id: 1,
    name: "Demo Hotel Dunav",
    city: "Beograd",
    sector: "Hotelijerstvo",
    owner: "Ana",
    value: 185000,
    stage: "Ponuda",
    unit: "LUU",
  },
  {
    id: 2,
    name: "Demo Studio Javor",
    city: "Novi Sad",
    sector: "Kancelarije",
    owner: "Marko",
    value: 72000,
    stage: "Kontakt",
    unit: "LUU",
  },
  {
    id: 3,
    name: "Demo Restoran Lipa",
    city: "Niš",
    sector: "Ugostiteljstvo",
    owner: "Ana",
    value: 96000,
    stage: "Pregovori",
    unit: "LUU",
  },
  {
    id: 4,
    name: "Demo Poslovni centar",
    city: "Beograd",
    sector: "Poslovni objekti",
    owner: "Jelena",
    value: 420000,
    stage: "Ponuda",
    unit: "INVEKTA",
  },
  {
    id: 5,
    name: "Demo Park Sever",
    city: "Novi Sad",
    sector: "Industrija",
    owner: "Ivan",
    value: 280000,
    stage: "Kontakt",
    unit: "INVEKTA",
  },
  {
    id: 6,
    name: "Demo Tržni centar",
    city: "Niš",
    sector: "Maloprodaja",
    owner: "Jelena",
    value: 350000,
    stage: "Pregovori",
    unit: "INVEKTA",
  },
];
export const stages = ["Kontakt", "Ponuda", "Pregovori"];
export function selectCompanies(unit: Unit, search = "") {
  const term = search.trim().toLocaleLowerCase("sr");
  return companies.filter(
    (c) =>
      c.unit === unit &&
      `${c.name} ${c.city} ${c.sector}`.toLocaleLowerCase("sr").includes(term),
  );
}
export const money = (value: number) =>
  new Intl.NumberFormat("sr-RS", {
    style: "currency",
    currency: "RSD",
    maximumFractionDigits: 0,
  }).format(value);
