import { expect, it } from "vitest";
import { tourLessons } from "./tourLessons";
import { tourAudio, pendingNarration } from "./tourAudio";
it("covers every narration with a recording or an explicitly documented text-only step", () => {
  const required = new Set<string>();
  for (const brand of ["LUU", "INVEKTA", "CENOBOTS", undefined]) {
    for (const lesson of tourLessons(brand, true, true)) {
      for (const step of lesson.steps) {
        const text = `${step.title}. ${step.text}`;
        required.add(text);
        if (pendingNarration.includes(text)) expect(tourAudio[text]).toBeUndefined();
        else expect(tourAudio[text], `${brand}: ${step.title}`).toMatch(/\.mp3(?:\?|$)/);
      }
    }
  }
  expect(new Set([...Object.keys(tourAudio), ...pendingNarration])).toEqual(required);
  expect(Object.keys(tourAudio)).toHaveLength(18);
  expect(pendingNarration).toHaveLength(8);
});
