import type { ChatMessage } from "@/lib/types";
import { formatCurrency, formatQuantity } from "@/lib/format";

export function ChatMessageItem({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const trades = message.actions?.trades ?? [];
  const watchlistChanges = message.actions?.watchlist_changes ?? [];

  return (
    <div
      data-testid="chat-message"
      data-role={message.role}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser ? "bg-blue text-white" : "bg-elevated"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>

        {(trades.length > 0 || watchlistChanges.length > 0) && (
          <div className="mt-2 space-y-1 border-t border-white/10 pt-2">
            {trades.map((trade, i) => (
              <div
                key={`trade-${i}`}
                data-testid="chat-trade-action"
                data-status={trade.status}
                className={`text-xs ${
                  trade.status === "executed" ? "text-up" : "text-down"
                }`}
              >
                {trade.status === "executed" ? "✓" : "✗"}{" "}
                {trade.side === "buy" ? "Bought" : "Sold"}{" "}
                {formatQuantity(trade.quantity)} {trade.ticker}
                {trade.price != null && ` @ ${formatCurrency(trade.price)}`}
                {trade.status === "failed" && trade.error && ` — ${trade.error}`}
              </div>
            ))}
            {watchlistChanges.map((change, i) => (
              <div
                key={`watchlist-${i}`}
                data-testid="chat-watchlist-action"
                data-status={change.status}
                className={`text-xs ${
                  change.status === "executed" ? "text-up" : "text-down"
                }`}
              >
                {change.status === "executed" ? "✓" : "✗"}{" "}
                {change.action === "add" ? "Added" : "Removed"} {change.ticker}
                {change.status === "failed" &&
                  change.error &&
                  ` — ${change.error}`}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
