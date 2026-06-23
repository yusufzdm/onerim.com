# Backend Log Görüntüleme & Analiz

Backend loglarını görüntüle, filtrele ve analiz et.

## Log Kaynakları

### 1. Uvicorn/FastAPI Logları
Backend çalışıyorsa canlı logları görüntüle:

```bash
# Son çalışan backend process'ini bul
ps aux | grep "python api.py\|uvicorn" | grep -v grep
```

### 2. Python Logging Çıktısı
`laptop_project/` dosyalarındaki logging yapılandırmasını kontrol et:

```python
# api.py, main.py, recommender.py dosyalarındaki logging seviyesini kontrol et
import logging
# Beklenen: logging.basicConfig(level=logging.INFO)
```

### 3. Log Dosyaları
```bash
# Proje dizinindeki log dosyalarını bul
find . -name "*.log" -not -path "./.git/*" -not -path "*/node_modules/*" 2>/dev/null
```

## Log Filtreleme

### Seviyeye Göre
Kullanıcıdan hangi seviyeyi görmek istediğini sor:
- **ERROR:** Sadece hatalar
- **WARNING:** Uyarılar ve hatalar
- **INFO:** Bilgilendirme, uyarılar ve hatalar
- **DEBUG:** Tüm loglar

### Bileşene Göre
- **API:** FastAPI endpoint logları (istek/yanıt)
- **LangGraph:** Akış düğüm geçişleri
- **Recommender:** Puanlama ve filtreleme logları
- **DB:** MongoDB bağlantı ve sorgu logları
- **OpenAI:** API çağrı logları

### Zaman Aralığına Göre
- Son 10 satır
- Son 50 satır
- Son 1 saat
- Belirli tarih aralığı

## Canlı Log İzleme

Backend çalışıyorken canlı log akışı:
```bash
# Eğer log dosyası varsa
tail -f laptop_project/*.log 2>/dev/null

# Eğer stdout'a yazıyorsa, process çıktısını izle
# (backend run_in_background ile başlatıldıysa)
```

## Log Analizi

### Hata Özeti
```python
# Log dosyasını oku ve hataları grupla
import re
from collections import Counter

errors = []
# Her log satırını parse et
# ERROR seviyesindeki mesajları topla
# En sık tekrarlanan hataları göster

error_counts = Counter(errors)
for error, count in error_counts.most_common(10):
    print(f"{count}x — {error}")
```

### Performans Analizi
- Ortalama istek süresi
- En yavaş istekler
- OpenAI API çağrı süreleri
- MongoDB sorgu süreleri

### Güvenlik Analizi
- Başarısız istekler (4xx, 5xx)
- Şüpheli mesajlar (injection denemeleri)
- CORS hataları

## Rapor Formatı

```markdown
# Log Raporu — [Tarih]

## Özet
- Toplam log satırı: X
- ERROR: X
- WARNING: X
- INFO: X

## Son Hatalar
| Zaman | Bileşen | Mesaj |
|-------|---------|-------|
| ... | API | ... |

## Tekrarlanan Sorunlar
1. [Hata açıklaması] — X kez

## Öneriler
- [ ] ...
```

## Notlar
- Log dosyalarında hassas bilgi olabilir (API key, kullanıcı mesajı) — dikkatli göster
- Büyük log dosyalarında `tail` kullan, tamamını okuma
- Logları temizlemek için `/project:clean` skill'ini öner
- Backend `logging` modülü kullanıyor, `print()` olmamalı
