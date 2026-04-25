/// <reference types="cypress" />

describe("Page d'accueil", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("affiche le titre et la barre de navigation", () => {
    cy.contains("h1", "Générateur").should("be.visible");
    cy.get(".topbar nav a").should("have.length", 2);
    cy.contains(".topbar nav a", "Générateur").should("be.visible");
    cy.contains(".topbar nav a", "Aide phonétique").should("be.visible");
  });

  it("affiche les trois champs du formulaire", () => {
    cy.contains("label", /Forme/i).should("be.visible");
    cy.contains("label", /Syllabes/i).should("be.visible");
    cy.contains("label", /Phonétique/i).should("be.visible");
  });

  it("propose les presets Sonnet / Haïku / Ballade", () => {
    cy.contains("button", "Sonnet").should("be.visible");
    cy.contains("button", "Haïku").should("be.visible");
    cy.contains("button", "Ballade").should("be.visible");
  });

  it("preset Sonnet remplit le champ forme", () => {
    cy.contains("button", "Sonnet").click();
    cy.contains("label", /Forme/i)
      .find("input")
      .should("have.value", "ABBA CDDC EEF GGF");
  });
});

describe("Aide phonétique", () => {
  it("la page se charge et liste des syllabes", () => {
    cy.visit("/aide");
    cy.contains("h1", "Aide phonétique").should("be.visible");
    cy.get("table.phon-table thead th").should("have.length", 4);
    cy.get("table.phon-table tbody tr", { timeout: 15000 })
      .its("length")
      .should("be.greaterThan", 50);
  });
});
