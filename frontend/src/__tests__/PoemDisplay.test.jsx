import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import PoemDisplay from "../components/PoemDisplay.jsx";

describe("PoemDisplay", () => {
  it("ne rend rien quand le poème est vide", () => {
    const { container } = render(<PoemDisplay poem={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("rend chaque ligne et un bouton de téléchargement", () => {
    render(<PoemDisplay poem={["Je marche.", "Tu cours."]} />);
    expect(screen.getByText(/Je marche/)).toBeInTheDocument();
    expect(screen.getByText(/Tu cours/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Télécharger/i })).toBeInTheDocument();
  });
});
