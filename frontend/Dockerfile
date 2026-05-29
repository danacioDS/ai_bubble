# frontend/Dockerfile
FROM node:22-slim AS build

WORKDIR /app

# Copiar solo package.json primero
COPY package.json ./

# Instalar dependencias limpiamente
RUN npm install

# Copiar el resto del código (excluyendo node_modules)
COPY . .

# Build
RUN npm run build

FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]