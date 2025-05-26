<template>
    <div class="dashboard">
      <div style="display: grid; grid-template-columns: 400px auto; grid-template-rows: auto auto; gap: 2rem;">
        <h1 style="font-size: 3rem; text-align: center;">Kiosque<br>🌱 FarmBot</h1>
        <div style="display: flex; flex-direction: column;">

          <div class="status-block">
            <div style="text-align: center;">
              <div v-if="status.busy" class="busy-indicator">
                  🔄 En mouvement...
              </div>
              <div v-else class="idle-indicator">
                  ✅ Prêt
              </div>
            </div>

            <p>
              <strong>Position:</strong> 
              X={{ status.position?.x }} 
              Y={{ status.position?.y }} 
              Z={{ status.position?.z }}
            </p>

          </div>
        </div>

        <div style="grid-column: 2; grid-row: 1 / span 2;" class="camera-block block">
            <h3>📷 Caméra</h3>

            <div v-if="photoError" class="error">{{ photoError }}</div>

            <img v-if="cameraUrl" :src="cameraUrl" alt="Photo FarmBot" class="camera-image" />
        </div>
      </div>

      <div class="robot-block block">
        <h3>🤖 Robot</h3>

        <div style="flex-grow: 1; display: flex; gap: 1rem;">
          <input v-model="zSlider" type="range" min="0" max="1" step="0.001" orient="vertical" style="appearance: slider-vertical;">

          <div ref="dragParent" style="flex-grow: 1; background-color: gray;">
            <div class="draggable"></div>
          </div>

          <div style="display: grid; justify-items: normal; align-items: start; grid-template-rows: repeat(3, auto); grid-template-columns: auto;">
            <button @click="move">📍 Déplacer</button>
            <button @click="goHome">🏠 Origine</button>

            <button @click="lock" style="align-self: end;">🛑 Arrêt</button>
          </div>
        </div>
      </div>

        <!--
        <div class="section">
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
            </div>

        </div>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        <pre v-if="!errorMessage">{{ result }}</pre>
        <pre>{{ result }}</pre>

        <div class="camera-block">
            <h3>📷 Caméra</h3>
            <button @click="takePhoto" :disabled="loadingPhoto">
                {{ loadingPhoto ? 'Capture en cours...' : '📸 Prendre une photo' }}
            </button>

            <div v-if="photoError" class="error">{{ photoError }}</div>

            <img v-if="cameraUrl" :src="cameraUrl" alt="Photo FarmBot" class="camera-image" />
        </div>
        -->
    </div>
</template>

<script setup>
import { ref, reactive, onMounted, useTemplateRef } from 'vue'

import axios from 'axios'
import interact from 'interactjs'

// Change this to match your backend address
const API_BASE = 'http://localhost:8000'

const dragParent = useTemplateRef('dragParent')

const result = ref('')
const errorMessage = ref('')
const status = ref({})
const cameraUrl = ref('/public/bot.png')
const loadingPhoto = ref(false)
const photoError = ref('')

const x = ref(null)
const y = ref(null)
const z = ref(null)

const zSlider = ref(0.5)
const dragPosition = reactive({
  x: 0,
  y: 0
})

async function move() {
    errorMessage.value = ''
    

    const dragSize = 44
    const z = 1 - zSlider.value
    const {width, height} = dragParent.value.getBoundingClientRect()
    const x = dragPosition.x / (width - dragSize)
    const y = 1 - (dragPosition.y / (height - dragSize))
    const params = {x, y, z}
    // if (typeof x.value === 'number' && !isNaN(x.value)) params.x = x
    // if (typeof y.value === 'number' && !isNaN(y.value)) params.y = y
    // if (typeof z.value === 'number' && !isNaN(z.value)) params.z = z

  console.log({ x, y, z })

  debugger;

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

  interact('.draggable').draggable({
   modifiers: [
    interact.modifiers.restrictRect({
      restriction: 'parent',
      endOnly: true
    }),
  ],
    listeners: {
      start (event) {
        // console.log(event.type, event.target)
      },
      move (event) {
        dragPosition.x += event.dx
        dragPosition.y += event.dy

        event.target.style.transform =
          `translate(${dragPosition.x}px, ${dragPosition.y}px)`
      },
    }
  })
})


</script>

<style scoped>

.dashboard {
  height: 100%;
  padding: 2rem;
  font-family: sans-serif;
  font-weight: normal;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 2rem;
}

#header {
  display: flex;
  align-items: baseline;
  gap: 2rem;
}

.draggable {
  width: 44px;
  aspect-ratio: 1;
  background-color: #29e;
  color: white;
  border-radius: 0.75em;
  user-select: none;
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
  background-color: #f3f3f3;
  padding: 1rem;
  border-top: 5px solid #77b255;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  gap: 2rem;
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
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.robot-block {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  flex-grow: 1;
}

.block {
  padding: 1rem;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
}

.camera-image {
  object-fit: cover;
  width: 100%;
  height: 296px;
  border: 1px solid #ccc;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.error {
  color: red;
  font-weight: bold;
  margin-top: 0.5rem;
}
</style>
