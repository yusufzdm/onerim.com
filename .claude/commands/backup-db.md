# MongoDB Yedekleme & Geri Yükleme

Laptop koleksiyonunu JSON dosyasına yedekle veya yedekten geri yükle.

## Yedekleme (Export)

### Adımlar

1. **MongoDB bağlantısı:**
```python
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import dotenv_values
from bson import json_util

config = dotenv_values("laptop_project/.env")
client = MongoClient(config["MONGODB_URI"])
db = client[config["MONGODB_DB"]]
col = db[config["MONGODB_COLLECTION"]]
```

2. **Verileri çek:**
```python
documents = list(col.find({}))
total = len(documents)
```

3. **JSON'a yaz:**
```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = f"laptop_project/backups/backup_{timestamp}.json"

# backups klasörünü oluştur
import os
os.makedirs("laptop_project/backups", exist_ok=True)

with open(backup_file, "w", encoding="utf-8") as f:
    json.dump(documents, f, default=json_util.default, ensure_ascii=False, indent=2)
```

4. **Rapor:**
- Yedeklenen kayıt sayısı
- Dosya boyutu
- Dosya yolu
- Marka dağılımı özeti

## Geri Yükleme (Import)

### Adımlar

1. **Mevcut yedekleri listele:**
```python
import glob
backups = sorted(glob.glob("laptop_project/backups/backup_*.json"), reverse=True)
```
En son 5 yedeği göster, kullanıcıdan seçmesini iste.

2. **Yedeği oku:**
```python
with open(secilen_yedek, "r", encoding="utf-8") as f:
    data = json.load(f, object_hook=json_util.object_hook)
```

3. **Geri yükleme modu seçimi:**
- **Birleştir (merge):** Mevcut verileri koru, sadece eksik kayıtları ekle
- **Değiştir (replace):** Mevcut koleksiyonu tamamen yerine koy (**tehlikeli**)

4. **Replace modu için:**
```python
# ÖNCE mevcut veriyi yedekle (güvenlik)
# Kullanıcıdan ÇİFT ONAY al
col.drop()
col.insert_many(data)
```

5. **Merge modu için:**
```python
inserted = 0
skipped = 0
for doc in data:
    if not col.find_one({"name": doc.get("name")}):
        col.insert_one(doc)
        inserted += 1
    else:
        skipped += 1
```

6. **Sonuç raporu:**
- Geri yüklenen kayıt sayısı
- Atlanan duplikasyonlar
- Koleksiyondaki yeni toplam

## Notlar
- Replace modunda **çift onay** mekanizması uygula
- `.env` bilgilerini ekrana yazdırma
- `backups/` klasörü `.gitignore`'da olmalı — yoksa ekle
- Yedek dosyalarında ObjectId'ler `bson.json_util` ile korunmalı
- Geri yükleme öncesi mevcut durumu otomatik yedekle
