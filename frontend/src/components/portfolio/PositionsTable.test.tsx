import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { PositionsTable } from "./PositionsTable";
import { PortfolioProvider } from "@/lib/PortfolioContext";
import { PriceStreamProvider } from "@/lib/PriceStreamContext";
import { mockPortfolio } from "@/test/fixtures";
import * as api from "@/lib/api";

vi.mock("@/lib/api");

describe("PositionsTable", () => {
  beforeEach(() => {
    vi.mocked(api.getPortfolio).mockResolvedValue(mockPortfolio);
  });

  it("renders position rows with quantity, avg cost, price, and P&L", async () => {
    render(
      <PriceStreamProvider>
        <PortfolioProvider>
          <PositionsTable />
        </PortfolioProvider>
      </PriceStreamProvider>
    );

    const row = await screen.findByTestId("position-row-AAPL");
    expect(row).toHaveTextContent("AAPL");
    expect(row).toHaveTextContent("10");
    expect(row).toHaveTextContent("$185.00");
    expect(row).toHaveTextContent("$191.23");
    expect(row).toHaveTextContent("+$62.30");
    expect(row).toHaveTextContent("+3.37%");
  });

  it("shows an empty state with no positions", async () => {
    vi.mocked(api.getPortfolio).mockResolvedValue({
      ...mockPortfolio,
      positions: [],
    });

    render(
      <PriceStreamProvider>
        <PortfolioProvider>
          <PositionsTable />
        </PortfolioProvider>
      </PriceStreamProvider>
    );

    expect(await screen.findByText("No open positions")).toBeInTheDocument();
  });
});
