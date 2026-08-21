"use client";

import { useRef, useState, type FormEvent } from "react";
import { postChatMessage } from "@/lib/api";
import { usePortfolio } from "@/lib/PortfolioContext";
import { useWatchlist } from "@/lib/WatchlistContext";
import type { ChatMessage } from "@/lib/types";
import { ChatMessageItem } from "./ChatMessageItem";

function makeId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function ChatPanel() {
  const { setPortfolio } = usePortfolio();
  const { refresh: refreshWatchlist } = useWatchlist();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const listEndRef = useRef<HTMLDivElement>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const userMessage: ChatMessage = {
      id: makeId(),
      role: "user",
      content: text,
      createdAt: Date.now(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await postChatMessage(text);
      setPortfolio(res.portfolio);
      if (res.actions.watchlist_changes.some((c) => c.status === "executed")) {
        refreshWatchlist();
      }
      const assistantMessage: ChatMessage = {
        id: makeId(),
        role: "assistant",
        content: res.message,
        actions: res.actions,
        createdAt: Date.now(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: "assistant",
          content: "Something went wrong reaching the AI assistant.",
          createdAt: Date.now(),
        },
      ]);
    } finally {
      setLoading(false);
      requestAnimationFrame(() =>
        listEndRef.current?.scrollIntoView?.({ behavior: "smooth" })
      );
    }
  };

  if (collapsed) {
    return (
      <button
        type="button"
        onClick={() => setCollapsed(false)}
        aria-label="Expand chat panel"
        className="flex h-full w-10 flex-col items-center justify-center gap-2 border-l border-border-muted bg-panel text-muted hover:text-foreground"
      >
        <span className="rotate-90 whitespace-nowrap text-xs font-semibold uppercase tracking-wide">
          AI Chat
        </span>
      </button>
    );
  }

  return (
    <section className="flex h-full flex-col border-l border-border-muted bg-panel" aria-label="AI chat">
      <div className="flex items-center justify-between border-b border-border-muted px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-muted">
          AI Assistant
        </h2>
        <button
          type="button"
          onClick={() => setCollapsed(true)}
          aria-label="Collapse chat panel"
          className="text-muted hover:text-foreground"
        >
          ✕
        </button>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto px-3 py-3">
        {messages.length === 0 && (
          <p className="text-sm text-muted">
            Ask FinAlly about your portfolio, or tell it to make a trade.
          </p>
        )}
        {messages.map((message) => (
          <ChatMessageItem key={message.id} message={message} />
        ))}
        {loading && (
          <div
            data-testid="chat-loading"
            className="flex justify-start text-sm text-muted"
          >
            FinAlly is thinking…
          </div>
        )}
        <div ref={listEndRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-t border-border-muted p-3"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask FinAlly…"
          aria-label="Chat message"
          disabled={loading}
          className="min-w-0 flex-1 rounded border border-border-muted bg-background px-2 py-1.5 text-sm outline-none focus:border-blue disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-purple px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </section>
  );
}
