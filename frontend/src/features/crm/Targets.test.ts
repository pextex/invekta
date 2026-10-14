import { expect, it } from "vitest";
import { targetPercent } from "./Targets";
import { demoTargets } from "./targetsDemo";
import { businessTypesFor } from "./businessTypes";
it("keeps the three company business categories and distinguishes missing goals from zero achievement", () => {
  expect(businessTypesFor("LUU")).toEqual(["sale"]);
  expect(businessTypesFor("INVEKTA")).toEqual(["contracted"]);
  expect(businessTypesFor("CENOBOTS")).toEqual(["sale", "leasing", "rental"]);
  expect(targetPercent(null, "100")).toBe(null);
  expect(targetPercent("100", "0")).toBe(0);
  expect(targetPercent("100", "125")).toBe(125);
});
it("counts each current realization once and credits the business type captured at realization", () => {
  const base = { id: 1, opportunity_id: 7, changed_at: "2026-10-14T12:00:00Z", company_name: "Test", title: "Prilika", amount: "55.50", actor_name: "Demo", from_stage: "Ponuda", to_stage: "Dobijeno", changes: null, business_type: "rental" };
  const data = demoTargets("2026-10", { organization: "CENOBOTS", events: [base, { ...base, id: 2, from_stage: "Dobijeno", to_stage: "Pregovori" }, { ...base, id: 3, amount: "100.25" }], opportunities: [{ id: 7, stage: "Dobijeno", business_type: "sale" }] }, { rental: "200" });
  expect(data.salespeople[0].targets.find(t => t.category === "rental")?.achieved_amount).toBe("100.25");
  expect(data.salespeople[0].targets.find(t => t.category === "sale")?.achieved_count).toBe(0);
});
