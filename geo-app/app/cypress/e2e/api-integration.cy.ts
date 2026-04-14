describe('API Integration', () => {
  it('should fetch heatmap data', () => {
    cy.request('GET', 'http://localhost:8000/predictions/heatmap?limit=5').then((response) => {
      expect(response.status).to.eq(200);
      expect(response.body).to.have.property('points');
      expect(response.body.points).to.be.an('array');
    });
  });

  it('should fetch city stats', () => {
    cy.request('GET', 'http://localhost:8000/predictions/stats-by-city').then((response) => {
      expect(response.status).to.eq(200);
      expect(response.body).to.have.property('cities');
    });
  });

  it('should require API key for training', () => {
    cy.request({
      method: 'POST',
      url: 'http://localhost:8000/train',
      failOnStatusCode: false,
      body: {},
    }).then((response) => {
      expect(response.status).to.be.oneOf([403, 422]);
    });
  });

  it('should return health status', () => {
    cy.request('GET', 'http://localhost:8000/health').then((response) => {
      expect(response.status).to.eq(200);
      expect(response.body).to.have.property('status');
    });
  });

  it('should expose prometheus metrics', () => {
    cy.request('GET', 'http://localhost:8000/metrics').then((response) => {
      expect(response.status).to.eq(200);
      expect(response.body).to.include('http_request');
    });
  });
});
