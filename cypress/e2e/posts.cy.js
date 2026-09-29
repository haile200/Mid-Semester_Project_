// Posting and commenting end to end, against the dev servers (npm run start:all).
// The tests tell one story in order: an author publishes a post with a photo, another climber likes
// it and comments, and the author replies. Each test logs in on its own; they share only the post.
// Every run creates its own accounts, so it never depends on data already in the database.

const stamp = Date.now();
const author = { name: 'E2E Author', email: `e2e-author-${stamp}@example.test`, password: 'Password123!' };
const reader = { name: 'E2E Reader', email: `e2e-reader-${stamp}@example.test`, password: 'Password123!' };
const title = `Crimpy V4 at the gym ${stamp}`;
const readerComment = 'Nice send! Did you use the heel hook at the top?';
const authorReply = 'Yes, the heel hook made all the difference.';

// Model calls (toxicity check, comment ideas) can take several seconds.
const AI_TIMEOUT = 30000;

const postCard = () => cy.contains('[data-cy="post-card"]', title);

describe('Posting and commenting end-to-end', () => {
  it('publishes a post with a photo and shows it at the top of the feed', () => {
    cy.intercept('POST', '**/api/uploads').as('upload');
    cy.intercept('POST', '**/api/posts').as('createPost');
    cy.visitAs(author, '/new-post');

    cy.get('[data-cy="new-post-title"]').type(title);
    cy.contains('.new-post-chip', 'Bouldering').click();
    cy.contains('.new-post-chip', 'V4').click();

    cy.get('[data-cy="image-upload-input"]').selectFile('cypress/fixtures/crag.jpg', { force: true });
    cy.wait('@upload').its('response.statusCode').should('eq', 201);
    cy.get('[data-cy="new-post-image-preview"] img')
      .should('have.attr', 'src')
      .and('match', /^\/uploads\/[0-9a-f]{32}\.jpg$/);

    cy.get('.ql-editor').type('Finally sent it after three sessions. Quiet feet on the last move.');
    cy.get('[data-cy="new-post-submit"]').click();
    cy.wait('@createPost', { responseTimeout: AI_TIMEOUT }).its('response.statusCode').should('eq', 201);

    cy.location('pathname').should('eq', '/');
    cy.get('[data-cy="post-card"]').first().should('contain', title);
    postCard()
      .find('[data-cy="post-image"]')
      .should('be.visible')
      .and(($image) => expect($image[0].naturalWidth).to.be.greaterThan(0));
  });

  it('refuses a hostile post and keeps the draft so it can be fixed', () => {
    cy.intercept('POST', '**/api/posts').as('createPost');
    cy.visitAs(author, '/new-post');

    cy.get('[data-cy="new-post-title"]').type('About the route setters');
    cy.get('.ql-editor').type('You are an idiot, shut up and learn to set.');
    cy.get('[data-cy="new-post-submit"]').click();

    cy.wait('@createPost', { responseTimeout: AI_TIMEOUT }).its('response.statusCode').should('eq', 400);
    cy.get('[data-cy="new-post-error"]').should('contain', 'Not published');
    cy.location('pathname').should('eq', '/new-post');
    cy.get('[data-cy="new-post-title"]').should('have.value', 'About the route setters');
  });

  it('lets another climber like the post, get comment ideas and comment', () => {
    cy.intercept('PUT', '**/api/posts/*/like').as('like');
    cy.intercept('GET', '**/api/posts/*/comment-ideas').as('ideas');
    cy.intercept('POST', '**/api/posts/*/comments').as('comment');
    cy.visitAs(reader, '/');

    postCard().find('[data-cy="like-button"]').click();
    cy.wait('@like').its('response.body.likeCount').should('eq', 1);
    postCard().find('[data-cy="like-button"]').should('contain', '1');

    postCard().find('[data-cy="beta-toggle"]').click();
    postCard().find('[data-cy="comment-thread"]').should('contain', 'No beta yet');

    // An idea only fills the box; the climber still decides what to send.
    postCard().find('[data-cy="comment-ideas-button"]').click();
    cy.wait('@ideas', { responseTimeout: AI_TIMEOUT }).its('response.statusCode').should('eq', 200);
    postCard().find('[data-cy="comment-idea"]').should('have.length', 3);
    postCard().find('[data-cy="comment-idea"]').first().invoke('text').then((idea) => {
      postCard().find('[data-cy="comment-idea"]').first().click();
      postCard().find('[data-cy="comment-input"]').should('have.value', idea);
    });

    postCard().find('[data-cy="comment-input"]').clear().type(readerComment);
    postCard().find('[data-cy="comment-submit"]').click();
    cy.wait('@comment', { responseTimeout: AI_TIMEOUT }).its('response.statusCode').should('eq', 201);
    postCard()
      .find('[data-cy="comment"]')
      .should('have.length', 1)
      .and('contain', reader.name)
      .and('contain', readerComment);
  });

  it('lets the author reply, and shows the reply inside the comment it answers', () => {
    cy.intercept('POST', '**/api/posts/*/comments').as('comment');
    cy.visitAs(author, '/');

    postCard().find('[data-cy="beta-toggle"]').click();
    postCard().contains('[data-cy="comment"]', readerComment).find('[data-cy="comment-reply"]').first().click();
    postCard().find('[data-cy="replying-to"]').should('contain', `Replying to ${reader.name}`);

    postCard().find('[data-cy="comment-input"]').type(authorReply);
    postCard().find('[data-cy="comment-submit"]').click();
    cy.wait('@comment', { responseTimeout: AI_TIMEOUT }).then(({ request, response }) => {
      expect(response.statusCode).to.equal(201);
      expect(request.body.parent_id).to.be.a('number');
    });

    // Nested inside the reader's comment, not added at the top level.
    postCard()
      .contains('[data-cy="comment"]', readerComment)
      .find('.comment-replies [data-cy="comment"]')
      .should('contain', author.name)
      .and('contain', authorReply);
    postCard().find('[data-cy="replying-to"]').should('not.exist');
  });
});
