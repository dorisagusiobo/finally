"use client";

import { usePriceFlash } from "@/lib/usePriceFlash";
import { formatCurrency, formatPercent } from "@/lib/format";
import type { HistoryPoint } from "@/lib/PriceStreamContext";
import type { PriceTick } from "@/lib/types";
import { LineChart } from "@/components/charts/LineChart";

interface WatchlistRowProps {
  ticker: string;
  tick: PriceTick | undefined;
  history: HistoryPoint[];
  selected: boolean;
  onSelect: (ticker: string) => void;
  onRemove: (ticker: string) => void;
}

export function WatchlistRow({
  ticker,
  tick,
  history,
  selected,
  onSelect,
  onRemove,
}: WatchlistRowProps) {
  const flashClass = usePriceFlash(tick?.price);
  const changePercent = tick?.change_percent ?? 0;
  const positive = changePercent >= 0;
  const sparklineColor = positive ? "#26a69a" : "#ef5350";

  return (
    <div
      role="row"
      aria-selected={selected}
      data-testid={`watchlist-row-${ticker}`}
      onClick={() => onSelect(ticker)}
      className={`group grid cursor-pointer grid-cols-[1fr_auto_auto_64px_auto] items-center gap-3 border-b border-border-muted px-3 py-2 text-sm transition-colors hover:bg-elevated ${
        selected ? "bg-elevated" : ""
      }`}
    >
      <span className="font-semibold">{ticker}</span>

      <span
        className={`rounded px-1.5 py-0.5 tabular-nums ${flashClass}`}
        data-testid={`watchlist-price-${ticker}`}
      >
        {tick?.price != null ? formatCurrency(tick.price) : "—"}
      </span>

      <span
        className={`w-16 text-right tabular-nums ${
          positive ? "text-up" : "text-down"
        }`}
      >
        {tick?.change_percent != null ? formatPercent(changePercent) : "—"}
      </span>

      <span className="h-9 w-16">
        {history.length > 1 ? (
          <LineChart data={history} color={sparklineColor} compact />
        ) : null}
      </span>

      <button
        type="button"
        aria-label={`Remove ${ticker} from watchlist`}
        onClick={(e) => {
          e.stopPropagation();
          onRemove(ticker);
        }}
        className="invisible text-muted hover:text-down group-hover:visible"
      >
        ✕
      </button>
    </div>
  );
}
