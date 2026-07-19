# Frontend GameCheck — build Vite/React e serve o SPA estático via nginx.

# --- Estágio 1: build ------------------------------------------------------
FROM node:20-alpine AS build

WORKDIR /app

# A URL do backend é embutida no bundle EM TEMPO DE BUILD (Vite/import.meta.env).
# Aponte para onde o NAVEGADOR alcança o backend (padrão: http://localhost:8000).
ARG VITE_API_BASE_URL=http://localhost:8000

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Grava a variável para o `vite build` (modo production) consumir.
RUN echo "VITE_API_BASE_URL=$VITE_API_BASE_URL" > .env.production \
    && npm run build

# --- Estágio 2: runtime (nginx) --------------------------------------------
FROM nginx:alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
