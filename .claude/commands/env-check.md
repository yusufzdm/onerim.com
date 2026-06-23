# Ortam Kontrolü

Tüm ortam değişkenlerini, bağımlılıkları, servisleri ve yapılandırmayı kontrol et.

## Adımlar

### 1. Sistem Gereksinimleri
```bash
python3 --version    # Python 3.9+ gerekli
node --version       # Node 18+ gerekli
npm --version        # npm 9+ önerilen
```

MongoDB durumunu kontrol et:
```bash
mongosh --eval "db.runCommand({ping:1})" --quiet 2>/dev/null || mongod --version 2>/dev/null || echo "MongoDB bulunamadı"
```

### 2. Backend Ortam Değişkenleri
`laptop_project/.env` dosyasını kontrol et (değerleri **göstermeden**):

| Değişken | Durum | Açıklama |
|----------|-------|----------|
| `OPENAI_API_KEY` | Var/Yok | sk-... ile başlamalı |
| `MONGODB_URI` | Var/Yok | mongodb:// veya mongodb+srv:// |
| `MONGODB_DB` | Var/Yok | Veritabanı adı |
| `MONGODB_COLLECTION` | Var/Yok | Koleksiyon adı |
| `OPENAI_MODEL` | Var/Yok | Varsayılan: gpt-4o-mini |
| `CORS_ORIGINS` | Var/Yok | Frontend URL'leri |

**Asla değer gösterme** — sadece var/yok ve format kontrolü.

### 3. Frontend Ortam Değişkenleri
`frontend/.env` dosyasını kontrol et:

| Değişken | Durum | Açıklama |
|----------|-------|----------|
| `VITE_API_URL` | Var/Yok | Backend URL (varsayılan: http://localhost:8000) |

### 4. Backend Bağımlılıkları
```bash
cd laptop_project && pip list --format=json 2>/dev/null | python3 -c "
import sys, json
installed = {p['name'].lower(): p['version'] for p in json.load(sys.stdin)}
required = ['fastapi', 'uvicorn', 'langgraph', 'langchain-openai', 'langchain-core', 'pymongo', 'python-dotenv']
for pkg in required:
    ver = installed.get(pkg, 'YOK')
    status = '✓' if pkg in installed else '✗'
    print(f'{status} {pkg}: {ver}')
"
```

### 5. Frontend Bağımlılıkları
```bash
cd frontend && node -e "
const pkg = require('./package.json');
const deps = {...pkg.dependencies, ...pkg.devDependencies};
const fs = require('fs');
const nmExists = fs.existsSync('node_modules');
console.log('node_modules:', nmExists ? 'Mevcut' : 'YOK — npm install gerekli');
for (const [name, version] of Object.entries(deps)) {
    try {
        const installed = require(name + '/package.json').version;
        console.log('✓', name + ':', installed);
    } catch { console.log('✗', name + ':', 'YOK'); }
}
"
```

### 6. Servis Durumları
```bash
# Backend
curl -s http://localhost:8000/health 2>/dev/null || echo "Backend çalışmıyor"

# Frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 2>/dev/null || echo "Frontend çalışmıyor"
```

### 7. Dosya Yapısı Kontrolü
Kritik dosyaların varlığını doğrula:

- `laptop_project/api.py`
- `laptop_project/main.py`
- `laptop_project/recommender.py`
- `laptop_project/config.py`
- `laptop_project/db.py`
- `laptop_project/prompts.py`
- `laptop_project/requirements.txt`
- `laptop_project/.env`
- `frontend/package.json`
- `frontend/src/App.vue`
- `frontend/src/components/ChatView.vue`
- `frontend/vite.config.js`

### 8. Git Durumu
```bash
git status --short
git log --oneline -5
```

## Rapor Formatı

```markdown
# Ortam Kontrolü — [Tarih]

## Sistem
| Bileşen | Versiyon | Durum |
|---------|----------|-------|
| Python | 3.x.x | OK |
| Node.js | 2x.x.x | OK |
| MongoDB | x.x | OK/Yok |

## Backend
- .env: X/Y değişken tanımlı
- Bağımlılıklar: X/Y kurulu
- Servis: Çalışıyor/Durmuş

## Frontend
- .env: OK/Eksik
- Bağımlılıklar: X/Y kurulu
- Servis: Çalışıyor/Durmuş

## Sorunlar
- [ ] ...

## Öneriler
- [ ] ...
```

## Notlar
- **Asla secret değerleri ekrana yazdırma** (API key, URI vb.)
- Sadece varlık ve format kontrolü yap
- Eksik varsa düzeltme talimatı ver
