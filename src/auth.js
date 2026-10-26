import { reactive } from 'vue'

function readUserFromStorage() {
  try {
    const raw = localStorage.getItem('auth_user')
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export const authState = reactive({
  user: readUserFromStorage(),
  token: localStorage.getItem('auth_token') || ''
})

export function getToken() {
  return authState.token || localStorage.getItem('auth_token') || ''
}

export function getUser() {
  return authState.user
}

export function setSession(token, user) {
  localStorage.setItem('auth_token', token)
  localStorage.setItem('auth_user', JSON.stringify(user))
  authState.token = token
  authState.user = user
}

export function clearSession() {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('auth_user')
  authState.token = ''
  authState.user = null
}
