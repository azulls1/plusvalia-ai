# ================================================================
# DOCKERFILE — Angular Frontend (Multi-Stage)
# Stage 1: Build Angular app
# Stage 2: Serve with Nginx
# ================================================================

# Stage 1 — Build
FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

COPY . .

# Create environment.ts (required by Angular file replacement, gitignored)
RUN if [ ! -f src/environments/environment.ts ]; then \
    cp src/environments/environment.prod.ts src/environments/environment.ts; \
    fi

RUN npm run build

# Stage 2 — Serve
FROM nginx:1.27-alpine AS production

LABEL maintainer="Samael Hernandez"
LABEL description="Frontend Plusvalia AI - Angular SPA"

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built Angular app
COPY --from=builder /app/dist/app /usr/share/nginx/html

# Security: run as non-root
RUN chown -R nginx:nginx /usr/share/nginx/html \
    && chown -R nginx:nginx /var/cache/nginx \
    && chown -R nginx:nginx /var/log/nginx \
    && touch /var/run/nginx.pid \
    && chown -R nginx:nginx /var/run/nginx.pid

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
