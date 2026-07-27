import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { HomePage } from "@/pages/public/HomePage";

describe("HomePage", () => {
  it("renders brand hero", () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>,
    );
    expect(screen.getAllByText("TetherFit").length).toBeGreaterThan(0);
    expect(screen.getByText(/Run your coaching business/i)).toBeInTheDocument();
  });
});
