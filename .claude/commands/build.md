# Frontend Production Build

Frontend'i production için derle ve sonucu doğrula.

## Adımlar

1. **Bağımlılık kontrolü:**
   ```bash
   cd frontend && npm install
   ```

2. **Build çalıştır:**
   ```bash
   cd frontend && npm run build
   ```

3. **Build doğrulama:**
   - `frontend/dist/` dizininin oluştuğunu kontrol et
   - `frontend/dist/index.html` dosyasının var olduğunu doğrula
   - `frontend/dist/assets/` altında JS ve CSS dosyalarının oluştuğunu kontrol et
   - Toplam build boyutunu hesapla

4. **Preview** (opsiyonel, kullanıcıya sor):
   ```bash
   cd frontend && npm run preview
   ```
   Port 4173'te production build'i önizle.

5. **Raporla:**
   - Build durumu: Başarılı / Başarısız
   - Build süresi
   - Dosya boyutları (JS, CSS, toplam)
   - Uyarı varsa bildir

## Notlar
- Build hatası olursa hata mesajını analiz et ve düzeltme öner
- `VITE_API_URL` ortam değişkeninin production URL'e ayarlanması gerekebilir, kullanıcıyı uyar
- `dist/` dizini `.gitignore`'da olmalı
