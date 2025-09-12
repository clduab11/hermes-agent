FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY server.js ./
COPY routes ./routes
COPY services ./services
EXPOSE 3001
CMD ["npm", "start"]
