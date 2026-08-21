"use client";

import { useEffect, useRef } from "react";
import {
  AreaSeries,
  ColorType,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";

export interface ChartPoint {
  time: number; // unix seconds
  value: number;
}

interface LineChartProps {
  data: ChartPoint[];
  color?: string;
  /** Hides axes/grid/crosshair for a minimal inline sparkline. */
  compact?: boolean;
}

export function LineChart({
  data,
  color = "#209dd7",
  compact = false,
}: LineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#8b93a3",
        fontSize: 11,
      },
      grid: {
        vertLines: { visible: !compact, color: "#1f2430" },
        horzLines: { visible: !compact, color: "#1f2430" },
      },
      rightPriceScale: { visible: !compact, borderVisible: false },
      timeScale: { visible: !compact, borderVisible: false },
      crosshair: {
        vertLine: { visible: !compact, labelVisible: !compact },
        horzLine: { visible: !compact, labelVisible: !compact },
      },
      handleScroll: !compact,
      handleScale: !compact,
      width: container.clientWidth,
      height: container.clientHeight,
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: color,
      topColor: `${color}33`,
      bottomColor: `${color}00`,
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: !compact,
      crosshairMarkerVisible: !compact,
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      if (width > 0 && height > 0) {
        chart.applyOptions({ width, height });
      }
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [compact, color]);

  useEffect(() => {
    if (!seriesRef.current) return;
    seriesRef.current.setData(
      data.map((p) => ({ time: p.time as UTCTimestamp, value: p.value }))
    );
    if (!compact) {
      chartRef.current?.timeScale().fitContent();
    }
  }, [data, compact]);

  return <div ref={containerRef} className="h-full w-full" />;
}
