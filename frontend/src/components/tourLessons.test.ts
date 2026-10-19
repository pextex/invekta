import { expect, it } from "vitest";
import { tourLessons } from "./tourLessons";
it("limits lessons to the current user's permissions", () => {
  expect(tourLessons("LUU").map(item => item.id)).not.toContain("history");
  expect(tourLessons("LUU").map(item => item.id)).not.toContain("users");
  expect(tourLessons("INVEKTA", true).map(item => item.id)).toContain("history");
  expect(tourLessons("INVEKTA", true).map(item => item.id)).not.toContain("users");
  expect(tourLessons("CENOBOTS", true, true).map(item => item.id)).toContain("users");
});
it("uses the current brand name with the shared AI route", () => {
  for (const brand of ["LUU", "INVEKTA", "CENOBOTS"]) {
    const ai = tourLessons(brand).find(item => item.id === "ai")!;
    expect(ai.title).toBe(`${brand} AI`);
    expect(ai.steps.every(step => step.page === "Invekta AI")).toBe(true);
  }
});
