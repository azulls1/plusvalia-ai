// Custom Cypress commands
declare namespace Cypress {
  interface Chainable {
    waitForMap(): Chainable<void>;
  }
}

Cypress.Commands.add('waitForMap', () => {
  cy.get('#map', { timeout: 15000 }).should('be.visible');
  cy.get('.leaflet-container', { timeout: 15000 }).should('exist');
});
