import { describe, expect, it } from "vitest";
import { wsUrl } from "@/features/live/ws-url";

describe("wsUrl", () => {
  it("turns http into ws and adds the api key", () => {
    expect(wsUrl("http://localhost:8000", "k 1")).toBe("ws://localhost:8000/ws?api_key=k%201");
  });
  it("turns https into wss and drops a trailing slash", () => {
    expect(wsUrl("https://api.example.com/", "")).toBe("wss://api.example.com/ws");
  });
});
