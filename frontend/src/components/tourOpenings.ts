import type { TourLesson } from "./tourLessons";
import { tourAudio } from "./tourAudio";

export function getTourNarration(lesson: TourLesson | undefined, index: number): string | undefined {
  const step = lesson?.steps[index];
  return step ? tourAudio[`${step.title}. ${step.text}`] : undefined;
}
