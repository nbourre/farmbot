<template>
    <div class="dashboard">
        <h1>FarmBot Kiosk</h1>

        <div class="section">
            <button @click="goHome">🏠 Home</button>
            <button @click="getStatus">📡 Status</button>
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
                <button @click="move">📍 Move</button>
            </div>

            <button @click="lock">🛑 Emergency Stop</button>
        </div>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        <pre v-if="!errorMessage">{{ result }}</pre>

        <pre>{{ result }}</pre>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

// Change this to match your backend address
const API_BASE = 'http://localhost:8000'

const result = ref('')
const errorMessage = ref('')

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
</style>
