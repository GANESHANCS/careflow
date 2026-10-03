# Stage 1: Build static assets
FROM node:24-alpine AS builder

WORKDIR /app

# Copy dependency specifications and lockfile
COPY package.json package-lock.json ./
RUN npm ci

# Copy frontend source code and configurations
COPY . .

# Build production bundle
RUN npm run build

# Stage 2: Serve with lightweight Nginx Alpine container
FROM nginx:alpine-slim

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

# Run Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
