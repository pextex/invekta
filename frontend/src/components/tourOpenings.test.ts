import { expect, it } from "vitest";
import { tourLessons } from "./tourLessons";
import { tourAudio } from "./tourAudio";
import { getTourNarration, lessonOpeningAudio } from "./tourOpenings";
it("uses card-name openings at the start of each affected lesson and keeps the remaining steps", () => {
  for (const brand of ["LUU", "INVEKTA", "CENOBOTS"]) {
    for (const lesson of tourLessons(brand, true, true)) {
      if (lessonOpeningAudio[lesson.title]) {
        expect(getTourNarration(lesson, 0)).toBe(lessonOpeningAudio[lesson.title]);
        expect(getTourNarration(lesson, 0)).toContain(`opening-${lesson.id}`);
      }
      for (let i = 1; i < lesson.steps.length; i++) {
        const step = lesson.steps[i];
        expect(getTourNarration(lesson, i)).toBe(tourAudio[`${step.title}. ${step.text}`]);
      }
    }
  }
});
it("keeps existing brand-name and history openings and handles absent lessons", () => {
  const lessons = tourLessons("LUU", true, true);
  for (const id of ["ai", "history"]) {
    const lesson = lessons.find(item => item.id === id)!;
    const step = lesson.steps[0];
    expect(getTourNarration(lesson, 0)).toBe(tourAudio[`${step.title}. ${step.text}`]);
  }
  expect(getTourNarration(undefined, 0)).toBeUndefined();
});
