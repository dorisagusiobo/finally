"use client";

import { useEffect, useState } from "react";
import { getPortfolioHistory } from "@/lib/api";
import type { PortfolioSnapshot } from "@/lib/types";
import { LineChart, type ChartPoint } from "@/components/charts/LineChart";

function toChartPoints(snapshots: PortfolioSnapshot[]): ChartPoint[] {
  return snapshots.map((s) => ({
    time: new Date(s.recorded_at).getTime() / 1000,
    value: s.total_value,
  }));
}

export function PnLChart() {
  const [points, setPoints] = useState<ChartPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPortfolioHistory()
      .then((res) => setPoints(toChartPoints(res.snapshots)))
      .catch(() => setPoints([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex h-full flex-col">
      <h2 className="px-3 pt-2 text-xs font-semibold uppercase tracking-wide text-muted">
        Portfolio Value
      </h2>
      <div className="min-h-0 flex-1 p-2">
        {loading ? (
          <div className="flex h-full items-center justify-center text-sm text-muted">
            Loading…
          </div>
        ) : points.length > 1 ? (
          <LineChart data={points} color="#209dd7" />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted">
            Not enough history yet
          </div>
        )}
      </div>
    </div>
  );
}
