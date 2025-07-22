# Multi-stage build para otimização
FROM node:18-alpine AS builder

# Definir diretório de trabalho
WORKDIR /app

# Copiar package.json se existir (para apps React/Vue/Angular)
COPY package*.json ./
RUN if [ -f package.json ]; then npm ci --only=production; fi

# Copiar código fonte
COPY . .

# Build se for SPA framework
RUN if [ -f package.json ]; then npm run build; fi

# Stage de produção com Nginx
FROM nginx:alpine

# Instalar curl para healthcheck
RUN apk add --no-cache curl

# Remover configuração padrão do nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copiar configuração customizada do nginx
COPY nginx.conf /etc/nginx/conf.d/

# Copiar arquivos estáticos
# Se tem build (React/Vue), copiar da pasta build
COPY --from=builder /app/dist /usr/share/nginx/html 2>/dev/null || \
     COPY --from=builder /app/build /usr/share/nginx/html 2>/dev/null || \
     COPY . /usr/share/nginx/html

# Criar usuário não-root
RUN addgroup -g 1001 -S nginx && \
    adduser -S nginx -u 1001

# Ajustar permissões
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Mudar para usuário não-root
USER nginx

# Expor porta 8080 (não-privilegiada)
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Comando para iniciar nginx
CMD ["nginx", "-g", "daemon off;"]