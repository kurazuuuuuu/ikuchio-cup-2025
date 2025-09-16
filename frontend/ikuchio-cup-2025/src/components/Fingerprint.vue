<template>
  <div>
    <h3>Device Fingerprint</h3>
    <p>{{ fingerprint }}</p>
    <button @click="refreshFingerprint">Refresh</button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { generateFingerprint } from '../utils/fingerprint'

const fingerprint = ref<string>('')

const refreshFingerprint = () => {
  fingerprint.value = generateFingerprint()
}

onMounted(() => {
  refreshFingerprint()
})
</script>
