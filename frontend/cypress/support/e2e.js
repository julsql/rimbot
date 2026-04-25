// Hooks et commandes globales Cypress.
// Logge les erreurs réseau pour debug, mais ne fait pas planter le test pour
// des warnings React Router en console.

Cypress.on("uncaught:exception", (err) => {
  if (err.message && err.message.includes("ResizeObserver")) {
    return false;
  }
});
