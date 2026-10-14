import type { Page } from "@playwright/test";
import { expect } from "./fixtures";
export async function login(page: Page, name: string, organization = "LUU") {
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
export async function navigate(page: Page, label: string) {
  await page.getByRole("button", { name: label, exact: true }).first().click();
}
export function metric(page: Page, label: string) {
  return page
    .locator(".metric")
    .filter({ has: page.getByText(label, { exact: true }) });
}
