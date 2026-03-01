FROM node:20-alpine

WORKDIR /app

# Copier uniquement les fichiers de dépendances d'abord
COPY package*.json ./

# Installer les dépendances
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]