FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/ikuchio-cup-2025/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ikuchio-cup-2025/ ./

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config template
COPY frontend/nginx.conf /etc/nginx/nginx.conf.template

# Install envsubst for environment variable substitution
RUN apk add --no-cache gettext

# Create startup script
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'envsubst "\$PORT" < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf' >> /start.sh && \
    echo 'nginx -g "daemon off;"' >> /start.sh && \
    chmod +x /start.sh

CMD ["/start.sh"]