# Proje Temizliği

Build artifact'lerini, cache'leri ve geçici dosyaları temizle.

## Temizlik Hedefleri

### 1. Güvenli Temizlik (Otomatik)
Kullanıcı onayı olmadan silinebilecek dosyalar:

```bash
# Python cache
find laptop_project -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find laptop_project -name "*.pyc" -delete 2>/dev/null
find pc-builder-agent -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Frontend build output
rm -rf frontend/dist

# Log dosyaları
find . -name "*.log" -not -path "./.git/*" -delete 2>/dev/null

# OS dosyaları
find . -name ".DS_Store" -delete 2>/dev/null
find . -name "Thumbs.db" -delete 2>/dev/null
```

### 2. Onaylı Temizlik (Kullanıcı Onayı Gerekli)
Silinmeden önce onay iste:

#### node_modules (büyük, yeniden kurulabilir)
```bash
# Boyut göster
du -sh frontend/node_modules 2>/dev/null
# Kullanıcı onaylarsa:
rm -rf frontend/node_modules
```

#### Python virtual environment
```bash
du -sh laptop_project/.venv 2>/dev/null
du -sh laptop_project/venv 2>/dev/null
# Kullanıcı onaylarsa:
rm -rf laptop_project/.venv laptop_project/venv
```

#### Yedek dosyalar
```bash
# backups klasörü
du -sh laptop_project/backups 2>/dev/null
```

### 3. Tehlikeli Temizlik (Çift Onay Gerekli)
**Asla otomatik silme:**
- `.env` dosyaları
- `.git/` dizini
- Kaynak kod dosyaları
- MongoDB verileri

## Temizlik Raporu

```markdown
# Temizlik Raporu — [Tarih]

## Silinen
| Hedef | Boyut | Durum |
|-------|-------|-------|
| __pycache__ | X MB | Silindi |
| frontend/dist | X MB | Silindi |
| .DS_Store | X KB | Silindi |
| *.log | X KB | Silindi |

## Kullanıcı Onayı Beklenen
| Hedef | Boyut | Durum |
|-------|-------|-------|
| node_modules | X MB | Onay bekleniyor |
| .venv | X MB | Onay bekleniyor |

## Toplam Kazanılan Alan: X MB

## Yeniden Kurulum
- node_modules: `cd frontend && npm install`
- .venv: `cd laptop_project && python -m venv .venv && pip install -r requirements.txt`
- dist: `cd frontend && npm run build`
```

## Notlar
- Temizlik öncesi `git status` kontrol et — commit edilmemiş değişiklik varsa uyar
- `node_modules` silindiyse `npm install` gerektiğini hatırlat
- `.venv` silindiyse `pip install` gerektiğini hatırlat
- Toplam kazanılan disk alanını göster
