# Kod Lint & Format Kontrolü

Frontend ve Backend kodlarını lint ve format kontrolünden geçir.

## Frontend (JavaScript/Vue)

### 1. ESLint Kontrolü
```bash
cd frontend && npx eslint src/ --ext .js,.vue --no-error-on-unmatched-pattern 2>&1 || true
```

Eğer ESLint yapılandırması yoksa:
- `eslint.config.js` veya `.eslintrc.*` dosyasını kontrol et
- Yoksa temel bir Vue 3 ESLint kontrolü öner

### 2. Manuel Kod Kalite Kontrolü
ESLint yoksa aşağıdakileri manuel kontrol et:

- **Kullanılmayan import'lar:** Tüm `.vue` ve `.js` dosyalarında
- **console.log kalıntıları:** Production'da olmaması gereken debug logları
- **Tanımsız değişkenler:** Template'lerde kullanılıp tanımlanmamış
- **CSS sorunları:** Kullanılmayan stiller, !important kötüye kullanımı
- **Türkçe karakter:** String'lerde düzgün Türkçe karakter kullanımı (ş, ç, ğ, ı, ö, ü)
- **DOMPurify:** `v-html` kullanan yerlerde sanitize uygulanmış mı?

### 3. Vue Best Practices
- `v-for` direktifinde `:key` var mı?
- Props validation tanımlı mı?
- Component naming convention (PascalCase)
- Event naming convention (kebab-case)

## Backend (Python)

### 1. Ruff/Flake8 Kontrolü
```bash
cd laptop_project && python -m ruff check . 2>&1 || python -m flake8 . 2>&1 || true
```

Eğer lint tool kurulu değilse:
- `pip install ruff` öner (hızlı ve modern)

### 2. Manuel Kod Kalite Kontrolü
Lint tool yoksa aşağıdakileri manuel kontrol et:

- **print() kullanımı:** `logging` modülü yerine `print()` var mı?
- **Kullanılmayan import'lar:** Tüm `.py` dosyalarında
- **Type hint eksiklikleri:** Fonksiyon parametreleri ve dönüş tipleri
- **Docstring eksiklikleri:** Public fonksiyonlarda
- **Güvenlik:** Hardcoded secret, SQL injection riski, input validation
- **async/sync karışımı:** Async fonksiyonlarda blocking call

### 3. Python Best Practices
- f-string kullanımı (`.format()` yerine)
- Context manager kullanımı (dosya işlemleri)
- Exception handling (bare `except:` yok)
- Constant naming (UPPER_CASE)

## Raporlama

```markdown
# Lint Raporu — [Tarih]

## Frontend
- Toplam sorun: X (Hata: N, Uyarı: N, Bilgi: N)
- Dosya bazlı dağılım

## Backend
- Toplam sorun: X (Hata: N, Uyarı: N, Bilgi: N)
- Dosya bazlı dağılım

## Otomatik Düzeltilebilir
- [ ] Sorun 1 — dosya:satır
- [ ] Sorun 2 — dosya:satır

## Manuel Düzeltme Gereken
- [ ] Sorun 1 — dosya:satır — açıklama
```

## Otomatik Düzeltme
Kullanıcı isterse:
- Frontend: `npx eslint src/ --fix`
- Backend: `python -m ruff check . --fix`

**Düzeltme öncesi mutlaka kullanıcıdan onay al.**

## Notlar
- Sadece proje dosyalarını kontrol et (`node_modules/`, `.venv/` hariç)
- Mevcut lint konfigürasyonuna saygı göster, yoksa varsayılan kurallar kullan
