<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1>患者注册</h1>
      <p class="hint">注册成功后自动登录，可使用 AI 问诊、在线挂号等功能。</p>
      <form @submit.prevent="submit">
        <label>用户名</label>
        <input v-model.trim="username" type="text" autocomplete="username" required minlength="3" placeholder="至少 3 个字符" />
        <label>密码</label>
        <input v-model="password" type="password" autocomplete="new-password" required minlength="4" placeholder="至少 4 个字符" />
        <label>确认密码</label>
        <input v-model="password2" type="password" autocomplete="new-password" required placeholder="再次输入密码" />
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="primary" :disabled="loading">{{ loading ? '注册中…' : '注册' }}</button>
      </form>
      <p class="footer-link">
        已有账号？
        <router-link to="/login">去登录</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { setSession } from '../auth'

export default {
  name: 'Register',
  data() {
    return {
      username: '',
      password: '',
      password2: '',
      error: '',
      loading: false
    }
  },
  methods: {
    async submit() {
      this.error = ''
      if (this.password !== this.password2) {
        this.error = '两次输入的密码不一致'
        return
      }
      this.loading = true
      try {
        const { data } = await axios.post('/api/auth/register', {
          username: this.username,
          password: this.password
        })
        if (data.status !== 'success' || !data.token) {
          this.error = data.message || '注册失败'
          return
        }
        setSession(data.token, data.user)
        const redir = this.$route.query.redirect
        this.$router.replace(typeof redir === 'string' && redir.startsWith('/') ? redir : '/')
      } catch (e) {
        this.error =
          (e.response && e.response.data && e.response.data.message) || e.message || '网络错误'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 2rem;
}
.auth-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  padding: 2rem 2.25rem;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}
.auth-card h1 {
  color: #667eea;
  margin-bottom: 0.75rem;
  text-align: center;
}
.hint {
  font-size: 0.85rem;
  color: #666;
  line-height: 1.5;
  margin-bottom: 1.25rem;
  text-align: center;
}
form {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
label {
  font-size: 0.9rem;
  color: #444;
  margin-top: 0.5rem;
}
input {
  padding: 0.65rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
}
.primary {
  margin-top: 1.25rem;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
  cursor: pointer;
}
.primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.error {
  color: #c0392b;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}
.footer-link {
  margin-top: 1.25rem;
  text-align: center;
  color: #666;
  font-size: 0.95rem;
}
.footer-link a {
  color: #667eea;
  font-weight: 500;
}
</style>
