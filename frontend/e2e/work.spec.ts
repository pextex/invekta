import { test, expect } from "./fixtures";
import { login, navigate } from "./helpers";
import { toLocalInput } from "../src/features/crm/workTypes";

test("tasks, activities and reminders stay linked across dashboard, profile and reports", async ({
  page,
  browser,
}) => {
  await login(page, "sales");
  await navigate(page, "Zadaci");
  await page.getByRole("button", { name: "Novi zadatak", exact: true }).click();
  await page
    .getByLabel("Naziv obaveze", { exact: true })
    .fill("Proveriti ponudu klijenta");
  await page.getByLabel("Prodajna prilika obaveze").selectOption("1");
  await page
    .getByLabel("Rok zadatka")
    .fill(toLocalInput(new Date(Date.now() + 20 * 60_000).toISOString()));
  await page
    .getByLabel("Vreme podsetnika")
    .fill(toLocalInput(new Date(Date.now() - 60_000).toISOString()));
  await page
    .getByRole("button", { name: "Sačuvaj obavezu", exact: true })
    .click();
  const row = page
    .getByRole("row")
    .filter({ hasText: "Proveriti ponudu klijenta" });
  await expect(row).toContainText("Browser ponuda");
  await expect(row).toContainText("Sales");
  await page.getByRole("button", { name: "Podsetnici", exact: true }).click();
  await expect(page.getByText("NOV PODSETNIK", { exact: false })).toBeVisible({
    timeout: 35_000,
  });
  await page.getByRole("button", { name: "Označi kao pročitan" }).click();
  await navigate(page, "Početna tabla");
  await expect(page.locator(".work-overview")).toContainText(
    "Proveriti ponudu klijenta",
  );
  await expect(page.locator(".work-overview")).toContainText(
    "Otvoreni zadaci: 1",
  );
  await navigate(page, "Izveštaji");
  await expect(page.locator(".work-overview")).toContainText(
    "Otvoreni zadaci: 1",
  );
  await navigate(page, "Kompanije");
  await page.getByRole("button", { name: "Otvori profil →" }).click();
  await page
    .getByRole("tab", { name: "Zadaci i aktivnosti", exact: true })
    .click();
  await expect(row).toBeVisible();
  await row
    .getByRole("button", { name: "Izmeni obavezu", exact: true })
    .click();
  await page.getByLabel("Status obaveze").selectOption("done");
  await page
    .getByRole("button", { name: "Sačuvaj obavezu", exact: true })
    .click();
  await expect(row).toContainText("Završen");
  await page.reload();
  await page
    .getByRole("tab", { name: "Zadaci i aktivnosti", exact: true })
    .click();
  await expect(row).toContainText("Završen");
  await row
    .getByRole("button", { name: "Istorija obaveze", exact: true })
    .click();
  await expect(page.locator(".history-panel")).toContainText("Sales");
  await page.getByRole("button", { name: "Aktivnosti", exact: true }).click();
  await page
    .getByRole("button", { name: "Nova aktivnost", exact: true })
    .click();
  await page
    .getByLabel("Naziv obaveze", { exact: true })
    .fill("Poziv za obilazak");
  await page.getByLabel("Prodajna prilika obaveze").selectOption("1");
  await page
    .getByLabel("Zakazano vreme")
    .fill(toLocalInput(new Date(Date.now() + 60 * 60_000).toISOString()));
  await page
    .getByLabel("Vreme podsetnika")
    .fill(toLocalInput(new Date(Date.now() - 60_000).toISOString()));
  await page
    .getByRole("button", { name: "Sačuvaj obavezu", exact: true })
    .click();
  const call = page.getByRole("row").filter({ hasText: "Poziv za obilazak" });
  await expect(call).toContainText("Zakazan");
  await call
    .getByRole("button", { name: "Izmeni obavezu", exact: true })
    .click();
  await page.getByLabel("Status obaveze").selectOption("done");
  await page.getByLabel("Ishod aktivnosti").fill("Dogovoren sledeći sastanak");
  await page
    .getByRole("button", { name: "Sačuvaj obavezu", exact: true })
    .click();
  await expect(call).toContainText("Dogovoren sledeći sastanak");
  await navigate(page, "Početna tabla");
  await expect(page.locator(".work-overview")).toContainText(
    "Završeni zadaci: 1",
  );
  await expect(page.locator(".work-overview")).toContainText(
    "Izvršeni pozivi: 1",
  );
  await page.getByRole("button", { name: "Odjava" }).click();
  await login(page, "sales");
  await expect(page.locator(".work-overview")).toContainText(
    "Izvršeni pozivi: 1",
  );
  const context = await browser.newContext({
    baseURL: "http://localhost:5173",
  });
  try {
    const manager = await context.newPage();
    await login(manager, "manager");
    await expect(manager.locator(".work-overview")).toContainText(
      "Završeni zadaci: 1",
    );
    await navigate(manager, "Izveštaji");
    await expect(manager.locator(".work-overview")).toContainText("Sales");
  } finally {
    await context.close();
  }
  await navigate(page, "Zadaci");
  await row.getByRole("button", { name: "Arhiviraj", exact: true }).click();
  await expect(row).toHaveCount(0);
  await page.getByLabel("Prikaži i arhivirane").check();
  await expect(row).toContainText("Arhiviran");
  await row
    .getByRole("button", { name: "Vrati iz arhive", exact: true })
    .click();
  await expect(row).toContainText("Otkazan");
  await page.getByRole("button", { name: "Odjava" }).click();
  await login(page, "outsider", "INVEKTA");
  expect((await page.request.get("/api/units/1/tasks")).status()).toBe(403);
  expect(
    (await page.request.get("/api/units/2/tasks?company_id=1")).status(),
  ).toBe(404);
  await expect(page.locator(".work-overview")).toContainText(
    "Završeni zadaci: 0",
  );
});

test("Invekta tasks are real and remain isolated from LUU", async ({
  page,
}) => {
  await login(page, "outsider", "INVEKTA");
  await navigate(page, "Zadaci");
  await page.getByRole("button", { name: "Novi zadatak", exact: true }).click();
  await page
    .getByLabel("Naziv obaveze", { exact: true })
    .fill("Invekta obilazak lokacije");
  await page.getByLabel("Prodajna prilika obaveze").selectOption("3");
  await page
    .getByRole("button", { name: "Sačuvaj obavezu", exact: true })
    .click();
  await expect(
    page.getByRole("row").filter({ hasText: "Invekta obilazak lokacije" }),
  ).toContainText("Browser Firma C");
  await navigate(page, "Početna tabla");
  await expect(page.locator(".work-overview")).toContainText(
    "Otvoreni zadaci: 1",
  );
  await page.getByRole("button", { name: "Odjava" }).click();
  await login(page, "sales");
  await expect(page.locator(".work-overview")).toContainText(
    "Otvoreni zadaci: 0",
  );
  await navigate(page, "Zadaci");
  await expect(
    page.getByRole("row").filter({ hasText: "Invekta obilazak lokacije" }),
  ).toHaveCount(0);
});
