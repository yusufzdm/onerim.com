<script setup>
import { ref, computed, watch } from 'vue';
import { categoryLabels } from '../../data/pcParts.js';

const props = defineProps({
  /** Secili tab'daki parca build objesi */
  builds: {
    type: Object,
    default: () => ({ ai: null, budget: null, premium: null })
  },
  /** Orijinal build'ler — alternatif gosterimi icin (degistirilmez) */
  originalBuilds: {
    type: Object,
    default: () => ({ ai: null, budget: null, premium: null })
  },
  /** Aktif olarak kullanilan build key'i */
  activeBuild: { type: String, default: 'ai' },
  /** Build'ler yukleniyor mu */
  isLoadingAlternatives: { type: Boolean, default: false },
  /** Uyumluluk durumu */
  compatResult: { type: Object, default: null }
});

const emit = defineEmits(['update:activeBuild', 'open-optimize-modal', 'select-build', 'swap-part']);

const activeTab = ref('ai');
const expandedPart = ref(null); // Tiklaninca alternatif gosterilen kategori

// Kategori ikonlari (SVG path'leri)
const categoryIcons = {
  motherboard: 'M4 4h16v16H4V4zm2 2v12h12V6H6zm3 3h2v2H9V9zm4 0h2v2h-2V9zm-4 4h2v2H9v-2zm4 0h2v2h-2v-2z',
  cpu: 'M9 2v2H7v2H5v2H3v4h2v2h2v2h2v2h6v-2h2v-2h2v-2h2V8h-2V6h-2V4h-2V2H9zm0 6h6v8H9V8z',
  gpu: 'M2 7h20v10H2V7zm2 2v6h16V9H4zm2 1h3v4H6v-4zm5 0h3v4h-3v-4z',
  ram: 'M3 6h18v12H3V6zm2 2v8h14V8H5zm1 1h2v6H6V9zm3 0h2v6H9V9zm3 0h2v6h-2V9zm3 0h2v6h-2V9z',
  fan: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 4c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2zm-4 8c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm8 0c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z',
  psu: 'M4 4h16v16H4V4zm2 2v5h5V6H6zm7 0v5h5V6h-5zM6 13v5h12v-5H6z',
  cable: 'M7 2v6H5v3h2v2H5v3h2v6h2v-6h2v-3H9v-2h2V8H9V2H7zm8 0v6h-2v3h2v2h-2v3h2v6h2v-6h2v-3h-2v-2h2V8h-2V2h-2z',
  case: 'M6 2h12v20H6V2zm2 2v16h8V4H8zm2 2h4v2h-4V6zm0 4h4v2h-4v-2zm1 6h2v2h-2v-2z'
};

const tabs = [
  { key: 'ai', label: 'AI Önerisi', icon: 'M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z' },
  { key: 'budget', label: 'Fiyat/Performans', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm0-4h-2V7h2v8z' },
  { key: 'premium', label: 'Kaliteli Sistem', icon: 'M5 9l1.5 4.5h3L11 9l1 4.5h3L16.5 9 19 13.5V19H5v-5.5L5 9zm7-7l2 4h-4l2-4z' }
];

const hasAnyBuild = computed(() => {
  return props.builds.ai || props.builds.budget || props.builds.premium;
});

const currentBuild = computed(() => {
  return props.builds[activeTab.value] || null;
});

const currentParts = computed(() => {
  if (!currentBuild.value || !currentBuild.value.parts) return [];
  const parts = currentBuild.value.parts;
  const result = [];
  const order = ['motherboard', 'cpu', 'gpu', 'ram', 'psu', 'case', 'fan', 'cable'];
  for (const cat of order) {
    if (parts[cat]) {
      result.push({
        category: cat,
        categoryLabel: categoryLabels[cat] || cat,
        ...parts[cat]
      });
    }
  }
  return result;
});

const totalPrice = computed(() => {
  if (!currentBuild.value) return 0;
  if (currentBuild.value.totalPrice) return currentBuild.value.totalPrice;
  return currentParts.value.reduce((sum, p) => sum + (p.price || 0), 0);
});

const isCompatible = computed(() => {
  if (!currentBuild.value) return null;
  if (currentBuild.value.compatible !== null && currentBuild.value.compatible !== undefined) {
    return currentBuild.value.compatible;
  }
  return null;
});

function togglePartExpand(category) {
  expandedPart.value = expandedPart.value === category ? null : category;
}

function getAlternative(category, buildKey) {
  // Orijinal build'lerden goster — kullanici degistirse bile orijinal alternatif gorunur
  const build = props.originalBuilds[buildKey];
  if (!build || !build.parts || !build.parts[category]) return null;
  return build.parts[category];
}

function swapPart(category, buildKey) {
  const alt = getAlternative(category, buildKey);
  if (alt) {
    emit('swap-part', { category, part: { ...alt } });
    expandedPart.value = null;
  }
}

// Aktif tab'a gore gosterilecek alternatif tab'lari dondur
const alternativeTabs = computed(() => {
  const all = [
    { key: 'ai', label: 'AI', badge: 'AI', badgeClass: 'ai-badge' },
    { key: 'budget', label: 'F/P', badge: 'F/P', badgeClass: '' },
    { key: 'premium', label: 'Kaliteli', badge: 'PRO', badgeClass: 'premium-badge' }
  ];
  return all.filter(t => t.key !== activeTab.value);
});

function selectTab(key) {
  activeTab.value = key;
  emit('update:activeBuild', key);
}

function selectCurrentBuild() {
  emit('select-build', activeTab.value);
}

// Dis erisim icin tab'i sync tut
watch(() => props.activeBuild, (val) => {
  if (val !== activeTab.value) {
    activeTab.value = val;
  }
});
</script>

<template>
  <aside class="build-panel">
    <!-- Baslik -->
    <div class="panel-header">
      <h2>Sistem Toplama</h2>
    </div>

    <!-- Bos durum: hicbir oneri yokken -->
    <div v-if="!hasAnyBuild" class="empty-state">
      <div class="empty-icon-wrapper">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
          <rect x="2" y="3" width="20" height="14" rx="2"/>
          <path d="M8 21h8M12 17v4"/>
        </svg>
      </div>
      <h3 class="empty-title">Henüz bir sistem oluşturulmadı</h3>
      <p class="empty-desc">
        Sağ paneldeki chat ile asistana bütçenizi ve kullanım amacınızı söyleyin, size en uygun sistemi önersin.
      </p>
      <button class="auto-build-btn" @click="$emit('open-optimize-modal')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="btn-icon">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
        Otomatik Topla
      </button>
      <p class="empty-hint">veya sağdaki sohbeti kullanın</p>
    </div>

    <!-- Build mevcut: 3 tab -->
    <template v-else>
      <!-- Tab bar -->
      <div class="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{
            active: activeTab === tab.key,
            'has-data': !!builds[tab.key],
            loading: !builds[tab.key] && isLoadingAlternatives && tab.key !== 'ai'
          }"
          @click="selectTab(tab.key)"
        >
          <span class="tab-label">{{ tab.label }}</span>
          <span v-if="!builds[tab.key] && isLoadingAlternatives && tab.key !== 'ai'" class="tab-spinner"></span>
        </button>
      </div>

      <!-- Tab icerik -->
      <div class="tab-content">
        <!-- Yukleniyor -->
        <div v-if="!currentBuild && isLoadingAlternatives" class="loading-state">
          <div class="loading-spinner"></div>
          <p>Alternatif hesaplanıyor...</p>
        </div>

        <!-- Veri yok -->
        <div v-else-if="!currentBuild" class="no-data-state">
          <p>Bu seçenek için henüz veri yok.</p>
        </div>

        <!-- Parca listesi -->
        <div v-else class="parts-list">
          <div
            v-for="part in currentParts"
            :key="part.category"
            class="part-wrapper"
          >
            <div class="part-card" :class="{ expanded: expandedPart === part.category }" @click="togglePartExpand(part.category)">
              <div class="part-card-left">
                <div class="part-cat-icon">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="cat-icon">
                    <path :d="categoryIcons[part.category] || categoryIcons.case"/>
                  </svg>
                </div>
                <div class="part-card-info">
                  <span class="part-cat-label">{{ part.categoryLabel }}</span>
                  <span class="part-name">{{ part.name }}</span>
                  <span v-if="part.specs" class="part-specs">{{ part.specs }}</span>
                </div>
              </div>
              <div class="part-card-right">
                <div class="part-card-price">
                  {{ (part.price || 0).toLocaleString('tr-TR') }} TL
                </div>
                <a
                  v-if="part._raw && part._raw.url"
                  :href="part._raw.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="part-link-btn"
                  @click.stop
                  title="Ürün sayfasına git"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 13V19C18 20.1 17.1 21 16 21H5C3.9 21 3 20.1 3 19V8C3 6.9 3.9 6 5 6H11"/>
                    <path d="M15 3H21V9"/>
                    <path d="M10 14L21 3"/>
                  </svg>
                </a>
                <svg class="expand-chevron" :class="{ open: expandedPart === part.category }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M6 9l6 6 6-6"/>
                </svg>
              </div>
            </div>

            <!-- Alternatifler (aktif tab haric diger 2 tab'dan) -->
            <div v-if="expandedPart === part.category" class="part-alternatives">
              <template v-for="alt in alternativeTabs" :key="alt.key">
                <div
                  v-if="getAlternative(part.category, alt.key)"
                  class="alt-card"
                  @click="swapPart(part.category, alt.key)"
                >
                  <div class="alt-badge" :class="alt.badgeClass">{{ alt.badge }}</div>
                  <div class="alt-info">
                    <span class="alt-name">{{ getAlternative(part.category, alt.key).name }}</span>
                    <span class="alt-specs">{{ getAlternative(part.category, alt.key).specs }}</span>
                  </div>
                  <span class="alt-price">{{ (getAlternative(part.category, alt.key).price || 0).toLocaleString('tr-TR') }} TL</span>
                  <a
                    v-if="getAlternative(part.category, alt.key)._raw && getAlternative(part.category, alt.key)._raw.url"
                    :href="getAlternative(part.category, alt.key)._raw.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="alt-link-btn"
                    @click.stop
                    title="Ürün sayfasına git"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M18 13V19C18 20.1 17.1 21 16 21H5C3.9 21 3 20.1 3 19V8C3 6.9 3.9 6 5 6H11"/>
                      <path d="M15 3H21V9"/>
                      <path d="M10 14L21 3"/>
                    </svg>
                  </a>
                </div>
              </template>

              <div v-if="alternativeTabs.every(t => !getAlternative(part.category, t.key))" class="alt-empty">
                Alternatif henüz yok
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Alt: Toplam + Uyumluluk + Aksiyon -->
      <div class="panel-footer" v-if="currentBuild">
        <div class="footer-row">
          <span class="total-label">Toplam</span>
          <span class="total-price">{{ totalPrice.toLocaleString('tr-TR') }} TL</span>
        </div>
        <div class="footer-row" v-if="isCompatible !== null">
          <span
            class="compat-badge"
            :class="isCompatible ? 'compat-ok' : 'compat-fail'"
          >
            <svg v-if="isCompatible" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="compat-icon">
              <path d="M9 12l2 2 4-4"/>
              <circle cx="12" cy="12" r="10"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="compat-icon">
              <circle cx="12" cy="12" r="10"/>
              <path d="M15 9l-6 6M9 9l6 6"/>
            </svg>
            {{ isCompatible ? 'Uyumlu' : 'Uyumsuz' }}
          </span>
        </div>
        <button class="select-build-btn" @click="selectCurrentBuild">
          Bu Sistemi Seç
        </button>
      </div>
    </template>
  </aside>
</template>

<style scoped>
.build-panel {
  width: 350px;
  flex-shrink: 0;
  background: var(--bg-navbar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 20px 16px;
  border-bottom: 1px solid var(--border);
}

.panel-header h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-main);
}

/* Bos durum */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
  text-align: center;
  gap: 12px;
}

.empty-icon-wrapper {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--accent-light);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.empty-icon {
  width: 36px;
  height: 36px;
  color: var(--accent-dark);
}

.empty-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-main);
}

.empty-desc {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.5;
  max-width: 280px;
}

.auto-build-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 12px 24px;
  background: var(--accent);
  color: #1A2332;
  border: none;
  border-radius: 24px;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 12px rgba(245,184,0,0.35);
}

.auto-build-btn:hover {
  background: var(--accent-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 18px rgba(245,184,0,0.45);
}

.btn-icon {
  width: 18px;
  height: 18px;
}

.empty-hint {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-muted);
  font-style: italic;
}

/* Tab bar */
.tab-bar {
  display: flex;
  border-bottom: 1px solid var(--border);
  padding: 0;
  flex-shrink: 0;
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 12px 6px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-family: 'Inter', sans-serif;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.tab-btn:hover:not(:disabled) {
  color: var(--text-main);
  background: var(--accent-light);
}

.tab-btn.active {
  color: var(--accent-dark);
  border-bottom-color: var(--accent);
  background: var(--accent-light);
}

.tab-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.tab-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Tab icerik */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  color: var(--text-muted);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-state p {
  font-size: 0.85rem;
  font-weight: 500;
}

.no-data-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-muted);
  font-size: 0.85rem;
  text-align: center;
}

/* Parca kartlari */
.parts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.part-wrapper {
  display: flex;
  flex-direction: column;
}

.part-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  background: var(--bg-card);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.part-card:hover {
  border-color: var(--accent);
  box-shadow: 0 2px 8px rgba(245,184,0,0.1);
}

.part-card.expanded {
  border-color: var(--accent);
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.part-card-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.part-link-btn, .alt-link-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  color: var(--text-muted);
  background: transparent;
  transition: all 0.2s ease;
  flex-shrink: 0;
  text-decoration: none;
}

.part-link-btn:hover, .alt-link-btn:hover {
  color: var(--accent-dark);
  background: var(--accent-light);
}

.part-link-btn svg, .alt-link-btn svg {
  width: 14px;
  height: 14px;
}

.expand-chevron {
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  transition: transform 0.2s ease;
}

.expand-chevron.open {
  transform: rotate(180deg);
}

/* Alternatifler */
.part-alternatives {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  background: var(--bg-input);
  border: 1.5px solid var(--accent);
  border-top: none;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}

.alt-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.alt-card:hover {
  border-color: var(--accent);
  transform: translateX(2px);
}

.alt-badge {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.65rem;
  font-weight: 700;
  background: #065f46;
  color: #ecfdf5;
  letter-spacing: 0.03em;
}

.alt-badge.premium-badge {
  background: #7c3aed;
  color: #f5f3ff;
}

.alt-badge.ai-badge {
  background: var(--accent);
  color: #1A2332;
}

body.dark-mode .alt-badge {
  background: #064e3b;
  color: #6ee7b7;
}

body.dark-mode .alt-badge.premium-badge {
  background: #5b21b6;
  color: #c4b5fd;
}

.alt-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.alt-name {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-main);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alt-specs {
  font-size: 0.68rem;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alt-price {
  flex-shrink: 0;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent-dark);
}

.alt-empty {
  text-align: center;
  padding: 8px;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.part-card-left {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.part-cat-icon {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-light);
  border-radius: 8px;
  color: var(--accent-dark);
}

.cat-icon {
  width: 16px;
  height: 16px;
}

.part-card-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.part-cat-label {
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.part-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-main);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.part-specs {
  font-size: 0.72rem;
  color: var(--text-muted);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.part-card-price {
  font-weight: 700;
  font-size: 0.82rem;
  color: var(--accent-dark);
  white-space: nowrap;
  flex-shrink: 0;
}

/* Footer */
.panel-footer {
  padding: 14px 20px;
  border-top: 2px solid var(--accent);
  background: var(--bg-card);
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}

.footer-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.total-label {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-main);
}

.total-price {
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--accent-dark);
}

.compat-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 600;
}

.compat-badge.compat-ok {
  background: #ecfdf5;
  color: #065f46;
}

.compat-badge.compat-fail {
  background: #fef2f2;
  color: #991b1b;
}

body.dark-mode .compat-badge.compat-ok {
  background: #064e3b33;
  color: #6ee7b7;
}

body.dark-mode .compat-badge.compat-fail {
  background: #7f1d1d33;
  color: #fca5a5;
}

.compat-icon {
  width: 16px;
  height: 16px;
}

.select-build-btn {
  width: 100%;
  padding: 12px;
  background: var(--accent);
  color: #1A2332;
  border: none;
  border-radius: 12px;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(245,184,0,0.3);
}

.select-build-btn:hover {
  background: var(--accent-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(245,184,0,0.4);
}

/* Responsive */
@media (max-width: 1200px) {
  .build-panel {
    width: 300px;
  }
}

@media (max-width: 768px) {
  .build-panel {
    width: 100%;
    max-height: 50vh;
  }
}
</style>
