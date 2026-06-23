# PC Builder Veri Senkronizasyonu

`pc-builder-agent/sample_data/` ile `frontend/src/data/pcParts.js` arasındaki veriyi senkronize et.

## Veri Kaynakları

### Kaynak (Source): `pc-builder-agent/sample_data/`
Backend tarafındaki ham parça verileri:
- `cpu.json` — İşlemciler
- `gpu.json` — Ekran kartları
- `motherboard.json` — Anakartlar
- `memory.json` — RAM modülleri
- `case.json` — Kasalar
- `psu.json` — Güç kaynakları

### Hedef (Target): `frontend/src/data/pcParts.js`
Frontend'de kullanılan parça listesi ve 3D model eşlemeleri.

## Adımlar

### 1. Kaynak Veriyi Oku
```python
import json
import os

data_dir = "pc-builder-agent/sample_data"
categories = ["cpu", "gpu", "motherboard", "memory", "case", "psu"]

source_data = {}
for cat in categories:
    path = os.path.join(data_dir, f"{cat}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            source_data[cat] = json.load(f)
        print(f"✓ {cat}: {len(source_data[cat])} parça")
    else:
        print(f"✗ {cat}: dosya bulunamadı")
```

### 2. Hedef Veriyi Oku
`frontend/src/data/pcParts.js` dosyasını oku ve mevcut yapıyı analiz et:
- Mevcut parça sayıları
- 3D model eşlemeleri (`glbNodeMap`)
- Veri formatı ve alanlar

### 3. Karşılaştırma
İki veri kaynağını karşılaştır:

```markdown
| Kategori | Kaynak | Hedef | Fark |
|----------|--------|-------|------|
| CPU | X adet | Y adet | +Z yeni |
| GPU | X adet | Y adet | +Z yeni |
| Anakart | X adet | Y adet | +Z yeni |
| RAM | X adet | Y adet | +Z yeni |
| Kasa | X adet | Y adet | +Z yeni |
| PSU | X adet | Y adet | +Z yeni |
```

### 4. Format Dönüşümü
Backend JSON formatını frontend JS formatına dönüştür:

```javascript
// Backend format (JSON):
{"name": "AMD Ryzen 5 5600X", "socket": "AM5", "price": 3500, ...}

// Frontend format (JS):
{
  id: 'cpu-1',
  name: 'AMD Ryzen 5 5600X',
  category: 'cpu',
  price: 3500,
  specs: { socket: 'AM5', ... },
  modelKey: 'cpu'  // GLB model eşlemesi
}
```

### 5. 3D Model Eşlemesi
Her parça kategorisi için GLB model eşlemesini kontrol et:

| Kategori | GLB Dosyası | Durum |
|----------|-------------|-------|
| CPU | `pc_cpu_processor.glb` | Var/Yok |
| GPU | `rtx_3090_asus_rog_strix_*.glb` | Var/Yok |
| Anakart | `x570_prime_motherboard_*.glb` | Var/Yok |
| RAM | `low_poly_ram_module.glb` | Var/Yok |
| Kasa | `nzxt_h500_pc_case.glb` | Var/Yok |
| PSU | `psu_power_supply_unit.glb` | Var/Yok |

### 6. Senkronizasyon
Kullanıcı onayı ile `pcParts.js` dosyasını güncelle:
- Yeni parçaları ekle
- Mevcut parçaları güncelle (fiyat, spec değişiklikleri)
- 3D model eşlemelerini koru
- `glbNodeMap` yapısını bozma

### 7. Doğrulama
Güncelleme sonrası kontrol:
- `pcParts.js` syntax hatası yok
- Tüm kategorilerde en az 1 parça var
- 3D model referansları geçerli
- Frontend build başarılı (`npm run build`)

## Rapor

```markdown
# Senkronizasyon Raporu — [Tarih]

## Değişiklikler
- Eklenen: X parça
- Güncellenen: X parça
- Silinen: X parça (kullanıcı onayı ile)

## Kategori Bazlı
| Kategori | Önceki | Sonraki |
|----------|--------|---------|
| CPU | X | Y |
| ... | ... | ... |

## 3D Model Durumu
- Eşleşen: X/6 kategori
- Eksik model: [liste]
```

## Notlar
- `pcParts.js` ES module formatında — `export` syntax'ını koru
- `glbNodeMap` Three.js ile entegre — yapısını değiştirme
- Mock veriyi gerçek veri ile değiştirirken mevcut ID referanslarını koru
- Frontend build testi ile doğrula
- Büyük değişikliklerde önce yedek al
