"use client";

import { useState } from "react";
import { Header } from "@/components/Header";
import { MainChart } from "@/components/MainChart";
import { TradeBar } from "@/components/TradeBar";
import { WatchlistPanel } from "@/components/watchlist/WatchlistPanel";
import { Heatmap } from "@/components/portfolio/Heatmap";
import { PnLChart } from "@/components/portfolio/PnLChart";
import { PositionsTable } from "@/components/portfolio/PositionsTable";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { PriceStreamProvider } from "@/lib/PriceStreamContext";
import { PortfolioProvider } from "@/lib/PortfolioContext";
import { WatchlistProvider } from "@/lib/WatchlistContext";

function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);

  return (
    <div className="flex h-screen flex-col">
      <Header />
      <div className="grid min-h-0 flex-1 grid-cols-[300px_1fr_340px]">
        <aside className="min-h-0 border-r border-border-muted bg-panel">
          <WatchlistPanel
            selectedTicker={selectedTicker}
            onSelectTicker={setSelectedTicker}
          />
        </aside>

        <main className="flex min-h-0 flex-col">
          <div className="min-h-0 flex-[3] border-b border-border-muted bg-panel">
            <MainChart ticker={selectedTicker} />
          </div>
          <div className="grid min-h-0 flex-[2] grid-cols-2 border-b border-border-muted">
            <div className="min-h-0 border-r border-border-muted bg-panel">
              <Heatmap />
            </div>
            <div className="min-h-0 bg-panel">
              <PnLChart />
            </div>
          </div>
          <div className="min-h-0 flex-[2] bg-panel">
            <PositionsTable />
          </div>
          <TradeBar />
        </main>

        <div className="min-h-0">
          <ChatPanel />
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <PriceStreamProvider>
      <PortfolioProvider>
        <WatchlistProvider>
          <Dashboard />
        </WatchlistProvider>
      </PortfolioProvider>
    </PriceStreamProvider>
  );
}
