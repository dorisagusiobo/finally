import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";
import { EventSourceMock } from "./src/test/EventSourceMock";

// @ts-expect-error jsdom does not implement EventSource
global.EventSource = EventSourceMock;

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

// jsdom has no canvas 2D context, and lightweight-charts is not the thing
// under test in component specs — stub it with inert chart/series objects.
vi.mock("lightweight-charts", () => {
  const series = {
    setData: vi.fn(),
    update: vi.fn(),
    applyOptions: vi.fn(),
  };
  const chart = {
    addSeries: vi.fn(() => series),
    applyOptions: vi.fn(),
    remove: vi.fn(),
    timeScale: vi.fn(() => ({ fitContent: vi.fn() })),
  };
  return {
    createChart: vi.fn(() => chart),
    AreaSeries: {},
    LineSeries: {},
    ColorType: { Solid: "solid" },
  };
});
