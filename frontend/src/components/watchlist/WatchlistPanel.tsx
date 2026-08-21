"use client";

import { useState, type FormEvent } from "react";
import { useWatchlist } from "@/lib/WatchlistContext";
import { usePriceStream } from "@/lib/PriceStreamContext";
import { WatchlistRow } from "./WatchlistRow";

interface WatchlistPanelProps {
  selectedTicker: string | null;
  onSelectTicker: (ticker: string) => void;
}

export function WatchlistPanel({
  selectedTicker,
  onSelectTicker,
}: WatchlistPanelProps) {
  const { tickers, loading, error, addTicker, removeTicker } = useWatchlist();
  const { ticks, history } = usePriceStream();
  const [newTicker, setNewTicker] = useState("");

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault();
    if (!newTicker.trim()) return;
    await addTicker(newTicker);
    setNewTicker("");
  };

  return (
    <section className="flex h-full flex-col" aria-label="Watchlist">
      <div className="flex items-center justify-between px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-muted">
          Watchlist
        </h2>
      </div>

      <form onSubmit={handleAdd} className="flex gap-2 px-3 pb-2">
        <input
          type="text"
          value={newTicker}
          onChange={(e) => setNewTicker(e.target.value)}
          placeholder="Add ticker..."
          aria-label="Add ticker to watchlist"
          className="min-w-0 flex-1 rounded border border-border-muted bg-background px-2 py-1 text-sm uppercase outline-none focus:border-blue"
        />
        <button
          type="submit"
          className="rounded bg-purple px-3 py-1 text-sm font-medium text-white hover:opacity-90"
        >
          Add
        </button>
      </form>

      {error && <p className="px-3 pb-2 text-xs text-down">{error}</p>}

      <div className="flex-1 overflow-y-auto" role="rowgroup">
        {loading ? (
          <p className="px-3 py-4 text-sm text-muted">Loading watchlist…</p>
        ) : tickers.length === 0 ? (
          <p className="px-3 py-4 text-sm text-muted">
            No tickers yet. Add one above.
          </p>
        ) : (
          tickers.map((ticker) => (
            <WatchlistRow
              key={ticker}
              ticker={ticker}
              tick={ticks[ticker]}
              history={history[ticker] ?? []}
              selected={ticker === selectedTicker}
              onSelect={onSelectTicker}
              onRemove={removeTicker}
            />
          ))
        )}
      </div>
    </section>
  );
}
