import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import HelpPage from "../pages/HelpPage.jsx";

vi.mock("../api/client.js", () => ({
  fetchSyllables: vi.fn(),
}));

import { fetchSyllables } from "../api/client.js";

describe("HelpPage", () => {
  beforeEach(() => {
    fetchSyllables.mockReset();
  });

  it("affiche un état de chargement initial", () => {
    fetchSyllables.mockReturnValue(new Promise(() => {}));
    render(
      <MemoryRouter>
        <HelpPage />
      </MemoryRouter>
    );
    expect(screen.getByText(/Chargement/)).toBeInTheDocument();
  });

  it("affiche les rangées renvoyées par l'API", async () => {
    fetchSyllables.mockResolvedValue([
      { courant: "t@t", dersyll: "tat", API: "t@t", nboccurence: 42 },
      { courant: "se", dersyll: "se", API: "se", nboccurence: 19 },
    ]);
    render(
      <MemoryRouter>
        <HelpPage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText("42")).toBeInTheDocument());
    // "t@t" apparaît deux fois (colonnes "Syllabes" et "API")
    expect(screen.getAllByText("t@t")).toHaveLength(2);
    expect(screen.getByText("19")).toBeInTheDocument();
  });

  it("affiche un message d'erreur en cas d'échec réseau", async () => {
    fetchSyllables.mockRejectedValue(new Error("boum"));
    render(
      <MemoryRouter>
        <HelpPage />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText(/boum/)).toBeInTheDocument());
  });
});
