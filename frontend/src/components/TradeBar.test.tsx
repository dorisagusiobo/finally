import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TradeBar } from "./TradeBar";
import { PortfolioProvider } from "@/lib/PortfolioContext";
import { PriceStreamProvider } from "@/lib/PriceStreamContext";
import { mockPortfolio } from "@/test/fixtures";
import * as api from "@/lib/api";

vi.mock("@/lib/api");

function renderTradeBar() {
  return render(
    <PriceStreamProvider>
      <PortfolioProvider>
        <TradeBar />
      </PortfolioProvider>
    </PriceStreamProvider>
  );
}

describe("TradeBar", () => {
  beforeEach(() => {
    vi.mocked(api.getPortfolio).mockResolvedValue(mockPortfolio);
  });

  it("submits a buy order and shows a success confirmation", async () => {
    const user = userEvent.setup();
    vi.mocked(api.postTrade).mockResolvedValue({
      success: true,
      trade: {
        id: "t1",
        ticker: "AAPL",
        side: "buy",
        quantity: 5,
        price: 191.23,
        executed_at: "2026-08-21T10:00:00+00:00",
      },
      portfolio: mockPortfolio,
    });

    renderTradeBar();

    await user.type(screen.getByLabelText("Trade ticker"), "aapl");
    await user.type(screen.getByLabelText("Trade quantity"), "5");
    await user.click(screen.getByRole("button", { name: "Buy" }));

    expect(api.postTrade).toHaveBeenCalledWith("AAPL", 5, "buy");
    expect(await screen.findByTestId("trade-feedback")).toHaveTextContent(
      "Bought 5 AAPL @ $191.23"
    );
  });

  it("surfaces a validation error from a failed trade", async () => {
    const user = userEvent.setup();
    vi.mocked(api.postTrade).mockResolvedValue({
      success: false,
      error: "Insufficient cash",
    });

    renderTradeBar();

    await user.type(screen.getByLabelText("Trade ticker"), "AAPL");
    await user.type(screen.getByLabelText("Trade quantity"), "999999");
    await user.click(screen.getByRole("button", { name: "Buy" }));

    expect(await screen.findByTestId("trade-feedback")).toHaveTextContent(
      "Insufficient cash"
    );
  });
});
