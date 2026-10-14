import type { Page } from "@playwright/test";
import { test, expect } from "./fixtures";
async function login(page: Page, name: string, organization = "LUU") {
  await page.goto("/");
  await page
    .getByRole("button", { name: new RegExp(organization, "i") })
    .first()
    .click();
  await page.getByLabel("Email adresa").fill(name + "@example.com");
  await page
    .getByLabel("Lozinka", { exact: true })
    .fill("Browser-test-only-123!");
  await page
    .getByRole("button", {
      name:
        "Prijavi se u " +
        (organization === "INVEKTA" ? "Invekta" : organization),
    })
    .click();
  await expect(
    page.getByRole("button", { name: "Početna tabla", exact: true }),
  ).toBeVisible();
  await navigate(page, "Početna tabla");
  await expect(
    page.getByRole("heading", { name: "Vaš prodajni pregled" }),
  ).toBeVisible();
}
async function navigate(page: Page, label: string) {
  await page.getByRole("button", { name: label, exact: true }).first().click();
}
function metric(page: Page, label: string) {
  return page
    .locator(".metric")
    .filter({ has: page.getByText(label, { exact: true }) });
}

test("persisted sales flow, reports, profile, reload, relogin, manager and foreign unit", async ({
  page,
}) => {
  await login(page, "sales");
  await expect(metric(page, "Otvorene prilike").locator("strong")).toHaveText(
    "1",
  );
  await navigate(page, "Prodajni levak");
  const card = page.locator('[data-opportunity-id="1"]');
  await expect(card).toBeVisible();
  await expect(card).toHaveAttribute("draggable", "true");
  await card.dragTo(page.locator('[data-stage="Dobijeno"]'), {
    sourcePosition: { x: 15, y: 15 },
    targetPosition: { x: 60, y: 80 },
  });
  await expect(card.getByLabel("Faza prilike Browser ponuda")).toHaveValue(
    "Dobijeno",
  );
  await navigate(page, "Početna tabla");
  await expect(metric(page, "Otvorene prilike").locator("strong")).toHaveText(
    "0",
  );
  await expect(metric(page, "Dobijeni poslovi")).toContainText("12.500,55");
  await navigate(page, "Izveštaji");
  await expect(
    page.getByRole("heading", { name: "Izveštaji prodaje" }),
  ).toBeVisible();
  const stages = page
    .locator("section")
    .filter({
      has: page.getByRole("heading", {
        name: "Broj i vrednost po fazama",
        exact: true,
      }),
    });
  await expect(
    stages
      .getByRole("row")
      .filter({
        has: page.getByRole("cell", { name: "Dobijeno", exact: true }),
      }),
  ).toContainText("12.500,55");
  await expect(
    page.getByText("Ponuda → Dobijeno", { exact: true }),
  ).toBeVisible();
  await navigate(page, "Kompanije");
  await page.getByRole("button", { name: "Otvori profil →" }).click();
  await page.getByRole("tab", { name: "Prodajne prilike" }).click();
  await expect(page.locator('[data-opportunity-id="1"] select')).toHaveValue(
    "Dobijeno",
  );
  await page.reload();
  await page.getByRole("tab", { name: "Prodajne prilike" }).click();
  await expect(page.locator('[data-opportunity-id="1"] select')).toHaveValue(
    "Dobijeno",
  );
  await page
    .locator('[data-opportunity-id="1"]')
    .getByRole("button", { name: "Istorija" })
    .click();
  await expect(page.locator(".history-panel")).toContainText("Sales");
  await expect(page.locator(".history-panel")).toContainText(
    "Ponuda → Dobijeno",
  );
  await page.getByRole("button", { name: "Odjava" }).click();
  await login(page, "sales");
  await expect(metric(page, "Dobijeni poslovi")).toContainText("12.500,55");
  await navigate(page, "Prodajni levak");
  await page
    .locator('[data-opportunity-id="1"] select')
    .selectOption("Pregovori");
  await expect(page.locator('[data-opportunity-id="1"] select')).toHaveValue(
    "Pregovori",
  );
  await page
    .locator('[data-opportunity-id="1"] select')
    .selectOption("Dobijeno");
  await expect(page.locator('[data-opportunity-id="1"] select')).toHaveValue(
    "Dobijeno",
  );
  await page.getByRole("button", { name: "Odjava" }).click();
  await login(page, "manager");
  await expect(metric(page, "Dobijeni poslovi")).toContainText("12.500,55");
  await expect(metric(page, "Otvorene prilike").locator("strong")).toHaveText(
    "1",
  );
  await navigate(page, "Izveštaji");
  await expect(
    page.getByRole("heading", { name: "Rezultati komercijalista" }),
  ).toBeVisible();
  await page.getByLabel("Komercijalista izveštaja").selectOption("1");
  await expect(metric(page, "Otvorene prilike").locator("strong")).toHaveText(
    "0",
  );
  await page.getByLabel("Poslovna jedinica izveštaja").selectOption("2");
  await expect(metric(page, "Dobijeni poslovi")).toContainText("300,3");
  await page.getByLabel("Poslovna jedinica izveštaja").selectOption("3");
  await expect(metric(page, "Otvorene prilike").locator("strong")).toHaveText(
    "0",
  );
  await expect(
    page.getByRole("heading", { name: "Izveštaji prodaje" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Odjava" }).click();
  await login(page, "outsider", "INVEKTA");
  const denied = await page.request.get("/api/units/1/summary");
  expect(denied.status()).toBe(403);
  const hidden = await page.request.get(
    "/api/units/2/opportunities?company_id=1",
  );
  expect(hidden.status()).toBe(404);
  await expect(metric(page, "Dobijeni poslovi")).toContainText("300,3");
});

test("new records and amount edits refresh aggregates; stale edits keep the form", async ({
  page,
}) => {
  await login(page, "sales");
  const initial = await (await page.request.get('/api/units/1/opportunities')).json();
  const original = initial.items.find((row: { id: number }) => row.id === 1);
  expect((await page.request.patch('/api/units/1/opportunities/1/stage', {
    headers: { Origin: 'http://localhost:5173' }, data: { stage: 'Dobijeno', version: original.version },
  })).status()).toBe(200);

  await navigate(page, "Kompanije");
  await page
    .getByRole("button", { name: "Nova kompanija", exact: true })
    .click();
  await page
    .getByLabel("Naziv kompanije", { exact: true })
    .fill("Browser Nova Firma");
  await page.getByLabel("Grad", { exact: true }).fill("Niš");
  await page.getByLabel("Delatnost", { exact: true }).fill("Usluge");
  await page.getByRole("button", { name: "Sačuvaj", exact: true }).click();
  const companyRow = page
    .getByRole("row")
    .filter({ hasText: "Browser Nova Firma" });
  await expect(companyRow).toBeVisible();
  await companyRow.getByRole("button", { name: "Otvori profil →" }).click();
  await page.getByRole("button", { name: "Novi kontakt", exact: true }).click();
  await page
    .getByLabel("Ime i prezime", { exact: true })
    .fill("Browser Kontakt");
  await page
    .getByLabel("E-mail", { exact: true })
    .fill("browser-contact@example.com");
  await page
    .getByRole("button", { name: "Sačuvaj kontakt", exact: true })
    .click();
  await expect(
    page.getByRole("cell", { name: "Browser Kontakt" }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Prodajne prilike" }).click();
  await page.getByRole("button", { name: "Nova prilika", exact: true }).click();
  await page
    .getByLabel("Naziv prilike", { exact: true })
    .fill("Browser novi posao");
  await page.getByLabel("Vrednost (RSD)", { exact: true }).fill("10.11");
  await page.getByLabel("Faza nove prilike").selectOption("Ponuda");
  await page
    .getByRole("button", { name: "Sačuvaj priliku", exact: true })
    .click();
  const card = page
    .locator(".opportunity-card")
    .filter({ hasText: "Browser novi posao" });
  await expect(card).toContainText("10,11");
  await navigate(page, "Početna tabla");
  await expect(metric(page, "Kompanije u bazi").locator("strong")).toHaveText(
    "2",
  );
  await expect(metric(page, "Kontakt osobe").locator("strong")).toHaveText("1");
  await expect(metric(page, "Vrednost otvorenih prilika")).toContainText(
    "10,11",
  );
  await navigate(page, "Prodajni levak");
  await card.getByRole("button", { name: "Izmeni", exact: true }).click();
  await page.getByLabel("Vrednost (RSD)", { exact: true }).fill("20.22");
  await page.getByLabel("Očekivani datum zatvaranja").fill("2027-01-01");
  await page
    .getByRole("button", { name: "Sačuvaj priliku", exact: true })
    .click();
  await expect(card).toContainText("20,22");
  await navigate(page, "Izveštaji");
  await expect(metric(page, "Vrednost otvorenih prilika")).toContainText(
    "20,22",
  );
  await page.reload();
  await expect(metric(page, "Vrednost otvorenih prilika")).toContainText(
    "20,22",
  );
  await navigate(page, "Prodajni levak");
  const data = await (
    await page.request.get("/api/units/1/opportunities")
  ).json();
  const record = data.items.find(
    (row: { title: string }) => row.title === "Browser novi posao",
  );
  await card.getByRole("button", { name: "Izmeni", exact: true }).click();
  await page.getByLabel("Vrednost (RSD)", { exact: true }).fill("99.99");
  const concurrent = await page.request.patch(
    `/api/units/1/opportunities/${record.id}/stage`,
    {
      headers: { Origin: "http://localhost:5173" },
      data: { version: record.version, stage: "Dobijeno" },
    },
  );
  expect(concurrent.status()).toBe(200);
  await page
    .getByRole("button", { name: "Sačuvaj priliku", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("u međuvremenu");
  await expect(page.getByLabel("Vrednost (RSD)", { exact: true })).toHaveValue(
    "99.99",
  );
  await page.getByRole("button", { name: "Otkaži", exact: true }).click();
  await expect(card.getByLabel("Faza prilike Browser novi posao")).toHaveValue(
    "Dobijeno",
  );
  await expect(card).toContainText("20,22");
});

test("another logged-in manager automatically receives persisted changes", async ({
  page,
  browser,
}) => {
  await login(page, "sales");
  const initial = await (await page.request.get('/api/units/1/opportunities')).json();
  const original = initial.items.find((row: { id: number }) => row.id === 1);
  expect((await page.request.patch('/api/units/1/opportunities/1/stage', {
    headers: { Origin: 'http://localhost:5173' }, data: { stage: 'Dobijeno', version: original.version },
  })).status()).toBe(200);

  const managerContext = await browser.newContext({
    baseURL: "http://localhost:5173",
    viewport: { width: 1920, height: 1080 },
  });
  const manager = await managerContext.newPage();
  try {
    await login(manager, "manager");
    await expect(metric(manager, "Dobijeni poslovi")).toContainText(
      "12.500,55",
    );
    await navigate(page, "Prodajni levak");
    await page
      .locator('[data-opportunity-id="1"]')
      .getByRole("button", { name: "Izmeni", exact: true })
      .click();
    await page.getByLabel("Vrednost (RSD)", { exact: true }).fill("25000");
    await page
      .getByRole("button", { name: "Sačuvaj priliku", exact: true })
      .click();
    await expect(metric(manager, "Dobijeni poslovi")).toContainText(
      "25.000",
      { timeout: 35_000 },
    );
  } finally {
    await managerContext.close();
  }
});
