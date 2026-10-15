import { expect, it } from "vitest";
import { todayTasks } from "./TodayTasks";
import type { CalendarTask } from "./taskCalendar";
it("shows only the selected day and prioritizes planned tasks by time", () => {
  const base: CalendarTask = { id: 1, title: "Zadatak", due_date: "2026-10-15", due_time: "09:00", status: "planned", notes: null, company_id: null, company_name: null, owner_id: 1, owner_name: "Test", business_unit_id: 1, version: 1 };
  const rows = todayTasks([base, { ...base, id: 2, due_time: "08:00", status: "done" }, { ...base, id: 3, due_date: "2026-10-16" }, { ...base, id: 4, due_time: "08:30" }], "2026-10-15");
  expect(rows.map(t => t.id)).toEqual([4, 1, 2]);
});
