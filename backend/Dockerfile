FROM node:18
WORKDIR /app
COPY package.json .
COPY server.js ./
COPY routes ./routes
COPY services ./services
RUN npm install
EXPOSE 3001
CMD ["npm", "start"]
