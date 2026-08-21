import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { WatchlistPanel } from "./WatchlistPanel";
import { WatchlistProvider } from "@/lib/WatchlistContext";
import { PriceStreamProvider } from "@/lib/PriceStreamContext";
import { mockWatchlist } from "@/test/fixtures";
import * as api from "@/lib/api";

vi.mock("@/lib/api");

function renderPanel() {
  return render(
    <PriceStreamProvider>
      <WatchlistProvider>
        <WatchlistPanel selectedTicker={null} onSelectTicker={() => {}} />
      </WatchlistProvider>
    </PriceStreamProvider>
  );
}

describe("WatchlistPanel", () => {
  beforeEach(() => {
    vi.mocked(api.getWatchlist).mockResolvedValue(mockWatchlist);
  });

  it("renders tickers from the initial watchlist fetch", async () => {
    renderPanel();
    expect(await screen.findByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("GOOGL")).toBeInTheDocument();
  });

  it("adds a ticker via the form", async () => {
    const user = userEvent.setup();
    vi.mocked(api.addToWatchlist).mockResolvedValue({
      watchlist: [
        ...mockWatchlist.watchlist,
        {
          ticker: "PYPL",
          price: null,
          previous_price: null,
          change: null,
          change_percent: null,
          direction: null,
        },
      ],
    });

    renderPanel();
    await screen.findByText("AAPL");

    await user.type(
      screen.getByLabelText("Add ticker to watchlist"),
      "pypl"
    );
    await user.click(screen.getByRole("button", { name: "Add" }));

    await waitFor(() =>
      expect(api.addToWatchlist).toHaveBeenCalledWith("PYPL")
    );
    expect(await screen.findByText("PYPL")).toBeInTheDocument();
  });

  it("removes a ticker", async () => {
    const user = userEvent.setup();
    vi.mocked(api.removeFromWatchlist).mockResolvedValue({
      watchlist: mockWatchlist.watchlist.filter((w) => w.ticker !== "AAPL"),
    });

    renderPanel();
    await screen.findByText("AAPL");

    await user.click(
      screen.getByRole("button", { name: "Remove AAPL from watchlist" })
    );

    await waitFor(() =>
      expect(api.removeFromWatchlist).toHaveBeenCalledWith("AAPL")
    );
    await waitFor(() =>
      expect(screen.queryByText("AAPL")).not.toBeInTheDocument()
    );
  });
});
