<script setup>
import { ref, onMounted } from 'vue';
import ChatView from './components/ChatView.vue';
import PcBuildView from './components/pcbuild/PcBuildView.vue';
import logoUrl from './images/logo.png';
import logoDarkUrl from './images/logo-dark.png';

const isDark = ref(false);
const currentPage = ref('chat');
const chatViewRef = ref(null);

const toggleDark = () => {
  isDark.value = !isDark.value;
  document.body.classList.toggle('dark-mode', isDark.value);
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light');
};

const goToChat = () => {
  currentPage.value = 'chat';
};

const newChat = () => {
  currentPage.value = 'chat';
  if (chatViewRef.value) {
    chatViewRef.value.resetChat();
  }
};

const goToPcBuild = () => {
  currentPage.value = 'pcbuild';
};

onMounted(() => {
  const saved = localStorage.getItem('theme');
  if (saved === 'dark') {
    isDark.value = true;
    document.body.classList.add('dark-mode');
  }
});
</script>

<template>
  <div class="app-container">
    <!-- Navbar -->
    <nav class="navbar">
      <div class="nav-left" @click="goToChat" style="cursor: pointer;">
        <img
          :src="isDark ? logoDarkUrl : logoUrl"
          alt="önerim.com logo"
          class="app-logo"
          style="pointer-events: none;"
        />
      </div>
      <div class="nav-right">
        <!-- Dark mode toggle -->
        <button class="btn-theme-toggle" @click="toggleDark" :title="isDark ? 'Açık Mod' : 'Koyu Mod'">
          <svg v-if="!isDark" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="4"/>
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
          </svg>
        </button>

        <!-- PC Build Button -->
        <button
          class="btn-nav"
          :class="{ active: currentPage === 'pcbuild' }"
          @click="goToPcBuild"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="icon">
            <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M8 21h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          PC Topla
        </button>

        <!-- New Chat Button -->
        <button class="btn-nav" @click="newChat">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="icon">
            <path d="M12 5V19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Yeni Sohbet
        </button>
      </div>
    </nav>

    <!-- Page Content -->
    <ChatView v-if="currentPage === 'chat'" ref="chatViewRef" />
    <PcBuildView v-else-if="currentPage === 'pcbuild'" :is-dark="isDark" />
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --bg-main:      #F7F4EE;
  --bg-navbar:    #FFFFFF;
  --bg-card:      #FFFFFF;
  --bg-input:     #EDEAE3;
  --bg-user-msg:  #1A2332;
  --bg-ai-msg:    #FFFFFF;
  --text-main:    #1A2332;
  --text-muted:   #6B7280;
  --accent:       #F5B800;
  --accent-dark:  #D4A000;
  --accent-light: #FFF8E1;
  --border:       #E5E0D5;
  --shadow-sm:    rgba(26,35,50,0.07);
  --shadow-md:    rgba(26,35,50,0.13);
  --bg-button:    #1A2332;
  --text-button:  #FFFFFF;
}

/* Dark Mode */
body.dark-mode {
  --bg-main:      #13151A;
  --bg-navbar:    #1A1D24;
  --bg-card:      #1E2129;
  --bg-input:     #1E2129;
  --bg-user-msg:  #2A3040;
  --bg-ai-msg:    #1E2129;
  --text-main:    #E8E5DF;
  --text-muted:   #9CA3AF;
  --accent:       #F5B800;
  --accent-dark:  #FFCA28;
  --accent-light: #2C2510;
  --border:       #2D323C;
  --shadow-sm:    rgba(0,0,0,0.25);
  --shadow-md:    rgba(0,0,0,0.40);
  --bg-button:    #F5B800;
  --text-button:  #1A2332;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: var(--bg-main);
  color: var(--text-main);
  height: 100vh;
  overflow: hidden;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

/* Navbar */
.navbar {
  height: 64px;
  background-color: var(--bg-navbar);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  border-bottom: 2px solid var(--accent);
  flex-shrink: 0;
  box-shadow: 0 2px 16px var(--shadow-sm);
  overflow: visible;
  z-index: 10;
}

.nav-left {
  display: flex;
  align-items: center;
  pointer-events: auto;
  max-height: 64px;
  overflow: visible;
}

.app-logo {
  height: 300px;
  width: auto;
  object-fit: contain;
  object-position: left center;
  filter: drop-shadow(0 2px 8px rgba(245,184,0,0.15));
  transition: transform 0.2s ease, opacity 0.2s ease;
  position: relative;
  z-index: 11;
  pointer-events: none;
}

body.dark-mode .app-logo {
  transform: scale(1);
}

.app-logo:hover {
  transform: scale(1.02);
}

/* Nav Buttons */
.nav-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 22px;
  background-color: var(--accent);
  border: none;
  border-radius: 24px;
  color: #1A2332;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease;
  box-shadow: 0 2px 12px rgba(245,184,0,0.35);
  letter-spacing: 0.01em;
}

.btn-nav:hover {
  background-color: var(--accent-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 18px rgba(245,184,0,0.45);
}

.btn-nav:active {
  transform: translateY(0);
}

.btn-nav.active {
  background-color: var(--bg-button);
  color: var(--text-button);
  box-shadow: 0 2px 12px var(--shadow-md);
}

.btn-nav .icon {
  width: 17px;
  height: 17px;
}

.btn-theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: 50%;
  color: var(--text-main);
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.15s ease;
}

.btn-theme-toggle:hover {
  background: var(--accent-light);
  border-color: var(--accent);
  color: var(--accent-dark);
  transform: rotate(20deg) scale(1.08);
}

/* Main Content */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  background-color: var(--bg-main);
}

.debug-copy-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 5;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.5;
  transition: all 0.2s ease;
}

.debug-copy-btn:hover {
  opacity: 1;
  border-color: var(--accent);
  color: var(--accent-dark);
}

.debug-copy-btn svg {
  width: 16px;
  height: 16px;
}

.chat-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 40px 20% 160px 20%;
  display: flex;
  flex-direction: column;
  gap: 24px;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}

.chat-wrapper::-webkit-scrollbar { width: 5px; }
.chat-wrapper::-webkit-scrollbar-track { background: transparent; }
.chat-wrapper::-webkit-scrollbar-thumb { background: var(--border); border-radius: 5px; }

/* Message Row */
.message-row {
  display: flex;
  gap: 14px;
  max-width: 100%;
  animation: msgIn 0.25s ease both;
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.message-row.user {
  flex-direction: row-reverse;
}

/* Avatar */
.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px var(--shadow-sm);
}

.message-row.assistant .avatar {
  background: var(--accent-light);
  border: 2px solid var(--accent);
  color: var(--accent-dark);
}

.message-row.user .avatar {
  background: var(--text-main);
  border: 2px solid transparent;
  color: #FFFFFF;
}

/* Message Bubble */
.message-bubble {
  max-width: 85%;
  overflow: hidden;
}

.message-row.assistant .message-bubble {
  background: var(--bg-ai-msg);
  border-radius: 4px 18px 18px 18px;
  padding: 14px 18px;
  border: 1px solid var(--border);
  box-shadow: 0 2px 12px var(--shadow-sm);
  color: var(--text-main);
}

.message-row.user .message-bubble {
  background: var(--bg-user-msg);
  border-radius: 18px 4px 18px 18px;
  padding: 10px 16px;
  color: #FFFFFF;
  box-shadow: 0 2px 12px var(--shadow-md);
}

.message-bubble.loading {
  background: var(--bg-ai-msg);
  border-radius: 4px 18px 18px 18px;
  padding: 12px 20px;
  border: 1px solid var(--border);
  box-shadow: 0 2px 12px var(--shadow-sm);
}

/* Markdown */
.message-content, .structured-content {
  line-height: 1.75;
  font-size: 15px;
}

.message-content h2, .structured-content h2 {
  color: var(--accent-dark);
  font-weight: 700;
  font-size: 1.2rem;
  border-bottom: 2px solid var(--accent);
  padding-bottom: 6px;
  margin-top: 20px;
  margin-bottom: 12px;
}

.message-content h3, .structured-content h3 {
  color: var(--accent-dark);
  font-weight: 700;
  font-size: 1.05rem;
  border-bottom: 1.5px solid var(--border);
  padding-bottom: 5px;
  margin-top: 16px;
  margin-bottom: 10px;
}

.message-content h4, .structured-content h4 {
  color: var(--text-main);
  font-weight: 600;
  font-size: 0.95rem;
  margin-top: 12px;
  margin-bottom: 6px;
}

.message-content p, .structured-content p {
  margin-bottom: 12px;
  line-height: 1.75;
}

.message-content ul, .structured-content ul {
  margin-left: 20px;
  margin-bottom: 14px;
  list-style: none;
  padding-left: 0;
}

.message-content ul li, .structured-content ul li {
  position: relative;
  padding-left: 20px;
  margin-bottom: 6px;
  line-height: 1.65;
}

.message-content ul li::before, .structured-content ul li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 9px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
}

.message-content ol, .structured-content ol {
  margin-left: 20px;
  margin-bottom: 14px;
  padding-left: 4px;
}

.message-content ol li, .structured-content ol li {
  margin-bottom: 6px;
  line-height: 1.65;
}

.message-content a, .structured-content a {
  color: var(--accent-dark);
  text-decoration: none;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--accent-light);
  transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
  border: 1px solid transparent;
}

.message-content a:hover, .structured-content a:hover {
  background: var(--accent);
  color: #1A2332;
  border-color: var(--accent-dark);
  box-shadow: 0 2px 8px rgba(245,184,0,0.25);
}

.message-content strong, .structured-content strong {
  color: var(--text-main);
  font-weight: 700;
}

.message-content em, .structured-content em {
  color: var(--text-muted);
  font-style: italic;
}

.message-content hr, .structured-content hr {
  border: none;
  border-top: 1.5px solid var(--border);
  margin: 16px 0;
}

.message-content code, .structured-content code {
  background: var(--bg-input);
  color: var(--accent-dark);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.88em;
  font-family: 'Courier New', Courier, monospace;
}

.message-content pre, .structured-content pre {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 18px;
  overflow-x: auto;
  margin: 12px 0;
}

.message-content pre code, .structured-content pre code {
  background: transparent;
  padding: 0;
  font-size: 0.88em;
  line-height: 1.6;
}

.message-content blockquote, .structured-content blockquote {
  border-left: 3px solid var(--accent);
  margin: 12px 0;
  padding: 8px 16px;
  background: var(--accent-light);
  border-radius: 0 8px 8px 0;
  color: var(--text-muted);
  font-style: italic;
}

.message-content, .structured-content {
  overflow-x: auto;
}

.message-content table, .structured-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 0.82em;
  white-space: nowrap;
}

.message-content th, .structured-content th {
  background: var(--accent-light);
  color: var(--accent-dark);
  font-weight: 700;
  text-align: left;
  padding: 6px 10px;
  border-bottom: 2px solid var(--accent);
}

.message-content td, .structured-content td {
  padding: 6px 10px;
  border-bottom: 1px solid var(--border);
  white-space: normal;
  max-width: 180px;
  word-break: break-word;
}

.intro-text, .followup-text { margin-bottom: 8px; }

/* Input Area */
.input-container {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 20% 36px 20%;
  background: linear-gradient(transparent, var(--bg-main) 28%);
}

.input-wrapper {
  background-color: var(--bg-card);
  border-radius: 32px;
  padding: 8px 8px 8px 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 24px var(--shadow-md);
  border: 2px solid var(--border);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.input-wrapper:focus-within {
  border-color: var(--accent);
  box-shadow: 0 4px 24px rgba(245,184,0,0.18);
}

.input-wrapper textarea,
.input-wrapper input[type="text"] {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-main);
  padding: 10px 0;
  font-size: 15px;
  font-family: 'Inter', sans-serif;
  outline: none;
  resize: none;
  overflow-y: auto;
  max-height: 150px;
  line-height: 1.5;
  min-height: 24px;
}

.input-wrapper textarea::placeholder,
.input-wrapper input[type="text"]::placeholder {
  color: var(--text-muted);
}

.input-wrapper button {
  background: var(--accent);
  border: none;
  color: var(--text-main);
  cursor: pointer;
  padding: 10px 14px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease, transform 0.15s ease;
  box-shadow: 0 2px 8px rgba(245,184,0,0.30);
}

.input-wrapper button:hover:not(:disabled) {
  background: var(--accent-dark);
  transform: scale(1.05);
}

.input-wrapper button svg {
  width: 20px;
  height: 20px;
}

.input-wrapper button:disabled {
  opacity: 0.35;
  background: var(--border);
  box-shadow: none;
  cursor: not-allowed;
}

/* Loading Indicator */
.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px 4px;
}

.loading-dots {
  display: flex;
  align-items: center;
  gap: 6px;
}

.loading-dots .dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--accent);
  animation: dot-bounce 1.4s ease-in-out infinite both;
}

.loading-dots .dot:nth-child(1) {
  animation-delay: 0s;
}
.loading-dots .dot:nth-child(2) {
  animation-delay: 0.16s;
}
.loading-dots .dot:nth-child(3) {
  animation-delay: 0.32s;
}

@keyframes dot-bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1.1);
    opacity: 1;
  }
}

/* Responsive */
@media (max-width: 1024px) {
  .chat-wrapper, .input-container { padding-left: 10%; padding-right: 10%; }
}

@media (max-width: 768px) {
  .chat-wrapper, .input-container { padding-left: 5%; padding-right: 5%; }
  .navbar { padding: 10px 20px; }
  .app-logo { height: 200px; }
}
</style>
