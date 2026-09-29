// Custom commands shared by the specs. https://on.cypress.io/custom-commands

// Creates the account if needed and logs in through the API. The auth spec already covers the
// signup and login forms; going through the API here keeps the other specs fast and focused.
Cypress.Commands.add('signUpAndLogIn', (user) => {
  // 400 means the account already exists, which is fine for a spec that logs in more than once.
  cy.request({ method: 'POST', url: '/api/signup', body: user, failOnStatusCode: false })
    .its('status')
    .should('be.oneOf', [201, 400]);

  // The server answers with the session cookie, which Cypress keeps for the next requests.
  return cy.request('POST', '/api/login', { email: user.email, password: user.password }).its('body.user');
});

// Opens a page as the given user: the app reads the logged-in user from localStorage, as the
// Login page leaves it.
Cypress.Commands.add('visitAs', (user, path) => {
  cy.signUpAndLogIn(user).then((loggedIn) => {
    cy.visit(path, {
      onBeforeLoad(win) {
        win.localStorage.setItem('currentUser', JSON.stringify(loggedIn));
      },
    });
  });
});
