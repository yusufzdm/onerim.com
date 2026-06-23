# MongoDB'den Laptop Sil

Veritabanından laptop kaydı silmek için arama yap, kullanıcıdan onay al ve sil.

## Adımlar

### 1. Arama
Kullanıcıdan silinecek laptopun adını veya filtresini al. MongoDB'de ara:

```python
from pymongo import MongoClient
from dotenv import dotenv_values

config = dotenv_values("laptop_project/.env")
client = MongoClient(config["MONGODB_URI"])
db = client[config["MONGODB_DB"]]
col = db[config["MONGODB_COLLECTION"]]

# İsimle arama (case-insensitive, kısmi eşleşme)
results = list(col.find({"name": {"$regex": ARAMA_TERIMI, "$options": "i"}}))
```

### 2. Eşleşmeleri Göster
Bulunan laptopları listele:
- Sıra numarası
- İsim, marka, fiyat
- `_id` değeri

Birden fazla sonuç varsa kullanıcıdan hangisini silmek istediğini sor.

### 3. Onay Al
Silinecek kaydı detaylı göster ve **açık onay** iste:
> "Bu kaydı silmek istediğinize emin misiniz? (evet/hayır)"

### 4. Silme İşlemi
```python
result = col.delete_one({"_id": ObjectId(secilen_id)})
print(f"Silinen kayıt sayısı: {result.deleted_count}")
```

### 5. Doğrulama
Silinen kaydın artık veritabanında olmadığını doğrula. Koleksiyondaki güncel toplam laptop sayısını göster.

## Toplu Silme
Kullanıcı filtre ile toplu silmek isterse (ör: "tüm Casper laptopları sil"):
- Etkilenecek kayıtları önce listele
- Tam sayıyı göster ve onay al
- `delete_many()` kullan
- Silinen sayıyı raporla

## Notlar
- **Onay olmadan asla silme yapma**
- `.env` bilgilerini ekrana yazdırma
- Yanlışlıkla tüm koleksiyonu silmeyi engellemek için boş filtre (`{}`) ile `delete_many()` kullanma
- Silme sonrası geri alma mümkün değil — kullanıcıyı uyar
