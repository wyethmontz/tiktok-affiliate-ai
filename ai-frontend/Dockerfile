# ── Build stage ──────────────────────────────────────────────────────────────
FROM node:22.22.2-alpine AS builder
WORKDIR /app

COPY package*.json .
RUN npm ci

COPY . .

ARG NEXT_PUBLIC_SUPABASE_URL=https://placeholder.supabase.co
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY=placeholder
ARG BACKEND_URL=http://backend:8000

ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY \
    BACKEND_URL=$BACKEND_URL

RUN npm run build

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM node:22.22.2-alpine AS runtime
WORKDIR /app

RUN apk upgrade --no-cache

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static
COPY --from=builder --chown=appuser:appgroup /app/public ./public

USER appuser

ENV HOSTNAME=0.0.0.0

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget -qO- http://127.0.0.1:3000 || exit 1

EXPOSE 3000
CMD ["node", "server.js"]
