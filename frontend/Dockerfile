FROM node:22

# Install updates
RUN apt-get update && apt-get upgrade -y && apt-get clean

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the app
COPY . .

# Expose the default dev port
EXPOSE 5173

# Start the service in dev mode
CMD ["npm", "run", "dev"]
