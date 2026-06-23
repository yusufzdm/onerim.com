# 💻 Laptop Öneri Asistanı (önerim.com)

Bu proje, kullanıcıların ihtiyaçlarına ve bütçelerine göre en uygun laptop modellerini öneren yapay zeka destekli bir web uygulamasıdır.

## 🚀 Özellikler

- **Yapay Zeka Destekli:** Kullanıcı mesajlarını analiz ederek en uygun modelleri filtreler.
- **Premium Tasarım:** Altın sarısı ve lacivert renk paletiyle modern ve şık arayüz.
- **Koyu Mod (Dark Mode):** Göz yormayan, otomatik logo değişimli karanlık tema.
- **Akıllı Filtreleme:** İstenmeyen markaları (Casper, Acer vb.) otomatik olarak eler.

## 🛠️ Kurulum

### 1. Backend (Python)

Backend tarafı FastAPI ve LangGraph kullanmaktadır.

```bash
cd laptop_project
# Sanal ortam oluşturun
python -m venv venv
source venv/bin/activate  # Windows için: venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# .env dosyasını oluşturun ve OpenAI API anahtarınızı ekleyin
# OPENAI_API_KEY=your_key_here
```

### 2. Frontend (Vue.js)

Frontend tarafı Vite ve Vue 3 kullanmaktadır.

```bash
cd frontend
# Bağımlılıkları yükleyin
npm install
```

## 🏃‍♂️ Çalıştırma

### Backend'i Başlatın
```bash
cd laptop_project
python api.py
```
Sunucu varsayılan olarak `http://localhost:8000` adresinde çalışacaktır.

### Frontend'i Başlatın
```bash
cd frontend
npm run dev
```
Uygulama varsayılan olarak `http://localhost:5173` adresinde açılacaktır.

## 📂 Proje Yapısı

- `laptop_project/`: Backend kodları, AI promptları ve öneri motoru.
- `frontend/`: Vue.js arayüz kodları ve tasarım bileşenleri.
- `frontend/src/images/`: Logo ve görsel varlıklar.

---
Geliştirenler: [Enes Menekse](https://github.com/EnesMenekse) & [Yusuf Ziya Demirci](https://github.com/yusufzdm)
