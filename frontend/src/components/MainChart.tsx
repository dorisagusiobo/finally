"use client";

import { usePriceStream } from "@/lib/PriceStreamContext";
import { formatCurrency, formatPercent } from "@/lib/format";
import { LineChart } from "@/components/charts/LineChart";

export function MainChart({ ticker }: { ticker: string | null }) {
  const { ticks, history } = usePriceStream();

  if (!ticker) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted">
        Select a ticker from the watchlist to see its chart
      </div>
    );
  }

  const tick = ticks[ticker];
  const points = history[ticker] ?? [];
  const positive = (tick?.change_percent ?? 0) >= 0;

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-baseline gap-3 px-4 pt-3">
        <h2 className="text-xl font-bold">{ticker}</h2>
        {tick && (
          <>
            <span className="text-lg tabular-nums">
              {formatCurrency(tick.price)}
            </span>
            <span
              className={`text-sm tabular-nums ${
                positive ? "text-up" : "text-down"
              }`}
            >
              {formatPercent(tick.change_percent)}
            </span>
          </>
        )}
      </div>
      <div className="min-h-0 flex-1 p-2">
        {points.length > 1 ? (
          <LineChart
            data={points}
            color={positive ? "#26a69a" : "#ef5350"}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted">
            Waiting for price data…
          </div>
        )}
      </div>
    </div>
  );
}
