# Stage 1: build the React app.
FROM node:24-alpine AS build
WORKDIR /app

# Cypress is only for end-to-end tests; skip downloading its large browser binary.
ENV CYPRESS_INSTALL_BINARY=0

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src
RUN npm run build

# Stage 2: serve the built files. Node and node_modules stay behind in stage 1.
FROM nginx:stable-alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
