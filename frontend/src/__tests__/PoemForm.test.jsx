import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PoemForm from "../components/PoemForm.jsx";

describe("PoemForm", () => {
  it("rend les trois champs et le bouton de soumission", () => {
    render(<PoemForm onSubmit={() => {}} />);
    expect(screen.getByLabelText(/Forme/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Syllabes/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Phonétique/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Générer/i })).toBeInTheDocument();
  });

  it("appelle onSubmit avec les valeurs du formulaire", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<PoemForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/Forme/i), "ABBA");
    await user.type(screen.getByLabelText(/Syllabes/i), "1=12");
    await user.click(screen.getByRole("button", { name: /Générer/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      forme: "ABBA",
      sylla: "1=12",
      phone: "",
    });
  });

  it("désactive le bouton quand isLoading est vrai", () => {
    render(<PoemForm onSubmit={() => {}} isLoading />);
    expect(screen.getByRole("button", { name: /Génération en cours/i })).toBeDisabled();
  });

  it("applique le preset Sonnet quand on clique dessus", async () => {
    const user = userEvent.setup();
    render(<PoemForm onSubmit={() => {}} />);
    await user.click(screen.getByRole("button", { name: /^Sonnet$/ }));
    expect(screen.getByLabelText(/Forme/i)).toHaveValue("ABBA CDDC EEF GGF");
    expect(screen.getByLabelText(/Syllabes/i)).toHaveValue("1=12");
  });
});
