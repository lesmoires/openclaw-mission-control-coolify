# syntax=docker/dockerfile:1

FROM node:20-alpine AS deps
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . ./

# Allows configuring the API URL at build time.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ARG NEXT_PUBLIC_AUTH_MODE
ENV NEXT_PUBLIC_AUTH_MODE=${NEXT_PUBLIC_AUTH_MODE}

RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# Next.js standalone output includes only the files needed to run.
# Copy the standalone server and static assets.
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# `public/` is optional in Next.js apps; repo may not have it.
# Create an empty directory so the server doesn't error on missing public/.
RUN mkdir -p ./public

EXPOSE 3000

# The standalone server is a single Node.js file.
CMD ["node", "server.js"]
