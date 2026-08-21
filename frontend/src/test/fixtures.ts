import type { Portfolio, WatchlistResponse } from "@/lib/types";

export const mockWatchlist: WatchlistResponse = {
  watchlist: [
    {
      ticker: "AAPL",
      price: 190.5,
      previous_price: 190.12,
      change: 0.38,
      change_percent: 0.2,
      direction: "up",
    },
    {
      ticker: "GOOGL",
      price: 175.2,
      previous_price: 176.0,
      change: -0.8,
      change_percent: -0.45,
      direction: "down",
    },
  ],
};

export const mockPortfolio: Portfolio = {
  cash_balance: 8500,
  positions: [
    {
      ticker: "AAPL",
      quantity: 10,
      avg_cost: 185,
      current_price: 191.23,
      market_value: 1912.3,
      unrealized_pnl: 62.3,
      unrealized_pnl_percent: 3.37,
    },
  ],
  total_value: 10412.3,
  total_unrealized_pnl: 62.3,
};

export function mockFetchJSON(data: unknown, ok = true) {
  return {
    ok,
    status: ok ? 200 : 400,
    json: async () => data,
  } as Response;
}
