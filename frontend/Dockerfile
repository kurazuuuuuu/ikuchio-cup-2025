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

# Copy nginx config
COPY frontend/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]