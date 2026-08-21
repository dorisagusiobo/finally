import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatPanel } from "./ChatPanel";
import { PortfolioProvider } from "@/lib/PortfolioContext";
import { WatchlistProvider } from "@/lib/WatchlistContext";
import { PriceStreamProvider } from "@/lib/PriceStreamContext";
import { mockPortfolio, mockWatchlist } from "@/test/fixtures";
import * as api from "@/lib/api";

vi.mock("@/lib/api");

function renderChat() {
  return render(
    <PriceStreamProvider>
      <PortfolioProvider>
        <WatchlistProvider>
          <ChatPanel />
        </WatchlistProvider>
      </PortfolioProvider>
    </PriceStreamProvider>
  );
}

describe("ChatPanel", () => {
  beforeEach(() => {
    vi.mocked(api.getPortfolio).mockResolvedValue(mockPortfolio);
    vi.mocked(api.getWatchlist).mockResolvedValue(mockWatchlist);
  });

  it("sends a message, shows a loading state, then renders the response with an inline trade confirmation", async () => {
    const user = userEvent.setup();
    let resolveChat!: (value: Awaited<ReturnType<typeof api.postChatMessage>>) => void;
    vi.mocked(api.postChatMessage).mockReturnValue(
      new Promise((resolve) => {
        resolveChat = resolve;
      })
    );

    renderChat();

    await user.type(screen.getByLabelText("Chat message"), "Buy 10 AAPL");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(screen.getByTestId("chat-loading")).toBeInTheDocument();

    resolveChat({
      message: "Bought 10 shares of AAPL at $191.23.",
      actions: {
        trades: [
          {
            ticker: "AAPL",
            side: "buy",
            quantity: 10,
            status: "executed",
            price: 191.23,
          },
        ],
        watchlist_changes: [],
      },
      portfolio: mockPortfolio,
    });

    expect(
      await screen.findByText("Bought 10 shares of AAPL at $191.23.")
    ).toBeInTheDocument();
    expect(screen.getByTestId("chat-trade-action")).toHaveTextContent(
      "Bought 10 AAPL @ $191.23"
    );
    expect(screen.queryByTestId("chat-loading")).not.toBeInTheDocument();
  });

  it("shows a failed trade action with its error", async () => {
    const user = userEvent.setup();
    vi.mocked(api.postChatMessage).mockResolvedValue({
      message: "I couldn't complete that trade.",
      actions: {
        trades: [
          {
            ticker: "AAPL",
            side: "buy",
            quantity: 999999,
            status: "failed",
            error: "Insufficient cash",
          },
        ],
        watchlist_changes: [],
      },
      portfolio: mockPortfolio,
    });

    renderChat();

    await user.type(screen.getByLabelText("Chat message"), "Buy 999999 AAPL");
    await user.click(screen.getByRole("button", { name: "Send" }));

    const action = await screen.findByTestId("chat-trade-action");
    expect(action).toHaveTextContent("Insufficient cash");
    expect(action).toHaveAttribute("data-status", "failed");
  });
});
