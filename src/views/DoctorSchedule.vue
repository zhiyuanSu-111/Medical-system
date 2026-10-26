<template>
  <div class="doctor-schedule">
    <div class="panel">
      <h1 class="title">我的出诊排班</h1>
      <p v-if="doctorInfo" class="sub">
        {{ doctorInfo.name }} · {{ doctorInfo.title }} · {{ doctorInfo.specialty }}
        <span class="muted">（工号 {{ doctorBusinessId }}）</span>
      </p>
      <p v-if="error" class="error">{{ error }}</p>
      <div v-if="loading" class="loading">加载中…</div>
      <template v-else>
        <section class="section">
          <h2>号源时段</h2>
          <div v-if="!slots.length" class="empty">暂无号源记录，请联系管理员初始化号源。</div>
          <div v-else class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>日期</th>
                  <th>时段</th>
                  <th>总号源</th>
                  <th>已预约</th>
                  <th>剩余</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(s, i) in slots" :key="i">
                  <td>{{ s.date }}</td>
                  <td>{{ s.time_slot }}</td>
                  <td>{{ s.total_count }}</td>
                  <td>{{ s.booked_count }}</td>
                  <td>{{ s.available_count }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
        <section class="section">
          <h2>预约患者（近期）</h2>
          <div v-if="!appointments.length" class="empty">暂无预约记录。</div>
          <div v-else class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>预约号</th>
                  <th>日期</th>
                  <th>时段</th>
                  <th>患者</th>
                  <th>手机</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in appointments" :key="a.appointment_id">
                  <td>{{ a.appointment_id }}</td>
                  <td>{{ a.date }}</td>
                  <td>{{ a.time_slot }}</td>
                  <td>{{ a.patient_name }}</td>
                  <td>{{ a.patient_phone }}</td>
                  <td>{{ a.status }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'DoctorSchedule',
  data() {
    return {
      loading: true,
      error: '',
      doctorInfo: null,
      doctorBusinessId: null,
      slots: [],
      appointments: []
    }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const { data } = await axios.get('/api/doctor/my-schedule')
        if (data.status !== 'success') {
          this.error = data.message || '加载失败'
          return
        }
        this.doctorInfo = data.doctor
        this.doctorBusinessId = data.doctorBusinessId
        this.slots = data.slots || []
        this.appointments = data.appointments || []
      } catch (e) {
        this.error =
          (e.response && e.response.data && e.response.data.message) || e.message || '加载失败'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.doctor-schedule {
  max-width: 1100px;
  margin: 0 auto;
}
.panel {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  padding: 1.75rem 2rem;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}
.title {
  color: #667eea;
  font-size: 1.75rem;
  margin-bottom: 0.5rem;
}
.sub {
  color: #444;
  margin-bottom: 1rem;
}
.muted {
  color: #888;
  font-size: 0.9rem;
}
.section {
  margin-top: 1.75rem;
}
.section h2 {
  font-size: 1.15rem;
  color: #333;
  margin-bottom: 0.75rem;
  border-left: 4px solid #667eea;
  padding-left: 0.5rem;
}
.table-wrap {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}
th,
td {
  border: 1px solid #e8e8f0;
  padding: 0.5rem 0.65rem;
  text-align: left;
}
th {
  background: #f5f6ff;
  color: #444;
}
.error {
  color: #c0392b;
  margin-bottom: 0.75rem;
}
.loading,
.empty {
  color: #666;
  padding: 1rem 0;
}
</style>
