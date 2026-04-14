describe('Map Page', () => {
  beforeEach(() => {
    cy.visit('/mapa');
  });

  it('should load the map', () => {
    cy.waitForMap();
    cy.get('.leaflet-tile-container').should('exist');
  });

  it('should display predictions count', () => {
    cy.get('[aria-label="Estadísticas del sistema"]', { timeout: 15000 }).should('be.visible');
    cy.contains('predicciones').should('exist');
  });

  it('should switch view modes', () => {
    cy.contains('button', 'Predicciones').click();
    cy.contains('Modo cambiado').should('be.visible');
    cy.contains('button', 'Precios').click();
    cy.contains('Modo cambiado').should('be.visible');
  });

  it('should filter by city', () => {
    cy.get('[aria-label="Filtrar predicciones por ciudad"]').select('Guadalajara');
    cy.contains('Cargando').should('exist');
  });

  it('should open and close chatbot', () => {
    cy.get('app-ai-chatbot').should('exist');
  });

  it('should have accessible elements', () => {
    cy.get('[role="main"]').should('have.attr', 'aria-label');
    cy.get('[role="application"]').should('have.attr', 'aria-label');
    cy.get('#map').should('exist');
  });

  it('should show export options', () => {
    cy.get('app-export-reports').should('exist');
  });

  it('should show stats dashboard', () => {
    cy.get('app-stats-dashboard').should('exist');
  });
});
