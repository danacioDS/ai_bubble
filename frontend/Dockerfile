FROM node:18

WORKDIR /app

COPY package.json pnpm-lock.yaml* ./

# Instalar pnpm versión estable (NO latest)
RUN npm install -g pnpm@9.12.0

RUN pnpm install

COPY . .

EXPOSE 5173

CMD ["pnpm", "dev", "--host", "0.0.0.0"]