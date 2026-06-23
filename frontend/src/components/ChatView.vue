<script setup>
import { ref, onMounted, nextTick } from 'vue';
import axios from 'axios';
import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';
import LaptopCard from './LaptopCard.vue';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true
});

// Linkleri yeni sekmede ac
const defaultRender = md.renderer.rules.link_open || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options);
};
md.renderer.rules.link_open = function(tokens, idx, options, env, self) {
  tokens[idx].attrSet('target', '_blank');
  tokens[idx].attrSet('rel', 'noopener noreferrer');
  return defaultRender(tokens, idx, options, env, self);
};

const messages = ref([
  {
    role: 'assistant',
    content: 'Merhaba! Ben Laptop Öneri Asistanıyım. Nasıl bir laptop arıyorsun? Kullanım amacını ve bütçeni söylersen sana en uygun modelleri bulabilirim.',
    isParsed: true,
    intro: 'Merhaba! Ben Laptop Öneri Asistanıyım. Nasıl bir laptop arıyorsun? Kullanım amacını ve bütçeni söylersen sana en uygun modelleri bulabilirim.',
    laptops: [],
    followup: ''
  }
]);

const userInput = ref('');
const isLoading = ref(false);
const chatContainer = ref(null);
const threadId = ref(`thread_${Math.random().toString(36).substr(2, 9)}`);

const scrollToBottom = async () => {
  await nextTick();
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

const resetChat = () => {
  messages.value = [
    {
      role: 'assistant',
      content: 'Yeni bir sohbet başlattık! Sana nasıl yardımcı olabilirim?',
      isParsed: true,
      intro: 'Yeni bir sohbet başlattık! Sana nasıl yardımcı olabilirim?',
      laptops: [],
      followup: ''
    }
  ];
  threadId.value = `thread_${Math.random().toString(36).substr(2, 9)}`;
};

const copyDebugLog = async () => {
  try {
    const resp = await axios.get(`${API_BASE_URL}/chat/history/${threadId.value}`, { timeout: 5000 });
    const data = resp.data;
    let log = `=== Thread: ${data.thread_id} ===\n`;
    log += `Preferences: ${JSON.stringify(data.preferences, null, 2)}\n\n`;
    for (const msg of (data.messages || [])) {
      log += `[${msg.role}]: ${msg.content}\n\n`;
    }
    await navigator.clipboard.writeText(log);
    alert('Konuşma logu panoya kopyalandı!');
  } catch {
    // Fallback: frontend mesajlarini kopyala
    let log = `=== Thread: ${threadId.value} ===\n\n`;
    for (const msg of messages.value) {
      log += `[${msg.role}]: ${msg.content?.substring(0, 500)}\n\n`;
    }
    await navigator.clipboard.writeText(log);
    alert('Konuşma logu panoya kopyalandı (frontend)!');
  }
};

defineExpose({ resetChat });

const parseAssistantMessage = (text) => {
  // Her laptop blogunu ayri ayri parse et
  const laptops = [];

  // Laptop bloklarini bul: [IMG:...] opsiyonel (bos satirlar olabilir), sonra ### N) baslik
  const blockRegex = /(?:\[IMG:(.*?)\]\n?\n?)?### (\d+)\) (.*?)(?=\n\n?\[IMG:|\n\n?### \d+\)|$)/gs;
  let blockMatch;

  while ((blockMatch = blockRegex.exec(text)) !== null) {
    const imgUrl = blockMatch[1] ? blockMatch[1].trim() : null;
    const id = blockMatch[2];
    const blockContent = blockMatch[3];

    // Baslik (ilk satir)
    const lines = blockContent.split('\n');
    const name = lines[0].trim();

    // Fiyat
    let price = '';
    const priceMatch = blockContent.match(/Fiyat:\s*([\d.,]+)\s*TL/);
    if (priceMatch) price = priceMatch[1].trim();

    // URL — hem Turkce hem ASCII varyasyonlari
    let url = '';
    const urlMatch = blockContent.match(/[🔗]\s*[ÜU]r[üu]n[üu]\s*[İI]ncele:\s*(https?:\/\/\S+)/i)
      || blockContent.match(/(https?:\/\/www\.\S+)/);
    if (urlMatch) url = urlMatch[1].trim();

    // Neden uygun
    let reason = '';
    const reasonMatch = blockContent.match(/Neden uygun\?\s*(.*?)(?=\n[ÖO]zellikler:|$)/s);
    if (reasonMatch) reason = reasonMatch[1].trim();

    // Ozellikler — hem Turkce hem ASCII
    let specs = '';
    const specsMatch = blockContent.match(/[ÖO]zellikler:\s*(.*?)$/s);
    if (specsMatch) specs = specsMatch[1].trim();

    laptops.push({ id, name, price, url, reason, specs, image: imgUrl });
  }

  if (laptops.length === 0) {
    return { intro: text, laptops: [], followup: '' };
  }

  // Intro: ilk laptop blogundan onceki metin
  const firstImgIdx = text.indexOf('[IMG:');
  const firstHeaderIdx = text.indexOf('### 1)');
  let startIdx = firstHeaderIdx;
  if (firstImgIdx !== -1 && (firstImgIdx < firstHeaderIdx || firstHeaderIdx === -1)) {
    startIdx = firstImgIdx;
  }
  const intro = startIdx > 0 ? text.substring(0, startIdx).trim() : '';

  // Followup: son laptop blogundan sonraki metin
  const lastBlock = laptops[laptops.length - 1];
  const lastBlockPattern = `### ${lastBlock.id})`;
  const lastBlockIdx = text.lastIndexOf(lastBlockPattern);
  let followup = '';
  if (lastBlockIdx !== -1) {
    // Son blogun sonundaki metni bul
    const afterLastBlock = text.substring(lastBlockIdx);
    const nextBlockMatch = afterLastBlock.match(/\n\n([A-ZÇĞİÖŞÜa-zçğıöşü].*)/s);
    if (nextBlockMatch) followup = nextBlockMatch[1].trim();
  }

  return { intro, laptops, followup };
};

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return;

  const userText = userInput.value;
  messages.value.push({ role: 'user', content: userText });
  userInput.value = '';
  isLoading.value = true;

  await scrollToBottom();

  try {
    const response = await axios.post(`${API_BASE_URL}/chat`, {
      message: userText,
      thread_id: threadId.value
    }, { timeout: 30000 });

    const rawReply = response.data.reply;
    const parsed = parseAssistantMessage(rawReply);

    messages.value.push({
      role: 'assistant',
      content: rawReply,
      ...parsed,
      isParsed: true
    });
  } catch (error) {
    console.error('API Error:', error);
    const errorMessage = error.code === 'ECONNABORTED'
      ? 'Yanıt süresi doldu, lütfen tekrar deneyin.'
      : 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.';
    messages.value.push({
      role: 'assistant',
      content: errorMessage,
      isParsed: false
    });
  } finally {
    isLoading.value = false;
    await scrollToBottom();
  }
};

const renderMarkdown = (content) => {
  // Backend'den gelen <br> tag'lerini newline'a cevir (html:false oldugu icin)
  const cleaned = content.replace(/&lt;br&gt;/g, '\n').replace(/<br\s*\/?>/gi, '\n');
  return DOMPurify.sanitize(md.render(cleaned), { ADD_ATTR: ['target', 'rel'] });
};

onMounted(() => {
  scrollToBottom();
});
</script>

<template>
  <main class="main-content">
    <button class="debug-copy-btn" @click="copyDebugLog" title="Konuşma logunu kopyala">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="9" y="9" width="13" height="13" rx="2"/>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
      </svg>
    </button>
    <div class="chat-wrapper" ref="chatContainer">
      <div v-for="(msg, index) in messages" :key="index" :class="['message-row', msg.role]">
        <div class="avatar">
          <svg v-if="msg.role === 'assistant'" xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 8V4H8"/>
            <rect width="16" height="12" x="4" y="8" rx="2"/>
            <path d="M2 14h2"/>
            <path d="M20 14h2"/>
            <path d="M15 13v2"/>
            <path d="M9 13v2"/>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="8" r="5"/>
            <path d="M20 21a8 8 0 0 0-16 0"/>
          </svg>
        </div>
        <div class="message-bubble">
          <div v-if="!msg.isParsed" class="message-content" v-html="renderMarkdown(msg.content)"></div>

          <div v-else class="structured-content">
            <div class="intro-text" v-if="msg.intro" v-html="renderMarkdown(msg.intro)"></div>

            <div class="laptop-list" v-if="msg.laptops && msg.laptops.length">
              <LaptopCard v-for="laptop in msg.laptops" :key="laptop.id" :laptop="laptop" />
            </div>

            <div class="followup-text" v-if="msg.followup" v-html="renderMarkdown(msg.followup)"></div>
          </div>
        </div>
      </div>

      <div v-if="isLoading" class="message-row assistant">
        <div class="avatar">
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 8V4H8"/>
            <rect width="16" height="12" x="4" y="8" rx="2"/>
            <path d="M2 14h2"/>
            <path d="M20 14h2"/>
            <path d="M15 13v2"/>
            <path d="M9 13v2"/>
          </svg>
        </div>
        <div class="message-bubble loading">
          <div class="loading-indicator">
            <div class="loading-dots">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="input-container">
      <div class="input-wrapper">
        <input
          v-model="userInput"
          @keyup.enter="sendMessage"
          placeholder="Kullanım amacını veya bütçeni yaz..."
          type="text"
        />
        <button @click="sendMessage" :disabled="isLoading || !userInput.trim()">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22 2L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
  </main>
</template>
