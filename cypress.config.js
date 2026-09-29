export default {
  projectId: 't85yns',
  allowCypressEnv: false,

  e2e: {
    baseUrl: 'http://localhost:5173',
    setupNodeEvents(on) {
      on('task', {
        log(message) {
          console.log(message);
          return null;
        },
      });
    },
  },

  component: {
    devServer: {
      framework: "react",
      bundler: "vite",
    },
  },
};
