# Use Node.js 20-alpine as the base image
FROM node:20-alpine

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port (matches default in src/index.js)
EXPOSE 3001

# Start the application
CMD ["npm", "start"]
