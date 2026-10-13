import { it, expect } from "vitest";
import { dailyRecommendations } from "./DailyWelcome";
it("prioritizes actual stages and does not suggest calling won or lost opportunities", () => {
  const items = dailyRecommendations(
    { "Novi lead": 2, Ponuda: 3, Pregovori: 1, Dobijeno: 10 },
    20,
  );
  expect(items).toHaveLength(3);
  expect(items[0].label).toContain("(2)");
  expect(items[1].label).toContain("(3)");
  expect(items.every((i) => i.page === "Prodajni levak")).toBe(true);
  expect(
    dailyRecommendations({ Dobijeno: 10, Izgubljeno: 4 }, 0)[0].label,
  ).toContain("prvu kompaniju");
});
