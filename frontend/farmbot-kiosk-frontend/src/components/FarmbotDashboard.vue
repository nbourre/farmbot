<template>
    <div class="dashboard">
        <h1>FarmBot Kiosk</h1>

        <div class="section">
            <button @click="goHome">🏠 Aller à l'origine</button>
            <button @click="getStatus">📡 Statut</button>
            <button @click="sendToast">📢 Toast</button>
            <div class="section">
                <label>
                    X:
                    <input type="number" v-model.number="x" placeholder="Entrer X > 770" />
                </label>
                <label>
                    Y:
                    <input type="number" v-model.number="y" placeholder="Entrer Y" />
                </label>
                <label>
                    Z:
                    <input type="number" v-model.number="z" placeholder="Entrer Z" />
                </label>
                <button @click="move">📍 Déplacer</button>
            </div>

            <button @click="lock">🛑 Arrêt d'urgence</button>
        </div>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        <pre v-if="!errorMessage">{{ result }}</pre>

        <pre>{{ result }}</pre>
        <div class="status-block">
            <h3>🛰 Statut du FarmBot</h3>
            <div v-if="status.busy" class="busy-indicator">
                🔄 En mouvement...
            </div>
            <div v-else class="idle-indicator">
                ✅ Prêt
            </div>
            <p><strong>Busy:</strong> {{ status.busy }}</p>
            <p><strong>Position:</strong> X={{ status.position?.x }} Y={{ status.position?.y }} Z={{ status.position?.z }}</p>
            <p><strong>Axes:</strong> X={{ status.axis_states?.x }} Y={{ status.axis_states?.y }} Z={{ status.axis_states?.z }}</p>
            <p><strong>Sync:</strong> {{ status.sync_status }}</p>
        </div>
        <div class="camera-block">
            <h3>📷 Caméra</h3>
            <button @click="takePhoto" :disabled="loadingPhoto">
                {{ loadingPhoto ? 'Capture en cours...' : '📸 Prendre une photo' }}
            </button>

            <div v-if="photoError" class="error">{{ photoError }}</div>

            <img v-if="cameraUrl" :src="cameraUrl" alt="Photo FarmBot" class="camera-image" />
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// Change this to match your backend address
const API_BASE = 'http://localhost:8000'

const result = ref('')
const errorMessage = ref('')
const status = ref({})
const cameraUrl = ref('')
const loadingPhoto = ref(false)
const photoError = ref('')

const x = ref(null)
const y = ref(null)
const z = ref(null)

async function move() {
    errorMessage.value = ''
    const params = {}

    if (typeof x.value === 'number' && !isNaN(x.value)) params.x = x.value
    if (typeof y.value === 'number' && !isNaN(y.value)) params.y = y.value
    if (typeof z.value === 'number' && !isNaN(z.value)) params.z = z.value

    if (Object.keys(params).length === 0) {
        errorMessage.value = '❌ Aucune valeur valide à envoyer.'
        return
    }

    const res = await axios.post(`${API_BASE}/move`, null, { params })

    if (res.data.status === 'error') {
        errorMessage.value = res.data.message;
    } else {
        result.value = res.data
    }

    console.log(res.data)
}

async function getStatus() {
    const res = await axios.get(`${API_BASE}/status`)
    result.value = res.data
}

async function sendToast() {
    const res = await axios.post(`${API_BASE}/toast`, null, {
        params: { message: 'Bonjour FarmBot!' }
    })
    result.value = res.data
}

async function goHome() {
  errorMessage.value = ''
  try {
    const res = await axios.post(`${API_BASE}/go_home`)
    result.value = res.data
  } catch (err) {
    errorMessage.value = '❌ Échec de l’envoi de la commande go_home.'
  }
}


async function lock() {
    const res = await axios.post(`${API_BASE}/lock`)
    result.value = res.data
}

async function fetchLiveStatus() {
  try {
    const res = await axios.get(`${API_BASE}/live_status`)
    status.value = res.data
  } catch (err) {
    console.error("Erreur de récupération du statut :", err)
  }
}

async function takePhoto() {
  loadingPhoto.value = true
  cameraUrl.value = ''
  photoError.value = ''

  try {
    const res = await axios.post(`${API_BASE}/take_photo`)
    if (res.data.url) {
      cameraUrl.value = res.data.url
    } else {
      photoError.value = res.data.error || 'Aucune URL reçue.'
    }
  } catch (err) {
    photoError.value = 'Erreur lors de la prise de photo.'
    console.error(err)
  } finally {
    loadingPhoto.value = false
  }
}


onMounted(() => {
  fetchLiveStatus()
  setInterval(fetchLiveStatus, 2000)
})


</script>

<style scoped>
.dashboard {
    padding: 2rem;
    font-family: sans-serif;
}

.section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

button {
    font-size: 1.2rem;
    padding: 0.75rem;
    cursor: pointer;
}

pre {
    background: #f0f0f0;
    padding: 1rem;
    margin-top: 2rem;
    white-space: pre-wrap;
}

label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

input[type="number"] {
    width: 120px;
    padding: 0.5rem;
    margin-bottom: 0.5rem;
}

.error {
    color: red;
    font-weight: bold;
    margin-top: 1rem;
}

.status-block {
  margin-top: 2rem;
  background-color: #f3f3f3;
  padding: 1rem;
  border-left: 5px solid #3c82f6;
}

.busy-indicator {
  color: #d97706;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.idle-indicator {
  color: #059669;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.camera-block {
  margin-top: 2rem;
  padding: 1rem;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
}

.camera-image {
  margin-top: 1rem;
  max-width: 100%;
  border: 1px solid #ccc;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.error {
  color: red;
  font-weight: bold;
  margin-top: 0.5rem;
}



</style>
