import { describe, expect, it } from "vitest";

describe("phase5 scheduling helpers", () => {
  it("maps weekday labels", () => {
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    expect(days[0]).toBe("Mon");
    expect(days.length).toBe(7);
  });
});
