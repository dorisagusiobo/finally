export class EventSourceMock {
  static instances: EventSourceMock[] = [];

  url: string;
  readyState = 0;
  onopen: ((ev: Event) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    EventSourceMock.instances.push(this);
  }

  emitOpen() {
    this.readyState = 1;
    this.onopen?.(new Event("open"));
  }

  emitMessage(data: unknown) {
    this.onmessage?.(
      new MessageEvent("message", { data: JSON.stringify(data) })
    );
  }

  emitError() {
    this.onerror?.(new Event("error"));
  }

  close() {
    this.readyState = 2;
  }

  static reset() {
    EventSourceMock.instances = [];
  }

  static latest(): EventSourceMock {
    const instance = EventSourceMock.instances.at(-1);
    if (!instance) throw new Error("No EventSourceMock instance created yet");
    return instance;
  }
}
