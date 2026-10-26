<template>
  <div class="patient-manager">
    <div class="header-section">
      <button @click="goBack" class="back-btn">← 返回</button>
      <h1 class="page-title">就诊人管理</h1>
      <button @click="openCreate" class="primary-btn">+ 新增就诊人</button>
    </div>

    <div class="content-card">
      <div v-if="patients.length === 0" class="empty-state">
        <p>暂无就诊人，请先添加。</p>
        <button @click="openCreate" class="primary-btn">立即添加</button>
      </div>

      <div v-else class="patient-list">
        <div 
          v-for="person in patients" 
          :key="person.id" 
          class="patient-card"
        >
          <div class="card-main">
            <div class="name-row">
              <span class="name">{{ person.name }}</span>
              <span class="tag">就诊人</span>
            </div>
            <div class="meta">
              <span>手机号：{{ person.phone }}</span>
              <span>身份证号：{{ person.idCard }}</span>
            </div>
          </div>
          <div class="card-actions">
            <button class="text-btn" @click="openEdit(person)">编辑</button>
            <button class="text-btn danger" @click.stop="showDeleteConfirm(person.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showDialog" class="modal-backdrop">
      <div class="modal">
        <h2>{{ isEdit ? '编辑就诊人' : '新增就诊人' }}</h2>
        <div class="form">
          <label>姓名</label>
          <input v-model="form.name" placeholder="请输入姓名" />
          <label>手机号</label>
          <input v-model="form.phone" placeholder="请输入手机号" />
          <label>身份证号</label>
          <input v-model="form.idCard" placeholder="请输入身份证号" />
          <div class="modal-actions">
            <button class="secondary-btn" @click="closeDialog">取消</button>
            <button class="primary-btn" @click="savePatient">保存</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirmModal" class="modal-backdrop" @click="cancelDelete">
      <div class="confirm-modal" @click.stop>
        <div class="confirm-header">
          <h3>确认删除</h3>
        </div>
        <div class="confirm-body">
          <div class="confirm-icon">⚠️</div>
          <p class="confirm-message">确定要删除这个就诊人吗？</p>
          <p class="confirm-hint">删除后无法恢复</p>
        </div>
        <div class="confirm-footer">
          <button @click="cancelDelete" class="cancel-btn">取消</button>
          <button @click="confirmDelete" class="confirm-delete-btn">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'PatientManager',
  data() {
    return {
      patients: [],
      showDialog: false,
      isEdit: false,
      editingId: null,
      showDeleteConfirmModal: false,
      deleteTargetId: null,
      form: {
        name: '',
        phone: '',
        idCard: ''
      }
    }
  },
  mounted() {
    this.loadPatients()
  },
  methods: {
    async loadPatients() {
      try {
        const response = await axios.get('/api/patients')
        if (response.data.status === 'success') {
          this.patients = response.data.data || []
        } else {
          console.error('获取就诊人列表失败:', response.data.message)
          this.patients = []
        }
      } catch (error) {
        console.error('获取就诊人列表失败:', error)
        this.patients = []
      }
    },
    openCreate() {
      this.isEdit = false
      this.editingId = null
      this.form = { name: '', phone: '', idCard: '' }
      this.showDialog = true
    },
    openEdit(person) {
      this.isEdit = true
      this.editingId = person.id
      this.form = { ...person }
      this.showDialog = true
    },
    closeDialog() {
      this.showDialog = false
    },
    async savePatient() {
      if (!this.form.name || !this.form.phone || !this.form.idCard) {
        alert('请完整填写姓名、手机号和身份证号')
        return
      }
      
      try {
        if (this.isEdit) {
          // 更新就诊人
          const response = await axios.put(`/api/patients/${this.editingId}`, {
            name: this.form.name,
            phone: this.form.phone,
            idCard: this.form.idCard
          })
          
          if (response.data.status === 'success') {
            // 重新加载列表
            await this.loadPatients()
            this.showDialog = false
          } else {
            alert(response.data.message || '更新失败')
          }
        } else {
          // 创建就诊人
          const response = await axios.post('/api/patients', {
            name: this.form.name,
            phone: this.form.phone,
            idCard: this.form.idCard
          })
          
          if (response.data.status === 'success') {
            // 重新加载列表
            await this.loadPatients()
            this.showDialog = false
          } else {
            alert(response.data.message || '创建失败')
          }
        }
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.message || '操作失败'
        alert(errorMsg)
      }
    },
    removePatient(id) {
      this.deleteTargetId = id
      this.showDeleteConfirmModal = true
    },
    showDeleteConfirm(id) {
      this.deleteTargetId = id
      this.showDeleteConfirmModal = true
    },
    cancelDelete() {
      this.showDeleteConfirmModal = false
      this.deleteTargetId = null
    },
    async confirmDelete() {
      if (!this.deleteTargetId) {
        this.cancelDelete()
        return
      }
      
      try {
        const response = await axios.delete(`/api/patients/${this.deleteTargetId}`)
        
        if (response.data.status === 'success') {
          // 重新加载列表
          await this.loadPatients()
          this.cancelDelete()
        } else {
          alert(response.data.message || '删除失败')
        }
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.message || '删除失败'
        alert(errorMsg)
      }
    },
    goBack() {
      // 优先返回上一页（如从医生/时段选择页进入），否则回首页
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
.patient-manager {
  max-width: 1000px;
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
.back-btn, .primary-btn, .secondary-btn {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 2px solid #667eea;
  cursor: pointer;
  font-size: 0.95rem;
}
.back-btn {
  background: white;
  color: #667eea;
}
.primary-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}
.secondary-btn {
  background: white;
  color: #667eea;
}
.content-card {
  background: white;
  border-radius: 15px;
  padding: 1.5rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}
.empty-state {
  text-align: center;
  color: #666;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.patient-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.patient-card {
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.name-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.name {
  font-size: 1.1rem;
  font-weight: 700;
}
.tag {
  background: #eef2ff;
  color: #4f46e5;
  padding: 0.15rem 0.4rem;
  border-radius: 6px;
  font-size: 0.8rem;
}
.meta {
  color: #555;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-top: 0.3rem;
}
.card-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.text-btn {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
}
.text-btn.danger {
  color: #e11d48;
}
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  width: 360px;
  box-shadow: 0 15px 40px rgba(0,0,0,0.2);
}
.form {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.form label {
  font-weight: 600;
  color: #333;
}
.form input {
  padding: 0.7rem;
  border: 1px solid #ddd;
  border-radius: 8px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
.confirm-modal {
  background: white;
  border-radius: 15px;
  width: 90%;
  max-width: 400px;
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
.cancel-btn,
.confirm-delete-btn {
  flex: 1;
  padding: 0.8rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}
.cancel-btn {
  background: #f0f0f0;
  color: #666;
}
.cancel-btn:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
}
.confirm-delete-btn {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  color: white;
}
.confirm-delete-btn:hover {
  background: linear-gradient(135deg, #ee5a6f 0%, #ff6b6b 100%);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
}
</style>
