FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

RUN npm run build

ENV NODE_ENV=production
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "npm run start"]
ENV PORT=3000
EXPOSE 3000

CMD ["sh", "-c", "npm run start"]
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
CMD ["npm", "run", "dev"]
