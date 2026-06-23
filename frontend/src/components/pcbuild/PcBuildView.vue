<script setup>
import { reactive, ref, computed, nextTick, watch } from 'vue';
import axios from 'axios';
import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';
import PartSelector from './PartSelector.vue';
import PcScene from './PcScene.vue';
import { optimizeBuild, checkCompatibility, frontendToBackendCategory, categoryLabels } from '../../data/pcParts.js';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const md = new MarkdownIt({ html: false, linkify: true, typographer: true });

// Linkleri yeni sekmede aç (perakendeci ürün linkleri için)
const defaultLinkRender = md.renderer.rules.link_open || function (tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options);
};
md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  tokens[idx].attrSet('target', '_blank');
  tokens[idx].attrSet('rel', 'noopener noreferrer');
  return defaultLinkRender(tokens, idx, options, env, self);
};

const props = defineProps({
  isDark: { type: Boolean, default: false }
});

// --- Selections (3D sahneye gonderilen aktif parca secimi) ---
const selections = reactive({
  motherboard: null,
  cpu: null,
  gpu: null,
  ram: null,
  fan: null,
  psu: null,
  cable: null,
  case: null
});

// --- Build'ler (3 tab icin) ---
const builds = reactive({
  ai: null,       // { parts: {...}, totalPrice: 0, usage: '', compatible: null }
  budget: null,   // fiyat/performans
  premium: null   // kaliteli sistem
});
// Orijinal build'ler — alternatif gosterimi icin degistirilmez kopya
const originalBuilds = reactive({
  ai: null,
  budget: null,
  premium: null
});
const activeBuild = ref('ai');
const isLoadingAlternatives = ref(false);

// Build'i hem calisma kopyasina hem orijinale kaydet
function setBuild(key, build) {
  builds[key] = build;
  // Derin kopya — orijinal degismesin
  originalBuilds[key] = JSON.parse(JSON.stringify(build));
}

// --- Sag panel: Chat ---
const showChat = ref(true);
const chatMessages = ref([
  { role: 'assistant', content: 'Merhaba! PC toplama asistanıyım. Bütçeni ve kullanım amacını söyle, sana en uygun sistemi önereyim.' }
]);
const chatInput = ref('');
const isChatLoading = ref(false);
const chatContainer = ref(null);
const chatThreadId = ref(`pc-${Math.random().toString(36).substring(2, 11)}`);

// --- Otomatik Topla Modal ---
const showOptimizeModal = ref(false);
const optimizeBudget = ref(30000);
const optimizeUsage = ref('gaming');
const isOptimizing = ref(false);
const optimizeError = ref(null);
const optimizeResult = ref(null);

const usageOptions = [
  { value: 'gaming', label: 'Oyun (Gaming)' },
  { value: 'ofis', label: 'Ofis / İş' },
  { value: 'render', label: '3D Render / Video' },
  { value: 'genel', label: 'Genel Kullanım' },
];

// --- Uyumluluk ---
const compatResult = ref(null);

// --- Yardimci ---
function renderMarkdown(content) {
  return DOMPurify.sanitize(md.render(content), { ADD_ATTR: ['target', 'rel'] });
}

async function scrollChatToBottom() {
  await nextTick();
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
}

function toggleChat() {
  showChat.value = !showChat.value;
}

// Turkce karakter normalize (I->i, S->s, vb.)
function trLower(str) {
  return str
    .replace(/İ/g, 'i').replace(/I/g, 'ı')
    .replace(/Ş/g, 'ş').replace(/Ç/g, 'ç')
    .replace(/Ğ/g, 'ğ').replace(/Ö/g, 'ö')
    .replace(/Ü/g, 'ü')
    .toLowerCase();
}

// Kategori eslesmesi
function matchCategory(raw) {
  const s = trLower(raw.trim()).replace(/:$/, '');
  if (s.includes('anakart') || s === 'motherboard') return 'motherboard';
  if (s.includes('lemci') || s === 'cpu') return 'cpu';
  if (s === 'ram' || s.includes('bellek') || s === 'memory') return 'ram';
  if (s.includes('ekran') || s === 'gpu' || s.includes('grafik')) return 'gpu';
  if (s.includes('kasa') || s === 'case') return 'case';
  if (s.includes('kayna') || s === 'psu') return 'psu';
  return null;
}

// Kullanim senaryosu cikarimi
function detectUsage(text) {
  const t = trLower(text);
  if (t.includes('oyun') || t.includes('gaming') || t.includes('game')) return 'gaming';
  if (t.includes('render') || t.includes('video') || t.includes('3d') || t.includes('montaj')) return 'render';
  if (t.includes('ofis') || t.includes('iş') || t.includes('is ') || t.includes('office')) return 'ofis';
  return 'genel';
}

// Fiyat cikarimi — chat yanitindan toplam fiyati bul
function extractTotalPrice(text) {
  // "Toplam: ~45.000 TL" veya "toplam maliyet: 42.500 TL" gibi kaliplari ara
  const patterns = [
    /toplam[^:]*:\s*~?\s*([\d.,]+)\s*TL/i,
    /toplam\s+(?:fiyat|maliyet|tutar)[^:]*:\s*~?\s*([\d.,]+)\s*TL/i,
    /~?\s*([\d.,]+)\s*TL\s*(?:toplam|civarında)/i,
  ];
  for (const pat of patterns) {
    const m = text.match(pat);
    if (m) {
      return parseFloat(m[1].replace(/\./g, '').replace(',', '.'));
    }
  }
  // Son care: tum fiyatlari topla
  return 0;
}

/**
 * Chat yanitindan parcalari parse et ve build objesi olustur
 */
function parseBuildFromChat(reply) {
  const lines = reply.split('\n');
  const parts = {};
  let totalFromParts = 0;

  for (const line of lines) {
    const m = line.match(/\*\*(.+?)\*\*\s*:\s*(.+)/);
    if (!m) continue;

    const frontendCat = matchCategory(m[1]);
    if (!frontendCat) continue;

    let partName = m[2].trim();

    // Fiyati cikar: " - **Fiyat**: 12.500 TL" veya "~ 12.500 TL" vb.
    let price = 0;
    const priceMatch = partName.match(/([\d.,]+)\s*TL/);
    if (priceMatch) {
      price = parseFloat(priceMatch[1].replace(/\./g, '').replace(',', '.'));
    }

    // " - **Fiyat**..." kismini kes
    const fiyatIdx = partName.indexOf(' - **Fiyat');
    if (fiyatIdx > 0) partName = partName.substring(0, fiyatIdx).trim();
    // " — " veya " - " ile gelen fiyat bilgisini kes
    const dashIdx = partName.search(/\s*[-–—]\s*~?\s*[\d.,]+\s*TL/);
    if (dashIdx > 0) partName = partName.substring(0, dashIdx).trim();
    // Markdown kalintilari temizle
    partName = partName.replace(/\*\*/g, '').trim();

    parts[frontendCat] = {
      id: `${frontendCat}-chat-${Date.now()}`,
      name: partName,
      price: price,
      specs: '',
      _raw: { name: partName, price: price }
    };
    totalFromParts += price;
  }

  if (Object.keys(parts).length === 0) return null;

  const extractedTotal = extractTotalPrice(reply);
  return {
    parts,
    totalPrice: extractedTotal || totalFromParts,
    usage: '',
    compatible: null
  };
}

/**
 * Chat'ten gelen AI onerisini isle ve 3 tab'a yansit
 */
/**
 * Chat yanitindan tek parca degisikligini tespit et
 * "X islemcisini secti", "X secildi", "X eklendi" gibi kaliplari ara
 */
function parseSinglePartChange(reply) {
  const text = reply.replace(/\*\*/g, '');
  const lower = trLower(text);

  // Kategori tespiti — yanit iceriginden
  const catPatterns = [
    { pattern: /lemci/i, cat: 'cpu' },
    { pattern: /cpu/i, cat: 'cpu' },
    { pattern: /ekran\s*kart/i, cat: 'gpu' },
    { pattern: /gpu/i, cat: 'gpu' },
    { pattern: /anakart/i, cat: 'motherboard' },
    { pattern: /ram|bellek/i, cat: 'ram' },
    { pattern: /kayna/i, cat: 'psu' },
    { pattern: /kasa/i, cat: 'case' },
  ];

  let detectedCat = null;
  for (const { pattern, cat } of catPatterns) {
    if (pattern.test(lower)) {
      detectedCat = cat;
      break;
    }
  }
  if (!detectedCat) return null;

  // "secti", "secildi", "eklendi", "degistirildi" gibi onay kaliplari
  if (!/se[cç]ti|se[cç]ildi|eklendi|de[gğ]i[sş]tirildi|onaylandi|güncellendi/i.test(lower)) return null;

  // Parca adini bul — genelde bold iceride veya yanit basinda
  // "Intel Core i7-13700F islemcisini basariyla sectiniz" → "Intel Core i7-13700F"
  const namePatterns = [
    // "X islemcisini/ekran kartini secti"
    /(.+?)\s+(?:i[sş]lemcisi|ekran\s*kart[ıi]|anakart[ıi]|ram|bellek|g[uü][cç]\s*kayna[gğ][ıi]|kasas[ıi]|psu)/i,
    // Bold isim: **Parca Adi**
    /\*\*(.+?)\*\*/,
  ];

  let partName = null;
  for (const pat of namePatterns) {
    const m = text.match(pat);
    if (m && m[1] && m[1].trim().length > 3) {
      partName = m[1].trim().replace(/\*\*/g, '');
      break;
    }
  }

  if (!partName) return null;

  // Fiyat cikar
  let price = 0;
  const priceMatch = text.match(/([\d.,]+)\s*TL/);
  if (priceMatch) {
    price = parseFloat(priceMatch[1].replace(/\./g, '').replace(',', '.'));
  }

  return { cat: detectedCat, name: partName, price };
}

/**
 * Onceki chat mesajlarindan parca fiyatini bul
 * "Intel Core i5-12400 ... Fiyat: 4.500 TL" gibi kaliplari ara
 */
function findPriceFromChatHistory(partName) {
  const nameLower = trLower(partName);
  // Son mesajlardan geriye dogru tara
  for (let i = chatMessages.value.length - 1; i >= 0; i--) {
    const msg = chatMessages.value[i];
    if (msg.role !== 'assistant') continue;

    const content = msg.content;
    // Bu mesajda parca adi var mi?
    if (!trLower(content).includes(nameLower)) continue;

    // Parca adinin oldugu satiri bul ve fiyati cikar
    const lines = content.split('\n');
    for (const line of lines) {
      if (!trLower(line).includes(nameLower)) continue;
      const priceMatch = line.match(/(?:Fiyat|fiyat)[:\s]*~?\s*([\d.,]+)\s*TL/);
      if (priceMatch) {
        return parseFloat(priceMatch[1].replace(/\./g, '').replace(',', '.'));
      }
    }

    // Satir bazli bulunamadiysa, parca adinin yakin satirlarinda ara
    for (let j = 0; j < lines.length; j++) {
      if (!trLower(lines[j]).includes(nameLower)) continue;
      // Bu satir ve sonraki 3 satiri tara
      for (let k = j; k < Math.min(j + 4, lines.length); k++) {
        const priceMatch = lines[k].match(/([\d.,]+)\s*TL/);
        if (priceMatch) {
          return parseFloat(priceMatch[1].replace(/\./g, '').replace(',', '.'));
        }
      }
    }
  }
  return 0;
}

/**
 * Backend'in /pc-builder/chat yanıtında dönen structured selected_components
 * dict'ini build formatına çevirir. Markdown-text parse'a göre çok daha güvenilir
 * — formatlama değişiklikleri (multi-retailer karşılaştırma vb.) bunu etkilemez.
 */
function buildFromSelectedComponents(selected, totalPrice) {
  if (!selected || typeof selected !== 'object') return null;
  const mapping = { cpu: 'cpu', gpu: 'gpu', motherboard: 'motherboard', memory: 'ram', psu: 'psu', case: 'case', cooler: 'fan' };
  const parts = {};
  for (const [backendCat, comp] of Object.entries(selected)) {
    const frontendCat = mapping[backendCat];
    if (!frontendCat || !comp || typeof comp !== 'object') continue;
    const specsEntries = Object.entries(comp)
      .filter(([k, v]) => !['name', 'price', '_id', 'id', 'category', 'component_type'].includes(k) && v != null && v !== '')
      .slice(0, 4);
    parts[frontendCat] = {
      id: `${frontendCat}-chat-${Date.now()}`,
      name: comp.name || backendCat,
      price: comp.price || 0,
      specs: specsEntries.map(([, v]) => (typeof v === 'object' ? '' : String(v))).filter(Boolean).join(', '),
      _raw: comp
    };
  }
  if (Object.keys(parts).length === 0) return null;
  const computedTotal = Object.values(parts).reduce((s, p) => s + (p.price || 0), 0);
  return { parts, totalPrice: totalPrice || computedTotal, usage: '', compatible: null };
}

async function applyPartsFromChat(reply, selected = null, totalPrice = null) {
  // Backend structured data döndürdüyse onu kullan (en güvenilir yol)
  const structured = buildFromSelectedComponents(selected, totalPrice);
  if (structured) {
    const allUserMessages = chatMessages.value.filter(m => m.role === 'user').map(m => m.content).join(' ');
    const usage = detectUsage(allUserMessages);
    structured.usage = usage;
    setBuild('ai', structured);
    activeBuild.value = 'ai';
    applyBuildToSelections(structured);
    await generateAlternatives(structured.totalPrice || 30000, usage);
    return;
  }

  const build = parseBuildFromChat(reply);

  if (build) {
    // Tam build — 3+ parca iceriyor
    const allUserMessages = chatMessages.value
      .filter(m => m.role === 'user')
      .map(m => m.content)
      .join(' ');
    const usage = detectUsage(allUserMessages);
    build.usage = usage;

    setBuild('ai', build);
    activeBuild.value = 'ai';
    applyBuildToSelections(build);
    await generateAlternatives(build.totalPrice || 30000, usage);
    return;
  }

  // Tek parca degisikligi dene
  const change = parseSinglePartChange(reply);
  if (change && builds.ai) {
    // Fiyat yoksa onceki chat mesajlarindan bul
    let price = change.price;
    if (!price) {
      price = findPriceFromChatHistory(change.name);
    }

    builds.ai.parts[change.cat] = {
      id: `${change.cat}-chat-${Date.now()}`,
      name: change.name,
      price: price,
      specs: '',
      _raw: { name: change.name, price: price }
    };
    builds.ai.totalPrice = Object.values(builds.ai.parts)
      .reduce((sum, p) => sum + (p.price || 0), 0);

    activeBuild.value = 'ai';
    applyBuildToSelections(builds.ai);
  }
}

/**
 * Bir build'i 3D sahne selections'ina uygula
 */
function applyBuildToSelections(build) {
  if (!build || !build.parts) return;

  // Once sifirla
  for (const key of Object.keys(selections)) {
    selections[key] = null;
  }

  // Sonra uygula
  for (const [cat, part] of Object.entries(build.parts)) {
    if (selections.hasOwnProperty(cat)) {
      selections[cat] = part;
    }
  }
}

/**
 * Backend'den 2 alternatif build olustur (fiyat/performans ve kaliteli)
 */
async function generateAlternatives(baseBudget, usage) {
  if (!baseBudget || baseBudget <= 0) return;

  isLoadingAlternatives.value = true;

  const budgetLow = Math.round(baseBudget * 0.75);
  const budgetHigh = Math.round(baseBudget * 1.4);

  // Paralel cagri
  const [lowResult, highResult] = await Promise.allSettled([
    optimizeBuild(budgetLow, usage),
    optimizeBuild(budgetHigh, usage)
  ]);

  // Fiyat/Performans
  if (lowResult.status === 'fulfilled' && lowResult.value && lowResult.value.build) {
    setBuild('budget', convertOptimizeResultToBuild(lowResult.value, usage));
  }

  // Kaliteli Sistem
  if (highResult.status === 'fulfilled' && highResult.value && highResult.value.build) {
    setBuild('premium', convertOptimizeResultToBuild(highResult.value, usage));
  }

  isLoadingAlternatives.value = false;
}

/**
 * Backend optimize sonucunu build formatina cevir
 */
function convertOptimizeResultToBuild(result, usage) {
  const mapping = {
    cpu: 'cpu',
    gpu: 'gpu',
    motherboard: 'motherboard',
    memory: 'ram',
    psu: 'psu',
    case: 'case'
  };

  const parts = {};
  const details = result.build_details || {};

  if (result.build) {
    for (const [backendCat, frontendCat] of Object.entries(mapping)) {
      const partName = result.build[backendCat];
      if (!partName) continue;

      const detail = details[backendCat];
      if (detail && typeof detail === 'object') {
        const specsEntries = Object.entries(detail)
          .filter(([k, v]) => !['name', 'price', '_id', 'id', 'category'].includes(k) && v != null && v !== '')
          .slice(0, 4);

        parts[frontendCat] = {
          id: `${frontendCat}-opt-${Date.now()}`,
          name: detail.name || partName,
          price: detail.price || 0,
          specs: specsEntries.map(([, v]) => String(v)).join(', '),
          _raw: detail
        };
      } else {
        parts[frontendCat] = {
          id: `${frontendCat}-opt-${Date.now()}`,
          name: partName,
          price: 0,
          specs: '',
          _raw: { name: partName }
        };
      }
    }
  }

  return {
    parts,
    totalPrice: result.total_price || 0,
    usage: usage,
    compatible: result.compatibility ? result.compatibility.valid : null
  };
}

// --- Tab degisimi => selections guncelle ---
function onActiveBuildChange(key) {
  activeBuild.value = key;
  const build = builds[key];
  if (build) {
    applyBuildToSelections(build);
  }
}

function onSelectBuild(key) {
  activeBuild.value = key;
  const build = builds[key];
  if (build) {
    applyBuildToSelections(build);
  }
}

function onSwapPart({ category, part }) {
  // Aktif tab'daki build'i guncelle
  const currentKey = activeBuild.value;
  const currentBuild = builds[currentKey];
  if (!currentBuild) return;

  currentBuild.parts[category] = part;
  currentBuild.totalPrice = Object.values(currentBuild.parts)
    .reduce((sum, p) => sum + (p.price || 0), 0);
  applyBuildToSelections(currentBuild);
}

// --- Chat ---
async function sendChatMessage() {
  const msg = chatInput.value.trim();
  if (!msg || isChatLoading.value) return;

  chatMessages.value.push({ role: 'user', content: msg });
  chatInput.value = '';
  isChatLoading.value = true;
  scrollChatToBottom();

  try {
    const resp = await axios.post(`${API_BASE_URL}/pc-builder/chat`, {
      message: msg,
      thread_id: chatThreadId.value
    }, { timeout: 60000 });

    chatMessages.value.push({ role: 'assistant', content: resp.data.reply });
    applyPartsFromChat(resp.data.reply, resp.data.selected_components, resp.data.total_price);
  } catch (err) {
    const errMsg = err.code === 'ECONNABORTED'
      ? 'Yanıt süresi doldu, lütfen tekrar deneyin.'
      : 'Bir hata oluştu. Backend servisini kontrol edin.';
    chatMessages.value.push({ role: 'assistant', content: errMsg });
  } finally {
    isChatLoading.value = false;
    scrollChatToBottom();
  }
}

// --- Otomatik Topla Modal ---
function openOptimizeModal() {
  optimizeError.value = null;
  optimizeResult.value = null;
  showOptimizeModal.value = true;
}

function closeOptimizeModal() {
  showOptimizeModal.value = false;
}

async function runOptimize() {
  isOptimizing.value = true;
  optimizeError.value = null;
  optimizeResult.value = null;

  try {
    const result = await optimizeBuild(optimizeBudget.value, optimizeUsage.value);
    optimizeResult.value = result;

    // AI onerisi tab'ina yaz
    const aiBuild = convertOptimizeResultToBuild(result, optimizeUsage.value);
    setBuild('ai', aiBuild);
    activeBuild.value = 'ai';
    applyBuildToSelections(aiBuild);

    // Alternatif build'leri de olustur
    await generateAlternatives(optimizeBudget.value, optimizeUsage.value);

    // Modal'i kapat
    showOptimizeModal.value = false;
  } catch (err) {
    console.error('[PC Builder] Otomatik toplama hatası:', err);
    optimizeError.value = err.response?.data?.detail || 'Otomatik toplama sırasında bir hata oluştu. Backend servisini kontrol edin.';
  } finally {
    isOptimizing.value = false;
  }
}

// Chat input textarea auto-resize
function handleChatKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChatMessage();
  }
}
</script>

<template>
  <div class="pcbuild-container">
    <!-- Sol Panel: Build Secenekleri -->
    <PartSelector
      :builds="builds"
      :original-builds="originalBuilds"
      :active-build="activeBuild"
      :is-loading-alternatives="isLoadingAlternatives"
      :compat-result="compatResult"
      @update:active-build="onActiveBuildChange"
      @open-optimize-modal="openOptimizeModal"
      @select-build="onSelectBuild"
      @swap-part="onSwapPart"
    />

    <!-- Orta: 3D Sahne -->
    <div class="scene-wrapper" :class="{ 'chat-open': showChat }">
      <PcScene
        :selections="selections"
        :is-dark="isDark"
      />
    </div>

    <!-- Chat Toggle Butonu -->
    <button v-if="!showChat" class="chat-toggle-btn" @click="toggleChat">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="chat-toggle-icon">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <span class="chat-toggle-label">Asistanla Konuş</span>
    </button>

    <!-- Sag Panel: Chat (tam yukseklik) -->
    <transition name="slide-chat">
      <div v-if="showChat" class="chat-panel">
        <div class="chat-header">
          <h3>PC Toplama Asistanı</h3>
          <button class="close-btn" @click="showChat = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div ref="chatContainer" class="chat-messages">
          <div
            v-for="(msg, i) in chatMessages"
            :key="i"
            class="chat-msg"
            :class="msg.role"
          >
            <div class="chat-avatar" :class="msg.role">
              <template v-if="msg.role === 'assistant'">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="avatar-icon">
                  <rect x="2" y="3" width="20" height="14" rx="2"/>
                  <path d="M8 21h8M12 17v4"/>
                </svg>
              </template>
              <template v-else>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="avatar-icon">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </template>
            </div>
            <div v-if="msg.role === 'assistant'" class="msg-bubble" v-html="renderMarkdown(msg.content)"></div>
            <div v-else class="msg-bubble">{{ msg.content }}</div>
          </div>
          <div v-if="isChatLoading" class="chat-msg assistant">
            <div class="chat-avatar assistant">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="avatar-icon">
                <rect x="2" y="3" width="20" height="14" rx="2"/>
                <path d="M8 21h8M12 17v4"/>
              </svg>
            </div>
            <div class="msg-bubble typing">
              <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <div class="chat-input-wrapper">
            <input
              v-model="chatInput"
              type="text"
              placeholder="Bütçenizi ve kullanım amacınızı yazın..."
              @keydown="handleChatKeydown"
              :disabled="isChatLoading"
            />
            <button class="send-btn" @click="sendChatMessage" :disabled="isChatLoading || !chatInput.trim()">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Otomatik Topla Modal -->
    <transition name="modal-fade">
      <div v-if="showOptimizeModal" class="modal-overlay" @click.self="closeOptimizeModal">
        <div class="modal-content">
          <div class="modal-header">
            <h2>Otomatik Sistem Topla</h2>
            <button class="close-btn" @click="closeOptimizeModal">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="form-group">
              <label for="budget">Bütçe (TL)</label>
              <input
                id="budget"
                v-model.number="optimizeBudget"
                type="number"
                min="5000"
                max="200000"
                step="1000"
                class="form-input"
              />
              <span class="form-hint">{{ optimizeBudget.toLocaleString('tr-TR') }} TL</span>
            </div>

            <div class="form-group">
              <label>Kullanım Senaryosu</label>
              <div class="usage-options">
                <button
                  v-for="opt in usageOptions"
                  :key="opt.value"
                  class="usage-btn"
                  :class="{ active: optimizeUsage === opt.value }"
                  @click="optimizeUsage = opt.value"
                >
                  {{ opt.label }}
                </button>
              </div>
            </div>

            <div v-if="optimizeError" class="optimize-error">
              {{ optimizeError }}
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="closeOptimizeModal">İptal</button>
            <button
              class="btn-primary"
              @click="runOptimize"
              :disabled="isOptimizing"
            >
              <template v-if="isOptimizing">
                <span class="btn-spinner"></span> Hesaplanıyor...
              </template>
              <template v-else>Sistemi Topla</template>
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
/* ===== ANA LAYOUT ===== */
.pcbuild-container {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.scene-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
  transition: margin-right 0.3s ease;
}

.scene-wrapper.chat-open {
  margin-right: 0;
}

/* ===== AKSIYON CUBUGU ===== */
.action-bar {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 5;
  display: flex;
  gap: 10px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border: none;
  border-radius: 20px;
  font-family: 'Inter', sans-serif;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 12px var(--shadow-md);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-icon {
  width: 16px;
  height: 16px;
}

.optimize-btn {
  background: var(--accent);
  color: #1A2332;
}

.optimize-btn:hover:not(:disabled) {
  background: var(--accent-dark);
  transform: translateY(-1px);
}

/* ===== CHAT TOGGLE ===== */
.chat-toggle-btn {
  position: fixed;
  bottom: 28px;
  right: 28px;
  padding: 14px 24px;
  border-radius: 28px;
  background: var(--accent);
  color: #1A2332;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 24px rgba(245, 184, 0, 0.35);
  z-index: 50;
  transition: all 0.25s ease;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  font-weight: 700;
}

.chat-toggle-btn:hover {
  transform: translateY(-2px);
  background: var(--accent-dark);
  box-shadow: 0 6px 32px rgba(245, 184, 0, 0.45);
}

.chat-toggle-icon {
  width: 22px;
  height: 22px;
}

.chat-toggle-label {
  white-space: nowrap;
}

/* ===== SAG CHAT PANELI (tam yukseklik) ===== */
.chat-panel {
  width: 400px;
  flex-shrink: 0;
  background: var(--bg-navbar);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.chat-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-main);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 50%;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  border-color: var(--accent);
  color: var(--text-main);
}

.close-btn svg {
  width: 16px;
  height: 16px;
}

/* Chat mesajlari */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}

.chat-msg {
  display: flex;
  gap: 10px;
  animation: msgIn 0.25s ease both;
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.chat-msg.user {
  flex-direction: row-reverse;
}

.chat-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-avatar.assistant {
  background: var(--accent-light);
  border: 1.5px solid var(--accent);
  color: var(--accent-dark);
}

.chat-avatar.user {
  background: var(--bg-user-msg);
  color: #fff;
}

.avatar-icon {
  width: 16px;
  height: 16px;
}

.msg-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 0.85rem;
  line-height: 1.55;
  word-break: break-word;
}

.chat-msg.user .msg-bubble {
  background: var(--accent);
  color: #1A2332;
  border-bottom-right-radius: 4px;
}

.chat-msg.assistant .msg-bubble {
  background: var(--bg-card);
  color: var(--text-main);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
}

.msg-bubble.typing {
  display: flex;
  gap: 4px;
  padding: 14px 18px;
}

.msg-bubble.typing .dot {
  width: 8px;
  height: 8px;
  background: var(--text-muted);
  border-radius: 50%;
  animation: typing-bounce 1.2s infinite;
}

.msg-bubble.typing .dot:nth-child(2) { animation-delay: 0.15s; }
.msg-bubble.typing .dot:nth-child(3) { animation-delay: 0.3s; }

@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

.msg-bubble :deep(p) { margin: 0 0 6px; }
.msg-bubble :deep(p:last-child) { margin: 0; }
.msg-bubble :deep(ul), .msg-bubble :deep(ol) { margin: 4px 0; padding-left: 18px; }
.msg-bubble :deep(strong) { font-weight: 700; }
.msg-bubble :deep(code) {
  background: var(--border);
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 0.8rem;
}

/* Chat input */
.chat-input-area {
  padding: 12px 16px 16px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

.chat-input-wrapper {
  display: flex;
  gap: 8px;
  background: var(--bg-card);
  border: 1.5px solid var(--border);
  border-radius: 24px;
  padding: 4px 4px 4px 16px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.chat-input-wrapper:focus-within {
  border-color: var(--accent);
  box-shadow: 0 2px 12px rgba(245,184,0,0.15);
}

.chat-input-wrapper input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-main);
  font-family: 'Inter', sans-serif;
  font-size: 0.85rem;
  outline: none;
  padding: 8px 0;
}

.chat-input-wrapper input::placeholder {
  color: var(--text-muted);
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent);
  color: #1A2332;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.send-btn:hover:not(:disabled) {
  background: var(--accent-dark);
}

.send-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.send-btn svg {
  width: 16px;
  height: 16px;
}

/* ===== MODAL ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-content {
  background: var(--bg-card);
  border-radius: 16px;
  width: 440px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 8px 40px var(--shadow-md);
  border: 1px solid var(--border);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
}

.modal-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid var(--border);
}

/* Form */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-main);
}

.form-input {
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  color: var(--text-main);
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  transition: border-color 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--accent);
}

.form-hint {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.usage-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.usage-btn {
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  color: var(--text-main);
  font-family: 'Inter', sans-serif;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.usage-btn:hover {
  border-color: var(--accent);
}

.usage-btn.active {
  border-color: var(--accent);
  background: var(--accent-light);
  color: var(--accent-dark);
  font-weight: 600;
}

.optimize-error {
  padding: 10px 14px;
  background: #fef2f2;
  color: #991b1b;
  border-radius: 10px;
  font-size: 0.85rem;
}

body.dark-mode .optimize-error {
  background: #7f1d1d33;
  color: #fca5a5;
}

/* Butonlar */
.btn-primary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px;
  background: var(--accent);
  color: #1A2332;
  border: none;
  border-radius: 20px;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-dark);
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 22px;
  background: transparent;
  color: var(--text-muted);
  border: 1.5px solid var(--border);
  border-radius: 20px;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  border-color: var(--accent);
  color: var(--text-main);
}

.btn-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #1A2332;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== TRANSITIONS ===== */
.slide-chat-enter-active,
.slide-chat-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-chat-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-chat-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.25s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

/* ===== RESPONSIVE ===== */
@media (max-width: 1200px) {
  .chat-panel {
    width: 340px;
  }

}

@media (max-width: 900px) {
  .pcbuild-container {
    flex-direction: column;
  }

  .chat-panel {
    position: fixed;
    top: 64px;
    right: 0;
    bottom: 0;
    width: 100%;
    max-width: 400px;
    z-index: 50;
    box-shadow: -4px 0 24px var(--shadow-md);
  }
}
</style>
