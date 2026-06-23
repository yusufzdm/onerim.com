<script setup>
defineProps({
  part: { type: Object, required: true },
  isSelected: { type: Boolean, default: false }
});

defineEmits(['select']);
</script>

<template>
  <div
    class="part-card"
    :class="{ selected: isSelected }"
    @click="$emit('select', part)"
  >
    <div class="part-info">
      <h4 class="part-name">{{ part.name }}</h4>
      <p class="part-specs">{{ part.specs }}</p>
    </div>
    <div class="part-price">{{ part.price.toLocaleString('tr-TR') }} TL</div>
  </div>
</template>

<style scoped>
.part-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1.5px solid var(--border);
  background: var(--bg-card);
  cursor: pointer;
  transition: all 0.2s ease;
  gap: 12px;
}

.part-card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245,184,0,0.15);
}

.part-card.selected {
  border-color: var(--accent);
  background: var(--accent-light);
  box-shadow: 0 2px 12px rgba(245,184,0,0.25);
}

.part-info {
  flex: 1;
  min-width: 0;
}

.part-name {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-main);
  line-height: 1.3;
}

.part-specs {
  margin: 4px 0 0;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.part-price {
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--accent-dark);
  white-space: nowrap;
}
</style>
