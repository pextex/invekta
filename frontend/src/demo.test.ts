import { describe, expect, it } from "vitest";
import { selectCompanies } from "./demo";
describe("Prikaz demonstracionih kompanija", () => {
  it("razdvaja poslovne module", () => {
    for (const unit of ["LUU", "INVEKTA"] as const) {
      const result = selectCompanies(unit);
      expect(result).toHaveLength(3);
      expect(result.every((c) => c.unit === unit)).toBe(true);
    }
  });
  it("pretražuje naziv, grad i delatnost bez obzira na velika slova", () => {
    expect(selectCompanies("LUU", " NOVI SAD ")).toHaveLength(1);
    expect(selectCompanies("LUU", "hotel")).toHaveLength(1);
    expect(selectCompanies("LUU", "industrija")).toHaveLength(0);
  });
});
