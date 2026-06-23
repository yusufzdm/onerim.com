# API Performans Testi

Backend API'nin performansını ve dayanıklılığını test et.

## Ön Koşul
Backend'in `http://localhost:8000` adresinde çalışıyor olması gerekir. Önce `/health` kontrol et.

## Test Senaryoları

### 1. Yanıt Süresi Testi (Baseline)
Tek isteklerle baseline ölç:

```python
import requests
import time

url = "http://localhost:8000/chat"
tests = [
    {"message": "5000 TL laptop öner", "thread_id": "perf-1"},
    {"message": "oyun için laptop", "thread_id": "perf-2"},
    {"message": "MacBook Air ile ThinkPad karşılaştır", "thread_id": "perf-3"},
    {"message": "RAM nedir?", "thread_id": "perf-4"},
]

for test in tests:
    start = time.time()
    resp = requests.post(url, json=test, timeout=60)
    elapsed = (time.time() - start) * 1000
    print(f"{test['message'][:30]}... → {elapsed:.0f}ms (HTTP {resp.status_code})")
```

**Beklenen:** Her istek < 10 saniye

### 2. Eşzamanlı İstek Testi
Birden fazla isteği aynı anda gönder:

```python
import concurrent.futures

def send_request(i):
    start = time.time()
    resp = requests.post(url, json={"message": f"Test {i}: laptop öner", "thread_id": f"concurrent-{i}"}, timeout=60)
    return time.time() - start, resp.status_code

# 3 eşzamanlı istek
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(send_request, i) for i in range(3)]
    results = [f.result() for f in futures]

# 5 eşzamanlı istek
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(send_request, i) for i in range(5)]
    results = [f.result() for f in futures]
```

### 3. Ardışık İstek Testi (Throughput)
10 ardışık istek göndererek throughput ölç:

```python
times = []
for i in range(10):
    start = time.time()
    resp = requests.post(url, json={"message": "laptop öner", "thread_id": f"seq-{i}"}, timeout=60)
    times.append(time.time() - start)

print(f"Ortalama: {sum(times)/len(times)*1000:.0f}ms")
print(f"Min: {min(times)*1000:.0f}ms")
print(f"Max: {max(times)*1000:.0f}ms")
print(f"Throughput: {len(times)/sum(times):.1f} req/s")
```

### 4. Büyük Mesaj Testi
Uzun mesajlarla API'nin davranışını test et:

```python
# 500 karakter mesaj
long_msg = "Bana bir laptop öner. " * 25
resp = requests.post(url, json={"message": long_msg, "thread_id": "long-1"}, timeout=60)

# 2000 karakter mesaj
very_long = "A" * 2000
resp = requests.post(url, json={"message": very_long, "thread_id": "long-2"}, timeout=60)
```

### 5. Health Endpoint Performansı
```python
times = []
for _ in range(20):
    start = time.time()
    requests.get("http://localhost:8000/health", timeout=5)
    times.append(time.time() - start)
print(f"Health endpoint ortalama: {sum(times)/len(times)*1000:.0f}ms")
```

**Beklenen:** < 100ms

### 6. MongoDB Sorgu Performansı
Veritabanı sorgu sürelerini dolaylı olarak ölç — recommendation isteği içindeki DB kısmı:

```python
# Geniş filtreli sorgu (tüm laptoplar)
resp1 = requests.post(url, json={"message": "laptop öner", "thread_id": "db-1"}, timeout=60)

# Dar filtreli sorgu (marka + bütçe)
resp2 = requests.post(url, json={"message": "10000-15000 TL Lenovo laptop", "thread_id": "db-2"}, timeout=60)
```

## Rapor Formatı

```markdown
# Performans Raporu — [Tarih]

## Özet
| Metrik | Değer |
|--------|-------|
| Baseline ortalama | Xms |
| Eşzamanlı (3) başarı | X/3 |
| Eşzamanlı (5) başarı | X/5 |
| Throughput | X req/s |
| Health endpoint | Xms |

## Detaylı Sonuçlar
[Her test senaryosu için detay]

## Darboğaz Analizi
- [ ] OpenAI API çağrısı → en yavaş kısım (beklenen)
- [ ] MongoDB sorgusu → kabul edilebilir / yavaş
- [ ] CORS/middleware → ihmal edilebilir

## Öneriler
- [ ] Önbellek ekle (sık sorulan sorular için)
- [ ] Connection pooling kontrol et
- [ ] Rate limiting ekle (production için)
```

## Notlar
- OpenAI API çağrısı en büyük darboğaz olacaktır — bu beklenen bir durum
- Eşzamanlı testlerde OpenAI rate limit'e dikkat
- Testleri çalıştırmak API kredisi harcar — kullanıcıyı uyar
- Her testte timeout kullan (60s)
