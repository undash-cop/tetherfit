import { expect, test } from "@playwright/test";

const API_BASE = process.env.PLAYWRIGHT_API_URL || "http://127.0.0.1:8000";

/**
 * Public + health smoke — no Keycloak required.
 *
 * Authenticated calendar (local only):
 * 1. Seed: `python scripts/seed_demo.py`
 * 2. Log in via `/login` with Keycloak
 * 3. Open `/app/calendar` — drag session chips on day/week views to reschedule
 */
test.describe("public smoke", () => {
  test("home loads", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });

  test("features page", async ({ page }) => {
    await page.goto("/features");
    await expect(page).toHaveURL(/\/features/);
    await expect(page.locator("body")).toBeVisible();
  });

  test("marketplace page", async ({ page }) => {
    await page.goto("/marketplace");
    await expect(page).toHaveURL(/\/marketplace/);
    await expect(page.locator("body")).toBeVisible();
  });
});

test.describe("api health", () => {
  test("GET /health", async ({ request }) => {
    const res = await request.get(`${API_BASE}/health`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty("status");
  });
});
