import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
  baseURL: BASE,
  timeout: 50000,
  headers: { 'Content-Type': 'application/json' },
})

export default client
