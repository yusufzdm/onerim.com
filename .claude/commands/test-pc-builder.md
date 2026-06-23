# PC Builder Test

PC Builder özelliğini kapsamlı test et: veri bütünlüğü, uyumluluk motoru ve frontend 3D bileşenleri.

## Ön Koşul
Frontend'in `http://localhost:5173` adresinde çalışıyor olması gerekir.

## Test Alanları

### 1. Veri Bütünlüğü Testi
`pc-builder-agent/sample_data/` klasöründeki JSON dosyalarını kontrol et:

```python
import json
import os

data_dir = "pc-builder-agent/sample_data"
categories = ["cpu", "gpu", "motherboard", "memory", "case", "psu"]

for cat in categories:
    path = os.path.join(data_dir, f"{cat}.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"{cat}: {len(data)} parça")
    # Zorunlu alan kontrolü
    # Fiyat tutarlılığı
    # Boş/null alan kontrolü
```

### 2. Uyumluluk Motoru Testi
`pc-builder-agent/logic_engine.py` içindeki uyumluluk kontrollerini test et:

- **Soket uyumu:** AM5 CPU + AM5 anakart → geçerli; AM5 CPU + LGA1700 anakart → hata
- **RAM uyumu:** DDR5 RAM + DDR5 destekli anakart → geçerli
- **PSU yeterliliği:** Toplam TDP < PSU watt → geçerli
- **Kasa uyumu:** ATX anakart + ATX kasa → geçerli; ATX anakart + ITX kasa → hata

### 3. Bütçe Hesaplama Testi
`logic_engine.py` bütçe dağılım algoritmasını test et:

| Bütçe | Beklenen Dağılım |
|-------|-----------------|
| 20.000 TL | Entry-level config |
| 40.000 TL | Mid-range config |
| 80.000 TL | High-end config |

Her bütçede toplam fiyatın bütçeyi aşmadığını doğrula.

### 4. Frontend Bileşen Testi
`frontend/src/components/pcbuild/` bileşenlerini kontrol et:

- **PcBuildView.vue:** Sayfa doğru yükleniyor mu?
- **PcScene.vue:** Three.js canvas oluşuyor mu?
- **PartSelector.vue:** Kategori listesi doğru mu?
- **PartCard.vue:** Parça bilgileri doğru gösteriliyor mu?

### 5. 3D Model Testi
`frontend/public/models/` altındaki GLB dosyalarını kontrol et:

```bash
ls -la frontend/public/models/*.glb
```
- Tüm modellerin mevcut olduğunu doğrula
- Dosya boyutlarının makul olduğunu kontrol et (0 byte = bozuk)
- `frontend/src/data/pcParts.js` ile model eşlemelerinin tutarlı olduğunu doğrula

### 6. Frontend-Backend Entegrasyon Durumu
- PC Builder agent'ın frontend ile entegre olup olmadığını kontrol et
- API endpoint'leri var mı?
- Veri akışı tanımlı mı?

## Raporlama

Her test alanı için:
- **Durum:** Geçti / Kaldı / Atlandı
- **Detay:** Bulgu açıklaması
- **Öneri:** Düzeltme önerisi

Sonunda genel bir entegrasyon durumu raporu oluştur.

## Notlar
- PC Builder henüz deneysel — entegrasyon eksikliklerini "beklenen" olarak işaretle
- 3D modeller büyük dosyalar, yükleme sürelerini not et
- `pcParts.js` mock veri kullanıyor — gerçek veri kaynağı ile uyumu kontrol et
