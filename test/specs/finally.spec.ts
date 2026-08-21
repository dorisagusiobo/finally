import { test, expect, type Page, type Locator } from "@playwright/test";

/**
 * FinAlly E2E suite (PLAN.md §12).
 *
 * Runs against a single shared backend/DB instance (see
 * test/docker-compose.test.yml) — there is no per-test reset, so scenarios
 * run serially and each may depend on state left by the previous one. Every
 * test still does its own `page.goto("/")` (state lives server-side in
 * SQLite, not in the browser), so a fresh `page` fixture per test is safe.
 */

const SEED_TICKERS = [
  "AAPL",
  "GOOGL",
  "MSFT",
  "AMZN",
  "TSLA",
  "NVDA",
  "META",
  "JPM",
  "V",
  "NFLX",
];

function cashValueLocator(page: Page): Locator {
  return page
    .locator("header div.text-right")
    .filter({ has: page.getByText("Cash", { exact: true }) })
    .locator("div.text-lg");
}

function totalValueLocator(page: Page): Locator {
  return page.getByTestId("header-total-value");
}

function connectionDot(page: Page): Locator {
  return page.getByTestId("connection-dot");
}

async function waitForConnected(page: Page, timeout = 10_000) {
  await expect(connectionDot(page)).toHaveAttribute(
    "data-state",
    "connected",
    { timeout }
  );
}

test.describe.serial("FinAlly E2E", () => {
  test("1. Fresh start: default watchlist, $10,000 cash, prices streaming", async ({
    page,
  }) => {
    await page.goto("/");

    for (const ticker of SEED_TICKERS) {
      await expect(page.getByTestId(`watchlist-row-${ticker}`)).toBeVisible();
    }
    // Exactly the 10 seed tickers, no more.
    await expect(page.locator('[data-testid^="watchlist-row-"]')).toHaveCount(
      SEED_TICKERS.length
    );

    await expect(totalValueLocator(page)).toHaveText("$10,000.00");
    await expect(cashValueLocator(page)).toHaveText("$10,000.00");

    await waitForConnected(page);

    const priceCell = page.getByTestId("watchlist-price-AAPL");
    await expect(priceCell).not.toHaveText("—", { timeout: 10_000 });
    const initialPrice = await priceCell.textContent();
    await expect
      .poll(async () => priceCell.textContent(), {
        timeout: 8_000,
        message: "AAPL price should update from the SSE stream within 8s",
      })
      .not.toBe(initialPrice);
  });

  test("2. Add and remove a ticker from the watchlist", async ({ page }) => {
    await page.goto("/");

    await page.getByLabel("Add ticker to watchlist").fill("PYPL");
    await page.getByRole("button", { name: "Add" }).click();

    const row = page.getByTestId("watchlist-row-PYPL");
    await expect(row).toBeVisible();

    // The remove button is CSS `invisible` until the row is hovered
    // (`group-hover:visible` in WatchlistRow.tsx) — hover the row first so
    // Playwright's visibility actionability check on the button passes.
    await row.hover();
    await page.getByLabel("Remove PYPL from watchlist").click();
    await expect(row).not.toBeVisible();
  });

  test("3 & 5. Buy shares (cash/position/heatmap); portfolio visualization renders", async ({
    page,
  }) => {
    await page.goto("/");

    const cashBefore = await cashValueLocator(page).textContent();

    await page.getByLabel("Trade ticker").fill("AAPL");
    await page.getByLabel("Trade quantity").fill("5");
    await page.getByRole("button", { name: "Buy", exact: true }).click();

    await expect(page.getByTestId("trade-feedback")).toContainText(
      "Bought 5 AAPL"
    );
    await expect(page.getByTestId("position-row-AAPL")).toBeVisible();
    await expect
      .poll(async () => cashValueLocator(page).textContent())
      .not.toBe(cashBefore);

    // Portfolio visualization (§12 scenario 5), checked while the position
    // is open: heatmap cell renders, and the backend recorded a snapshot
    // immediately on trade execution (portfolio.py inserts one per trade).
    await expect(page.getByTestId("heatmap-cell-AAPL")).toBeVisible();

    const history = await page.request.get("/api/portfolio/history");
    expect(history.ok()).toBeTruthy();
    const historyBody = await history.json();
    expect(historyBody.snapshots.length).toBeGreaterThanOrEqual(1);
  });

  test("4. Sell shares: cash increases, position fully closes", async ({
    page,
  }) => {
    await page.goto("/");

    const cashBefore = await cashValueLocator(page).textContent();

    await page.getByLabel("Trade ticker").fill("AAPL");
    await page.getByLabel("Trade quantity").fill("5");
    await page.getByRole("button", { name: "Sell", exact: true }).click();

    await expect(page.getByTestId("trade-feedback")).toContainText(
      "Sold 5 AAPL"
    );
    // Selling exactly the held quantity fully closes the position
    // (backend deletes the row — app/portfolio.py execute_trade).
    await expect(page.getByTestId("position-row-AAPL")).not.toBeVisible();
    await expect(page.getByTestId("heatmap-cell-AAPL")).not.toBeVisible();
    await expect
      .poll(async () => cashValueLocator(page).textContent())
      .not.toBe(cashBefore);
  });

  test("6. AI chat (mocked): message triggers a trade, shown inline and executed", async ({
    page,
  }) => {
    await page.goto("/");

    const cashBefore = await cashValueLocator(page).textContent();

    // Lowercase "buy" deliberately: the mock heuristic (backend/app/llm/mock.py)
    // scans for the first all-caps 1-5 letter word as the "ticker" — an
    // all-caps "BUY" would itself match before reaching MSFT.
    await page.getByLabel("Chat message").fill("please buy 2 shares of MSFT");
    await page.getByRole("button", { name: "Send" }).click();

    // Not asserting the "chat-loading" indicator's visibility: with
    // LLM_MOCK=true the round trip is a local SQLite call with no network
    // latency, so the indicator can mount and unmount between polls —
    // asserting on it would be flaky. Wait directly for the response instead.
    const tradeAction = page.getByTestId("chat-trade-action").last();
    await expect(tradeAction).toBeVisible();
    await expect(tradeAction).toHaveAttribute("data-status", "executed");
    await expect(tradeAction).toContainText("Bought 2 MSFT");

    await expect(page.getByTestId("position-row-MSFT")).toBeVisible();
    await expect
      .poll(async () => cashValueLocator(page).textContent())
      .not.toBe(cashBefore);
  });

  test("7. SSE resilience: connection indicator reflects disconnect and recovers", async ({
    page,
  }) => {
    await page.goto("/");
    await waitForConnected(page);

    // context.setOffline() blocks new requests but does not sever an
    // already-open SSE stream in Chromium (CDP offline emulation only
    // intercepts new network attempts) — the dot would stay "connected"
    // for the life of the existing stream. Instead, abort the SSE route
    // and reload, which forces a fresh EventSource that fails immediately.
    await page.route("**/api/stream/prices", (route) => route.abort());
    await page.reload();

    await expect(connectionDot(page)).toHaveAttribute(
      "data-state",
      "reconnecting",
      { timeout: 10_000 }
    );

    // Backend sends `retry: 1000` (app/market/stream.py), so the browser's
    // built-in EventSource retry should reconnect ~1s after unblocking.
    await page.unroute("**/api/stream/prices");
    await waitForConnected(page, 15_000);
  });
});
