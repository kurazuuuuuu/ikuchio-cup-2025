FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build-only

# Install serve to serve static files
RUN npm install -g serve

# Expose port
EXPOSE 80

# Start command
CMD ["serve", "-s", "dist", "-l", "80"]