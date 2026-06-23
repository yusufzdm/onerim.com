# Chat Akışı Debug

Tek bir sohbet mesajını LangGraph akışı boyunca adım adım izle ve her aşamayı raporla.

## Kullanım
Kullanıcıdan debug edilecek mesajı al (ör: "10000 TL oyun laptopu öner").

## Adımlar

### 1. Intent Extraction (Niyet Çıkarımı)
`laptop_project/prompts.py` dosyasındaki system prompt'u oku ve mesajı analiz et:

```python
import json
from dotenv import dotenv_values

config = dotenv_values("laptop_project/.env")

# OpenAI'a gönderilecek prompt'u göster
# Beklenen çıktı: intent, budget_min, budget_max, brand, usage, specs
```

Gerçek API çağrısı yaparak intent extraction sonucunu göster:
```python
from openai import OpenAI

client = OpenAI(api_key=config["OPENAI_API_KEY"])
# prompts.py'deki EXTRACT_PROMPT'u kullanarak intent çıkar
```

**Raporla:**
- Algılanan intent (recommend/compare/question/other)
- Çıkarılan tercihler (bütçe, marka, kullanım, özellikler)
- JSON çıktısı

### 2. Preference Merge (Tercih Birleştirme)
`laptop_project/main.py` dosyasındaki `_merge_preferences()` mantığını simüle et:
- Önceki turların tercihleri (varsa)
- Yeni tercihlerin birleştirilmesi
- Final tercih durumu

### 3. MongoDB Sorgusu
`laptop_project/recommender.py` dosyasındaki filtre oluşturma mantığını izle:

```python
from pymongo import MongoClient

client_db = MongoClient(config["MONGODB_URI"])
db = client_db[config["MONGODB_DB"]]
col = db[config["MONGODB_COLLECTION"]]

# Oluşturulan filtre
filter_query = {}  # tercihlerden üretilen filtre
print(f"MongoDB filtresi: {json.dumps(filter_query, indent=2)}")

# Sorgu sonucu
results = list(col.find(filter_query))
print(f"Bulunan laptop sayısı: {len(results)}")
```

**Raporla:**
- Oluşturulan MongoDB filtresi
- Eşleşen laptop sayısı
- Eşleşen laptopların listesi (kısa)

### 4. Scoring (Puanlama)
`recommender.py` dosyasındaki puanlama algoritmasını adım adım göster:

- Kullanım tipine göre ağırlıklar
- Her laptopun alt puanları (CPU, GPU, RAM, fiyat, batarya, ağırlık)
- Toplam puan sıralaması
- Seçilen top 3

**Raporla:**
- Kullanılan ağırlıklar tablosu
- Her laptopun puan dökümü
- Final sıralama

### 5. AI Reason Generation (Sebep Üretimi)
Her önerilen laptop için OpenAI'ın ürettiği kişiselleştirilmiş sebepleri göster.

### 6. Response Formatting (Yanıt Formatlama)
Final markdown yanıtını göster:
- Markdown yapısı doğru mu?
- Türkçe karakterler sağlam mı?
- Fiyat formatı doğru mu?
- Link'ler çalışır durumda mı?

## Özet Rapor

```markdown
# Debug Raporu — "[mesaj]"

## Akış Özeti
| Adım | Durum | Süre | Detay |
|------|-------|------|-------|
| Intent Extraction | OK/HATA | Xms | intent=recommend |
| Preference Merge | OK/HATA | - | budget=10000-15000 |
| MongoDB Sorgusu | OK/HATA | Xms | 12 laptop bulundu |
| Scoring | OK/HATA | Xms | Top 3 seçildi |
| AI Reasons | OK/HATA | Xms | 3 sebep üretildi |
| Formatting | OK/HATA | - | Markdown geçerli |

## Tespit Edilen Sorunlar
- [ ] ...

## Öneriler
- [ ] ...
```

## Notlar
- Bu skill API kredisi harcar (OpenAI çağrısı yapar) — kullanıcıyı uyar
- `.env` bilgilerini ekrana yazdırma
- Her adımda hata olursa detaylı hata mesajı göster ve sonraki adıma geç
- Thread memory'yi temiz tutmak için benzersiz thread_id kullan
