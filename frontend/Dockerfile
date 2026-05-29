# Build stage
FROM node:22-slim AS build

WORKDIR /app

# Copiar archivos de configuración primero
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del código
COPY . .

# Usar la variable del .env
RUN export VITE_API_URL=http://localhost:8000 && npm run build

# Verificar que la URL está en los archivos construidos
RUN grep -r "localhost:8000" dist/ && echo "URL encontrada!" || echo "ERROR: URL no encontrada"

# Production stage
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
