/// <reference types="cypress" />

describe("Génération de poème (smoke e2e)", () => {
  it("génère un poème ABBA via l'API réelle et l'affiche", () => {
    cy.visit("/");
    cy.contains("label", /Forme/i).find("input").type("ABBA");

    // Capture la requête réseau pour vérifier le payload aussi.
    cy.intercept("POST", "/api/poem/generate").as("generate");
    cy.contains("button", "Générer").click();

    cy.wait("@generate", { timeout: 60000 })
      .its("response.statusCode")
      .should("eq", 200);

    cy.get(".poem-display .poem", { timeout: 60000 })
      .should("be.visible")
      .invoke("text")
      .then((text) => {
        const lines = text
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean);
        expect(lines.length, "nombre de vers").to.be.gte(4);
      });

    cy.contains("button", "Télécharger").should("be.visible");
  });

  it("affiche un message d'erreur quand la forme est vide", () => {
    cy.visit("/");
    cy.intercept("POST", "/api/poem/generate").as("generate");
    // On enlève l'attribut `required` HTML5 pour pouvoir soumettre vide,
    // puis on déclenche la requête côté API.
    cy.contains("label", /Forme/i)
      .find("input")
      .invoke("removeAttr", "required");
    cy.contains("button", "Générer").click();

    cy.wait("@generate").its("response.statusCode").should("eq", 400);
    cy.contains(/aucune forme/i).should("be.visible");
  });

  it("génère un haïku 3 vers (5/7/5)", () => {
    cy.visit("/");
    cy.contains("button", "Haïku").click();

    cy.intercept("POST", "/api/poem/generate").as("generate");
    cy.contains("button", "Générer").click();

    cy.wait("@generate", { timeout: 60000 })
      .its("response.statusCode")
      .should("eq", 200);

    cy.get(".poem-display .poem", { timeout: 60000 })
      .invoke("text")
      .then((text) => {
        const lines = text
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean);
        expect(lines.length, "vers de haïku").to.be.gte(3);
      });
  });
});
