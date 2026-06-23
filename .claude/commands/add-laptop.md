# MongoDB'ye Laptop Ekle

Yeni laptop verisi eklemek için kullanıcıdan bilgi al ve MongoDB'ye kaydet.

## Gerekli Alanlar

Kullanıcıdan şu bilgileri iste (zorunlu olanlar * ile işaretli):

| Alan | Tip | Açıklama |
|------|-----|----------|
| name* | string | Laptop adı (ör: "Lenovo IdeaPad 3 15IAU7") |
| brand* | string | Marka (ör: "Lenovo") |
| price* | number | Fiyat (TL cinsinden) |
| cpu | string | İşlemci (ör: "Intel Core i5-1235U") |
| gpu | string | Ekran kartı (ör: "NVIDIA RTX 3050") |
| ram_gb | number | RAM miktarı (GB) |
| storage_gb | number | Depolama (GB) |
| screen_size | number | Ekran boyutu (inç) |
| weight_kg | number | Ağırlık (kg) |
| battery_wh | number | Batarya (Wh) |
| link | string | Ürün linki (URL) |

## Adımlar

1. Kullanıcıdan laptop bilgilerini al. Tek seferde tüm bilgileri JSON olarak verebilir ya da interaktif olarak her alanı sorabiliriz.

2. Veriyi doğrula:
   - `name`, `brand`, `price` zorunlu
   - `price` pozitif sayı olmalı
   - `ram_gb`, `storage_gb` pozitif tam sayı olmalı
   - `link` varsa http:// veya https:// ile başlamalı

3. MongoDB'ye ekle:
   ```python
   from pymongo import MongoClient
   from dotenv import dotenv_values
   
   config = dotenv_values("laptop_project/.env")
   client = MongoClient(config["MONGODB_URI"])
   db = client[config["MONGODB_DB"]]
   col = db[config["MONGODB_COLLECTION"]]
   
   result = col.insert_one(laptop_data)
   print(f"Eklendi: {result.inserted_id}")
   ```

4. Eklenen kaydı doğrula — ID ile geri oku ve kullanıcıya göster.

## Toplu Ekleme

Kullanıcı birden fazla laptop eklemek isterse JSON array kabul et:
```json
[
  {"name": "...", "brand": "...", "price": 15000, ...},
  {"name": "...", "brand": "...", "price": 22000, ...}
]
```
`insert_many()` ile toplu ekle ve sonucu raporla.

## Notlar
- `.env` dosyasındaki hassas bilgileri ekrana yazdırma
- Ekleme öncesi kullanıcıdan onay al
- Aynı isimde laptop var mı kontrol et (duplikasyon uyarısı)
