<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  laptop: {
    type: Object,
    required: true
  }
});

const isValidUrl = computed(() => {
  const url = props.laptop.url;
  return url && (url.startsWith('http://') || url.startsWith('https://'));
});

const hasValidImage = computed(() => {
  const img = props.laptop.image;
  return img && (img.startsWith('http://') || img.startsWith('https://'));
});

const imageError = ref(false);
const onImageError = () => {
  imageError.value = true;
};
</script>

<template>
  <div class="laptop-card">
    <!-- Yatay layout: resim solda, bilgiler sagda -->
    <div class="card-layout">
      <div v-if="hasValidImage && !imageError" class="card-image">
        <img
          :src="laptop.image"
          :alt="laptop.name"
          loading="lazy"
          @error="onImageError"
        />
      </div>

      <div class="card-content">
        <div class="card-header">
          <h3 class="laptop-title">{{ laptop.name }}</h3>
          <div class="price-badge">{{ laptop.price }} TL</div>
        </div>

        <div class="card-body">
          <div v-if="laptop.reason" class="reason-section">
            <strong>Neden Öneriyoruz?</strong>
            <p>{{ laptop.reason }}</p>
          </div>

          <div v-if="laptop.specs" class="specs-section">
            <strong>Özellikler:</strong>
            <p>{{ laptop.specs }}</p>
          </div>
        </div>

        <div class="card-footer" v-if="isValidUrl">
          <a :href="laptop.url" target="_blank" rel="noopener noreferrer" class="buy-button">
            Ürüne Git
            <svg viewBox="0 0 24 24" fill="none" class="icon">
              <path d="M18 13V19C18 19.5304 17.7893 20.0391 17.4142 20.4142C17.0391 20.7893 16.5304 21 16 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V8C3 7.46957 3.21071 6.96086 3.58579 6.58579C3.96086 6.21071 4.46957 6 5 6H11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M15 3H21V9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M10 14L21 3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.laptop-card {
  background: var(--bg-card);
  border-radius: 14px;
  margin: 10px 0;
  border: 1.5px solid var(--border);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  box-shadow: var(--shadow-sm);
  font-family: 'Inter', sans-serif;
  overflow: hidden;
}

.laptop-card:hover {
  transform: translateY(-2px);
  border-color: var(--accent);
  box-shadow: 0 4px 18px rgba(245,184,0,0.15);
}

.card-layout {
  display: flex;
  gap: 0;
}

.card-image {
  width: 140px;
  min-height: 100%;
  flex-shrink: 0;
  overflow: hidden;
  background: var(--bg-main);
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  padding: 8px;
  transition: transform 0.3s ease;
}

.laptop-card:hover .card-image img {
  transform: scale(1.05);
}

.card-content {
  flex: 1;
  padding: 14px 16px;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 8px;
}

.laptop-title {
  color: var(--text-main);
  margin: 0;
  font-size: 0.92rem;
  font-weight: 700;
  line-height: 1.35;
}

.price-badge {
  background: var(--accent);
  color: #1A2332;
  padding: 4px 10px;
  border-radius: 14px;
  font-weight: 700;
  font-size: 0.78rem;
  white-space: nowrap;
  flex-shrink: 0;
}

.card-body {
  flex: 1;
  margin-bottom: 8px;
}

.reason-section, .specs-section {
  margin-bottom: 6px;
}

.reason-section strong, .specs-section strong {
  display: block;
  color: var(--accent-dark);
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
  margin-bottom: 2px;
}

.reason-section p, .specs-section p {
  color: var(--text-main);
  font-size: 0.82rem;
  line-height: 1.45;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  margin-top: auto;
}

.buy-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-button);
  color: var(--text-button);
  text-decoration: none;
  padding: 7px 14px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.8rem;
  font-family: 'Inter', sans-serif;
  transition: background 0.2s ease, transform 0.15s ease;
}

.buy-button:hover {
  background: var(--accent);
  color: #1A2332;
  transform: translateY(-1px);
}

.icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

/* Resim yoksa daha kompakt */
.card-layout:not(:has(.card-image)) .card-content {
  padding: 16px 18px;
}

/* Responsive: kucuk ekranda dikey layout */
@media (max-width: 600px) {
  .card-layout {
    flex-direction: column;
  }
  .card-image {
    width: 100%;
    height: 120px;
    min-height: auto;
  }
  .card-image img {
    object-fit: cover;
    height: 120px;
  }
}
</style>
