# 1. Limpiar todo el caché de Docker
docker system prune -af --volumes

# 2. Limpiar específicamente el frontend
docker compose down --volumes --remove-orphans

# 3. Eliminar node_modules local (opcional)
rm -rf frontend/node_modules

# 4. Reconstruir sin caché
docker compose build --no-cache frontend

# 5. Levantar
docker compose up