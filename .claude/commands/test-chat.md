# Chatbot API Test

Backend API'yi farklı senaryolarla test et ve sonuçları raporla.

## Ön Koşul
Backend'in `http://localhost:8000` adresinde çalışıyor olması gerekir. Önce `/health` endpoint'ini kontrol et.

## Test Senaryoları

Aşağıdaki senaryoları sırayla `POST http://localhost:8000/chat` endpoint'ine gönder. Her istekte aynı `thread_id` kullan (çok turlu konuşmayı test etmek için).

### 1. Temel Öneri
```json
{"message": "5000-10000 TL arası öğrenci için laptop önerir misin?", "thread_id": "test-1"}
```
**Beklenen:** 3 laptop önerisi, fiyatları bütçe aralığında, markdown formatında

### 2. Marka Tercihi
```json
{"message": "Lenovo veya HP marka, oyun için bir laptop istiyorum", "thread_id": "test-2"}
```
**Beklenen:** Sadece Lenovo/HP markaları, GPU bilgisi içermeli

### 3. Karşılaştırma
```json
{"message": "MacBook Air ile ThinkPad karşılaştır", "thread_id": "test-3"}
```
**Beklenen:** İki laptopun özellik karşılaştırması

### 4. Genel Soru
```json
{"message": "Laptop alırken RAM ne kadar önemli?", "thread_id": "test-4"}
```
**Beklenen:** Bilgilendirici yanıt, laptop odaklı

### 5. Konu Dışı
```json
{"message": "Bugün hava nasıl?", "thread_id": "test-5"}
```
**Beklenen:** Kibarca laptop konusuna yönlendirme

## Raporlama

Her test için şunu raporla:
- **Durum:** Başarılı / Başarısız / Kısmi
- **Yanıt süresi:** ms cinsinden
- **Yanıt özeti:** Kısa açıklama
- **Sorunlar:** Varsa tespit edilen problemler

Sonunda genel bir özet tablo oluştur.

## Notlar
- İsteklerde 30 saniye timeout kullan
- HTTP hata kodlarını (4xx, 5xx) yakala ve raporla
- Türkçe karakter desteğini doğrula (ş, ç, ğ, ı, ö, ü)
