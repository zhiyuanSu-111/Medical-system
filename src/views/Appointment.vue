<template>
  <div class="appointment">
    <div class="appointment-container">
      <h1 class="page-title">在线挂号</h1>
      
      <!-- 温馨提示弹窗 -->
      <div v-if="showTipModal" class="tip-modal-overlay" @click="closeTipModal">
        <div class="tip-modal-content" @click.stop>
          <div class="tip-modal-header">
            <h2>温馨提示</h2>
            <button @click="closeTipModal" class="tip-close-btn">✕</button>
          </div>
          <div class="tip-modal-body">
            <div class="tip-content">
              <div class="tip-item">
                <div class="tip-number">1、</div>
                <div class="tip-text">
                  <strong>取消预约：</strong>一周内取消预约4次或四周内取消预约6次，限制手机预约4周，但不影响到院后现场当日挂号；
                </div>
              </div>
              <div class="tip-item">
                <div class="tip-number">2、</div>
                <div class="tip-text">
                  <strong>爽约：</strong>三个月内累计爽约3次，限制手机预约8周，但不影响到院后现场当日挂号。
                </div>
              </div>
            </div>
          </div>
          <div class="tip-modal-footer">
            <button @click="closeTipModal" class="tip-confirm-btn">确定</button>
          </div>
        </div>
      </div>
      
      <div class="appointment-form">
        <div class="form-section">
          <h2>选择科室</h2>
          <div class="department-grid">
            <div
              v-for="dept in departments"
              :key="dept.id"
              @click="selectDepartment(dept)"
              :class="['department-card', {
                active: selectedDepartment?.id === dept.id
              }]"
            >
              <div class="dept-icon">{{ dept.icon }}</div>
              <h3>{{ dept.name }}</h3>
            </div>
          </div>
        </div>

        
        <!-- 显示子科室（仅内科） -->
        <div v-if="selectedDepartment && selectedDepartment.id === 1 && !selectedSubDepartment" class="form-section">
          <div class="back-section">
            <button @click="goBackToDepartments" class="back-btn">← 返回选择科室</button>
          </div>
          <h2>选择内科科室</h2>
          <div class="subdepartment-grid">
            <div 
              v-for="subDept in internalSubDepartments" 
              :key="subDept.id"
              @click="selectSubDepartment(subDept)"
              class="subdepartment-card"
            >
              <div class="subdept-icon">{{ subDept.icon }}</div>
              <h3>{{ subDept.name }}</h3>
            </div>
          </div>
        </div>
        
        <!-- 选择医生和时间（当选择了子科室后显示） -->
        <div v-if="selectedSubDepartment" class="form-section">
          <div class="back-section">
            <button @click="goBackToSubDepartments" class="back-btn">← 返回选择科室</button>
          </div>
          
          <!-- 时间选择（放在上方） -->
          <div class="date-time-selection-top">
            <h2>选择日期和时间</h2>
            <div class="date-time-wrapper">
              <div class="date-picker">
                <label>选择日期：</label>
                <div class="custom-date-picker">
                  <select v-model="selectedYear" @change="updateDate" class="date-select">
                    <option v-for="year in availableYears" :key="year" :value="year">{{ year }}年</option>
                  </select>
                  <select v-model="selectedMonth" @change="updateDate" class="date-select">
                    <option v-for="month in 12" :key="month" :value="month">{{ month }}月</option>
                  </select>
                  <select v-model="selectedDay" @change="updateDate" class="date-select">
                    <option v-for="day in availableDays" :key="day" :value="day">{{ day }}日</option>
                  </select>
                </div>
              </div>
              <div class="time-slots">
                <label>选择时间段：</label>
                <div class="time-grid">
                  <div 
                    v-for="slot in timeSlots" 
                    :key="slot"
                    @click="selectTimeSlot(slot)"
                    :class="['time-slot', { active: selectedTimeSlot === slot }]"
                  >
                    {{ slot }}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 医生列表 -->
          <div class="doctor-selection">
            <h2>选择医生</h2>
            <div class="doctor-list">
              <div 
                v-for="doctor in doctors" 
                :key="doctor.id"
                @click="selectDoctor(doctor)"
                :class="['doctor-card', { active: selectedDoctor?.id === doctor.id }]"
              >
                <div class="doctor-info">
                  <h3>{{ doctor.name }}</h3>
                  <p>{{ doctor.title }}</p>
                  <p class="doctor-specialty">{{ doctor.specialty }}</p>
                </div>
                <div class="doctor-availability">
                  <span class="available">可预约</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="selectedDoctor && selectedDate && selectedTimeSlot" class="form-section">
          <h2>患者信息</h2>
          <div class="patient-info">
            <input type="text" v-model="patientName" placeholder="请输入姓名" />
            <input type="tel" v-model="patientPhone" placeholder="请输入手机号" />
            <input type="text" v-model="patientIdCard" placeholder="请输入身份证号" />
          </div>
        </div>
        
        <div v-if="canSubmit" class="submit-section">
          <button @click="submitAppointment" class="submit-btn">确认预约</button>
        </div>
      </div>
    </div>
    
    <!-- 消息提示 -->
    <transition name="message-fade">
      <div v-if="message.show" :class="['message-toast', message.type]">
        <div class="message-icon">
          <span v-if="message.type === 'success'">✓</span>
          <span v-else-if="message.type === 'error'">✕</span>
          <span v-else>!</span>
        </div>
        <div class="message-content">{{ message.text }}</div>
      </div>
    </transition>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Appointment',
  data() {
    return {
      showTipModal: false, // 默认不显示，根据情况决定是否显示
      message: {
        show: false,
        text: '',
        type: 'success' // success, error, warning
      },
      departments: [
        { id: 1, name: '内科', icon: '🫀' },
        { id: 2, name: '外科', icon: '🔪' },
        { id: 3, name: '多学科协作诊治', icon: '👥' },
        { id: 4, name: '感染病科', icon: '🦠' },
        { id: 5, name: '肿瘤科', icon: '🎗️' },
        { id: 6, name: '耳鼻咽喉科', icon: '👂' },
        { id: 7, name: '眼科', icon: '👁️' },
        { id: 8, name: '口腔科', icon: '🦷' },
        { id: 9, name: '妇产科', icon: '👩' },
        { id: 10, name: '生殖医学', icon: '👶' },
        { id: 11, name: '儿科', icon: '🧒' },
        { id: 12, name: '变态反应（过敏）科', icon: '🤧' },
        { id: 13, name: '皮肤科', icon: '🧴' },
        { id: 14, name: '精神科卫生科', icon: '🧠' },
        { id: 15, name: '中医科', icon: '🌿' },
        { id: 16, name: '麻醉科', icon: '💉' },
        { id: 17, name: '医学影像科', icon: '📷' },
        { id: 18, name: '疼痛科', icon: '😣' },
        { id: 19, name: '医疗美容科', icon: '✨' },
        { id: 20, name: '全科医疗科', icon: '🏥' },
        { id: 21, name: '康复医学科', icon: '🔄' },
        { id: 22, name: '病理科', icon: '🔬' },
        { id: 23, name: '营养科', icon: '🥗' },
        { id: 24, name: '临床药学', icon: '📋' },
        { id: 25, name: '专科护理', icon: '💊' },
        { id: 26, name: '高压氧', icon: '💨' },
        { id: 27, name: '资深专家门诊', icon: '👨‍⚕️' },
        { id: 28, name: '我的收藏', icon: '⭐' }
      ],
      doctors: [],
      selectedDepartment: null,
      selectedSubDepartment: null,
      selectedDoctor: null,
      selectedDate: '',
      selectedYear: new Date().getFullYear(),
      selectedMonth: new Date().getMonth() + 1,
      selectedDay: new Date().getDate() + 1,
      selectedTimeSlot: '',
      patientName: '',
      patientPhone: '',
      patientIdCard: '',
      // 内科子科室
      internalSubDepartments: [
        { id: 1, name: '消化内科', icon: '🫁' },
        { id: 2, name: '心血管内科', icon: '❤️' },
        { id: 3, name: '呼吸内科', icon: '🫁' },
        { id: 4, name: '血液科', icon: '🩸' },
        { id: 5, name: '肾脏病', icon: '🔬' },
        { id: 6, name: '神经内科', icon: '🧠' },
        { id: 7, name: '内分泌科', icon: '⚕️' },
        { id: 8, name: '风湿免疫科', icon: '🦴' },
        { id: 9, name: '老年医学科', icon: '👴' },
        { id: 10, name: '普内科', icon: '🏥' }
      ],
      // 各子科室的医生数据（每个科室：专家医生数量少于普通医生）
      subDepartmentDoctors: {
        1: [ // 消化内科：1 专家 + 3 普通
          { id: 100258, name: '张明', title: '主任医师', specialty: '消化内科' },           // 专家
          { id: 100259, name: '李华', title: '主治医师', specialty: '消化内科' },
          { id: 100260, name: '王强', title: '主治医师', specialty: '消化内科' },
          { id: 100261, name: '赵敏', title: '医师',     specialty: '消化内科' }
        ],
        2: [ // 心血管内科：1 专家 + 4 普通
          { id: 100262, name: '陈建国', title: '主任医师', specialty: '心血管内科' },       // 专家
          { id: 100263, name: '刘芳',   title: '主治医师', specialty: '心血管内科' },
          { id: 100264, name: '周伟',   title: '主治医师', specialty: '心血管内科' },
          { id: 100265, name: '吴丽',   title: '医师',     specialty: '心血管内科' },
          { id: 100266, name: '郑强',   title: '医师',     specialty: '心血管内科' }
        ],
        3: [ // 呼吸内科：1 专家 + 2 普通
          { id: 100267, name: '孙立', title: '主任医师', specialty: '呼吸内科' },           // 专家
          { id: 100268, name: '马静', title: '主治医师', specialty: '呼吸内科' },
          { id: 100269, name: '钱勇', title: '医师',     specialty: '呼吸内科' }
        ],
        4: [ // 血液科：1 专家 + 2 普通
          { id: 100270, name: '冯军', title: '主任医师', specialty: '血液科' },             // 专家
          { id: 100271, name: '韩梅', title: '主治医师', specialty: '血液科' },
          { id: 100272, name: '杨波', title: '医师',     specialty: '血液科' }
        ],
        5: [ // 肾脏病：1 专家 + 3 普通
          { id: 100273, name: '朱文', title: '主任医师', specialty: '肾脏病' },             // 专家
          { id: 100274, name: '林雪', title: '主治医师', specialty: '肾脏病' },
          { id: 100275, name: '何刚', title: '主治医师', specialty: '肾脏病' },
          { id: 100276, name: '罗敏', title: '医师',     specialty: '肾脏病' }
        ],
        6: [ // 神经内科：1 专家 + 3 普通
          { id: 100277, name: '徐亮', title: '主任医师', specialty: '神经内科' },           // 专家
          { id: 100278, name: '高红', title: '主治医师', specialty: '神经内科' },
          { id: 100279, name: '谢军', title: '主治医师', specialty: '神经内科' },
          { id: 100280, name: '唐丽', title: '医师',     specialty: '神经内科' }
        ],
        7: [ // 内分泌科：1 专家 + 2 普通
          { id: 100281, name: '邓强', title: '主任医师', specialty: '内分泌科' },           // 专家
          { id: 100282, name: '许静', title: '主治医师', specialty: '内分泌科' },
          { id: 100283, name: '曹勇', title: '医师',     specialty: '内分泌科' }
        ],
        8: [ // 风湿免疫科：1 专家 + 2 普通
          { id: 100284, name: '袁文', title: '主任医师', specialty: '风湿免疫科' },         // 专家
          { id: 100285, name: '田梅', title: '主治医师', specialty: '风湿免疫科' },
          { id: 100286, name: '宋刚', title: '医师',     specialty: '风湿免疫科' }
        ],
        9: [ // 老年医学科：1 专家 + 3 普通
          { id: 100287, name: '潘明', title: '主任医师', specialty: '老年医学科' },         // 专家
          { id: 100288, name: '方丽', title: '主治医师', specialty: '老年医学科' },
          { id: 100289, name: '石强', title: '主治医师', specialty: '老年医学科' },
          { id: 100290, name: '姚静', title: '医师',     specialty: '老年医学科' }
        ],
        10: [ // 普内科：1 专家 + 2 普通
          { id: 100291, name: '胡军', title: '主任医师', specialty: '普内科' },           // 专家
          { id: 100292, name: '范红', title: '主治医师', specialty: '普内科' },
          { id: 100293, name: '卢勇', title: '医师',     specialty: '普内科' }
        ]
      },
      timeSlots: [
        '08:00-12:00',
        '14:00-18:00'
      ]
    }
  },
  mounted() {
    // 检查是否是首次进入（不是从其他页面返回）
    // 如果路由查询参数中有 fromBack 标记，说明是从其他页面返回的，不显示温馨提示
    const fromBack = this.$route.query.fromBack === 'true'
    
    // 只有在首次进入（不是从其他页面返回）时才显示温馨提示
    if (!fromBack) {
      this.showTipModal = true
    }
  },
  computed: {
    minDate() {
      const tomorrow = new Date()
      tomorrow.setDate(tomorrow.getDate() + 1)
      return tomorrow.toISOString().split('T')[0]
    },
    availableYears() {
      const currentYear = new Date().getFullYear()
      const years = []
      for (let i = 0; i < 3; i++) {
        years.push(currentYear + i)
      }
      return years
    },
    availableDays() {
      const daysInMonth = new Date(this.selectedYear, this.selectedMonth, 0).getDate()
      const days = []
      const tomorrow = new Date()
      tomorrow.setDate(tomorrow.getDate() + 1)
      const minDay = (this.selectedYear === tomorrow.getFullYear() && 
                      this.selectedMonth === tomorrow.getMonth() + 1) 
                      ? tomorrow.getDate() : 1
      
      for (let i = minDay; i <= daysInMonth; i++) {
        days.push(i)
      }
      return days
    },
    canSubmit() {
      return this.selectedSubDepartment &&
             this.selectedDoctor && 
             this.selectedDate && 
             this.selectedTimeSlot && 
             this.patientName && 
             this.patientPhone && 
             this.patientIdCard
    }
  },
  watch: {
    selectedMonth() {
      // 当月份改变时，检查日期是否有效
      const maxDay = new Date(this.selectedYear, this.selectedMonth, 0).getDate()
      if (this.selectedDay > maxDay) {
        this.selectedDay = maxDay
      }
      this.updateDate()
    },
    selectedYear() {
      this.updateDate()
    }
  },
  methods: {

    // 关闭温馨提示
    closeTipModal() {
      this.showTipModal = false
    },
    
    selectDepartment(dept) {
      // 如果是内科/外科/肿瘤科/口腔科/妇产科/生殖医学/儿科/变态反应（过敏）科/皮肤科/精神科卫生科/中医科/麻醉科/医学影像科/疼痛科/医疗美容科/全科医疗科/康复医学科/病理科/营养科/临床药学/专科护理/高压氧/资深专家门诊，跳转到子科室选择页面
      if (dept.id === 1 || dept.id === 2 || dept.id === 5 || dept.id === 8 || dept.id === 9 || dept.id === 10 || dept.id === 11 || dept.id === 12 || dept.id === 13 || dept.id === 14 || dept.id === 15 || dept.id === 16 || dept.id === 17 || dept.id === 18 || dept.id === 19 || dept.id === 20 || dept.id === 21 || dept.id === 22 || dept.id === 23 || dept.id === 24 || dept.id === 25 || dept.id === 26 || dept.id === 27) {
        this.$router.push({
          name: 'AppointmentSubDepartment',
          query: {
            departmentId: dept.id,
            departmentName: dept.name
          }
        })
      } else if (dept.id === 3 || dept.id === 4 || dept.id === 6 || dept.id === 7) {
        // 多学科协作诊治、感染病科、耳鼻咽喉科、眼科：直接进入专科门诊选择页面
        this.$router.push({
          name: 'AppointmentSpecialty',
          query: {
            departmentId: dept.id,
            departmentName: dept.name,
            subDepartmentId: 0,
            subDepartmentName: dept.name
          }
        })
      } else {
        // 其他科室保持原有逻辑（暂时）
        this.selectedDepartment = dept
        this.selectedSubDepartment = null
        this.selectedDoctor = null
        this.selectedDate = ''
        this.selectedTimeSlot = ''
        this.loadDoctors(dept.id)
      }
    },
    
    // 选择子科室
    selectSubDepartment(subDept) {
      this.selectedSubDepartment = subDept
      this.selectedDoctor = null
      this.selectedDate = ''
      this.selectedTimeSlot = ''
      // 加载该子科室的医生
      this.loadSubDepartmentDoctors(subDept.id)
    },
    
    // 加载子科室的医生
    loadSubDepartmentDoctors(subDeptId) {
      this.doctors = this.subDepartmentDoctors[subDeptId] || []
    },
    
    // 返回科室选择
    goBackToDepartments() {
      this.selectedDepartment = null
      this.selectedSubDepartment = null
      this.selectedDoctor = null
      this.selectedDate = ''
      this.selectedTimeSlot = ''
      this.doctors = []
      this.showingDepartmentName = null
      this.departmentClickCount = {}
    },
    
    // 返回子科室选择
    goBackToSubDepartments() {
      this.selectedSubDepartment = null
      this.selectedDoctor = null
      this.selectedDate = ''
      this.selectedTimeSlot = ''
      this.doctors = []
    },
    
    loadDoctors(deptId) {
      // 其他科室的医生数据（非内科）
      const doctorsData = {
        2: [
          { id: 3, name: '王医生', title: '主任医师', specialty: '普外科' },
          { id: 4, name: '赵医生', title: '主治医师', specialty: '神经外科' }
        ]
      }
      
      this.doctors = doctorsData[deptId] || [
        { id: 5, name: '刘医生', title: '主任医师', specialty: '专科' }
      ]
    },
    
    selectDoctor(doctor) {
      this.selectedDoctor = doctor
    },
    
    selectTimeSlot(slot) {
      this.selectedTimeSlot = slot
    },
    
    // 显示消息提示
    showMessage(text, type = 'success', duration = 3000) {
      this.message = {
        show: true,
        text: text,
        type: type
      }
      setTimeout(() => {
        this.message.show = false
      }, duration)
    },
    
    async submitAppointment() {
      const appointmentData = {
        department: this.selectedDepartment.name,
        subDepartment: this.selectedSubDepartment ? this.selectedSubDepartment.name : '',
        doctor: this.selectedDoctor.name,
        date: this.selectedDate,
        timeSlot: this.selectedTimeSlot,
        patientName: this.patientName,
        patientPhone: this.patientPhone,
        patientIdCard: this.patientIdCard
      }
      
      try {
        const response = await axios.post('/api/appointment', appointmentData)
        if (response.data.status === 'error') {
          this.showMessage(response.data.message || '预约失败', 'error', 3000)
          return
        }
        const appointmentId = response.data.appointmentId || 'A' + Date.now()
        this.showMessage(`预约成功！预约号：${appointmentId}`, 'success', 3000)
        setTimeout(() => {
          this.resetForm()
        }, 2000)
      } catch (error) {
        if (error.response && error.response.status === 401) {
          this.showMessage('请先登录患者账号后再预约', 'error', 2500)
          this.$router.push({ path: '/login', query: { redirect: this.$route.fullPath } })
          return
        }
        const msg = error.response?.data?.message || '预约失败，请稍后重试'
        this.showMessage(msg, 'error', 3000)
      }
    },
    
    resetForm() {
      this.selectedDepartment = null
      this.selectedSubDepartment = null
      this.selectedDoctor = null
      this.selectedDate = ''
      this.selectedTimeSlot = ''
      this.patientName = ''
      this.patientPhone = ''
      this.patientIdCard = ''
      this.doctors = []
    }
  }
}
</script>

<style scoped>
.appointment {
  max-width: 1000px;
  margin: 0 auto;
}

.page-title {
  color: white;
  text-align: center;
  font-size: 2.5rem;
  margin-bottom: 2rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

/* 温馨提示弹窗样式 */
.tip-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.tip-modal-content {
  background: white;
  border-radius: 15px;
  width: 90%;
  max-width: 600px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
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

.tip-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 2px solid #f0f0f0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.tip-modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: white;
}

.tip-close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 1.5rem;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  line-height: 1;
  padding: 0;
}

.tip-close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

.tip-modal-body {
  padding: 2rem;
  flex: 1;
  overflow-y: auto;
}

.tip-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.tip-item {
  display: flex;
  gap: 0.5rem;
  line-height: 1.8;
}

.tip-number {
  color: #667eea;
  font-weight: 600;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.tip-text {
  color: #333;
  font-size: 1rem;
  flex: 1;
}

.tip-text strong {
  color: #667eea;
  font-weight: 600;
}

.tip-modal-footer {
  padding: 1.5rem;
  border-top: 2px solid #f0f0f0;
  text-align: center;
  background: #f8f9fa;
}

.tip-confirm-btn {
  padding: 0.8rem 3rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.tip-confirm-btn:hover {
  opacity: 0.9;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.appointment-form {
  background: white;
  border-radius: 15px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.form-section {
  margin-bottom: 2.5rem;
}

.form-section h2 {
  color: #667eea;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
}

.department-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 1rem;
  max-height: 600px;
  overflow-y: auto;
  padding: 0.5rem;
}

.department-card {
  background: #f8f9fa;
  border: 2px solid transparent;
  border-radius: 10px;
  padding: 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.department-card:hover,
.department-card.active {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-5px);
}

.dept-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.department-card h3 {
  font-size: 1.1rem;
}



/* 子科室样式 */
.back-section {
  margin-bottom: 1rem;
}

.back-btn {
  padding: 0.5rem 1rem;
  background: #f0f0f0;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  color: #666;
  transition: all 0.3s;
}

.back-btn:hover {
  background: #e0e0e0;
  color: #667eea;
}

.subdepartment-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 1rem;
}

.subdepartment-card {
  background: #f8f9fa;
  border: 2px solid transparent;
  border-radius: 10px;
  padding: 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.subdepartment-card:hover {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-5px);
}

.subdept-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.subdepartment-card h3 {
  font-size: 1rem;
  margin: 0;
}

/* 时间选择在上方的样式 */
.date-time-selection-top {
  margin-bottom: 2.5rem;
  padding-bottom: 2rem;
  border-bottom: 2px solid #f0f0f0;
}

.date-time-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.doctor-selection {
  margin-top: 2rem;
}

.doctor-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.doctor-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: #f8f9fa;
  border: 2px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.doctor-card:hover,
.doctor-card.active {
  border-color: #667eea;
  background: white;
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
}

.doctor-info h3 {
  color: #333;
  margin-bottom: 0.5rem;
}

.doctor-info p {
  color: #666;
  margin: 0.3rem 0;
}

.doctor-specialty {
  color: #667eea !important;
  font-weight: 600;
}

.available {
  color: #28a745;
  font-weight: 600;
}

.date-time-selection {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.date-picker label,
.time-slots label {
  display: block;
  margin-bottom: 0.5rem;
  color: #333;
  font-weight: 600;
}

.date-picker input {
  padding: 0.8rem;
  border: 2px solid #eee;
  border-radius: 8px;
  font-size: 1rem;
  width: 100%;
  max-width: 300px;
}

.custom-date-picker {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.date-select {
  padding: 0.8rem 1rem;
  border: 2px solid #eee;
  border-radius: 8px;
  font-size: 1rem;
  background: white;
  cursor: pointer;
  transition: border-color 0.3s;
  min-width: 100px;
}

.date-select:focus {
  outline: none;
  border-color: #667eea;
}

.date-select:hover {
  border-color: #667eea;
}

.time-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 1rem;
}

.time-slot {
  padding: 0.8rem;
  background: #f8f9fa;
  border: 2px solid transparent;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.time-slot:hover,
.time-slot.active {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.patient-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.patient-info input {
  padding: 0.8rem;
  border: 2px solid #eee;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.patient-info input:focus {
  outline: none;
  border-color: #667eea;
}

.submit-section {
  text-align: center;
  margin-top: 2rem;
}

.submit-btn {
  padding: 1rem 3rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 1.2rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.3s;
}

.submit-btn:hover {
  opacity: 0.9;
}

/* 消息提示样式 */
.message-toast {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 12px;
  padding: 1.5rem 2rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  z-index: 10000;
  display: flex;
  align-items: center;
  gap: 1rem;
  min-width: 300px;
  max-width: 500px;
  animation: slideDown 0.3s ease-out;
}

.message-toast.success {
  border-left: 4px solid #4caf50;
}

.message-toast.error {
  border-left: 4px solid #f44336;
}

.message-toast.warning {
  border-left: 4px solid #ff9800;
}

.message-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: bold;
  flex-shrink: 0;
}

.message-toast.success .message-icon {
  background: #e8f5e9;
  color: #4caf50;
}

.message-toast.error .message-icon {
  background: #ffebee;
  color: #f44336;
}

.message-toast.warning .message-icon {
  background: #fff3e0;
  color: #ff9800;
}

.message-content {
  flex: 1;
  font-size: 1rem;
  color: #333;
  line-height: 1.5;
}

.message-fade-enter-active,
.message-fade-leave-active {
  transition: all 0.3s ease;
}

.message-fade-enter-from {
  opacity: 0;
  transform: translate(-50%, -60%);
}

.message-fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -40%);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translate(-50%, -60%);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%);
  }
}
</style>
