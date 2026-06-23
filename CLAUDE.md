# Laptop Öneri Asistanı — Claude Code Rehberi

## Proje Özeti
Vue 3 + Vite frontend, FastAPI + LangGraph + MongoDB backend ile yapılmış yapay zeka destekli laptop öneri chatbot'u.

## Mimari
- **Frontend:** `frontend/` — Vue 3, Vite, axios, markdown-it, DOMPurify
- **Backend:** `laptop_project/` — FastAPI, LangGraph, LangChain, OpenAI, PyMongo
- **Veritabanı:** MongoDB (laptoplar koleksiyonu)

## Çalıştırma
```bash
# Backend
cd laptop_project && pip install -r requirements.txt && python api.py

# Frontend
cd frontend && npm install && npm run dev
```

## Ortam Değişkenleri
Backend `.env` dosyası (`laptop_project/.env`):
- `OPENAI_API_KEY` — zorunlu
- `MONGODB_URI`, `MONGODB_DB`, `MONGODB_COLLECTION` — zorunlu
- `CORS_ORIGINS` — virgülle ayrılmış origin listesi (varsayılan: localhost:5173,localhost:3000)
- `OPENAI_MODEL` — varsayılan: gpt-4o-mini

Frontend `.env` dosyası (`frontend/.env`):
- `VITE_API_URL` — backend URL (varsayılan: http://localhost:8000)

## Kullanıcı Tercihleri
- Kullanıcıdan izin sorma, onay isteme — tüm işlemlere önceden onay verilmiştir
- Dosya silme, oluşturma, düzenleme, commit, push dahil her şeyi doğrudan yap
- Otonom çalış, soru sormadan en iyi kararı ver ve uygula

## Kodlama Kuralları
- Türkçe string'lerde düzgün Türkçe karakter kullan (ş, ç, ğ, ı, ö, ü, İ, Ş, Ç, Ğ, Ö, Ü)
- Backend'de `logging` modülü kullan, `print()` kullanma
- Frontend'de `v-html` kullanırken mutlaka `DOMPurify.sanitize()` uygula
- Yeni endpoint eklerken Pydantic validasyonu ile `min_length`/`max_length` tanımla
- CSS'te renk değerleri için CSS değişkenlerini kullan (`var(--accent)` vb.)

---

## Takım Agent'ları (Subagent — Opus)

Aşağıdaki agent'lar **Agent tool ile subagent olarak** başlatılmalıdır. Her biri `model: "opus"` ile çalışır.

Kullanıcı bir agent adı söylediğinde (ör: "QA agent'ını çalıştır", "Frontend Dev başlat"):
1. İlgili `/project:` skill dosyasını oku (prompt kaynağı)
2. Agent tool ile `model: "opus"` parametresiyle subagent olarak başlat
3. Bağımsız agent'ları paralel başlat (tek mesajda birden fazla Agent tool call)

### Agent Listesi

| Agent | Skill | Tür | Paralel Grup |
|-------|-------|-----|--------------|
| **Team Lead** | `/project:team-lead` | Planlama (read-only) | - |
| **QA** | `/project:qa` | Analiz (read-only) | A |
| **Frontend Dev** | `/project:frontend-dev` | Geliştirme (yazma) | B |
| **Backend Dev** | `/project:backend-dev` | Geliştirme (yazma) | B |

- Grup A agent'ları (QA) paralel çalışabilir
- Grup B agent'ları (Dev) **worktree isolation ile** paralel çalışabilir, merge conflict'i önlemek için
- Team Lead her zaman tek çalışır (diğer agent'ların çıktısına bağımlı)

### Otomatik Dispatch Kuralları

Kullanıcının verdiği görev türüne göre ilgili agent **otomatik olarak** Opus subagent olarak başlatılır. Kullanıcının "agent çalıştır" demesine gerek yok.

**Frontend görevi algılandığında** (Vue bileşeni, CSS, UI, UX, responsive, dark mode, a11y, Three.js, Vite, frontend/ ile ilgili herhangi bir değişiklik):
→ **Frontend Dev** agent'ını Opus subagent olarak başlat

**Backend görevi algılandığında** (API, endpoint, FastAPI, LangGraph, MongoDB, recommender, prompt, backend/ ile ilgili herhangi bir değişiklik):
→ **Backend Dev** agent'ını Opus subagent olarak başlat

**Hem frontend hem backend içeren görevlerde:**
→ **Frontend Dev** ve **Backend Dev** agent'larını paralel Opus subagent olarak başlat (worktree isolation)

**QA / inceleme / analiz / test isteğinde:**
→ **QA** agent'ını Opus subagent olarak başlat

**Planlama / sprint / görev atama isteğinde:**
→ **Team Lead** agent'ını Opus subagent olarak başlat

**"Takımı çalıştır" / "Tam döngü":**
→ QA → Team Lead → Dev'ler (sıralı pipeline)

### Manuel Dispatch
Agent adı açıkça söylendiğinde de çalışır:
```
"QA agent'ını çalıştır"
"Frontend Dev ve Backend Dev'i paralel çalıştır"
```
