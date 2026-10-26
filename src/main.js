import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import { getToken } from './auth'
import 'leaflet/dist/leaflet.css'

// Web 默认走相对路径 /api；移动端可通过 .env.mobile 设置完整后端地址
if (import.meta.env.VITE_API_BASE_URL) {
  axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL
}

axios.interceptors.request.use((config) => {
  const t = getToken()
  if (t) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${t}`
  }
  return config
})

createApp(App).use(router).mount('#app')
