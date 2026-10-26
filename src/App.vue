<template>
  <div id="app">
    <header class="header">
      <h1>医疗系统</h1>
      <nav v-if="isPatient" class="nav">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/ai-consultation" class="nav-link">AI问诊</router-link>
        <router-link to="/appointment" class="nav-link">挂号</router-link>
        <router-link to="/navigation-preview" class="nav-link">院内导航</router-link>
        <router-link to="/patients" class="nav-link">就诊人管理</router-link>
        <router-link to="/appointment-history" class="nav-link">挂号记录</router-link>
      </nav>
      <nav v-else-if="isDoctor" class="nav">
        <router-link to="/doctor/schedule" class="nav-link">我的排班</router-link>
      </nav>
      <nav v-else-if="isAdmin" class="nav">
        <router-link to="/admin" class="nav-link">管理后台</router-link>
      </nav>
      <div class="user-bar">
        <template v-if="currentUser">
          <span class="user-name">{{ currentUser.displayName || currentUser.username }}</span>
          <span class="role-tag">{{ roleLabel }}</span>
          <button type="button" class="logout-btn" @click="logout">退出</button>
        </template>
        <template v-else>
          <router-link to="/login" class="nav-link">登录</router-link>
          <router-link to="/register" class="nav-link">注册</router-link>
        </template>
      </div>
    </header>

    <main class="main-content">
      <router-view />
    </main>

    <footer class="footer">
      <p>&copy; 2026 智能医疗挂号与室内就诊导航系统. 保留所有权利.</p>
    </footer>
  </div>
</template>

<script>
import { authState, clearSession } from './auth'

export default {
  name: 'App',
  computed: {
    currentUser() {
      return authState.user
    },
    isPatient() {
      return this.currentUser && this.currentUser.role === 'patient'
    },
    isDoctor() {
      return this.currentUser && this.currentUser.role === 'doctor'
    },
    isAdmin() {
      return this.currentUser && this.currentUser.role === 'admin'
    },
    roleLabel() {
      const r = this.currentUser && this.currentUser.role
      if (r === 'patient') return '患者'
      if (r === 'doctor') return '医生'
      if (r === 'admin') return '管理员'
      return ''
    }
  },
  methods: {
    logout() {
      clearSession()
      this.$router.push('/login')
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Microsoft YaHei', Arial, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: rgba(255, 255, 255, 0.95);
  padding: 1rem 2rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem 1rem;
  position: relative;
  z-index: 100;
}

.header h1 {
  color: #667eea;
  font-size: 1.8rem;
}

.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  align-items: center;
  flex: 1;
  justify-content: center;
}

.user-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.user-name {
  color: #333;
  font-size: 0.95rem;
  max-width: 10rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-tag {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  background: #eef0ff;
  color: #667eea;
}

.logout-btn {
  padding: 0.45rem 0.85rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.9rem;
}

.logout-btn:hover {
  background: #f5f5f5;
}

.nav-link {
  text-decoration: none;
  color: #333;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  transition: all 0.3s;
}

.nav-link:hover,
.nav-link.router-link-active {
  background: #667eea;
  color: white;
}

.main-content {
  flex: 1;
  padding: 2rem;
}

.footer {
  background: rgba(255, 255, 255, 0.95);
  padding: 1rem;
  text-align: center;
  color: #666;
  margin-top: auto;
}
</style>
