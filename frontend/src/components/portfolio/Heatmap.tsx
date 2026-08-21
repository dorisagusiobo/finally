"use client";

import { useMemo } from "react";
import { useLivePortfolio } from "@/lib/PortfolioContext";
import { computeTreemap } from "@/lib/treemap";
import { useElementSize } from "@/lib/useElementSize";
import { formatPercent } from "@/lib/format";

const MAX_PNL_PERCENT_FOR_INTENSITY = 15;

function pnlColor(pnlPercent: number): string {
  const magnitude = Math.min(
    Math.abs(pnlPercent) / MAX_PNL_PERCENT_FOR_INTENSITY,
    1
  );
  const alpha = 0.18 + magnitude * 0.62;
  return pnlPercent >= 0
    ? `rgba(38, 166, 154, ${alpha})`
    : `rgba(239, 83, 80, ${alpha})`;
}

export function Heatmap() {
  const portfolio = useLivePortfolio();
  const { ref, size } = useElementSize<HTMLDivElement>();

  const positions = useMemo(() => portfolio?.positions ?? [], [portfolio]);
  const totalValue = portfolio?.total_value ?? 0;

  const rects = useMemo(() => {
    const items = positions
      .filter((p) => p.market_value > 0)
      .map((p) => ({ id: p.ticker, value: p.market_value }));
    return computeTreemap(items, size.width, size.height);
  }, [positions, size.width, size.height]);

  const byTicker = useMemo(
    () => new Map(positions.map((p) => [p.ticker, p])),
    [positions]
  );

  return (
    <div className="flex h-full flex-col">
      <h2 className="px-3 pt-2 text-xs font-semibold uppercase tracking-wide text-muted">
        Portfolio Heatmap
      </h2>
      <div ref={ref} className="relative min-h-0 flex-1 m-2">
        {positions.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-muted">
            No positions yet
          </div>
        ) : (
          rects.map((rect) => {
            const position = byTicker.get(rect.id);
            if (!position) return null;
            const weight =
              totalValue > 0 ? (position.market_value / totalValue) * 100 : 0;
            return (
              <div
                key={rect.id}
                data-testid={`heatmap-cell-${rect.id}`}
                title={`${rect.id}: ${formatPercent(
                  position.unrealized_pnl_percent
                )} · ${weight.toFixed(1)}% of portfolio`}
                style={{
                  position: "absolute",
                  left: rect.x,
                  top: rect.y,
                  width: rect.w,
                  height: rect.h,
                  backgroundColor: pnlColor(position.unrealized_pnl_percent),
                }}
                className="flex flex-col items-center justify-center overflow-hidden border border-background p-1 text-center"
              >
                <span className="truncate text-xs font-semibold">
                  {rect.id}
                </span>
                {rect.w > 50 && rect.h > 34 && (
                  <span className="truncate text-[11px] tabular-nums text-muted">
                    {formatPercent(position.unrealized_pnl_percent)}
                  </span>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
