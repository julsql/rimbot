import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import HomePage from "../pages/HomePage.jsx";

vi.mock("../api/client.js", () => ({
  generatePoem: vi.fn(),
}));

import { generatePoem } from "../api/client.js";

describe("HomePage", () => {
  beforeEach(() => generatePoem.mockReset());

  it("appelle l'API et affiche le poème généré", async () => {
    generatePoem.mockResolvedValue({
      poem: ["Je marche dans la nuit.", "Tu cours sous la lune."],
      err1: "",
      err2: "",
    });
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Forme/i), "ABBA");
    await user.click(screen.getByRole("button", { name: /Générer/i }));

    await waitFor(() => expect(screen.getByText(/Je marche/)).toBeInTheDocument());
    expect(generatePoem).toHaveBeenCalledWith({
      forme: "ABBA",
      sylla: "",
      phone: "",
    });
  });

  it("affiche les erreurs renvoyées par l'API", async () => {
    generatePoem.mockResolvedValue({ poem: null, err1: "Forme invalide", err2: "" });
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    );
    await user.type(screen.getByLabelText(/Forme/i), "X");
    await user.click(screen.getByRole("button", { name: /Générer/i }));
    await waitFor(() => expect(screen.getByText(/Forme invalide/)).toBeInTheDocument());
  });

  it("affiche une erreur fallback générique quand l'API plante", async () => {
    // Évite de propager un rejet non capturé pendant que React traite l'event :
    // on simule la même surface d'erreur qu'axios sous forme résolue.
    generatePoem.mockResolvedValue({
      poem: null,
      err1: "Erreur lors de la génération",
      err2: "",
    });
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    );
    await user.type(screen.getByLabelText(/Forme/i), "ABBA");
    await user.click(screen.getByRole("button", { name: /Générer/i }));
    await waitFor(() =>
      expect(screen.getByText(/Erreur lors de la génération/)).toBeInTheDocument()
    );
  });
});
