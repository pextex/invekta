import { expect, it } from "vitest";
import { reportPeriod } from "./Reports";
it("keeps daily selection and includes the last day of every selected month", () => {
  expect(reportPeriod("day", "2026-10-14")).toEqual({ from: "2026-10-14", to: "2026-10-14" });
  expect(reportPeriod("month", "2026-10")).toEqual({ from: "2026-10-01", to: "2026-10-31" });
  expect(reportPeriod("month", "2024-02").to).toBe("2024-02-29");
  expect(reportPeriod("month", "2026-02").to).toBe("2026-02-28");
  expect(reportPeriod("month", "2026-12").to).toBe("2026-12-31");
});

import { summarizeChanges, type Change } from "./Reports";
it("counts every event while counting each affected opportunity once", () => {
  const base: Change = { id: 1, changed_at: "2026-10-14T12:00:00Z", company_name: "Test", opportunity_id: 7, title: "Prilika", amount: "123.45", actor_name: "Ana", from_stage: null, to_stage: "Novi lead", changes: null };
  const result = summarizeChanges([
    base,
    { ...base, id: 2, from_stage: "Novi lead", to_stage: "Ponuda" },
    { ...base, id: 3, from_stage: "Ponuda", to_stage: "Dobijeno" },
    { ...base, id: 4, from_stage: "Dobijeno", to_stage: "Dobijeno" },
  ]);
  expect(result.total).toBe(4);
  expect(result.opportunity_count).toBe(1);
  expect(result.created_count).toBe(1);
  expect(result.stage_change_count).toBe(2);
  expect(result.edit_count).toBe(1);
  expect(result.realized_count).toBe(1);
});
