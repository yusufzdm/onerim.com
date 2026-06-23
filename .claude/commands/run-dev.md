# Geliştirme Ortamını Başlat

Backend ve Frontend dev sunucularını birlikte başlat.

## Adımlar

1. Önce ortam değişkenlerini kontrol et:
   - `laptop_project/.env` dosyasının var olduğunu doğrula
   - `frontend/.env` dosyasının var olduğunu doğrula (yoksa varsayılan `VITE_API_URL=http://localhost:8000` kullanılır)

2. Backend'i başlat (arka planda):
   ```bash
   cd laptop_project && python api.py
   ```
   - Port 8000'de çalışmalı
   - Başlamadan önce `pip install -r requirements.txt` ile bağımlılıkları kontrol et (sadece ilk çalıştırmada veya requirements değiştiyse)

3. Frontend'i başlat (arka planda):
   ```bash
   cd frontend && npm run dev
   ```
   - Port 5173'te çalışmalı
   - Başlamadan önce `node_modules/` yoksa `npm install` çalıştır

4. Her iki sunucunun da ayakta olduğunu doğrula:
   - `GET http://localhost:8000/health` → backend sağlık kontrolü
   - `GET http://localhost:5173` → frontend erişilebilirlik kontrolü

5. Kullanıcıya sonucu raporla:
   - Backend URL: http://localhost:8000
   - Frontend URL: http://localhost:5173
   - Varsa hataları bildir

## Notlar
- Her iki sunucuyu da `run_in_background` ile başlat
- Backend başarısız olursa `.env` dosyasındaki `OPENAI_API_KEY` ve MongoDB bilgilerini kontrol et
- Frontend başarısız olursa `node_modules/` temizleyip `npm install` öner
