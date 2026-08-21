import type { ConnectionState } from "@/lib/types";

const STATE_STYLES: Record<ConnectionState, { color: string; label: string }> = {
  connected: { color: "bg-up", label: "Connected" },
  reconnecting: { color: "bg-yellow", label: "Reconnecting" },
  disconnected: { color: "bg-down", label: "Disconnected" },
};

export function ConnectionDot({ state }: { state: ConnectionState }) {
  const { color, label } = STATE_STYLES[state];
  return (
    <div className="flex items-center gap-2" data-testid="connection-dot" data-state={state}>
      <span
        className={`h-2.5 w-2.5 rounded-full ${color} ${
          state === "reconnecting" ? "animate-pulse" : ""
        }`}
      />
      <span className="text-xs text-muted">{label}</span>
    </div>
  );
}
