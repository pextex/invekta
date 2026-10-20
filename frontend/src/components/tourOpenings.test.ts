import { expect, it } from "vitest";
import { tourLessons } from "./tourLessons";
import { tourAudio } from "./tourAudio";
import { getTourNarration } from "./tourOpenings";
it("uses the uniform voice for all steps including card-name openings", () => {
  for (const brand of ["LUU", "INVEKTA", "CENOBOTS", undefined]) {
    for (const lesson of tourLessons(brand, true, true)) {
      for (let index = 0; index < lesson.steps.length; index++) {
        const step = lesson.steps[index];
        const source = getTourNarration(lesson, index);
        expect(source).toBe(tourAudio[`${step.title}. ${step.text}`]);
        expect(source).toContain("/uniform/kore-");
      }
    }
  }
});
it("handles absent lessons and out-of-range steps", () => {
  expect(getTourNarration(undefined, 0)).toBeUndefined();
  const lesson = tourLessons("LUU")[0];
  expect(getTourNarration(lesson, lesson.steps.length)).toBeUndefined();
});

it("records each lesson's card name before its explanation", async () => {
  const { default: manifest } = await import("./tourVoiceManifest.json");
  expect(manifest.recordings).toHaveLength(26);
  for (const brand of ["LUU", "INVEKTA", "CENOBOTS", undefined]) {
    for (const lesson of tourLessons(brand, true, true)) {
      const first = lesson.steps[0];
      const clip = manifest.recordings.find(item => item.text === `${first.title}. ${first.text}`);
      expect(clip?.voice).toBe("Kore");
      expect(clip?.spoken.startsWith(`${lesson.title}.`), lesson.title).toBe(true);
    }
  }
});
