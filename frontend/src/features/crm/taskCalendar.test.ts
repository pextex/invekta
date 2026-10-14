import { expect, it } from "vitest";
import { calendarDays, shiftMonth } from "./taskCalendar";
it("uses Monday-first calendar including adjacent days across month and year boundaries", () => {
  const days = calendarDays("2026-10");
  expect(days).toHaveLength(42);
  expect(days[0]).toBe("2026-09-28");
  expect(days[41]).toBe("2026-11-08");
  expect(new Set(days).size).toBe(42);
  expect(calendarDays("2024-02")).toContain("2024-02-29");
  expect(shiftMonth("2026-12", 1)).toBe("2027-01");
  expect(shiftMonth("2026-01", -1)).toBe("2025-12");
});
