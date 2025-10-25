# MommyShops - Guía de Deployment

## Tabla de Contenidos

- [Prerequisitos](#prerequisitos)
- [Deployment Local](#deployment-local)
- [Deployment en Producción](#deployment-en-producción)
- [Variables de Entorno](#variables-de-entorno)
- [Monitoreo](#monitoreo)
- [Troubleshooting](#troubleshooting)

## Prerequisitos

### Software Requerido

- Docker & Docker Compose 20+
- PostgreSQL 13+
- Redis 6+
- (Opcional) Kubernetes 1.24+
- (Opcional) Ollama para AI local

### Accesos Necesarios

- Credenciales de PostgreSQL
- API Keys de servicios externos (FDA, EWG, etc.)
- Firebase service account (si se usa)
- Dominio configurado con DNS

## Deployment Local

### 1. Configuración Inicial

```bash
# Clonar repositorio
git clone https://github.com/yourusername/mommyshops.git
cd mommyshops

# Copiar variables de entorno
cp env.example .env

# Editar .env con tus credenciales
nano .env
```

### 2. Iniciar con Docker Compose

```bash
# Construir imágenes
docker-compose build

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### 3. Inicializar Base de Datos

```bash
# Ejecutar migraciones
docker-compose exec python-backend alembic upgrade head

# Poblar datos iniciales (opcional)
docker-compose exec python-backend python scripts/populate_initial_data.py
```

### 4. Verificar Deployment

```bash
# Health check Python
curl http://localhost:8000/health

# Health check Java
curl http://localhost:8080/api/health

# Frontend
open http://localhost:8080
```

## Deployment en Producción

### Opción 1: Docker Compose (Recomendado para proyectos pequeños)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USERNAME}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USERNAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  python-backend:
    build:
      context: .
      dockerfile: Dockerfile.python
    environment:
      - DATABASE_URL=postgresql://${DB_USERNAME}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  java-backend:
    build:
      context: ./mommyshops-app
      dockerfile: Dockerfile
    environment:
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/${DB_NAME}
      - SPRING_DATASOURCE_USERNAME=${DB_USERNAME}
      - SPRING_DATASOURCE_PASSWORD=${DB_PASSWORD}
      - PYTHON_BACKEND_URL=http://python-backend:8000
    depends_on:
      postgres:
        condition: service_healthy
      python-backend:
        condition: service_healthy
    restart: unless-stopped
    ports:
      - "80:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    ports:
      - "443:443"
      - "80:80"
    depends_on:
      - java-backend
    restart: unless-stopped

volumes:
  postgres_data:
```

### Opción 2: Kubernetes (Recomendado para producción escalable)

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: python-backend
  template:
    metadata:
      labels:
        app: python-backend
    spec:
      containers:
      - name: python-backend
        image: mommyshops/python-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mommyshops-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: java-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: java-backend
  template:
    metadata:
      labels:
        app: java-backend
    spec:
      containers:
      - name: java-backend
        image: mommyshops/java-backend:latest
        ports:
        - containerPort: 8080
        env:
        - name: SPRING_DATASOURCE_URL
          valueFrom:
            secretKeyRef:
              name: mommyshops-secrets
              key: datasource-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "4000m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health/quick
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: python-backend-service
spec:
  selector:
    app: python-backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: java-backend-service
spec:
  selector:
    app: java-backend
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: LoadBalancer
```

### Configuración de Nginx (Reverse Proxy)

```nginx
# nginx.conf
upstream python_backend {
    least_conn;
    server python-backend:8000 max_fails=3 fail_timeout=30s;
}

upstream java_backend {
    least_conn;
    server java-backend:8080 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name mommyshops.com www.mommyshops.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mommyshops.com www.mommyshops.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript;

    # Frontend (Vaadin) and Java API
    location / {
        proxy_pass http://java_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Python API (interno, no expuesto directamente)
    location /python-api/ {
        deny all;  # Solo acceso interno
    }

    # Metrics (protegido)
    location /metrics {
        allow 10.0.0.0/8;  # Solo red interna
        deny all;
        proxy_pass http://python_backend/metrics;
    }

    # Health checks (público)
    location /health {
        proxy_pass http://java_backend/api/health;
    }
}
```

## Variables de Entorno

### Producción (Mínimas Requeridas)

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
DB_USERNAME=mommyshops
DB_PASSWORD=STRONG_RANDOM_PASSWORD

# Redis
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=STRONG_RANDOM_PASSWORD

# Security
JWT_SECRET=VERY_LONG_RANDOM_SECRET_MIN_64_CHARS
JWT_EXPIRATION=3600

# CORS
CORS_ORIGINS=https://mommyshops.com,https://www.mommyshops.com
TRUSTED_HOSTS=mommyshops.com,www.mommyshops.com

# APIs (Opcionales pero recomendadas)
FDA_API_KEY=your_fda_key
EWG_API_KEY=your_ewg_key
GOOGLE_VISION_API_KEY=your_google_vision_key

# Firebase (Opcional)
FIREBASE_CREDENTIALS={"type":"service_account",...}

# Monitoring
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO

# Performance
MAX_UPLOAD_SIZE=5242880
OLLAMA_BASE_URL=http://ollama:11434
```

## Monitoreo

### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=prometheus
    ports:
      - "3000:3000"
    restart: unless-stopped
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
```

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'python-backend'
    static_configs:
      - targets: ['python-backend:8000']
    metrics_path: '/metrics'

  - job_name: 'java-backend'
    static_configs:
      - targets: ['java-backend:8080']
    metrics_path: '/actuator/prometheus'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Métricas Clave a Monitorear

- **Request Rate**: Requests por segundo
- **Error Rate**: % de errores (5xx)
- **Latency**: P50, P95, P99
- **Database Connections**: Activas, idle
- **Cache Hit Rate**: % de cache hits
- **Analysis Duration**: Tiempo de análisis
- **External API Calls**: Rate y éxito
- **Memory Usage**: JVM, Python
- **CPU Usage**: Por servicio

### Alertas Recomendadas

```yaml
# alerts.yml
groups:
  - name: mommyshops
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 5m
        annotations:
          summary: "95th percentile response time > 2s"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        annotations:
          summary: "PostgreSQL is down"

      - alert: HighMemoryUsage
        expr: (process_resident_memory_bytes / 1024 / 1024 / 1024) > 3
        for: 10m
        annotations:
          summary: "Memory usage > 3GB"
```

## Troubleshooting

### Problema: Servicio no inicia

```bash
# Ver logs
docker-compose logs python-backend
docker-compose logs java-backend

# Verificar conectividad a DB
docker-compose exec python-backend psql $DATABASE_URL -c "SELECT 1"

# Verificar variables de entorno
docker-compose exec python-backend env | grep DATABASE
```

### Problema: Errores de conexión entre servicios

```bash
# Ping entre servicios
docker-compose exec java-backend ping python-backend

# Verificar DNS
docker-compose exec java-backend nslookup python-backend

# Test endpoint desde Java
docker-compose exec java-backend curl http://python-backend:8000/health
```

### Problema: Alto uso de memoria

```bash
# Monitorear memoria
docker stats

# Limitar memoria en docker-compose
services:
  python-backend:
    deploy:
      resources:
        limits:
          memory: 2G
```

### Problema: Base de datos lenta

```bash
# Analizar queries lentas
docker-compose exec postgres psql -U mommyshops -d mommyshops -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Crear índices faltantes
docker-compose exec postgres psql -U mommyshops -d mommyshops -f scripts/create_indexes.sql
```

---

**Última actualización**: 2025-10-24  
**Versión**: 3.0.0

