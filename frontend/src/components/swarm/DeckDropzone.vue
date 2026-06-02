<template>
  <div class="dropzone-wrap">
    <div class="dropzone-or"><span class="h-eyebrow">or drop a PDF deck</span></div>
    <div
      class="dropzone"
      :class="{
        'dz-dragover': dzDragover,
        'dz-filled': !!file,
        'dz-error': !!dzError,
        'dz-disabled': disabled,
      }"
      role="button"
      tabindex="0"
      :aria-label="file ? 'PDF selected: ' + file.name + '. Press to change.' : 'Drop a PDF or click to browse'"
      :aria-disabled="disabled ? 'true' : undefined"
      @click="!disabled && fileInput.click()"
      @keydown.enter.space.prevent="!disabled && fileInput.click()"
      @dragenter.prevent="!disabled && (dzDragover = true)"
      @dragover.prevent="!disabled && (dzDragover = true)"
      @dragleave.prevent="dzDragover = false"
      @drop.prevent="onFileDrop"
    >
      <input
        ref="fileInput"
        type="file"
        accept="application/pdf"
        class="dz-hidden-input"
        :disabled="disabled"
        @change="onFileChange"
      />
      <template v-if="file">
        <div class="dz-file-info">
          <span class="dz-filename">{{ file.name }}</span>
          <span class="dz-size">{{ formatFileSize(file.size) }}</span>
        </div>
        <button type="button" class="dz-clear" :disabled="disabled" @click.stop="clearDeck" aria-label="Remove PDF">
          <span aria-hidden="true">x</span> clear
        </button>
      </template>
      <template v-else>
        <div class="dz-prompt">
          <span class="dz-icon" aria-hidden="true">&#8593;</span>
          <span class="dz-label">drop PDF or click to browse</span>
          <span class="dz-hint">PDF only &middot; max 25 MB</span>
        </div>
      </template>
    </div>
    <p v-if="dzError" class="dz-error-msg" role="alert">{{ dzError }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const file = defineModel('file', { default: null })
const props = defineProps({ disabled: { type: Boolean, default: false } })

const dzDragover = ref(false)
const dzError = ref('')
const fileInput = ref(null)

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function validateAndSetFile(f) {
  dzError.value = ''
  if (!f) return
  if (f.type !== 'application/pdf') {
    dzError.value = 'Only PDF files are accepted. Try dropping a .pdf deck.'
    return
  }
  if (f.size > 25 * 1024 * 1024) {
    dzError.value = 'File is too large. Max 25 MB.'
    return
  }
  file.value = f
}

function onFileChange(e) {
  validateAndSetFile(e.target.files?.[0])
  // Reset input so same file can be re-selected after clearing
  if (fileInput.value) fileInput.value.value = ''
}

function onFileDrop(e) {
  dzDragover.value = false
  if (props.disabled) return
  validateAndSetFile(e.dataTransfer?.files?.[0])
}

function clearDeck() {
  file.value = null
  dzError.value = ''
  if (fileInput.value) fileInput.value.value = ''
}
</script>

<style scoped>
.dropzone-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex-shrink: 0;
}
.dropzone-or {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--ink-4);
}
.dropzone-or::before,
.dropzone-or::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--rule);
}

.dz-hidden-input {
  display: none;
}

.dropzone {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--paper-2);
  border: 1px dashed var(--rule-2);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition:
    border-color var(--dur-base) var(--ease-out),
    background var(--dur-base) var(--ease-out);
  min-height: 64px;
  user-select: none;
  outline: none;
}
.dropzone:hover:not(.dz-disabled) {
  border-color: var(--ink-3);
  background: color-mix(in oklch, var(--paper-2) 85%, var(--paper-3));
}
.dropzone:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 2px;
  border-radius: var(--radius-lg);
}
.dropzone:active:not(.dz-disabled) {
  background: var(--paper-3);
}
.dropzone.dz-dragover {
  border-color: var(--accent);
  border-style: solid;
  background: var(--accent-soft);
}
.dropzone.dz-filled {
  border-style: solid;
  border-color: var(--live);
  background: var(--live-soft);
}
.dropzone.dz-error {
  border-color: var(--warn);
  background: var(--warn-soft);
}
.dropzone.dz-disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.dz-prompt {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.dz-icon {
  display: none;
}
.dz-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-3);
}
.dz-hint {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.06em;
  color: var(--ink-4);
}

.dz-file-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.dz-filename {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.06em;
  color: var(--live);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dz-size {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  color: var(--ink-4);
}

.dz-clear {
  flex-shrink: 0;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 4px 10px;
  background: transparent;
  border: 1px solid color-mix(in oklch, var(--live) 40%, transparent);
  color: var(--live);
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.dz-clear:hover { background: var(--live-soft); }
.dz-clear:disabled { opacity: 0.4; cursor: not-allowed; }

.dz-error-msg {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.04em;
  color: var(--warn);
  margin: 0;
}
</style>
