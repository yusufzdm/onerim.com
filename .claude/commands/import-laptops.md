# Toplu Laptop Import

CSV veya JSON dosyasından MongoDB'ye toplu laptop verisi aktar.

## Desteklenen Formatlar

### JSON
```json
[
  {
    "name": "Lenovo IdeaPad 3",
    "brand": "Lenovo",
    "price": 12000,
    "cpu": "Intel Core i5-1235U",
    "gpu": "Intel Iris Xe",
    "ram_gb": 8,
    "storage_gb": 256,
    "screen_size": 15.6,
    "weight_kg": 1.7,
    "battery_wh": 45,
    "link": "https://example.com/laptop1"
  }
]
```

### CSV
```csv
name,brand,price,cpu,gpu,ram_gb,storage_gb,screen_size,weight_kg,battery_wh,link
Lenovo IdeaPad 3,Lenovo,12000,Intel Core i5-1235U,Intel Iris Xe,8,256,15.6,1.7,45,https://example.com/laptop1
```

## Adımlar

### 1. Dosya Okuma
Kullanıcıdan dosya yolunu al ve formatı belirle:

```python
import json
import csv
from pymongo import MongoClient
from dotenv import dotenv_values

config = dotenv_values("laptop_project/.env")
client = MongoClient(config["MONGODB_URI"])
db = client[config["MONGODB_DB"]]
col = db[config["MONGODB_COLLECTION"]]

# JSON
with open(dosya_yolu, "r", encoding="utf-8") as f:
    data = json.load(f)

# CSV
with open(dosya_yolu, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    data = list(reader)
    # Sayısal alanları dönüştür
    for row in data:
        for field in ["price", "ram_gb", "storage_gb", "screen_size", "weight_kg", "battery_wh"]:
            if field in row and row[field]:
                row[field] = float(row[field]) if "." in str(row[field]) else int(row[field])
```

### 2. Veri Doğrulama
Her kayıt için kontrol et:
- **Zorunlu alanlar:** `name`, `brand`, `price` mevcut mu?
- **Tip kontrolü:** `price` sayı mı? `ram_gb` tam sayı mı?
- **URL kontrolü:** `link` varsa geçerli URL mi?
- **Duplikasyon:** Aynı isimde kayıt veritabanında var mı?

Hatalı kayıtları listele, geçerli kayıtların özetini göster.

### 3. Önizleme
```
Toplam kayıt: 50
Geçerli: 47
Hatalı: 3 (satır 12, 28, 45)
Markalar: Lenovo (15), HP (12), ASUS (10), Acer (10)
Fiyat aralığı: 8.000 - 45.000 TL
```

### 4. Onay ve Import
Kullanıcıdan onay al:
```python
result = col.insert_many(gecerli_kayitlar)
print(f"Eklenen: {len(result.inserted_ids)} kayıt")
```

### 5. Sonuç Raporu
- Eklenen kayıt sayısı
- Atlanan kayıt sayısı ve nedenleri
- Veritabanındaki yeni toplam
- Duplikasyon uyarıları

## Seçenekler
- `--skip-duplicates`: Aynı isimli kayıtları atla (varsayılan)
- `--overwrite`: Aynı isimli kayıtları güncelle
- `--dry-run`: Sadece doğrulama yap, import etme

## Notlar
- Büyük dosyalarda (1000+) `insert_many()` batch'ler halinde (100'lük gruplar) yap
- UTF-8 encoding kullan (Türkçe karakter desteği)
- `.env` bilgilerini ekrana yazdırma
- Import öncesi `backup-db` skill'ini öner
