# MongoDB Veritabanı Durumu

MongoDB bağlantısını, koleksiyon istatistiklerini ve örnek verileri kontrol et.

## Adımlar

1. **Bağlantı kontrolü:** Backend'in `/health` endpoint'ini çağır:
   ```
   GET http://localhost:8000/health
   ```
   Eğer backend çalışmıyorsa, kullanıcıya `/project:run-dev` ile başlatmasını öner.

2. **Doğrudan MongoDB kontrolü** (backend çalışmıyorsa alternatif):
   `laptop_project/.env` dosyasından MongoDB bağlantı bilgilerini oku, ardından Python ile kontrol et:
   ```python
   from pymongo import MongoClient
   from dotenv import dotenv_values
   
   config = dotenv_values("laptop_project/.env")
   client = MongoClient(config["MONGODB_URI"])
   db = client[config["MONGODB_DB"]]
   col = db[config["MONGODB_COLLECTION"]]
   
   print(f"Toplam laptop: {col.count_documents({})}")
   print(f"Markalar: {col.distinct('brand')}")
   print(f"Fiyat aralığı: {col.find_one(sort=[('price', 1)])['price']} - {col.find_one(sort=[('price', -1)])['price']}")
   ```

3. **Raporla:**
   - Bağlantı durumu (başarılı/başarısız)
   - Toplam laptop sayısı
   - Marka listesi ve her markadan kaç tane olduğu
   - Fiyat aralığı (min-max)
   - Örnek 3 laptop kaydı (ilk 3 doküman)
   - Eksik alan uyarıları (price, name, brand alanları olmayan kayıtlar varsa)

## Notlar
- `.env` dosyasındaki hassas bilgileri (URI, API key) ekrana yazdırma
- MongoDB'ye bağlanamazsa olası nedenleri listele (URI yanlış, MongoDB çalışmıyor, IP whitelist)
