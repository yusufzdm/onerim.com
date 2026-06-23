# Tam QA Döngüsü

Frontend QA ve Backend QA analizlerini paralel çalıştır, bulgularını birleştir ve önceliklendirilmiş rapor oluştur.

## Adımlar

### 1. Paralel QA Analizi

İki agent'ı **aynı anda** başlat:

**Frontend QA Agent:**
```
Sen bir Frontend QA mühendisisin. frontend/ klasörünü incele.
Kontrol et: bileşen kalitesi, stil/CSS sorunları, API entegrasyonu, markdown parse,
erişilebilirlik (a11y), performans, Vite/build konfigürasyonu.
Her dosyayı oku ve analiz et. Bulguları önem derecesine göre (Kritik / Orta / Düşük) sırala.
Türkçe raporla. Sadece araştırma yap, kod değiştirme.
```

**Backend QA Agent:**
```
Sen bir Backend QA mühendisisin. laptop_project/ klasörünü incele.
Kontrol et: API katmanı, LangGraph akışı, öneri motoru, veritabanı, konfigürasyon,
prompt mühendisliği, thread safety, async/sync karışımı, hata yönetimi, loglama.
Her dosyayı oku ve analiz et. Bulguları önem derecesine göre (Kritik / Orta / Düşük) sırala.
Türkçe raporla. Sadece araştırma yap, kod değiştirme.
```

### 2. Bulguları Birleştir

Her iki QA raporunu al ve tek bir birleşik rapor oluştur:

#### Rapor Formatı

```markdown
# QA Raporu — [Tarih]

## Özet
- Frontend bulgu sayısı: X (Kritik: N, Orta: N, Düşük: N)
- Backend bulgu sayısı: X (Kritik: N, Orta: N, Düşük: N)

## Kritik Bulgular
1. [Bulgu açıklaması] — Frontend/Backend — Dosya:satır

## Orta Öncelikli Bulgular
1. ...

## Düşük Öncelikli Bulgular
1. ...

## Önerilen Aksiyon Planı
### Sprint 1 (Hemen)
- [ ] ...
### Sprint 2 (Kısa vade)
- [ ] ...
### Backlog
- [ ] ...
```

### 3. Team Lead Değerlendirmesi

Birleşik raporu Team Lead perspektifiyle değerlendir:
- Bu küçük ölçekli bir MVP — enterprise seviyesinde olmayan bulguları "kabul edilebilir" olarak işaretle
- Net görev tanımları oluştur: hangi bulguyu kim (Frontend Dev / Backend Dev) düzeltecek
- Öncelik sıralamasını belirle

## Notlar
- Her iki QA agent'ı da sadece okuma yapar, kod değiştirmez
- Raporu kullanıcıya sunduktan sonra düzeltme yapılıp yapılmayacağını sor
- Kullanıcı onaylarsa `/project:frontend-dev` veya `/project:backend-dev` önerebilirsin (varsa)
