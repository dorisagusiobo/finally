"use client";

import { useLivePortfolio } from "@/lib/PortfolioContext";
import {
  formatCurrency,
  formatPercent,
  formatQuantity,
  formatSignedCurrency,
} from "@/lib/format";

export function PositionsTable() {
  const portfolio = useLivePortfolio();
  const positions = portfolio?.positions ?? [];

  return (
    <div className="flex h-full flex-col">
      <h2 className="px-3 pt-2 text-xs font-semibold uppercase tracking-wide text-muted">
        Positions
      </h2>
      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-2">
        {positions.length === 0 ? (
          <p className="px-1 py-4 text-sm text-muted">No open positions</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-muted">
                <th className="py-1 font-medium">Ticker</th>
                <th className="py-1 text-right font-medium">Qty</th>
                <th className="py-1 text-right font-medium">Avg Cost</th>
                <th className="py-1 text-right font-medium">Price</th>
                <th className="py-1 text-right font-medium">P&amp;L</th>
                <th className="py-1 text-right font-medium">%</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr
                  key={p.ticker}
                  data-testid={`position-row-${p.ticker}`}
                  className="border-t border-border-muted"
                >
                  <td className="py-1.5 font-semibold">{p.ticker}</td>
                  <td className="py-1.5 text-right tabular-nums">
                    {formatQuantity(p.quantity)}
                  </td>
                  <td className="py-1.5 text-right tabular-nums">
                    {formatCurrency(p.avg_cost)}
                  </td>
                  <td className="py-1.5 text-right tabular-nums">
                    {formatCurrency(p.current_price)}
                  </td>
                  <td
                    className={`py-1.5 text-right tabular-nums ${
                      p.unrealized_pnl >= 0 ? "text-up" : "text-down"
                    }`}
                  >
                    {formatSignedCurrency(p.unrealized_pnl)}
                  </td>
                  <td
                    className={`py-1.5 text-right tabular-nums ${
                      p.unrealized_pnl_percent >= 0 ? "text-up" : "text-down"
                    }`}
                  >
                    {formatPercent(p.unrealized_pnl_percent)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
