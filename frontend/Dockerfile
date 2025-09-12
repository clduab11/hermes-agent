FROM node:18
WORKDIR /app
COPY package.json vite.config.js .
COPY src ./src
COPY public ./public
RUN npm install
EXPOSE 5173
CMD ["npm", "run", "dev"]
