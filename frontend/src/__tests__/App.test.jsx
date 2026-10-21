import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../api/client.js", () => ({
  fetchSyllables: vi.fn(() => new Promise(() => {})),
  generatePoem: vi.fn(),
}));

import App from "../App.jsx";
import { PAGES } from "../seo.js";

describe("App page meta", () => {
  beforeEach(() => {
    document.head.innerHTML =
      '<link rel="canonical" href="https://rimbot.julsql.fr/" />' +
      '<meta name="description" content="" />';
  });

  it.each([
    ["/", "https://rimbot.julsql.fr/"],
    ["/aide", "https://rimbot.julsql.fr/aide"],
  ])("met à jour les métadonnées pour %s", (path, expected) => {
    render(
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    );
    expect(document.querySelector('link[rel="canonical"]').getAttribute("href")).toBe(expected);
    expect(document.title).toBe(PAGES[path].title);
    expect(document.querySelector('meta[name="description"]').getAttribute("content")).toBe(
      PAGES[path].description
    );
  });
});
