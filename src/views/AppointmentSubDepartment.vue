<template>
  <div class="appointment-subdepartment">
    <div class="appointment-container">
      <div class="header-section">
        <button @click="goBack" class="back-btn">← 返回</button>
        <h1 class="page-title">{{ departmentName }} - 选择科室</h1>
      </div>
      
      <!-- 温馨提示弹窗（妇产科：妇科/产科均提示） -->
      <div v-if="showPregnancyTip" class="tip-modal-overlay" @click="cancelPregnancyTip">
        <div class="tip-modal-content" @click.stop>
          <div class="tip-modal-header">
            <h2>温馨提醒</h2>
            <button @click="cancelPregnancyTip" class="tip-close-btn">✕</button>
          </div>
          <div class="tip-modal-body">
            <div class="tip-content">
              <div class="tip-text">
                <strong>早孕女性（孕12周内）首次就诊，请先挂早孕门诊！</strong>
              </div>
            </div>
          </div>
          <div class="tip-modal-footer">
            <button @click="confirmPregnancyTip" class="tip-confirm-btn">我已知晓，继续</button>
          </div>
        </div>
      </div>

      <div class="subdepartment-form">
        <div class="form-section">
          <h2>请选择具体科室</h2>
          <!-- 调试信息 -->
          <div v-if="!departmentId || subDepartments.length === 0" class="debug-info" style="padding: 1rem; background: #fff3cd; border-radius: 8px; margin-bottom: 1rem;">
            <p><strong>调试信息：</strong></p>
            <p>科室ID: {{ departmentId || '未设置' }}</p>
            <p>科室名称: {{ departmentName || '未设置' }}</p>
            <p>子科室数量: {{ subDepartments.length }}</p>
            <p>openSub参数: {{ $route.query.openSub || '无' }}</p>
          </div>
          <div v-if="subDepartments.length === 0" class="no-subdepartments" style="text-align: center; padding: 2rem;">
            <p style="color: #999; font-size: 1.1rem;">暂无可用科室，请返回重新选择</p>
            <button @click="goBack" class="back-btn" style="margin-top: 1rem;">返回</button>
          </div>
          <div v-else class="subdepartment-grid">
            <div 
              v-for="subDept in subDepartments" 
              :key="subDept.id"
              @click="selectSubDepartment(subDept)"
              class="subdepartment-card"
            >
              <div class="subdept-icon">{{ subDept.icon }}</div>
              <h3>{{ subDept.name }}</h3>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AppointmentSubDepartment',
  data() {
    return {
      departmentId: null,
      departmentName: '',
      subDepartments: [],
      showPregnancyTip: false,
      pendingSubDept: null,
      showMainDepartment: false, // 是否显示主科室（生殖医学等）
      mainDepartmentClicked: false // 主科室是否已被点击
    }
  },
  mounted() {
    // 从路由查询参数获取科室信息
    const deptId = this.$route.query.departmentId
    this.departmentId = deptId ? parseInt(deptId) : null
    this.departmentName = this.$route.query.departmentName || '内科'
    
    // 调试信息
    console.log('AppointmentSubDepartment mounted:', {
      departmentId: this.departmentId,
      departmentName: this.departmentName,
      query: this.$route.query,
      openSub: this.$route.query.openSub,
      rawDepartmentId: deptId
    })
    
    // 检查 departmentId 是否有效
    if (!this.departmentId || isNaN(this.departmentId)) {
      console.error('无效的科室ID:', deptId)
      this.subDepartments = []
      return
    }
    
    // 根据科室ID加载子科室
    if (this.departmentId === 1) {
      // 内科子科室
      this.subDepartments = [
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
      ]
    } else if (this.departmentId === 2) {
      // 外科子科室
      this.subDepartments = [
        { id: 1, name: '肝胆胰外科', icon: '🔪' },
        { id: 2, name: '胃肠外科', icon: '🍽️' },
        { id: 3, name: '甲状腺外科', icon: '🦋' },
        { id: 4, name: '乳腺外科', icon: '💗' },
        { id: 5, name: '肿瘤外科', icon: '🎗️' },
        { id: 6, name: '结直肠外科', icon: '🩺' },
        { id: 7, name: '骨科', icon: '🦴' },
        { id: 8, name: '泌尿外科', icon: '💧' },
        { id: 9, name: '神经外科', icon: '🧠' },
        { id: 10, name: '普胸外科', icon: '🫁' },
        { id: 11, name: '心脏大血管外科', icon: '❤️' },
        { id: 12, name: '血管外科', icon: '🩸' }
      ]
    } else if (this.departmentId === 5) {
      // 肿瘤科子科室
      this.subDepartments = [
        { id: 1, name: '肿瘤内科', icon: '🎗️' },
        { id: 2, name: '放疗科', icon: '☢️' }
      ]
    } else if (this.departmentId === 8) {
      // 口腔科子科室
      this.subDepartments = [
        { id: 1, name: '口腔内科', icon: '🦷' },
        { id: 2, name: '口腔颌面外科', icon: '🔪' },
        { id: 3, name: '口腔修复科', icon: '🦷' },
        { id: 4, name: '口腔正畸', icon: '😁' },
        { id: 5, name: '口腔种植修复', icon: '🦷' },
        { id: 6, name: '儿童早期错颌畸形专科', icon: '🧒' },
        { id: 7, name: '儿童牙科', icon: '🧒' }
      ]
    } else if (this.departmentId === 9) {
      // 妇产科子科室
      this.subDepartments = [
        { id: 1, name: '妇科', icon: '👩' },
        { id: 2, name: '产科', icon: '🤰' }
      ]
    } else if (this.departmentId === 10) {
      // 生殖医学：先显示主科室
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '生殖医学', icon: '👶' }
      ]
    } else if (this.departmentId === 11) {
      // 儿科：先显示主科室
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '儿科', icon: '🧒' }
      ]
    } else if (this.departmentId === 12) {
      // 变态反应（过敏）科：先显示主科室
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '变态反应（过敏）科', icon: '🤧' }
      ]
    } else if (this.departmentId === 13) {
      // 皮肤科：先显示主科室，第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '皮肤科', icon: '🧴' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '皮肤科门诊', icon: '🧴' }
        ]
      }
    } else if (this.departmentId === 14) {
      // 精神科卫生科：先显示主科室，第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '精神科卫生科', icon: '🧠' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '精神卫生科门诊', icon: '🧠' },
          { id: 2, name: '睡眠障碍门诊', icon: '😴' },
          { id: 3, name: '注意缺陷多动障碍专科门诊', icon: '🎯' },
          { id: 4, name: '抑郁障碍研究型门诊', icon: '💙' }
        ]
      }
    } else if (this.departmentId === 15) {
      // 中医科：先显示主科室，第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '中医科', icon: '🌿' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '中医科门诊', icon: '🌿' },
          { id: 2, name: '中医妇科专科门诊', icon: '👩' },
          { id: 3, name: '中医儿科门诊', icon: '🧒' },
          { id: 4, name: '中医针灸专科门诊', icon: '💉' },
          { id: 5, name: '中医体重管理专科门诊', icon: '⚖️' },
          { id: 6, name: '中医脾胃病专科门诊', icon: '🫁' }
        ]
      }
    } else if (this.departmentId === 16) {
      // 麻醉科：先显示主科室，第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '麻醉科', icon: '💉' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '麻醉科门诊', icon: '💉' }
        ]
      }
    } else if (this.departmentId === 17) {
      // 医学影像科：先显示主科室，第二次点击展示子科室
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '医学影像科', icon: '📷' }
      ]
      // 如果带 openSub=true，直接展示子科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '放射科', icon: '📷' },
          { id: 2, name: '超声医学', icon: '🔊' },
          { id: 3, name: '核医学科', icon: '☢️' }
        ]
      }
    } else if (this.departmentId === 18) {
      // 疼痛科：先显示主科室，第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '疼痛科', icon: '😣' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '疼痛科门诊', icon: '😣' },
          { id: 2, name: '带状疱疹神经痛专科门诊', icon: '🦠' },
          { id: 3, name: '头面痛专科门诊', icon: '😫' }
        ]
      }
    } else if (this.departmentId === 19) {
      // 医疗美容科：显示两个子科室（整形外科、整形美容）
      this.showMainDepartment = false
      this.subDepartments = [
        { id: 1, name: '整形外科', icon: '🩺' },
        { id: 2, name: '整形美容', icon: '💄' }
      ]
    } else if (this.departmentId === 20) {
      // 全科医疗科：先显示主科室，第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '全科医疗科', icon: '🏥' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '全科医学科门诊', icon: '🏥' },
          { id: 2, name: '水肿专科门诊', icon: '💧' },
          { id: 3, name: '全科未分化疾病专科门诊', icon: '🧩' }
        ]
      }
    } else if (this.departmentId === 26) {
      // 高压氧：先显示主科室，第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '高压氧', icon: '💨' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '高压氧科门诊', icon: '💨' }
        ]
      }
    } else if (this.departmentId === 25) {
      // 专科护理：先显示主科室（门诊护理），第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '门诊护理', icon: '💊' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '静脉置管护理门诊', icon: '💉' },
          { id: 2, name: '造口、慢性伤口护理门诊', icon: '🩹' },
          { id: 3, name: '淋巴水肿护理门诊', icon: '💧' }
        ]
      }
    } else if (this.departmentId === 24) {
      // 临床药学：先显示主科室，第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '临床药学', icon: '💊' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '药学门诊', icon: '💊' },
          { id: 2, name: '妊娠哺乳期用药专科门诊', icon: '🤱' }
        ]
      }
    } else if (this.departmentId === 23) {
      // 营养科：先显示主科室，第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '营养科', icon: '🥗' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '营养科门诊', icon: '🥗' },
          { id: 2, name: '围孕期营养门诊', icon: '🤰' },
          { id: 3, name: '营养减肥门诊', icon: '⚖️' },
          { id: 4, name: '体重管理（营养）门诊', icon: '📊' }
        ]
      }
    } else if (this.departmentId === 22) {
      // 病理科：先显示主科室，第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '病理科', icon: '🔬' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '病理科门诊', icon: '🔬' }
        ]
      }
    } else if (this.departmentId === 21) {
      // 康复医学科：先显示主科室，第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '康复医学科', icon: '🔄' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '康复医学科门诊', icon: '🔄' },
          { id: 2, name: '运动损伤康复专科门诊', icon: '🏃' },
          { id: 3, name: '颞颌关节紊乱康复专科门诊', icon: '🦷' },
          { id: 4, name: '疼痛康复专科门诊', icon: '😣' },
          { id: 5, name: '教学门诊/康复医学科', icon: '📚' }
        ]
      }
    } else if (this.departmentId === 27) {
      // 资深专家门诊：先显示主科室，第二次点击展示细分
      this.showMainDepartment = true
      this.subDepartments = [
        { id: 0, name: '资深专家门诊', icon: '👨‍⚕️' }
      ]
      // 如果带 openSub=true，直接展示细分科室（用于医生页返回保持层级）
      if (this.$route.query.openSub === 'true') {
        this.mainDepartmentClicked = true
        this.showMainDepartment = false
        this.subDepartments = [
          { id: 1, name: '肝胆胰外科资深专家门诊', icon: '🔪' },
          { id: 2, name: '心脏大血管外科资深专家门诊', icon: '❤️' },
          { id: 3, name: '肾脏病中心资深专家门诊', icon: '🔬' },
          { id: 4, name: '普胸外科资深专家门诊', icon: '🫁' },
          { id: 5, name: '血液科资深专家门诊', icon: '🩸' },
          { id: 6, name: '风湿免疫资深专家门诊', icon: '🦴' },
          { id: 7, name: '骨科资深专家门诊', icon: '🦴' },
          { id: 8, name: '超声医学科资深专家门诊', icon: '🔊' },
          { id: 9, name: '甲状腺外科资深专家门诊', icon: '🦋' },
          { id: 10, name: '乳腺外科资深专家门诊', icon: '💗' },
          { id: 11, name: '泌尿外科资深专家门诊', icon: '💧' },
          { id: 12, name: '消化内科资深专家门诊', icon: '🫁' },
          { id: 13, name: '神经内科资深专家门诊', icon: '🧠' },
          { id: 14, name: '心血管内科资深专家门诊', icon: '❤️' },
          { id: 15, name: '精神卫生科资深专家门诊', icon: '🧠' },
          { id: 16, name: '内分泌科资深专家门诊', icon: '⚕️' }
        ]
      }
    } else {
      // 如果没有匹配到任何科室，显示错误提示
      console.error('未找到科室ID对应的子科室:', this.departmentId)
      this.subDepartments = []
    }
    
    // 最终调试信息
    console.log('最终加载的子科室:', this.subDepartments)
  },
  methods: {
    selectSubDepartment(subDept) {
      // 妇产科：不论妇科/产科都先弹温馨提醒
      if (this.departmentId === 9) {
        this.pendingSubDept = subDept
        this.showPregnancyTip = true
        return
      }

      // 生殖医学、儿科、变态反应（过敏）科、皮肤科、精神科卫生科、中医科、麻醉科、医学影像科、疼痛科、全科医疗科、康复医学科、病理科、营养科、临床药学、专科护理、高压氧、资深专家门诊的主科室点击处理
      if ((this.departmentId === 10 || this.departmentId === 11 || this.departmentId === 12 || this.departmentId === 13 || this.departmentId === 14 || this.departmentId === 15 || this.departmentId === 16 || this.departmentId === 17 || this.departmentId === 18 || this.departmentId === 20 || this.departmentId === 21 || this.departmentId === 22 || this.departmentId === 23 || this.departmentId === 24 || this.departmentId === 25 || this.departmentId === 26 || this.departmentId === 27) && subDept.id === 0 && !this.mainDepartmentClicked) {
        // 第一次点击主科室，显示实际的子科室
        this.mainDepartmentClicked = true
        this.showMainDepartment = false

        if (this.departmentId === 10) {
          // 生殖医学的实际子科室
          this.subDepartments = [
            { id: 1, name: '生殖医学门诊', icon: '👶' },
            { id: 2, name: '生殖男科门诊', icon: '👨' },
            { id: 3, name: '遗传咨询（生殖）专科门诊', icon: '🧬' }
          ]
        } else if (this.departmentId === 11) {
          // 儿科的实际子科室
          this.subDepartments = [
            { id: 1, name: '儿内科门诊', icon: '🧒' },
            { id: 2, name: '儿童生长发育门诊', icon: '📏' },
            { id: 3, name: '儿童骨龄测评门诊', icon: '🦴' },
            { id: 4, name: '儿童呼吸/过敏门诊', icon: '🫁' },
            { id: 5, name: '儿童哮喘/咳嗽门诊', icon: '🫁' },
            { id: 6, name: '儿童脱敏专科门诊', icon: '💉' },
            { id: 7, name: '儿童消化专科门诊', icon: '🫁' },
            { id: 8, name: '儿童肥胖专科门诊', icon: '⚖️' },
            { id: 9, name: '儿童保健门诊', icon: '🏥' },
            { id: 10, name: '儿童保健/高危儿保健门诊', icon: '🍼' },
            { id: 11, name: '教学门诊/儿内科', icon: '📚' },
            { id: 12, name: '儿童糖尿病门诊', icon: '💉' },
            { id: 13, name: '儿童临床研究随访专科门诊', icon: '🔬' },
            { id: 14, name: '儿童遗尿症肾脏病专科门诊', icon: '🩺' },
            { id: 15, name: '儿童遗传病/罕见病门诊', icon: '🧬' }
          ]
        } else if (this.departmentId === 12) {
          // 变态反应（过敏）科的实际子科室
          this.subDepartments = [
            { id: 1, name: '变态反应（过敏）科门诊', icon: '🤧' },
            { id: 2, name: '猫毛过敏症专科门诊', icon: '🐱' }
          ]
        } else if (this.departmentId === 13) {
          // 皮肤科的实际子科室
          this.subDepartments = [
            { id: 1, name: '皮肤科门诊', icon: '🧴' }
          ]
        } else if (this.departmentId === 14) {
          // 精神科卫生科的实际子科室
          this.subDepartments = [
            { id: 1, name: '精神卫生科门诊', icon: '🧠' },
            { id: 2, name: '睡眠障碍门诊', icon: '😴' },
            { id: 3, name: '注意缺陷多动障碍专科门诊', icon: '🎯' },
            { id: 4, name: '抑郁障碍研究型门诊', icon: '💙' }
          ]
        } else if (this.departmentId === 15) {
          // 中医科的实际子科室
          this.subDepartments = [
            { id: 1, name: '中医科门诊', icon: '🌿' },
            { id: 2, name: '中医妇科专科门诊', icon: '👩' },
            { id: 3, name: '中医儿科门诊', icon: '🧒' },
            { id: 4, name: '中医针灸专科门诊', icon: '💉' },
            { id: 5, name: '中医体重管理专科门诊', icon: '⚖️' },
            { id: 6, name: '中医脾胃病专科门诊', icon: '🫁' }
          ]
        } else if (this.departmentId === 16) {
          // 麻醉科的实际子科室
          this.subDepartments = [
            { id: 1, name: '麻醉科门诊', icon: '💉' }
          ]
        } else if (this.departmentId === 17) {
          // 医学影像科的实际子科室
          this.subDepartments = [
            { id: 1, name: '放射科', icon: '📷' },
            { id: 2, name: '超声医学', icon: '🔊' },
            { id: 3, name: '核医学科', icon: '☢️' }
          ]
        } else if (this.departmentId === 18) {
          // 疼痛科的实际子科室
          this.subDepartments = [
            { id: 1, name: '疼痛科门诊', icon: '😣' },
            { id: 2, name: '带状疱疹神经痛专科门诊', icon: '🦠' },
            { id: 3, name: '头面痛专科门诊', icon: '😫' }
          ]
        } else if (this.departmentId === 20) {
          // 全科医疗科的实际子科室
          this.subDepartments = [
            { id: 1, name: '全科医学科门诊', icon: '🏥' },
            { id: 2, name: '水肿专科门诊', icon: '💧' },
            { id: 3, name: '全科未分化疾病专科门诊', icon: '🧩' }
          ]
        } else if (this.departmentId === 26) {
          // 高压氧的实际子科室
          this.subDepartments = [
            { id: 1, name: '高压氧科门诊', icon: '💨' }
          ]
        } else if (this.departmentId === 25) {
          // 专科护理的实际子科室
          this.subDepartments = [
            { id: 1, name: '静脉置管护理门诊', icon: '💉' },
            { id: 2, name: '造口、慢性伤口护理门诊', icon: '🩹' },
            { id: 3, name: '淋巴水肿护理门诊', icon: '💧' }
          ]
        } else if (this.departmentId === 24) {
          // 临床药学的实际子科室
          this.subDepartments = [
            { id: 1, name: '药学门诊', icon: '💊' },
            { id: 2, name: '妊娠哺乳期用药专科门诊', icon: '🤱' }
          ]
        } else if (this.departmentId === 23) {
          // 营养科的实际子科室
          this.subDepartments = [
            { id: 1, name: '营养科门诊', icon: '🥗' },
            { id: 2, name: '围孕期营养门诊', icon: '🤰' },
            { id: 3, name: '营养减肥门诊', icon: '⚖️' },
            { id: 4, name: '体重管理（营养）门诊', icon: '📊' }
          ]
        } else if (this.departmentId === 22) {
          // 病理科的实际子科室
          this.subDepartments = [
            { id: 1, name: '病理科门诊', icon: '🔬' }
          ]
        } else if (this.departmentId === 21) {
          // 康复医学科的实际子科室
          this.subDepartments = [
            { id: 1, name: '康复医学科门诊', icon: '🔄' },
            { id: 2, name: '运动损伤康复专科门诊', icon: '🏃' },
            { id: 3, name: '颞颌关节紊乱康复专科门诊', icon: '🦷' },
            { id: 4, name: '疼痛康复专科门诊', icon: '😣' },
            { id: 5, name: '教学门诊/康复医学科', icon: '📚' }
          ]
        } else if (this.departmentId === 27) {
          // 资深专家门诊的实际子科室
          this.subDepartments = [
            { id: 1, name: '肝胆胰外科资深专家门诊', icon: '🔪' },
            { id: 2, name: '心脏大血管外科资深专家门诊', icon: '❤️' },
            { id: 3, name: '肾脏病中心资深专家门诊', icon: '🔬' },
            { id: 4, name: '普胸外科资深专家门诊', icon: '🫁' },
            { id: 5, name: '血液科资深专家门诊', icon: '🩸' },
            { id: 6, name: '风湿免疫资深专家门诊', icon: '🦴' },
            { id: 7, name: '骨科资深专家门诊', icon: '🦴' },
            { id: 8, name: '超声医学科资深专家门诊', icon: '🔊' },
            { id: 9, name: '甲状腺外科资深专家门诊', icon: '🦋' },
            { id: 10, name: '乳腺外科资深专家门诊', icon: '💗' },
            { id: 11, name: '泌尿外科资深专家门诊', icon: '💧' },
            { id: 12, name: '消化内科资深专家门诊', icon: '🫁' },
            { id: 13, name: '神经内科资深专家门诊', icon: '🧠' },
            { id: 14, name: '心血管内科资深专家门诊', icon: '❤️' },
            { id: 15, name: '精神卫生科资深专家门诊', icon: '🧠' },
            { id: 16, name: '内分泌科资深专家门诊', icon: '⚕️' }
          ]
        }
        return
      }

      // 如果是内科的特定子科室，跳转到专科门诊选择页面
      if (this.departmentId === 1 && 
          ((subDept.id === 1 && subDept.name === '消化内科') || 
           (subDept.id === 2 && subDept.name === '心血管内科') ||
           (subDept.id === 3 && subDept.name === '呼吸内科') ||
           (subDept.id === 4 && subDept.name === '血液科') ||
           (subDept.id === 5 && subDept.name === '肾脏病') ||
           (subDept.id === 6 && subDept.name === '神经内科') ||
           (subDept.id === 7 && subDept.name === '内分泌科') ||
           (subDept.id === 8 && subDept.name === '风湿免疫科') ||
           (subDept.id === 9 && subDept.name === '老年医学科') ||
           (subDept.id === 10 && subDept.name === '普内科'))) {
        this.$router.push({
          name: 'AppointmentSpecialty',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            subDepartmentId: subDept.id,
            subDepartmentName: subDept.name
          }
        })
      } else if (this.departmentId === 2 && 
          ((subDept.id === 1 && subDept.name === '肝胆胰外科') || 
           (subDept.id === 2 && subDept.name === '胃肠外科') ||
           (subDept.id === 3 && subDept.name === '甲状腺外科') ||
           (subDept.id === 4 && subDept.name === '乳腺外科') ||
           (subDept.id === 5 && subDept.name === '肿瘤外科') ||
           (subDept.id === 6 && subDept.name === '结直肠外科') ||
           (subDept.id === 7 && subDept.name === '骨科') ||
           (subDept.id === 8 && subDept.name === '泌尿外科') ||
           (subDept.id === 9 && subDept.name === '神经外科') ||
           (subDept.id === 10 && subDept.name === '普胸外科') ||
           (subDept.id === 11 && subDept.name === '心脏大血管外科') ||
           (subDept.id === 12 && subDept.name === '血管外科'))) {
        // 如果是外科的肝胆胰外科、胃肠外科、甲状腺外科、乳腺外科、肿瘤外科、结直肠外科、骨科、泌尿外科、神经外科、普胸外科、心脏大血管外科或血管外科，跳转到专科门诊选择页面
        this.$router.push({
          name: 'AppointmentSpecialty',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            subDepartmentId: subDept.id,
            subDepartmentName: subDept.name
          }
        })
      } else if (this.departmentId === 5 &&
          ((subDept.id === 1 && subDept.name === '肿瘤内科') ||
           (subDept.id === 2 && subDept.name === '放疗科'))) {
        // 肿瘤科：子科室进入专科门诊选择页面
        this.$router.push({
          name: 'AppointmentSpecialty',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            subDepartmentId: subDept.id,
            subDepartmentName: subDept.name
          }
        })
      } else if (this.departmentId === 8) {
        // 口腔科：子科室进入专科门诊选择页面
        this.$router.push({
          name: 'AppointmentSpecialty',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            subDepartmentId: subDept.id,
            subDepartmentName: subDept.name
          }
        })
      } else if (this.departmentId === 19) {
        // 医疗美容科：子科室（整形外科/整形美容）进入专科门诊选择页面
        this.$router.push({
          name: 'AppointmentSpecialty',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            subDepartmentId: subDept.id,
            subDepartmentName: subDept.name
          }
        })
      } else if (this.departmentId === 10) {
        // 生殖医学：直接进入医生选择页面
        this.$router.push({
          name: 'AppointmentDoctor',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            subDepartmentId: subDept.id,
            subDepartmentName: subDept.name,
            specialtyId: subDept.id,
            specialtyName: subDept.name
          }
        })
      } else if (this.departmentId === 11) {
        // 儿科：直接进入医生选择页面
        this.$router.push({
          name: 'AppointmentDoctor',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            subDepartmentId: subDept.id,
            subDepartmentName: subDept.name,
            specialtyId: subDept.id,
            specialtyName: subDept.name
          }
        })
      } else if (this.departmentId === 12) {
        // 变态反应（过敏）科：直接进入医生选择页面
        this.$router.push({
          name: 'AppointmentDoctor',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            subDepartmentId: subDept.id,
            subDepartmentName: subDept.name,
            specialtyId: subDept.id,
            specialtyName: subDept.name
          }
        })
      } else if (this.departmentId === 13 || this.departmentId === 14 || this.departmentId === 15 || this.departmentId === 16 || this.departmentId === 18 || this.departmentId === 20 || this.departmentId === 21 || this.departmentId === 22 || this.departmentId === 23 || this.departmentId === 24 || this.departmentId === 25 || this.departmentId === 26 || this.departmentId === 27) {
        // 皮肤科、精神科卫生科、中医科、麻醉科、疼痛科、全科医疗科、康复医学科、病理科、营养科、临床药学、专科护理、高压氧、资深专家门诊：直接进入医生选择页面（专科键使用 departmentId*1000+子科室ID 避免与内科ID冲突）
        this.$router.push({
          name: 'AppointmentDoctor',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            subDepartmentId: subDept.id,
            subDepartmentName: subDept.name,
            specialtyId: this.departmentId * 1000 + subDept.id,
            specialtyName: subDept.name
          }
        })
      } else if (this.departmentId === 17) {
        // 医学影像科：子科室（放射科、超声医学、核医学科）跳转到专科门诊选择页面
        this.$router.push({
          name: 'AppointmentSpecialty',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            subDepartmentId: subDept.id,
            subDepartmentName: subDept.name
          }
        })
      } else {
        // 其他科室直接跳转到医生选择页面
        this.$router.push({
          name: 'AppointmentDoctor',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            subDepartmentId: subDept.id,
            subDepartmentName: subDept.name
          }
        })
      }
    },

    confirmPregnancyTip() {
      const subDept = this.pendingSubDept
      this.showPregnancyTip = false
      this.pendingSubDept = null
      if (!subDept) return

      // 妇产科：进入专科门诊选择页（妇科/产科进一步细分）
      this.$router.push({
        name: 'AppointmentSpecialty',
        query: {
          departmentId: this.departmentId,
          departmentName: this.departmentName,
          subDepartmentId: subDept.id,
          subDepartmentName: subDept.name
        }
      })
    },

    cancelPregnancyTip() {
      this.showPregnancyTip = false
      this.pendingSubDept = null
    },
    
    goBack() {
      // 如果是生殖医学、儿科、变态反应（过敏）科、皮肤科、精神科卫生科、中医科、麻醉科、疼痛科、全科医疗科、康复医学科、病理科、营养科、临床药学、专科护理、高压氧、资深专家门诊且已经点击了主科室，返回到主科室显示
      if ((this.departmentId === 10 || this.departmentId === 11 || this.departmentId === 12 || this.departmentId === 13 || this.departmentId === 14 || this.departmentId === 15 || this.departmentId === 16 || this.departmentId === 18 || this.departmentId === 20 || this.departmentId === 21 || this.departmentId === 22 || this.departmentId === 23 || this.departmentId === 24 || this.departmentId === 25 || this.departmentId === 26 || this.departmentId === 27) && this.mainDepartmentClicked) {
        this.mainDepartmentClicked = false
        this.showMainDepartment = true

        if (this.departmentId === 10) {
          this.subDepartments = [{ id: 0, name: '生殖医学', icon: '👶' }]
        } else if (this.departmentId === 11) {
          this.subDepartments = [{ id: 0, name: '儿科', icon: '🧒' }]
        } else if (this.departmentId === 12) {
          this.subDepartments = [{ id: 0, name: '变态反应（过敏）科', icon: '🤧' }]
        } else if (this.departmentId === 13) {
          this.subDepartments = [{ id: 0, name: '皮肤科', icon: '🧴' }]
        } else if (this.departmentId === 14) {
          this.subDepartments = [{ id: 0, name: '精神科卫生科', icon: '🧠' }]
        } else if (this.departmentId === 15) {
          this.subDepartments = [{ id: 0, name: '中医科', icon: '🌿' }]
        } else if (this.departmentId === 16) {
          this.subDepartments = [{ id: 0, name: '麻醉科', icon: '💉' }]
        } else if (this.departmentId === 17) {
          this.subDepartments = [{ id: 0, name: '医学影像科', icon: '📷' }]
        } else if (this.departmentId === 18) {
          this.subDepartments = [{ id: 0, name: '疼痛科', icon: '😣' }]
        } else if (this.departmentId === 20) {
          this.subDepartments = [{ id: 0, name: '全科医疗科', icon: '🏥' }]
        } else if (this.departmentId === 26) {
          this.subDepartments = [{ id: 0, name: '高压氧', icon: '💨' }]
        } else if (this.departmentId === 25) {
          this.subDepartments = [{ id: 0, name: '门诊护理', icon: '💊' }]
        } else if (this.departmentId === 24) {
          this.subDepartments = [{ id: 0, name: '临床药学', icon: '💊' }]
        } else if (this.departmentId === 23) {
          this.subDepartments = [{ id: 0, name: '营养科', icon: '🥗' }]
        } else if (this.departmentId === 22) {
          this.subDepartments = [{ id: 0, name: '病理科', icon: '🔬' }]
        } else if (this.departmentId === 21) {
          this.subDepartments = [{ id: 0, name: '康复医学科', icon: '🔄' }]
        } else if (this.departmentId === 27) {
          this.subDepartments = [{ id: 0, name: '资深专家门诊', icon: '👨‍⚕️' }]
        }
        return
      }

      this.$router.push({
        name: 'Appointment',
        query: { fromBack: 'true' } // 标记是从其他页面返回的
      })
    }
  }
}
</script>

<style scoped>
.appointment-subdepartment {
  max-width: 1000px;
  margin: 0 auto;
}

/* 温馨提示弹窗样式（复用挂号页同名样式风格） */
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
}

.tip-modal-content {
  background: white;
  border-radius: 15px;
  width: 90%;
  max-width: 520px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.tip-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.2rem 1.5rem;
  border-bottom: 2px solid #f0f0f0;
}

.tip-modal-header h2 {
  margin: 0;
  color: #667eea;
  font-size: 1.3rem;
}

.tip-close-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #999;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
  border-radius: 6px;
}

.tip-close-btn:hover {
  background: #f0f0f0;
  color: #667eea;
}

.tip-modal-body {
  padding: 1.5rem;
}

.tip-content {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 1rem 1.2rem;
}

.tip-modal-footer {
  padding: 1.2rem 1.5rem;
  border-top: 2px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
}

.tip-confirm-btn {
  padding: 0.8rem 1.4rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
}

.tip-confirm-btn:hover {
  opacity: 0.92;
}

.header-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.back-btn {
  padding: 0.5rem 1rem;
  background: white;
  border: 2px solid #667eea;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  color: #667eea;
  transition: all 0.3s;
}

.back-btn:hover {
  background: #667eea;
  color: white;
}

.page-title {
  color: white;
  font-size: 2rem;
  margin: 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.subdepartment-form {
  background: white;
  border-radius: 15px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.form-section h2 {
  color: #667eea;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
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
</style>
