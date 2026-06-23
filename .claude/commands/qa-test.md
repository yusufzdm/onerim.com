# Otomatik QA Test

Laptop oneri asistanini otomatik test senaryolariyla test et ve rapor olustur.

## Ön Koşul
Backend'in `http://localhost:8000` adresinde calisiyor olmasi gerekir.

## Calistirma
```bash
cd laptop_project && .venv/bin/python3 qa_test.py
```

## Test Senaryolari
- Gaming laptop onerisi (GPU tier kontrolu)
- Ofis laptop onerisi (fiyat kontrolu)
- Tasarim/AutoCAD onerisi (discrete GPU zorunlu)
- Ogrenci laptop (ucuz, butce icinde)
- AMD islemci isteme / Intel dislanmasi
- Marka filtresi (Asus)
- Cok turlu konusma (butce sonra verme)
- Fikir degistirme (AMD → Intel)
- Edge case'ler (PC kelimesi, k butce formati, resim URL)

## Kontroller
- `check_has_recommendations`: Oneri sayisi kontrolu
- `check_no_error`: Hata mesaji yoklugu
- `check_gpu_discrete`: Harici GPU zorunlulugu
- `check_gpu_tier`: GPU seviye kontrolu
- `check_brand_included/excluded`: Marka filtre dogrulugu
- `check_price_range`: Butce asim kontrolu
- `check_has_images`: Resim URL varlik kontrolu

## Rapor
Sonuclar konsolda gosterilir:
- GECTI / KALDI durumu
- Hata detaylari
- Yanit sureleri
- Toplam basari orani

## Yeni Test Ekleme
`qa_test.py` icindeki `TEST_CASES` listesine yeni `TestCase` ekle:
```python
TestCase(
    name="Test adi",
    messages=["ilk mesaj", "ikinci mesaj"],
    checks=[
        {"check_no_error": {}, "check_has_recommendations": {"count": 2}},
        {"check_no_error": {}, "check_brand_included": {"brand": "Asus"}},
    ],
)
```
