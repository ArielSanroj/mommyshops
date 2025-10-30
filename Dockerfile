# syntax=docker/dockerfile:1.5

# Stage 1: install dependencies with caching
FROM node:20 AS deps
WORKDIR /app

COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

# Stage 2: bring in source code (and optional build)
FROM deps AS builder
COPY . .
# RUN npm run build

# Stage 3: run tests to fail fast
FROM builder AS test
RUN npm test

# Stage 4: prepare release artefacts without node_modules
FROM builder AS release
RUN rm -rf node_modules

# Stage 5: production image
FROM node:20-slim AS production
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

COPY --from=deps /app/package*.json ./
COPY --from=deps /app/node_modules ./node_modules
RUN npm prune --omit=dev

COPY --from=release /app ./

EXPOSE ${PORT}
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:' + process.env.PORT + '/health').then(res => { if (!res.ok) process.exit(1); }).catch(() => process.exit(1));"

USER node
CMD ["npm", "start"]
