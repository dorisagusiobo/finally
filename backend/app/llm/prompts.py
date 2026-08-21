"""System prompt and portfolio/watchlist context construction (PLAN.md §9)."""

from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = (
    "You are FinAlly, an AI trading assistant for a simulated trading platform. "
    "Analyze the user's portfolio composition, risk concentration, and P&L. "
    "Suggest trades with clear reasoning, and execute trades when the user asks "
    "or agrees. Proactively manage the user's watchlist when relevant. Be "
    "concise and data-driven in your responses. Always respond with valid JSON "
    "matching the required schema."
)


def build_context_message(portfolio: dict[str, Any], watchlist: list[dict[str, Any]]) -> str:
    """Render current portfolio + watchlist state as text for the prompt."""
    lines = [
        f"Cash balance: ${portfolio['cash_balance']:.2f}",
        f"Total portfolio value: ${portfolio['total_value']:.2f}",
        f"Total unrealized P&L: ${portfolio['total_unrealized_pnl']:.2f}",
        "",
        "Positions:",
    ]
    if portfolio["positions"]:
        for p in portfolio["positions"]:
            lines.append(
                f"- {p['ticker']}: {p['quantity']} shares @ avg cost ${p['avg_cost']:.2f}, "
                f"current ${p['current_price']:.2f}, unrealized P&L "
                f"${p['unrealized_pnl']:.2f} ({p['unrealized_pnl_percent']:.2f}%)"
            )
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Watchlist:")
    if watchlist:
        for w in watchlist:
            if w["price"] is None:
                lines.append(f"- {w['ticker']}: price unavailable")
            else:
                lines.append(f"- {w['ticker']}: ${w['price']:.2f} ({w['change_percent']:+.2f}%)")
    else:
        lines.append("- none")

    return "\n".join(lines)


def build_messages(
    portfolio: dict[str, Any],
    watchlist: list[dict[str, Any]],
    history: list[dict[str, Any]],
    user_message: str,
) -> list[dict[str, str]]:
    """Assemble the full message list: system+context, history, new message."""
    system_content = SYSTEM_PROMPT + "\n\n" + build_context_message(portfolio, watchlist)
    messages = [{"role": "system", "content": system_content}]
    messages.extend({"role": h["role"], "content": h["content"]} for h in history)
    messages.append({"role": "user", "content": user_message})
    return messages
