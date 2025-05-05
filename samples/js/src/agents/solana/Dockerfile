FROM node:20-slim

# Set base working directory
WORKDIR /app

# Copy entire JS project into container
COPY . .

WORKDIR /app/samples/js

# Install all deps
RUN npm install

# Default entrypoint
CMD ["npm", "run", "agents:solana"]
