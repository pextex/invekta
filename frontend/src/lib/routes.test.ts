import { afterEach, expect, it, vi } from "vitest";
import { readRoute, writeRoute } from "./routes";
afterEach(() => vi.unstubAllGlobals());
it("keeps old client bookmarks opening Companies and uses the current route for new navigation", () => {
  const browser = { location: { hash: "#crm/leads?unit=101" }, history: { replaceState: vi.fn() } };
  vi.stubGlobal("window", browser);
  expect(readRoute().page).toBe("Kompanije");
  writeRoute("Kompanije", 101);
  expect(browser.location.hash).toBe("#crm/companies?unit=101");
  writeRoute("Zadaci", 101);
  expect(readRoute().page).toBe("Zadaci");
});
