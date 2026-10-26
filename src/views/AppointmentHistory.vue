<template>
  <div class="appointment-history">
    <div class="header-section">
      <button @click="goBack" class="back-btn">← 返回</button>
      <h1 class="page-title">挂号记录查询</h1>
    </div>

    <div class="content-card">
      <!-- 时间筛选区域 -->
      <div class="filter-section">
        <div class="filter-title">时间筛选</div>
        <div class="filter-controls">
          <div class="date-input-group">
            <label>开始日期：</label>
            <input 
              type="date" 
              v-model="startDate" 
              class="date-input"
              @change="loadAppointments"
            />
          </div>
          <div class="date-input-group">
            <label>结束日期：</label>
            <input 
              type="date" 
              v-model="endDate" 
              class="date-input"
              @change="loadAppointments"
            />
          </div>
          <button @click="resetFilter" class="secondary-btn">重置为近三个月</button>
        </div>
      </div>

      <!-- 挂号记录列表 -->
      <div v-if="loading" class="loading-state">
        <p>加载中...</p>
      </div>
      <div v-else-if="appointments.length === 0" class="empty-state">
        <p>暂无挂号记录</p>
      </div>
      <div v-else class="appointment-list">
        <div 
          v-for="appointment in appointments" 
          :key="appointment.appointment_id" 
          class="appointment-card"
        >
          <div class="card-main">
            <div class="appointment-header">
              <div class="appointment-id">
                <span class="label">预约号：</span>
                <span class="value">{{ appointment.appointment_id }}</span>
              </div>
              <span 
                class="status-tag" 
                :class="{ 'status-confirmed': appointment.status === 'confirmed', 'status-cancelled': appointment.status === 'cancelled' }"
              >
                {{ appointment.status === 'confirmed' ? '已确认' : '已取消' }}
              </span>
            </div>
            <div class="appointment-info">
              <div class="info-row">
                <span class="info-label">就诊人：</span>
                <span class="info-value">{{ appointment.patient_name }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">手机号：</span>
                <span class="info-value">{{ appointment.patient_phone }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">科室：</span>
                <span class="info-value">
                  {{ [appointment.department, appointment.sub_department, appointment.specialty].filter(Boolean).join(' - ') || '未指定' }}
                </span>
              </div>
              <div class="info-row">
                <span class="info-label">医生：</span>
                <span class="info-value">{{ appointment.doctor_name }} {{ appointment.doctor_title }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">就诊日期：</span>
                <span class="info-value">{{ appointment.date }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">就诊时段：</span>
                <span class="info-value">{{ appointment.time_slot }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">预约时间：</span>
                <span class="info-value">{{ formatDateTime(appointment.created_at) }}</span>
              </div>
            </div>
          </div>
          <div class="card-actions">
            <button 
              v-if="appointment.status === 'confirmed'"
              class="cancel-btn" 
              @click="showCancelConfirm(appointment)"
            >
              取消预约
            </button>
            <button 
              v-if="appointment.status === 'cancelled'"
              class="delete-btn" 
              @click="showDeleteConfirm(appointment)"
            >
              删除记录
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 消息提示 -->
    <div v-if="toastMessage" class="toast-message" :class="toastType">
      <span>{{ toastMessage }}</span>
    </div>

    <!-- 取消预约确认对话框 -->
    <div v-if="showCancelConfirmModal" class="modal-backdrop" @click="cancelCancelConfirm">
      <div class="confirm-modal" @click.stop>
        <div class="confirm-header">
          <h3>确认取消预约</h3>
        </div>
        <div class="confirm-body">
          <div class="confirm-icon">⚠️</div>
          <p class="confirm-message">确定要取消这个预约吗？</p>
          <div v-if="cancelTargetAppointment" class="appointment-detail">
            <p><strong>预约号：</strong>{{ cancelTargetAppointment.appointment_id }}</p>
            <p><strong>就诊人：</strong>{{ cancelTargetAppointment.patient_name }}</p>
            <p><strong>就诊日期：</strong>{{ cancelTargetAppointment.date }} {{ cancelTargetAppointment.time_slot }}</p>
          </div>
          <p class="confirm-hint">取消后无法恢复，号源将自动释放</p>
        </div>
        <div class="confirm-footer">
          <button @click="cancelCancelConfirm" class="cancel-btn">取消</button>
          <button @click="confirmCancel" class="confirm-delete-btn">确认取消</button>
        </div>
      </div>
    </div>

    <!-- 删除记录确认对话框 -->
    <div v-if="showDeleteConfirmModal" class="modal-backdrop" @click="cancelDeleteConfirm">
      <div class="confirm-modal" @click.stop>
        <div class="confirm-header">
          <h3>确认删除记录</h3>
        </div>
        <div class="confirm-body">
          <div class="confirm-icon">🗑️</div>
          <p class="confirm-message">确定要删除这条预约记录吗？</p>
          <div v-if="deleteTargetAppointment" class="appointment-detail">
            <p><strong>预约号：</strong>{{ deleteTargetAppointment.appointment_id }}</p>
            <p><strong>就诊人：</strong>{{ deleteTargetAppointment.patient_name }}</p>
            <p><strong>就诊日期：</strong>{{ deleteTargetAppointment.date }} {{ deleteTargetAppointment.time_slot }}</p>
          </div>
          <p class="confirm-hint">删除后无法恢复</p>
        </div>
        <div class="confirm-footer">
          <button @click="cancelDeleteConfirm" class="cancel-btn">取消</button>
          <button @click="confirmDelete" class="confirm-delete-btn">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AppointmentHistory',
  data() {
    // 默认显示近三个月
    const today = new Date()
    const threeMonthsAgo = new Date()
    threeMonthsAgo.setMonth(today.getMonth() - 3)
    
    return {
      appointments: [],
      loading: false,
      startDate: threeMonthsAgo.toISOString().split('T')[0],
      endDate: today.toISOString().split('T')[0],
      showCancelConfirmModal: false,
      cancelTargetAppointment: null,
      showDeleteConfirmModal: false,
      deleteTargetAppointment: null,
      toastMessage: '',
      toastType: 'success'
    }
  },
  async mounted() {
    await this.loadAppointments()
    if (this.$route.query.booked === '1') {
      this.showToast('预约已成功，记录如下', 'success')
      this.$router.replace({ path: this.$route.path, query: {} })
    }
  },
  methods: {
    async loadAppointments() {
      this.loading = true
      try {
        const params = {}
        if (this.startDate) params.start_date = this.startDate
        if (this.endDate) params.end_date = this.endDate

        const { data } = await axios.get('/api/appointments', { params })

        if (data.status === 'success') {
          this.appointments = data.appointments || []
        } else {
          this.showToast('查询失败：' + (data.message || '未知错误'), 'error')
          this.appointments = []
        }
      } catch (error) {
        console.error('加载挂号记录失败:', error)
        const msg =
          (error.response && error.response.data && error.response.data.message) ||
          error.message ||
          '请检查网络或重新登录'
        this.showToast('加载挂号记录失败：' + msg, 'error')
        this.appointments = []
      } finally {
        this.loading = false
      }
    },
    resetFilter() {
      const today = new Date()
      const threeMonthsAgo = new Date()
      threeMonthsAgo.setMonth(today.getMonth() - 3)
      
      this.startDate = threeMonthsAgo.toISOString().split('T')[0]
      this.endDate = today.toISOString().split('T')[0]
      this.loadAppointments()
    },
    showCancelConfirm(appointment) {
      this.cancelTargetAppointment = appointment
      this.showCancelConfirmModal = true
    },
    cancelCancelConfirm() {
      this.showCancelConfirmModal = false
      this.cancelTargetAppointment = null
    },
    async confirmCancel() {
      if (!this.cancelTargetAppointment) return
      
      const appointmentId = this.cancelTargetAppointment.appointment_id
      
      try {
        const { data } = await axios.post(`/api/appointments/${appointmentId}/cancel`)

        if (data.status === 'success') {
          this.showToast('预约已成功取消', 'success')
          this.cancelCancelConfirm()
          // 重新加载列表
          this.loadAppointments()
        } else {
          this.showToast('取消失败：' + (data.message || '未知错误'), 'error')
        }
      } catch (error) {
        console.error('取消预约失败:', error)
        this.showToast('取消预约失败，请检查网络连接', 'error')
      }
    },
    formatDateTime(dateTimeStr) {
      if (!dateTimeStr) return ''
      const s = String(dateTimeStr).trim()
      // SQLite CURRENT_TIMESTAMP 为 UTC，常见为 "YYYY-MM-DD HH:mm:ss" 无时区；
      // 浏览器会误当作本地时间，在东八区会少 8 小时。已带 Z 或 ±偏移的按标准解析。
      const hasExplicitZone = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(s)
      const sqliteUtc = /^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)$/.test(s) && !hasExplicitZone
      let ms
      if (sqliteUtc) {
        const m = s.match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)$/)
        ms = Date.parse(`${m[1]}T${m[2]}Z`)
      } else {
        ms = Date.parse(s.includes('T') ? s : s.replace(' ', 'T'))
      }
      if (Number.isNaN(ms)) return dateTimeStr
      const date = new Date(ms)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}`
    },
    showDeleteConfirm(appointment) {
      this.deleteTargetAppointment = appointment
      this.showDeleteConfirmModal = true
    },
    cancelDeleteConfirm() {
      this.showDeleteConfirmModal = false
      this.deleteTargetAppointment = null
    },
    async confirmDelete() {
      if (!this.deleteTargetAppointment) return
      
      const appointmentId = this.deleteTargetAppointment.appointment_id
      
      try {
        const { data } = await axios.delete(`/api/appointments/${appointmentId}`)

        if (data.status === 'success') {
          this.showToast('预约记录已成功删除', 'success')
          this.cancelDeleteConfirm()
          // 重新加载列表
          this.loadAppointments()
        } else {
          this.showToast('删除失败：' + (data.message || '未知错误'), 'error')
        }
      } catch (error) {
        console.error('删除预约记录失败:', error)
        this.showToast('删除预约记录失败，请检查网络连接', 'error')
      }
    },
    showToast(message, type = 'success') {
      this.toastMessage = message
      this.toastType = type
      setTimeout(() => {
        this.toastMessage = ''
      }, 3000)
    },
    goBack() {
      if (window.history.length > 1) {
        this.$router.back()
      } else {
        this.$router.push({ name: 'Home' })
      }
    }
  }
}
</script>

<style scoped>
.appointment-history {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 0;
}

.header-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.page-title {
  color: white;
  font-size: 1.8rem;
  margin: 0;
}

.back-btn {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 2px solid #667eea;
  background: white;
  color: #667eea;
  cursor: pointer;
  font-size: 0.95rem;
}

.content-card {
  background: white;
  border-radius: 15px;
  padding: 1.5rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.filter-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid #f0f0f0;
}

.filter-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 1rem;
}

.filter-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
}

.date-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.date-input-group label {
  font-weight: 500;
  color: #555;
  font-size: 0.9rem;
}

.date-input {
  padding: 0.6rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 0.95rem;
}

.secondary-btn {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: 2px solid #667eea;
  background: white;
  color: #667eea;
  cursor: pointer;
  font-size: 0.95rem;
  white-space: nowrap;
}

.secondary-btn:hover {
  background: #f0f0ff;
}

.loading-state,
.empty-state {
  text-align: center;
  color: #666;
  padding: 3rem 0;
}

.appointment-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.appointment-card {
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: box-shadow 0.3s;
}

.appointment-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-main {
  flex: 1;
}

.appointment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.appointment-id {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.appointment-id .label {
  color: #666;
  font-size: 0.9rem;
}

.appointment-id .value {
  color: #333;
  font-weight: 600;
  font-size: 1.1rem;
}

.status-tag {
  padding: 0.3rem 0.8rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-confirmed {
  background: #e0f2fe;
  color: #0369a1;
}

.status-cancelled {
  background: #fee2e2;
  color: #991b1b;
}

.appointment-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-row {
  display: flex;
  gap: 0.5rem;
}

.info-label {
  color: #666;
  font-size: 0.9rem;
  min-width: 80px;
}

.info-value {
  color: #333;
  font-size: 0.9rem;
}

.card-actions {
  display: flex;
  align-items: flex-start;
  margin-left: 1rem;
}

.cancel-btn {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  color: white;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s;
}

.cancel-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
}

.delete-btn {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s;
}

.delete-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(107, 114, 128, 0.4);
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.confirm-modal {
  background: white;
  border-radius: 15px;
  width: 90%;
  max-width: 450px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  animation: slideUp 0.3s;
}

@keyframes slideUp {
  from {
    transform: translateY(50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.confirm-header {
  padding: 1.5rem;
  border-bottom: 2px solid #f0f0f0;
  text-align: center;
}

.confirm-header h3 {
  color: #667eea;
  margin: 0;
  font-size: 1.3rem;
}

.confirm-body {
  padding: 2rem 1.5rem;
  text-align: center;
}

.confirm-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.confirm-message {
  font-size: 1.1rem;
  color: #333;
  margin: 0.5rem 0;
  font-weight: 600;
}

.appointment-detail {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
  text-align: left;
}

.appointment-detail p {
  margin: 0.5rem 0;
  color: #555;
  font-size: 0.95rem;
}

.confirm-hint {
  font-size: 0.9rem;
  color: #999;
  margin: 0.5rem 0 0 0;
}

.confirm-footer {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 2px solid #f0f0f0;
}

.confirm-footer .cancel-btn,
.confirm-footer .confirm-delete-btn {
  flex: 1;
  padding: 0.8rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.confirm-footer .cancel-btn {
  background: #f0f0f0;
  color: #666;
}

.confirm-footer .cancel-btn:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
}

.confirm-footer .confirm-delete-btn {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  color: white;
}

.confirm-footer .confirm-delete-btn:hover {
  background: linear-gradient(135deg, #ee5a6f 0%, #ff6b6b 100%);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
}

.toast-message {
  position: fixed;
  top: 100px;
  left: 50%;
  transform: translateX(-50%);
  padding: 1rem 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 2000;
  animation: slideDown 0.3s ease-out;
  min-width: 300px;
  text-align: center;
  font-weight: 500;
}

.toast-message.success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.toast-message.error {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

@keyframes slideDown {
  from {
    transform: translateX(-50%) translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
}
</style>
