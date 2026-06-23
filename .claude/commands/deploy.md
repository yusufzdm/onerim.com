# Production Deploy

Uygulamayı production ortamına hazırla ve deploy et.

## Ön Kontroller

### 1. Ortam Kontrolü
Önce `/project:env-check` çalıştır ve tüm gereksinimlerin karşılandığını doğrula.

### 2. Kod Kalitesi
```bash
# Lint kontrolü
# /project:lint çalıştır veya manuel kontrol et

# Git durumu — commit edilmemiş değişiklik olmamalı
git status
git log --oneline -5
```

### 3. Test
Backend API testlerini çalıştır:
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

## Deploy Seçenekleri

### Seçenek A: Docker ile Deploy

#### 1. Backend Dockerfile
```dockerfile
# laptop_project/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Frontend Build + Nginx
```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

#### 3. Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./laptop_project
    ports:
      - "8000:8000"
    env_file:
      - ./laptop_project/.env
    depends_on:
      - mongodb

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: http://api.yourdomain.com
    ports:
      - "80:80"

  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

#### 4. Build & Çalıştır
```bash
docker-compose build
docker-compose up -d
docker-compose ps
```

### Seçenek B: Manuel Deploy (VPS)

#### 1. Frontend Build
```bash
cd frontend
VITE_API_URL=https://api.yourdomain.com npm run build
# dist/ klasörünü web sunucusuna kopyala
```

#### 2. Backend
```bash
cd laptop_project
pip install -r requirements.txt
# systemd service veya pm2 ile başlat
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Seçenek C: Cloud Deploy (Railway/Render/Fly.io)

Kullanıcıya platform seçimi sor ve platforma özel talimatlar ver:
- **Railway:** `railway.toml` yapılandırması
- **Render:** `render.yaml` yapılandırması
- **Fly.io:** `fly.toml` yapılandırması

## Deploy Sonrası Kontroller

1. **Health check:**
   ```bash
   curl -s https://api.yourdomain.com/health
   ```

2. **Frontend erişim:**
   ```bash
   curl -s -o /dev/null -w "%{http_code}" https://yourdomain.com
   ```

3. **Chat testi:**
   ```bash
   curl -X POST https://api.yourdomain.com/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "laptop öner", "thread_id": "deploy-test"}'
   ```

4. **CORS kontrolü:** Frontend'den backend'e istek yapılabiliyor mu?

## Checklist

- [ ] `.env` dosyası production değerleriyle güncellendi
- [ ] `CORS_ORIGINS` production frontend URL'ini içeriyor
- [ ] `OPENAI_API_KEY` production key ile ayarlandı
- [ ] MongoDB production URI ayarlandı
- [ ] Frontend `VITE_API_URL` production backend URL'i
- [ ] SSL/HTTPS yapılandırıldı
- [ ] Health check başarılı
- [ ] Chat testi başarılı

## Notlar
- **Asla .env dosyasını git'e commit etme**
- Production'da `OPENAI_MODEL` seçimini gözden geçir (maliyet vs kalite)
- Rate limiting ve logging production'da aktif olmalı
- MongoDB Atlas kullanıyorsan IP whitelist'i güncelle
- Deploy öncesi `/project:backup-db` ile yedek al
