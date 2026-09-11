FROM node:20-alpine AS dependencies

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder

WORKDIR /app

# Local-safe defaults. Production CI must override all public build arguments explicitly.
ARG NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
ARG NEXT_PUBLIC_PAPERFORGE_PREVIEW_AUTO_LOGIN=false
ARG NEXT_PUBLIC_PAPERFORGE_APP_ENV=development
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    NEXT_PUBLIC_PAPERFORGE_PREVIEW_AUTO_LOGIN=${NEXT_PUBLIC_PAPERFORGE_PREVIEW_AUTO_LOGIN} \
    NEXT_PUBLIC_PAPERFORGE_APP_ENV=${NEXT_PUBLIC_PAPERFORGE_APP_ENV} \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.ts ./next.config.ts

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
