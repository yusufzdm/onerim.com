# MongoDB'de Laptop Güncelle

Mevcut bir laptop kaydının alanlarını güncelle.

## Adımlar

### 1. Arama
Kullanıcıdan güncellenecek laptopun adını al ve MongoDB'de ara:

```python
from pymongo import MongoClient
from dotenv import dotenv_values
from bson import ObjectId

config = dotenv_values("laptop_project/.env")
client = MongoClient(config["MONGODB_URI"])
db = client[config["MONGODB_DB"]]
col = db[config["MONGODB_COLLECTION"]]

results = list(col.find({"name": {"$regex": ARAMA_TERIMI, "$options": "i"}}))
```

Birden fazla sonuç varsa kullanıcıdan seçmesini iste.

### 2. Mevcut Kaydı Göster
Seçilen laptopun tüm alanlarını tablo formatında göster:

| Alan | Mevcut Değer |
|------|-------------|
| name | ... |
| brand | ... |
| price | ... |
| cpu | ... |
| gpu | ... |
| ram_gb | ... |
| storage_gb | ... |
| screen_size | ... |
| weight_kg | ... |
| battery_wh | ... |
| link | ... |

### 3. Güncelleme Bilgilerini Al
Kullanıcıdan hangi alanları değiştirmek istediğini sor. Kabul edilen formatlar:
- Tek alan: `price: 15000`
- Birden fazla alan: `{"price": 15000, "ram_gb": 16}`
- Doğal dil: "fiyatını 15000 yap ve RAM'i 16 GB olarak güncelle"

### 4. Doğrulama
- `price` → pozitif sayı
- `ram_gb`, `storage_gb` → pozitif tam sayı
- `link` → http:// veya https:// ile başlamalı
- `name`, `brand` → boş olamaz

### 5. Güncelleme
Değişiklikleri önizle (eski → yeni) ve onay al:

```python
result = col.update_one(
    {"_id": ObjectId(secilen_id)},
    {"$set": guncellenecek_alanlar}
)
print(f"Güncellenen kayıt: {result.modified_count}")
```

### 6. Doğrulama
Güncellenen kaydı tekrar oku ve kullanıcıya göster.

## Toplu Güncelleme
Birden fazla laptop güncellemek için (ör: "tüm Lenovo laptopların fiyatını %10 artır"):
- Etkilenecek kayıtları listele
- Yeni değerleri önizle
- Onay al
- `update_many()` kullan

## Notlar
- Onay olmadan güncelleme yapma
- `_id` alanını değiştirme
- `.env` bilgilerini ekrana yazdırma
