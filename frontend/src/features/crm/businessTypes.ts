export type BusinessType = "sale" | "contracted" | "leasing" | "rental";
export const businessTypeLabels: Record<BusinessType, string> = {
  sale: "Prodaja", contracted: "Ugovoren posao", leasing: "Lizing", rental: "Najam",
};
export function businessTypesFor(code: string): BusinessType[] {
  if (code === "INVEKTA") return ["contracted"];
  if (code === "CENOBOTS") return ["sale", "leasing", "rental"];
  return ["sale"];
}
export const businessTypeLabel = (type: string | null | undefined) => type && type in businessTypeLabels ? businessTypeLabels[type as BusinessType] : "Vrsta posla nije odabrana";
