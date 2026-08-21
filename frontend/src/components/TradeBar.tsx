"use client";

import { useState } from "react";
import { postTrade } from "@/lib/api";
import { usePortfolio } from "@/lib/PortfolioContext";
import { formatCurrency } from "@/lib/format";
import type { TradeSide } from "@/lib/types";

interface Feedback {
  type: "success" | "error";
  text: string;
}

export function TradeBar() {
  const { setPortfolio } = usePortfolio();
  const [ticker, setTicker] = useState("");
  const [quantity, setQuantity] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  const handleTrade = async (side: TradeSide) => {
    const normalizedTicker = ticker.trim().toUpperCase();
    const qty = Number(quantity);

    if (!normalizedTicker || !qty || qty <= 0) {
      setFeedback({
        type: "error",
        text: "Enter a ticker and a positive quantity",
      });
      return;
    }

    setSubmitting(true);
    setFeedback(null);
    try {
      const res = await postTrade(normalizedTicker, qty, side);
      if (res.success) {
        setPortfolio(res.portfolio);
        setFeedback({
          type: "success",
          text: `${side === "buy" ? "Bought" : "Sold"} ${qty} ${normalizedTicker} @ ${formatCurrency(
            res.trade.price
          )}`,
        });
        setQuantity("");
      } else {
        setFeedback({ type: "error", text: res.error });
      }
    } catch {
      setFeedback({ type: "error", text: "Trade request failed" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex items-center gap-2 border-t border-border-muted bg-panel px-4 py-3">
      <input
        type="text"
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        placeholder="Ticker"
        aria-label="Trade ticker"
        className="w-24 rounded border border-border-muted bg-background px-2 py-1.5 text-sm uppercase outline-none focus:border-blue"
      />
      <input
        type="number"
        min="0"
        step="any"
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        placeholder="Qty"
        aria-label="Trade quantity"
        className="w-24 rounded border border-border-muted bg-background px-2 py-1.5 text-sm outline-none focus:border-blue"
      />
      <button
        type="button"
        disabled={submitting}
        onClick={() => handleTrade("buy")}
        className="rounded bg-purple px-4 py-1.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
      >
        Buy
      </button>
      <button
        type="button"
        disabled={submitting}
        onClick={() => handleTrade("sell")}
        className="rounded border border-down px-4 py-1.5 text-sm font-semibold text-down hover:bg-down/10 disabled:opacity-50"
      >
        Sell
      </button>
      {feedback && (
        <span
          data-testid="trade-feedback"
          className={`text-sm ${
            feedback.type === "success" ? "text-up" : "text-down"
          }`}
        >
          {feedback.text}
        </span>
      )}
    </div>
  );
}
