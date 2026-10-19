import type { TourLesson } from "./tourLessons";
import { tourAudio } from "./tourAudio";
import companies from "../assets/tour-narration/opening-companies.mp3";
import pipeline from "../assets/tour-narration/opening-pipeline.mp3";
import targets from "../assets/tour-narration/opening-targets.mp3";
import tasks from "../assets/tour-narration/opening-tasks.mp3";
import reports from "../assets/tour-narration/opening-reports.mp3";

// The opening recording announces the navigation card name, then its explanation.
export const lessonOpeningAudio: Record<string, string> = {
  "Kompanije": companies,
  "Prodajni levak": pipeline,
  "Targeti": targets,
  "Zadaci": tasks,
  "Izveštaji": reports,
};
export function getTourNarration(lesson: TourLesson | undefined, index: number): string | undefined {
  const step = lesson?.steps[index];
  if (!lesson || !step) return undefined;
  if (index === 0 && lessonOpeningAudio[lesson.title]) return lessonOpeningAudio[lesson.title];
  return tourAudio[`${step.title}. ${step.text}`];
}
