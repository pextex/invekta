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

import { nextTourPosition, previousTourPosition } from "./tourLessons";
it("uses the same lesson titles as the corresponding navigation cards", () => {
  const lessons = tourLessons("LUU", true, true);
  expect(lessons.map(item => item.title)).toEqual([
    "Početna tabla", "Kompanije", "Prodajni levak", "Targeti", "Zadaci", "LUU AI", "Izveštaji", "Hronologija promena - log", "Korisnici i pristup",
  ]);
});
it("continues between lessons, permits going back across their boundary, and ends at the last permitted lesson", () => {
  for (const privileged of [false, true]) {
    const lessons = tourLessons("LUU", privileged, privileged);
    for (let i = 0; i < lessons.length - 1; i++) {
      const current = lessons[i], next = lessons[i + 1];
      expect(nextTourPosition(lessons, current.id, current.steps.length - 1)).toEqual({ lessonId: next.id, index: 0 });
      expect(previousTourPosition(lessons, next.id, 0)).toEqual({ lessonId: current.id, index: current.steps.length - 1 });
    }
    const last = lessons[lessons.length - 1];
    expect(nextTourPosition(lessons, last.id, last.steps.length - 1)).toBeNull();
    expect(previousTourPosition(lessons, lessons[0].id, 0)).toBeNull();
  }
});

it("begins on the dashboard and then continues to Companies", () => {
  for (const brand of ["LUU", "INVEKTA", "CENOBOTS"]) {
    const lessons = tourLessons(brand);
    expect(lessons[0].id).toBe("dashboard");
    expect(lessons[0].steps.every(step => step.page === "Početna tabla")).toBe(true);
    expect(nextTourPosition(lessons, "dashboard", lessons[0].steps.length - 1)).toEqual({ lessonId: "companies", index: 0 });
  }
});
