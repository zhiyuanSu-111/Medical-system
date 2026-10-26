<template>
  <div class="admin-panel">
    <div class="panel">
      <h1 class="title">管理后台</h1>
      <p class="sub">科室与医生信息的维护（增删改查）</p>

      <div class="tabs">
        <button type="button" :class="{ active: tab === 'dept' }" @click="tab = 'dept'">科室管理</button>
        <button type="button" :class="{ active: tab === 'doc' }" @click="tab = 'doc'">医生管理</button>
      </div>

      <p v-if="message" :class="['banner', messageType]">{{ message }}</p>

      <!-- 科室 -->
      <section v-show="tab === 'dept'" class="section">
        <div class="toolbar">
          <h2>科室列表</h2>
          <button type="button" class="btn primary" @click="openDeptForm()">新增科室</button>
        </div>
        <div v-if="deptLoading" class="muted">加载中…</div>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>名称</th>
                <th>图标</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in departments" :key="d.id">
                <td>{{ d.id }}</td>
                <td>{{ d.name }}</td>
                <td>{{ d.icon }}</td>
                <td class="actions">
                  <button type="button" class="btn sm" @click="openDeptForm(d)">编辑</button>
                  <button type="button" class="btn sm danger" @click="deleteDept(d)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 医生 -->
      <section v-show="tab === 'doc'" class="section">
        <div class="toolbar">
          <h2>医生列表</h2>
          <button type="button" class="btn primary" @click="openDocForm()">新增医生</button>
        </div>
        <div v-if="docLoading" class="muted">加载中…</div>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>工号</th>
                <th>姓名</th>
                <th>职称</th>
                <th>专科</th>
                <th>科室ID</th>
                <th>子科室ID</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="doc in doctors" :key="doc.id">
                <td>{{ doc.doctor_id }}</td>
                <td>{{ doc.name }}</td>
                <td>{{ doc.title }}</td>
                <td>{{ doc.specialty }}</td>
                <td>{{ doc.department_id }}</td>
                <td>{{ doc.sub_department_id ?? '—' }}</td>
                <td class="actions">
                  <button type="button" class="btn sm" @click="openDocForm(doc)">编辑</button>
                  <button type="button" class="btn sm danger" @click="deleteDoc(doc)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <!-- 科室表单弹层 -->
    <div v-if="deptForm.show" class="modal-mask" @click.self="deptForm.show = false">
      <div class="modal">
        <h3>{{ deptForm.editingId ? '编辑科室' : '新增科室' }}</h3>
        <label>名称</label>
        <input v-model.trim="deptForm.name" type="text" />
        <label>图标（Emoji）</label>
        <input v-model.trim="deptForm.icon" type="text" placeholder="🏥" />
        <div class="modal-actions">
          <button type="button" class="btn" @click="deptForm.show = false">取消</button>
          <button type="button" class="btn primary" @click="saveDept">保存</button>
        </div>
      </div>
    </div>

    <!-- 医生表单弹层 -->
    <div v-if="docForm.show" class="modal-mask" @click.self="docForm.show = false">
      <div class="modal wide">
        <h3>{{ docForm.rowId ? '编辑医生' : '新增医生' }}</h3>
        <label>医生工号（6 位：100000 + 科室×100 + 序号 1–999）</label>
        <input v-model.number="docForm.doctorId" type="number" placeholder="如 100101" />
        <label>姓名</label>
        <input v-model.trim="docForm.name" type="text" />
        <label>职称</label>
        <input v-model.trim="docForm.title" type="text" />
        <label>专科 / 方向</label>
        <input v-model.trim="docForm.specialty" type="text" />
        <label>科室 ID（department_id）</label>
        <input v-model.number="docForm.departmentId" type="number" />
        <label>子科室 ID（可选）</label>
        <input v-model.number="docForm.subDepartmentId" type="number" />
        <label>专科门诊 ID（可选）</label>
        <input v-model.number="docForm.specialtyId" type="number" />
        <div class="modal-actions">
          <button type="button" class="btn" @click="docForm.show = false">取消</button>
          <button type="button" class="btn primary" @click="saveDoc">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AdminPanel',
  data() {
    return {
      tab: 'dept',
      message: '',
      messageType: 'ok',
      departments: [],
      doctors: [],
      deptLoading: false,
      docLoading: false,
      deptForm: {
        show: false,
        editingId: null,
        name: '',
        icon: '🏥'
      },
      docForm: {
        show: false,
        rowId: null,
        doctorId: '',
        name: '',
        title: '医师',
        specialty: '门诊',
        departmentId: null,
        subDepartmentId: null,
        specialtyId: null
      }
    }
  },
  mounted() {
    this.loadDepartments()
    this.loadDoctors()
  },
  methods: {
    flash(text, type = 'ok') {
      this.message = text
      this.messageType = type
      setTimeout(() => {
        this.message = ''
      }, 3200)
    },
    async loadDepartments() {
      this.deptLoading = true
      try {
        const { data } = await axios.get('/api/admin/departments')
        if (data.status === 'success') this.departments = data.departments || []
      } catch (e) {
        this.flash((e.response && e.response.data && e.response.data.message) || '加载科室失败', 'err')
      } finally {
        this.deptLoading = false
      }
    },
    async loadDoctors() {
      this.docLoading = true
      try {
        const { data } = await axios.get('/api/admin/doctors')
        if (data.status === 'success') this.doctors = data.doctors || []
      } catch (e) {
        this.flash((e.response && e.response.data && e.response.data.message) || '加载医生失败', 'err')
      } finally {
        this.docLoading = false
      }
    },
    openDeptForm(row) {
      if (row) {
        this.deptForm = {
          show: true,
          editingId: row.id,
          name: row.name,
          icon: row.icon || '🏥'
        }
      } else {
        this.deptForm = { show: true, editingId: null, name: '', icon: '🏥' }
      }
    },
    async saveDept() {
      if (!this.deptForm.name) {
        this.flash('请填写科室名称', 'err')
        return
      }
      try {
        if (this.deptForm.editingId) {
          await axios.put(`/api/admin/departments/${this.deptForm.editingId}`, {
            name: this.deptForm.name,
            icon: this.deptForm.icon
          })
        } else {
          await axios.post('/api/admin/departments', {
            name: this.deptForm.name,
            icon: this.deptForm.icon
          })
        }
        this.deptForm.show = false
        this.flash('科室已保存')
        await this.loadDepartments()
      } catch (e) {
        this.flash((e.response && e.response.data && e.response.data.message) || '保存失败', 'err')
      }
    },
    async deleteDept(d) {
      if (!confirm(`确定删除科室「${d.name}」？`)) return
      try {
        await axios.delete(`/api/admin/departments/${d.id}`)
        this.flash('已删除')
        await this.loadDepartments()
      } catch (e) {
        this.flash((e.response && e.response.data && e.response.data.message) || '删除失败', 'err')
      }
    },
    openDocForm(row) {
      if (row) {
        this.docForm = {
          show: true,
          rowId: row.id,
          doctorId: row.doctor_id,
          name: row.name,
          title: row.title,
          specialty: row.specialty,
          departmentId: row.department_id,
          subDepartmentId: row.sub_department_id,
          specialtyId: row.specialty_id
        }
      } else {
        this.docForm = {
          show: true,
          rowId: null,
          doctorId: '',
          name: '',
          title: '医师',
          specialty: '门诊',
          departmentId: null,
          subDepartmentId: null,
          specialtyId: null
        }
      }
    },
    async saveDoc() {
      if (!this.docForm.name || this.docForm.doctorId === '' || this.docForm.doctorId === null) {
        this.flash('请填写工号与姓名', 'err')
        return
      }
      const body = {
        doctorId: this.docForm.doctorId,
        name: this.docForm.name,
        title: this.docForm.title,
        specialty: this.docForm.specialty,
        departmentId: this.docForm.departmentId,
        subDepartmentId: this.docForm.subDepartmentId,
        specialtyId: this.docForm.specialtyId
      }
      try {
        if (this.docForm.rowId) {
          await axios.put(`/api/admin/doctors/${this.docForm.rowId}`, body)
        } else {
          await axios.post('/api/admin/doctors', body)
        }
        this.docForm.show = false
        this.flash('医生已保存')
        await this.loadDoctors()
      } catch (e) {
        this.flash((e.response && e.response.data && e.response.data.message) || '保存失败', 'err')
      }
    },
    async deleteDoc(doc) {
      if (!confirm(`确定删除医生「${doc.name}」？`)) return
      try {
        await axios.delete(`/api/admin/doctors/${doc.id}`)
        this.flash('已删除')
        await this.loadDoctors()
      } catch (e) {
        this.flash((e.response && e.response.data && e.response.data.message) || '删除失败', 'err')
      }
    }
  }
}
</script>

<style scoped>
.admin-panel {
  max-width: 1200px;
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
}
.sub {
  color: #666;
  margin: 0.35rem 0 1rem;
}
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.tabs button {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
}
.tabs button.active {
  background: #667eea;
  color: #fff;
  border-color: #667eea;
}
.banner {
  padding: 0.65rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}
.banner.ok {
  background: #e8f8ef;
  color: #1e7e34;
}
.banner.err {
  background: #fdecea;
  color: #c0392b;
}
.section {
  margin-top: 0.5rem;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.toolbar h2 {
  font-size: 1.15rem;
  color: #333;
}
.table-wrap {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
}
th,
td {
  border: 1px solid #e8e8f0;
  padding: 0.45rem 0.55rem;
  text-align: left;
}
th {
  background: #f5f6ff;
}
.actions {
  white-space: nowrap;
}
.btn {
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #ccc;
  background: #fff;
  cursor: pointer;
  font-size: 0.9rem;
}
.btn.sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.85rem;
  margin-right: 0.35rem;
}
.btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
}
.btn.danger {
  color: #c0392b;
  border-color: #f5c6cb;
}
.muted {
  color: #888;
}
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 1rem;
}
.modal {
  background: #fff;
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}
.modal.wide {
  max-width: 520px;
}
.modal h3 {
  margin-bottom: 1rem;
  color: #333;
}
.modal label {
  display: block;
  font-size: 0.88rem;
  color: #555;
  margin-top: 0.5rem;
}
.modal input {
  width: 100%;
  padding: 0.5rem 0.6rem;
  margin-top: 0.2rem;
  border: 1px solid #ddd;
  border-radius: 6px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1.25rem;
}
</style>
