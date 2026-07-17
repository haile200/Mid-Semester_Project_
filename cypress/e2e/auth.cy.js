describe('Authentication end-to-end', () => {
  const email = `e2e+${Date.now()}@example.com`;
  const password = 'Password123!';
  const name = 'E2E User';

  it('signs up, logs in, and logs out successfully', () => {
    cy.intercept('POST', '**/api/signup').as('signup');
    cy.intercept('POST', '**/api/login').as('login');
    cy.intercept('POST', '**/api/logout').as('logout');
    cy.intercept('GET', '**/api/auth/me').as('me');

    cy.visit('/signup');

    // Signup process
    cy.get('[data-cy="signup-name"]').find('input').type(name);
    cy.get('[data-cy="signup-email"]').find('input').type(email);
    cy.get('[data-cy="signup-password"]').find('input').type(password);
    cy.get('[data-cy="signup-confirm-password"]').find('input').type(password);
    cy.get('[data-cy="signup-submit"]').click();

    cy.wait('@signup', { timeout: 10000 }).its('response.statusCode').should('eq', 201);
    cy.location('pathname', { timeout: 10000 }).should('eq', '/login');

    // Login process
    cy.get('[data-cy="login-email"]').find('input').clear().type(email).should('have.value', email);
    cy.get('[data-cy="login-password"]').find('input').clear().type(password).should('have.value', password);
    cy.get('[data-cy="login-submit"]').should('be.visible').click();

    cy.wait('@login', { timeout: 10000 }).then(({ response, request }) => {
      expect(response.statusCode).to.equal(200);
      expect(request.body).to.deep.equal({ email, password });
    });

    // Verify successful login
    cy.location('pathname', { timeout: 15000 }).should('eq', '/');
    cy.contains(email, { timeout: 15000 }).should('exist');

    // View Profile process
    cy.get('[data-cy="profile-link"]').click();

    // Assert the UI correctly displays the profile page and user data
    cy.location('pathname', { timeout: 10000 }).should('eq', '/profile');
    cy.wait('@me', { timeout: 10000 }).its('response.statusCode').should('eq', 200);
    cy.get('[data-cy="profile-name"]').should('contain', name);
    cy.get('[data-cy="profile-email"]').should('contain', email);

    // Logout process
    cy.get('[data-cy="logout-button"]').click();
    cy.wait('@logout', { timeout: 10000 }).its('response.statusCode').should('eq', 200);
    cy.contains('Login', { timeout: 10000 }).should('exist');
  });
});