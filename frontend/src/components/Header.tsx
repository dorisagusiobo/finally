"use client";

import { useLivePortfolio } from "@/lib/PortfolioContext";
import { usePriceStream } from "@/lib/PriceStreamContext";
import { formatCurrency, formatSignedCurrency } from "@/lib/format";
import { ConnectionDot } from "./ConnectionDot";

export function Header() {
  const livePortfolio = useLivePortfolio();
  const { connectionState } = usePriceStream();

  const totalValue = livePortfolio?.total_value ?? 0;
  const cash = livePortfolio?.cash_balance ?? 0;
  const pnl = livePortfolio?.total_unrealized_pnl ?? 0;
  const pnlPositive = pnl >= 0;

  return (
    <header className="flex items-center justify-between border-b border-border-muted bg-panel px-6 py-3">
      <div className="flex items-center gap-3">
        <span className="text-lg font-bold tracking-tight text-yellow">
          FinAlly
        </span>
        <span className="text-xs text-muted">AI Trading Workstation</span>
      </div>

      <div className="flex items-center gap-8">
        <div className="text-right">
          <div className="text-[11px] uppercase tracking-wide text-muted">
            Total Value
          </div>
          <div
            className="text-lg font-semibold tabular-nums"
            data-testid="header-total-value"
          >
            {formatCurrency(totalValue)}
          </div>
        </div>

        <div className="text-right">
          <div className="text-[11px] uppercase tracking-wide text-muted">
            Unrealized P&amp;L
          </div>
          <div
            className={`text-lg font-semibold tabular-nums ${
              pnlPositive ? "text-up" : "text-down"
            }`}
          >
            {formatSignedCurrency(pnl)}
          </div>
        </div>

        <div className="text-right">
          <div className="text-[11px] uppercase tracking-wide text-muted">
            Cash
          </div>
          <div className="text-lg font-semibold tabular-nums">
            {formatCurrency(cash)}
          </div>
        </div>

        <ConnectionDot state={connectionState} />
      </div>
    </header>
  );
}
