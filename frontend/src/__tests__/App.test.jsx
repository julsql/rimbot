import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../api/client.js", () => ({
  fetchSyllables: vi.fn(() => new Promise(() => {})),
  generatePoem: vi.fn(),
}));

import App from "../App.jsx";

describe("App canonical", () => {
  beforeEach(() => {
    document.head.innerHTML = '<link rel="canonical" href="https://rimbot.julsql.fr/" />';
  });

  it.each([
    ["/", "https://rimbot.julsql.fr/"],
    ["/aide", "https://rimbot.julsql.fr/aide"],
  ])("met à jour le canonical pour %s", (path, expected) => {
    render(
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    );
    expect(document.querySelector('link[rel="canonical"]').getAttribute("href")).toBe(expected);
  });
});
