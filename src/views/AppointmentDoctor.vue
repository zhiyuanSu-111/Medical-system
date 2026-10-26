<template>
  <div class="appointment-doctor">
    <div class="appointment-container">
      <div class="header-section">
        <button @click="goBack" class="back-btn">← 返回</button>
        <h1 class="page-title">{{ displayTitle }} - 选择医生</h1>
      </div>
      
      <div class="appointment-form">
        <!-- 时间选择（放在上方） -->
        <div class="form-section">
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
                  :class="['time-slot', { 
                    active: selectedTimeSlot === slot,
                    disabled: getSlotAvailability(slot) === 0
                  }]"
                  :title="getSlotAvailability(slot) === 0 ? '该时段号源已满' : (getSlotAvailability(slot) !== null ? `剩余${getSlotAvailability(slot)}个号源` : '号源信息加载中...')"
                >
                  <div class="slot-time">{{ slot }}</div>
                  <div class="slot-count" v-if="slotAvailability[slot] !== undefined && slotAvailability[slot] !== null">
                    <span v-if="slotAvailability[slot] > 0" class="available-count">剩余{{ slotAvailability[slot] }}</span>
                    <span v-else-if="slotAvailability[slot] === 0" class="full-count">已满</span>
                  </div>
                  <div class="slot-count" v-else-if="loadingSlots">
                    <span class="loading-count">加载中...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 医生列表 -->
        <div class="form-section">
          <h2>选择医生</h2>
          <div v-if="loadingDoctors" class="no-doctors">
            <p>正在加载医生信息...</p>
          </div>
          <div v-else-if="doctors.length === 0" class="no-doctors">
            <p>{{ doctorsLoadError || '当前条件下暂无可挂号医生，请返回上一页重试。' }}</p>
          </div>
          <div v-else class="doctor-list">
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
                <div class="quota-line" v-if="doctorQuotas[doctor.id]">
                  <span class="quota-remaining">剩余号源：{{ doctorQuotas[doctor.id].remaining }}</span>
                  <span class="quota-total">/ 共 {{ doctorQuotas[doctor.id].total }}</span>
              </div>
                <div class="quota-line pending" v-else>
                  <span>号源加载中...</span>
                </div>
                <span 
                  class="level-tag"
                  :class="{ expert: isExpertDoctor(doctor), normal: !isExpertDoctor(doctor) }"
                >
                  {{ isExpertDoctor(doctor) ? '专家号' : '普通号' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 就诊人选择 -->
        <div class="form-section">
          <div class="section-header">
            <h2>选择就诊人</h2>
            <button class="mini-btn" @click="goToPatientManager">管理就诊人</button>
          </div>
          <div v-if="patients.length === 0" class="no-patient">
            <p>尚未添加就诊人，请先添加。</p>
            <button class="primary-btn" @click="goToPatientManager">立即添加</button>
          </div>
          <div v-else class="patient-grid">
            <div 
              v-for="person in patients"
              :key="person.id"
              @click="selectPatient(person.id)"
              :class="['patient-card', { active: selectedPatientId === person.id }]"
            >
              <div class="patient-name">{{ person.name }}</div>
              <div class="patient-meta">手机号：{{ person.phone }}</div>
              <div class="patient-meta">身份证：{{ person.idCard }}</div>
            </div>
          </div>
        </div>

        <!-- 提交按钮 -->
        <div v-if="canSubmit" class="submit-section">
          <button @click="confirmAppointment" class="next-btn">确认预约</button>
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
  name: 'AppointmentDoctor',
  data() {
    return {
      departmentId: null,
      departmentName: '',
      subDepartmentId: null,
      subDepartmentName: '',
      specialtyId: null,
      specialtyName: '',
      doctors: [],
      loadingDoctors: true,
      doctorsLoadError: '',
      selectedDoctor: null,
      selectedDate: '',
      selectedYear: null,
      selectedMonth: null,
      selectedDay: null,
      selectedTimeSlot: '',
      patients: [],
      selectedPatientId: null,
      timeSlots: [
        '08:00-12:00',
        '14:00-18:00'
      ],
      slotAvailability: {}, // 存储每个时段的号源数量 { '08:00-09:00': 5, ... }
      loadingSlots: false, // 是否正在加载号源
      doctorQuotas: {}, // 每个医生在当前日期的号源总数和剩余数 { [doctorId]: { total, remaining } }
      message: {
        show: false,
        text: '',
        type: 'success' // success, error, warning
      },
      // 各子科室的医生数据
      subDepartmentDoctors: {
        1: [ // 消化内科
          { id: 100101, name: '张明', title: '主任医师', specialty: '消化内科' },
          { id: 100102, name: '李华', title: '副主任医师', specialty: '消化内科' },
          { id: 100103, name: '王强', title: '主治医师', specialty: '消化内科' },
          { id: 100104, name: '赵敏', title: '主任医师', specialty: '消化内科' }
        ],
        2: [ // 心血管内科
          { id: 100105, name: '陈建国', title: '主任医师', specialty: '心血管内科' },
          { id: 100106, name: '刘芳', title: '副主任医师', specialty: '心血管内科' },
          { id: 100107, name: '周伟', title: '主治医师', specialty: '心血管内科' },
          { id: 100108, name: '吴丽', title: '主任医师', specialty: '心血管内科' },
          { id: 100109, name: '郑强', title: '副主任医师', specialty: '心血管内科' }
        ],
        3: [ // 呼吸内科
          { id: 100110, name: '孙立', title: '主任医师', specialty: '呼吸内科' },
          { id: 100111, name: '马静', title: '副主任医师', specialty: '呼吸内科' },
          { id: 100112, name: '钱勇', title: '主治医师', specialty: '呼吸内科' }
        ],
        4: [ // 血液科
          { id: 100113, name: '冯军', title: '主任医师', specialty: '血液科' },
          { id: 100114, name: '韩梅', title: '副主任医师', specialty: '血液科' },
          { id: 100115, name: '杨波', title: '主治医师', specialty: '血液科' }
        ],
        5: [ // 肾脏病
          { id: 100116, name: '朱文', title: '主任医师', specialty: '肾脏病' },
          { id: 100117, name: '林雪', title: '副主任医师', specialty: '肾脏病' },
          { id: 100118, name: '何刚', title: '主治医师', specialty: '肾脏病' },
          { id: 100119, name: '罗敏', title: '主任医师', specialty: '肾脏病' }
        ],
        6: [ // 神经内科
          { id: 100120, name: '徐亮', title: '主任医师', specialty: '神经内科' },
          { id: 100121, name: '高红', title: '副主任医师', specialty: '神经内科' },
          { id: 100122, name: '谢军', title: '主治医师', specialty: '神经内科' },
          { id: 100123, name: '唐丽', title: '主任医师', specialty: '神经内科' }
        ],
        7: [ // 内分泌科
          { id: 100124, name: '邓强', title: '主任医师', specialty: '内分泌科' },
          { id: 100125, name: '许静', title: '副主任医师', specialty: '内分泌科' },
          { id: 100126, name: '曹勇', title: '主治医师', specialty: '内分泌科' }
        ],
        8: [ // 风湿免疫科
          { id: 100127, name: '袁文', title: '主任医师', specialty: '风湿免疫科' },
          { id: 100128, name: '田梅', title: '副主任医师', specialty: '风湿免疫科' },
          { id: 100129, name: '宋刚', title: '主治医师', specialty: '风湿免疫科' }
        ],
        9: [ // 老年医学科
          { id: 100130, name: '潘明', title: '主任医师', specialty: '老年医学科' },
          { id: 100131, name: '方丽', title: '副主任医师', specialty: '老年医学科' },
          { id: 100132, name: '石强', title: '主治医师', specialty: '老年医学科' },
          { id: 100133, name: '姚静', title: '主任医师', specialty: '老年医学科' }
        ],
        10: [ // 普内科
          { id: 100134, name: '胡军', title: '主任医师', specialty: '普内科' },
          { id: 100135, name: '范红', title: '副主任医师', specialty: '普内科' },
          { id: 100136, name: '卢勇', title: '主治医师', specialty: '普内科' }
        ],
        // 外科子科室的医生数据（使用 departmentId * 100 + subDepartmentId 作为键）
        201: [ // 肝胆胰外科 (departmentId=2, subDepartmentId=1)
          { id: 100201, name: '王医生', title: '主任医师', specialty: '肝胆胰外科' },
          { id: 100202, name: '李医生', title: '副主任医师', specialty: '肝胆胰外科' },
          { id: 100203, name: '张医生', title: '主治医师', specialty: '肝胆胰外科' },
          { id: 100204, name: '刘医生', title: '主任医师', specialty: '肝胆胰外科' }
        ],
        202: [ // 胃肠外科 (departmentId=2, subDepartmentId=2)
          { id: 100205, name: '陈医生', title: '主任医师', specialty: '胃肠外科' },
          { id: 100206, name: '周医生', title: '副主任医师', specialty: '胃肠外科' },
          { id: 100207, name: '吴医生', title: '主治医师', specialty: '胃肠外科' }
        ],
        203: [ // 甲状腺外科 (departmentId=2, subDepartmentId=3)
          { id: 100208, name: '郑医生', title: '主任医师', specialty: '甲状腺外科' },
          { id: 100209, name: '孙医生', title: '副主任医师', specialty: '甲状腺外科' },
          { id: 100210, name: '马医生', title: '主治医师', specialty: '甲状腺外科' }
        ],
        204: [ // 乳腺外科 (departmentId=2, subDepartmentId=4)
          { id: 100211, name: '钱医生', title: '主任医师', specialty: '乳腺外科' },
          { id: 100212, name: '冯医生', title: '副主任医师', specialty: '乳腺外科' },
          { id: 100213, name: '韩医生', title: '主治医师', specialty: '乳腺外科' },
          { id: 100214, name: '杨医生', title: '主任医师', specialty: '乳腺外科' }
        ],
        205: [ // 肿瘤外科 (departmentId=2, subDepartmentId=5)
          { id: 100215, name: '朱医生', title: '主任医师', specialty: '肿瘤外科' },
          { id: 100216, name: '林医生', title: '副主任医师', specialty: '肿瘤外科' },
          { id: 100217, name: '何医生', title: '主治医师', specialty: '肿瘤外科' }
        ],
        206: [ // 结直肠外科 (departmentId=2, subDepartmentId=6)
          { id: 100218, name: '罗医生', title: '主任医师', specialty: '结直肠外科' },
          { id: 100219, name: '徐医生', title: '副主任医师', specialty: '结直肠外科' },
          { id: 100220, name: '高医生', title: '主治医师', specialty: '结直肠外科' }
        ],
        207: [ // 骨科 (departmentId=2, subDepartmentId=7)
          { id: 100221, name: '谢医生', title: '主任医师', specialty: '骨科' },
          { id: 100222, name: '唐医生', title: '副主任医师', specialty: '骨科' },
          { id: 100223, name: '邓医生', title: '主治医师', specialty: '骨科' },
          { id: 100224, name: '许医生', title: '主任医师', specialty: '骨科' }
        ],
        208: [ // 泌尿外科 (departmentId=2, subDepartmentId=8)
          { id: 100225, name: '曹医生', title: '主任医师', specialty: '泌尿外科' },
          { id: 100226, name: '袁医生', title: '副主任医师', specialty: '泌尿外科' },
          { id: 100227, name: '田医生', title: '主治医师', specialty: '泌尿外科' }
        ],
        10001: [ // 生殖医学门诊
          { id: 101001, name: '王主任', title: '主任医师', specialty: '生殖医学门诊' },
          { id: 101002, name: '李医生', title: '副主任医师', specialty: '生殖医学门诊' },
          { id: 101003, name: '张医生', title: '主治医师', specialty: '生殖医学门诊' }
        ],
        10002: [ // 生殖男科门诊
          { id: 101004, name: '陈主任', title: '主任医师', specialty: '生殖男科门诊' },
          { id: 101005, name: '刘医生', title: '副主任医师', specialty: '生殖男科门诊' },
          { id: 101006, name: '周医生', title: '主治医师', specialty: '生殖男科门诊' }
        ],
        10003: [ // 遗传咨询（生殖）专科门诊
          { id: 101007, name: '赵主任', title: '主任医师', specialty: '遗传咨询（生殖）专科门诊' },
          { id: 101008, name: '孙医生', title: '副主任医师', specialty: '遗传咨询（生殖）专科门诊' },
          { id: 101009, name: '马医生', title: '主治医师', specialty: '遗传咨询（生殖）专科门诊' }
        ],
        // 儿科子科室的医生数据
        11001: [ // 儿内科门诊
          { id: 101101, name: '郑主任', title: '主任医师', specialty: '儿内科门诊' },
          { id: 101102, name: '钱医生', title: '副主任医师', specialty: '儿内科门诊' },
          { id: 101103, name: '冯医生', title: '主治医师', specialty: '儿内科门诊' }
        ],
        11002: [ // 儿童生长发育门诊
          { id: 101104, name: '韩主任', title: '主任医师', specialty: '儿童生长发育门诊' },
          { id: 101105, name: '杨医生', title: '副主任医师', specialty: '儿童生长发育门诊' },
          { id: 101106, name: '朱医生', title: '主治医师', specialty: '儿童生长发育门诊' }
        ],
        11003: [ // 儿童骨龄测评门诊
          { id: 101107, name: '林主任', title: '主任医师', specialty: '儿童骨龄测评门诊' },
          { id: 101108, name: '何医生', title: '副主任医师', specialty: '儿童骨龄测评门诊' },
          { id: 101109, name: '罗医生', title: '主治医师', specialty: '儿童骨龄测评门诊' }
        ],
        11004: [ // 儿童呼吸/过敏门诊
          { id: 101110, name: '徐主任', title: '主任医师', specialty: '儿童呼吸/过敏门诊' },
          { id: 101111, name: '高医生', title: '副主任医师', specialty: '儿童呼吸/过敏门诊' },
          { id: 101112, name: '谢医生', title: '主治医师', specialty: '儿童呼吸/过敏门诊' }
        ],
        11005: [ // 儿童哮喘/咳嗽门诊
          { id: 101113, name: '唐主任', title: '主任医师', specialty: '儿童哮喘/咳嗽门诊' },
          { id: 101114, name: '邓医生', title: '副主任医师', specialty: '儿童哮喘/咳嗽门诊' },
          { id: 101115, name: '许医生', title: '主治医师', specialty: '儿童哮喘/咳嗽门诊' }
        ],
        11006: [ // 儿童脱敏专科门诊
          { id: 101116, name: '曹主任', title: '主任医师', specialty: '儿童脱敏专科门诊' },
          { id: 101117, name: '袁医生', title: '副主任医师', specialty: '儿童脱敏专科门诊' },
          { id: 101118, name: '田医生', title: '主治医师', specialty: '儿童脱敏专科门诊' }
        ],
        11007: [ // 儿童消化专科门诊
          { id: 101119, name: '宋主任', title: '主任医师', specialty: '儿童消化专科门诊' },
          { id: 101120, name: '潘医生', title: '副主任医师', specialty: '儿童消化专科门诊' },
          { id: 101121, name: '方医生', title: '主治医师', specialty: '儿童消化专科门诊' }
        ],
        11008: [ // 儿童肥胖专科门诊
          { id: 101122, name: '石主任', title: '主任医师', specialty: '儿童肥胖专科门诊' },
          { id: 101123, name: '姚医生', title: '副主任医师', specialty: '儿童肥胖专科门诊' },
          { id: 101124, name: '胡医生', title: '主治医师', specialty: '儿童肥胖专科门诊' }
        ],
        11009: [ // 儿童保健门诊
          { id: 101125, name: '范主任', title: '主任医师', specialty: '儿童保健门诊' },
          { id: 101126, name: '卢医生', title: '副主任医师', specialty: '儿童保健门诊' },
          { id: 101127, name: '王医生', title: '主治医师', specialty: '儿童保健门诊' }
        ],
        11010: [ // 儿童保健/高危儿保健门诊
          { id: 101128, name: '李主任', title: '主任医师', specialty: '儿童保健/高危儿保健门诊' },
          { id: 101129, name: '张医生', title: '副主任医师', specialty: '儿童保健/高危儿保健门诊' },
          { id: 101130, name: '刘医生', title: '主治医师', specialty: '儿童保健/高危儿保健门诊' }
        ],
        11011: [ // 教学门诊/儿内科
          { id: 101131, name: '陈主任', title: '主任医师', specialty: '教学门诊/儿内科' },
          { id: 101132, name: '周医生', title: '副主任医师', specialty: '教学门诊/儿内科' },
          { id: 101133, name: '吴医生', title: '主治医师', specialty: '教学门诊/儿内科' }
        ],
        11012: [ // 儿童糖尿病门诊
          { id: 101134, name: '郑主任', title: '主任医师', specialty: '儿童糖尿病门诊' },
          { id: 101135, name: '钱医生', title: '副主任医师', specialty: '儿童糖尿病门诊' },
          { id: 101136, name: '冯医生', title: '主治医师', specialty: '儿童糖尿病门诊' }
        ],
        11013: [ // 儿童临床研究随访专科门诊
          { id: 101137, name: '韩主任', title: '主任医师', specialty: '儿童临床研究随访专科门诊' },
          { id: 101138, name: '杨医生', title: '副主任医师', specialty: '儿童临床研究随访专科门诊' },
          { id: 101139, name: '朱医生', title: '主治医师', specialty: '儿童临床研究随访专科门诊' }
        ],
        11014: [ // 儿童遗尿症肾脏病专科门诊
          { id: 101140, name: '林主任', title: '主任医师', specialty: '儿童遗尿症肾脏病专科门诊' },
          { id: 101141, name: '何医生', title: '副主任医师', specialty: '儿童遗尿症肾脏病专科门诊' },
          { id: 101142, name: '罗医生', title: '主治医师', specialty: '儿童遗尿症肾脏病专科门诊' }
        ],
        11015: [ // 儿童遗传病/罕见病门诊
          { id: 101143, name: '徐主任', title: '主任医师', specialty: '儿童遗传病/罕见病门诊' },
          { id: 101144, name: '高医生', title: '副主任医师', specialty: '儿童遗传病/罕见病门诊' },
          { id: 101145, name: '谢医生', title: '主治医师', specialty: '儿童遗传病/罕见病门诊' }
        ],
        // 变态反应（过敏）科子科室的医生数据
        12001: [ // 变态反应（过敏）科门诊
          { id: 101201, name: '唐主任', title: '主任医师', specialty: '变态反应（过敏）科门诊' },
          { id: 101202, name: '邓医生', title: '副主任医师', specialty: '变态反应（过敏）科门诊' },
          { id: 101203, name: '许医生', title: '主治医师', specialty: '变态反应（过敏）科门诊' }
        ],
        12002: [ // 猫毛过敏症专科门诊
          { id: 101204, name: '曹主任', title: '主任医师', specialty: '猫毛过敏症专科门诊' },
          { id: 101205, name: '袁医生', title: '副主任医师', specialty: '猫毛过敏症专科门诊' },
          { id: 101206, name: '田医生', title: '主治医师', specialty: '猫毛过敏症专科门诊' }
        ],
        13001: [ // 皮肤科门诊 (departmentId=13, subDepartmentId=1)
          { id: 101301, name: '张主任', title: '主任医师', specialty: '皮肤科门诊' },
          { id: 101302, name: '李医生', title: '副主任医师', specialty: '皮肤科门诊' },
          { id: 101303, name: '王医生', title: '主治医师', specialty: '皮肤科门诊' }
        ],
        // 精神科卫生科子科室的医生数据
        14001: [ // 精神卫生科门诊 (departmentId=14, subDepartmentId=1)
          { id: 101401, name: '陈主任', title: '主任医师', specialty: '精神卫生科门诊' },
          { id: 101402, name: '刘医生', title: '副主任医师', specialty: '精神卫生科门诊' },
          { id: 101403, name: '周医生', title: '主治医师', specialty: '精神卫生科门诊' }
        ],
        14002: [ // 睡眠障碍门诊 (departmentId=14, subDepartmentId=2)
          { id: 101404, name: '吴主任', title: '主任医师', specialty: '睡眠障碍门诊' },
          { id: 101405, name: '郑医生', title: '副主任医师', specialty: '睡眠障碍门诊' },
          { id: 101406, name: '钱医生', title: '主治医师', specialty: '睡眠障碍门诊' }
        ],
        14003: [ // 注意缺陷多动障碍专科门诊 (departmentId=14, subDepartmentId=3)
          { id: 101407, name: '冯主任', title: '主任医师', specialty: '注意缺陷多动障碍专科门诊' },
          { id: 101408, name: '韩医生', title: '副主任医师', specialty: '注意缺陷多动障碍专科门诊' },
          { id: 101409, name: '杨医生', title: '主治医师', specialty: '注意缺陷多动障碍专科门诊' }
        ],
        14004: [ // 抑郁障碍研究型门诊 (departmentId=14, subDepartmentId=4)
          { id: 101410, name: '朱主任', title: '主任医师', specialty: '抑郁障碍研究型门诊' },
          { id: 101411, name: '林医生', title: '副主任医师', specialty: '抑郁障碍研究型门诊' },
          { id: 101412, name: '何医生', title: '主治医师', specialty: '抑郁障碍研究型门诊' }
        ],
        209: [ // 神经外科 (departmentId=2, subDepartmentId=9)
          { id: 100228, name: '宋医生', title: '主任医师', specialty: '神经外科' },
          { id: 100229, name: '潘医生', title: '副主任医师', specialty: '神经外科' },
          { id: 100230, name: '方医生', title: '主治医师', specialty: '神经外科' },
          { id: 100231, name: '石医生', title: '主任医师', specialty: '神经外科' }
        ],
        210: [ // 普胸外科 (departmentId=2, subDepartmentId=10)
          { id: 100232, name: '姚医生', title: '主任医师', specialty: '普胸外科' },
          { id: 100233, name: '胡医生', title: '副主任医师', specialty: '普胸外科' },
          { id: 100234, name: '范医生', title: '主治医师', specialty: '普胸外科' }
        ],
        211: [ // 心脏大血管外科 (departmentId=2, subDepartmentId=11)
          { id: 100235, name: '卢医生', title: '主任医师', specialty: '心脏大血管外科' },
          { id: 100236, name: '王医生', title: '副主任医师', specialty: '心脏大血管外科' },
          { id: 100237, name: '李医生', title: '主治医师', specialty: '心脏大血管外科' },
          { id: 100238, name: '张医生', title: '主任医师', specialty: '心脏大血管外科' }
        ],
        212: [ // 血管外科 (departmentId=2, subDepartmentId=12)
          { id: 100239, name: '刘医生', title: '主任医师', specialty: '血管外科' },
          { id: 100240, name: '陈医生', title: '副主任医师', specialty: '血管外科' },
          { id: 100241, name: '周医生', title: '主治医师', specialty: '血管外科' }
        ],
        // 中医科子科室的医生数据
        15001: [ // 中医科门诊 (departmentId=15, subDepartmentId=1)
          { id: 101501, name: '王主任', title: '主任医师', specialty: '中医科门诊' },
          { id: 101502, name: '李医生', title: '副主任医师', specialty: '中医科门诊' },
          { id: 101503, name: '张医生', title: '主治医师', specialty: '中医科门诊' }
        ],
        15002: [ // 中医妇科专科门诊 (departmentId=15, subDepartmentId=2)
          { id: 101504, name: '赵主任', title: '主任医师', specialty: '中医妇科专科门诊' },
          { id: 101505, name: '孙医生', title: '副主任医师', specialty: '中医妇科专科门诊' },
          { id: 101506, name: '周医生', title: '主治医师', specialty: '中医妇科专科门诊' }
        ],
        15003: [ // 中医儿科门诊 (departmentId=15, subDepartmentId=3)
          { id: 101507, name: '吴主任', title: '主任医师', specialty: '中医儿科门诊' },
          { id: 101508, name: '郑医生', title: '副主任医师', specialty: '中医儿科门诊' },
          { id: 101509, name: '钱医生', title: '主治医师', specialty: '中医儿科门诊' }
        ],
        15004: [ // 中医针灸专科门诊 (departmentId=15, subDepartmentId=4)
          { id: 101510, name: '冯主任', title: '主任医师', specialty: '中医针灸专科门诊' },
          { id: 101511, name: '韩医生', title: '副主任医师', specialty: '中医针灸专科门诊' },
          { id: 101512, name: '杨医生', title: '主治医师', specialty: '中医针灸专科门诊' }
        ],
        15005: [ // 中医体重管理专科门诊 (departmentId=15, subDepartmentId=5)
          { id: 101513, name: '朱主任', title: '主任医师', specialty: '中医体重管理专科门诊' },
          { id: 101514, name: '林医生', title: '副主任医师', specialty: '中医体重管理专科门诊' },
          { id: 101515, name: '何医生', title: '主治医师', specialty: '中医体重管理专科门诊' }
        ],
        15006: [ // 中医脾胃病专科门诊 (departmentId=15, subDepartmentId=6)
          { id: 101516, name: '罗主任', title: '主任医师', specialty: '中医脾胃病专科门诊' },
          { id: 101517, name: '徐医生', title: '副主任医师', specialty: '中医脾胃病专科门诊' },
          { id: 101518, name: '高医生', title: '主治医师', specialty: '中医脾胃病专科门诊' }
        ],
        // 麻醉科子科室的医生数据
        16001: [ // 麻醉科门诊 (departmentId=16, subDepartmentId=1)
          { id: 101601, name: '谢主任', title: '主任医师', specialty: '麻醉科门诊' },
          { id: 101602, name: '唐医生', title: '副主任医师', specialty: '麻醉科门诊' },
          { id: 101603, name: '邓医生', title: '主治医师', specialty: '麻醉科门诊' }
        ],
        // 医学影像科子科室的医生数据（通过specialtyId访问）
        17001: [ // 放射诊断门诊 (departmentId=17, subDepartmentId=1, specialtyId=17001)
          { id: 101701, name: '许主任', title: '主任医师', specialty: '放射诊断门诊' },
          { id: 101702, name: '曹医生', title: '副主任医师', specialty: '放射诊断门诊' },
          { id: 101703, name: '袁医生', title: '主治医师', specialty: '放射诊断门诊' }
        ],
        17002: [ // 超声医学科门诊 (departmentId=17, subDepartmentId=2, specialtyId=17002)
          { id: 101704, name: '田主任', title: '主任医师', specialty: '超声医学科门诊' },
          { id: 101705, name: '宋医生', title: '副主任医师', specialty: '超声医学科门诊' },
          { id: 101706, name: '潘医生', title: '主治医师', specialty: '超声医学科门诊' }
        ],
        17003: [ // 产科超声检查门诊 (departmentId=17, subDepartmentId=2, specialtyId=17003)
          { id: 101707, name: '方主任', title: '主任医师', specialty: '产科超声检查门诊' },
          { id: 101708, name: '石医生', title: '副主任医师', specialty: '产科超声检查门诊' },
          { id: 101709, name: '姚医生', title: '主治医师', specialty: '产科超声检查门诊' }
        ],
        17004: [ // 妇科超声检查门诊 (departmentId=17, subDepartmentId=2, specialtyId=17004)
          { id: 101710, name: '胡主任', title: '主任医师', specialty: '妇科超声检查门诊' },
          { id: 101711, name: '范医生', title: '副主任医师', specialty: '妇科超声检查门诊' },
          { id: 101712, name: '卢医生', title: '主治医师', specialty: '妇科超声检查门诊' }
        ],
        17005: [ // 核医学科门诊 (departmentId=17, subDepartmentId=3, specialtyId=17005)
          { id: 101713, name: '王主任', title: '主任医师', specialty: '核医学科门诊' },
          { id: 101714, name: '李医生', title: '副主任医师', specialty: '核医学科门诊' },
          { id: 101715, name: '张医生', title: '主治医师', specialty: '核医学科门诊' }
        ],
        // 疼痛科子科室的医生数据
        18001: [ // 疼痛科门诊 (departmentId=18, subDepartmentId=1)
          { id: 101801, name: '刘主任', title: '主任医师', specialty: '疼痛科门诊' },
          { id: 101802, name: '陈医生', title: '副主任医师', specialty: '疼痛科门诊' },
          { id: 101803, name: '周医生', title: '主治医师', specialty: '疼痛科门诊' }
        ],
        18002: [ // 带状疱疹神经痛专科门诊 (departmentId=18, subDepartmentId=2)
          { id: 101804, name: '吴主任', title: '主任医师', specialty: '带状疱疹神经痛专科门诊' },
          { id: 101805, name: '郑医生', title: '副主任医师', specialty: '带状疱疹神经痛专科门诊' },
          { id: 101806, name: '钱医生', title: '主治医师', specialty: '带状疱疹神经痛专科门诊' }
        ],
        18003: [ // 头面痛专科门诊 (departmentId=18, subDepartmentId=3)
          { id: 101807, name: '冯主任', title: '主任医师', specialty: '头面痛专科门诊' },
          { id: 101808, name: '韩医生', title: '副主任医师', specialty: '头面痛专科门诊' },
          { id: 101809, name: '杨医生', title: '主治医师', specialty: '头面痛专科门诊' }
        ],
        // 全科医疗科子科室的医生数据
        20001: [ // 全科医学科门诊 (departmentId=20, subDepartmentId=1)
          { id: 102001, name: '刘主任', title: '主任医师', specialty: '全科医学科门诊' },
          { id: 102002, name: '陈医生', title: '副主任医师', specialty: '全科医学科门诊' },
          { id: 102003, name: '周医生', title: '主治医师', specialty: '全科医学科门诊' }
        ],
        20002: [ // 水肿专科门诊 (departmentId=20, subDepartmentId=2)
          { id: 102004, name: '吴主任', title: '主任医师', specialty: '水肿专科门诊' },
          { id: 102005, name: '郑医生', title: '副主任医师', specialty: '水肿专科门诊' },
          { id: 102006, name: '钱医生', title: '主治医师', specialty: '水肿专科门诊' }
        ],
        20003: [ // 全科未分化疾病专科门诊 (departmentId=20, subDepartmentId=3)
          { id: 102007, name: '冯主任', title: '主任医师', specialty: '全科未分化疾病专科门诊' },
          { id: 102008, name: '韩医生', title: '副主任医师', specialty: '全科未分化疾病专科门诊' },
          { id: 102009, name: '杨医生', title: '主治医师', specialty: '全科未分化疾病专科门诊' }
        ],
        // 高压氧子科室的医生数据
        26001: [ // 高压氧科门诊 (departmentId=26, subDepartmentId=1)
          { id: 102601, name: '周主任', title: '主任医师', specialty: '高压氧科门诊' },
          { id: 102602, name: '吴医生', title: '副主任医师', specialty: '高压氧科门诊' },
          { id: 102603, name: '郑医生', title: '主治医师', specialty: '高压氧科门诊' }
        ],
        // 专科护理子科室的医生数据
        25001: [ // 静脉置管护理门诊 (departmentId=25, subDepartmentId=1)
          { id: 102501, name: '王护士', title: '主管护师', specialty: '静脉置管护理门诊' },
          { id: 102502, name: '李护士', title: '护师', specialty: '静脉置管护理门诊' },
          { id: 102503, name: '张护士', title: '主任护师', specialty: '静脉置管护理门诊' }
        ],
        25002: [ // 造口、慢性伤口护理门诊 (departmentId=25, subDepartmentId=2)
          { id: 102504, name: '赵护士', title: '主管护师', specialty: '造口、慢性伤口护理门诊' },
          { id: 102505, name: '孙护士', title: '护师', specialty: '造口、慢性伤口护理门诊' },
          { id: 102506, name: '周护士', title: '主任护师', specialty: '造口、慢性伤口护理门诊' }
        ],
        25003: [ // 淋巴水肿护理门诊 (departmentId=25, subDepartmentId=3)
          { id: 102507, name: '吴护士', title: '主管护师', specialty: '淋巴水肿护理门诊' },
          { id: 102508, name: '郑护士', title: '护师', specialty: '淋巴水肿护理门诊' },
          { id: 102509, name: '钱护士', title: '主任护师', specialty: '淋巴水肿护理门诊' }
        ],
        // 临床药学子科室的医生数据
        24001: [ // 药学门诊 (departmentId=24, subDepartmentId=1)
          { id: 102401, name: '刘药师', title: '主管药师', specialty: '药学门诊' },
          { id: 102402, name: '陈药师', title: '药师', specialty: '药学门诊' },
          { id: 102403, name: '周药师', title: '主任药师', specialty: '药学门诊' }
        ],
        24002: [ // 妊娠哺乳期用药专科门诊 (departmentId=24, subDepartmentId=2)
          { id: 102404, name: '吴药师', title: '主管药师', specialty: '妊娠哺乳期用药专科门诊' },
          { id: 102405, name: '郑药师', title: '药师', specialty: '妊娠哺乳期用药专科门诊' },
          { id: 102406, name: '钱药师', title: '主任药师', specialty: '妊娠哺乳期用药专科门诊' }
        ],
        // 营养科子科室的医生数据
        23001: [ // 营养科门诊 (departmentId=23, subDepartmentId=1)
          { id: 102301, name: '刘营养师', title: '主任营养师', specialty: '营养科门诊' },
          { id: 102302, name: '陈营养师', title: '副主任营养师', specialty: '营养科门诊' },
          { id: 102303, name: '周营养师', title: '营养师', specialty: '营养科门诊' }
        ],
        23002: [ // 围孕期营养门诊 (departmentId=23, subDepartmentId=2)
          { id: 102304, name: '吴营养师', title: '主任营养师', specialty: '围孕期营养门诊' },
          { id: 102305, name: '郑营养师', title: '副主任营养师', specialty: '围孕期营养门诊' },
          { id: 102306, name: '钱营养师', title: '营养师', specialty: '围孕期营养门诊' }
        ],
        23003: [ // 营养减肥门诊 (departmentId=23, subDepartmentId=3)
          { id: 102307, name: '冯营养师', title: '主任营养师', specialty: '营养减肥门诊' },
          { id: 102308, name: '韩营养师', title: '副主任营养师', specialty: '营养减肥门诊' },
          { id: 102309, name: '杨营养师', title: '营养师', specialty: '营养减肥门诊' }
        ],
        23004: [ // 体重管理（营养）门诊 (departmentId=23, subDepartmentId=4)
          { id: 102310, name: '赵营养师', title: '主任营养师', specialty: '体重管理（营养）门诊' },
          { id: 102311, name: '孙营养师', title: '副主任营养师', specialty: '体重管理（营养）门诊' },
          { id: 102312, name: '周营养师', title: '营养师', specialty: '体重管理（营养）门诊' }
        ],
        // 病理科子科室的医生数据
        22001: [ // 病理科门诊 (departmentId=22, subDepartmentId=1)
          { id: 102201, name: '张主任', title: '主任医师', specialty: '病理科门诊' },
          { id: 102202, name: '李医生', title: '副主任医师', specialty: '病理科门诊' },
          { id: 102203, name: '王医生', title: '主治医师', specialty: '病理科门诊' }
        ],
        // 康复医学科子科室的医生数据
        21001: [ // 康复医学科门诊 (departmentId=21, subDepartmentId=1)
          { id: 102101, name: '刘主任', title: '主任医师', specialty: '康复医学科门诊' },
          { id: 102102, name: '陈医生', title: '副主任医师', specialty: '康复医学科门诊' },
          { id: 102103, name: '周医生', title: '主治医师', specialty: '康复医学科门诊' }
        ],
        21002: [ // 运动损伤康复专科门诊 (departmentId=21, subDepartmentId=2)
          { id: 102104, name: '吴主任', title: '主任医师', specialty: '运动损伤康复专科门诊' },
          { id: 102105, name: '郑医生', title: '副主任医师', specialty: '运动损伤康复专科门诊' },
          { id: 102106, name: '钱医生', title: '主治医师', specialty: '运动损伤康复专科门诊' }
        ],
        21003: [ // 颞颌关节紊乱康复专科门诊 (departmentId=21, subDepartmentId=3)
          { id: 102107, name: '冯主任', title: '主任医师', specialty: '颞颌关节紊乱康复专科门诊' },
          { id: 102108, name: '韩医生', title: '副主任医师', specialty: '颞颌关节紊乱康复专科门诊' },
          { id: 102109, name: '杨医生', title: '主治医师', specialty: '颞颌关节紊乱康复专科门诊' }
        ],
        21004: [ // 疼痛康复专科门诊 (departmentId=21, subDepartmentId=4)
          { id: 102110, name: '赵主任', title: '主任医师', specialty: '疼痛康复专科门诊' },
          { id: 102111, name: '孙医生', title: '副主任医师', specialty: '疼痛康复专科门诊' },
          { id: 102112, name: '周医生', title: '主治医师', specialty: '疼痛康复专科门诊' }
        ],
        21005: [ // 教学门诊/康复医学科 (departmentId=21, subDepartmentId=5)
          { id: 102113, name: '李主任', title: '主任医师', specialty: '教学门诊/康复医学科' },
          { id: 102114, name: '王医生', title: '副主任医师', specialty: '教学门诊/康复医学科' },
          { id: 102115, name: '张医生', title: '主治医师', specialty: '教学门诊/康复医学科' }
        ],
        // 资深专家门诊子科室的医生数据
        27001: [ // 肝胆胰外科资深专家门诊 (departmentId=27, subDepartmentId=1)
          { id: 102701, name: '张专家', title: '主任医师', specialty: '肝胆胰外科资深专家门诊' },
          { id: 102702, name: '李专家', title: '主任医师', specialty: '肝胆胰外科资深专家门诊' },
          { id: 102703, name: '王专家', title: '主任医师', specialty: '肝胆胰外科资深专家门诊' }
        ],
        27002: [ // 心脏大血管外科资深专家门诊 (departmentId=27, subDepartmentId=2)
          { id: 102704, name: '刘专家', title: '主任医师', specialty: '心脏大血管外科资深专家门诊' },
          { id: 102705, name: '陈专家', title: '主任医师', specialty: '心脏大血管外科资深专家门诊' },
          { id: 102706, name: '周专家', title: '主任医师', specialty: '心脏大血管外科资深专家门诊' }
        ],
        27003: [ // 肾脏病中心资深专家门诊 (departmentId=27, subDepartmentId=3)
          { id: 102707, name: '吴专家', title: '主任医师', specialty: '肾脏病中心资深专家门诊' },
          { id: 102708, name: '郑专家', title: '主任医师', specialty: '肾脏病中心资深专家门诊' },
          { id: 102709, name: '钱专家', title: '主任医师', specialty: '肾脏病中心资深专家门诊' }
        ],
        27004: [ // 普胸外科资深专家门诊 (departmentId=27, subDepartmentId=4)
          { id: 102710, name: '冯专家', title: '主任医师', specialty: '普胸外科资深专家门诊' },
          { id: 102711, name: '韩专家', title: '主任医师', specialty: '普胸外科资深专家门诊' },
          { id: 102712, name: '杨专家', title: '主任医师', specialty: '普胸外科资深专家门诊' }
        ],
        27005: [ // 血液科资深专家门诊 (departmentId=27, subDepartmentId=5)
          { id: 102713, name: '赵专家', title: '主任医师', specialty: '血液科资深专家门诊' },
          { id: 102714, name: '孙专家', title: '主任医师', specialty: '血液科资深专家门诊' },
          { id: 102715, name: '周专家', title: '主任医师', specialty: '血液科资深专家门诊' }
        ],
        27006: [ // 风湿免疫资深专家门诊 (departmentId=27, subDepartmentId=6)
          { id: 102716, name: '李专家', title: '主任医师', specialty: '风湿免疫资深专家门诊' },
          { id: 102717, name: '王专家', title: '主任医师', specialty: '风湿免疫资深专家门诊' },
          { id: 102718, name: '张专家', title: '主任医师', specialty: '风湿免疫资深专家门诊' }
        ],
        27007: [ // 骨科资深专家门诊 (departmentId=27, subDepartmentId=7)
          { id: 102719, name: '刘专家', title: '主任医师', specialty: '骨科资深专家门诊' },
          { id: 102720, name: '陈专家', title: '主任医师', specialty: '骨科资深专家门诊' },
          { id: 102721, name: '周专家', title: '主任医师', specialty: '骨科资深专家门诊' }
        ],
        27008: [ // 超声医学科资深专家门诊 (departmentId=27, subDepartmentId=8)
          { id: 102722, name: '吴专家', title: '主任医师', specialty: '超声医学科资深专家门诊' },
          { id: 102723, name: '郑专家', title: '主任医师', specialty: '超声医学科资深专家门诊' },
          { id: 102724, name: '钱专家', title: '主任医师', specialty: '超声医学科资深专家门诊' }
        ],
        27009: [ // 甲状腺外科资深专家门诊 (departmentId=27, subDepartmentId=9)
          { id: 102725, name: '冯专家', title: '主任医师', specialty: '甲状腺外科资深专家门诊' },
          { id: 102726, name: '韩专家', title: '主任医师', specialty: '甲状腺外科资深专家门诊' },
          { id: 102727, name: '杨专家', title: '主任医师', specialty: '甲状腺外科资深专家门诊' }
        ],
        27010: [ // 乳腺外科资深专家门诊 (departmentId=27, subDepartmentId=10)
          { id: 102728, name: '赵专家', title: '主任医师', specialty: '乳腺外科资深专家门诊' },
          { id: 102729, name: '孙专家', title: '主任医师', specialty: '乳腺外科资深专家门诊' },
          { id: 102730, name: '周专家', title: '主任医师', specialty: '乳腺外科资深专家门诊' }
        ],
        27011: [ // 泌尿外科资深专家门诊 (departmentId=27, subDepartmentId=11)
          { id: 102731, name: '李专家', title: '主任医师', specialty: '泌尿外科资深专家门诊' },
          { id: 102732, name: '王专家', title: '主任医师', specialty: '泌尿外科资深专家门诊' },
          { id: 102733, name: '张专家', title: '主任医师', specialty: '泌尿外科资深专家门诊' }
        ],
        27012: [ // 消化内科资深专家门诊 (departmentId=27, subDepartmentId=12)
          { id: 102734, name: '刘专家', title: '主任医师', specialty: '消化内科资深专家门诊' },
          { id: 102735, name: '陈专家', title: '主任医师', specialty: '消化内科资深专家门诊' },
          { id: 102736, name: '周专家', title: '主任医师', specialty: '消化内科资深专家门诊' }
        ],
        27013: [ // 神经内科资深专家门诊 (departmentId=27, subDepartmentId=13)
          { id: 102737, name: '吴专家', title: '主任医师', specialty: '神经内科资深专家门诊' },
          { id: 102738, name: '郑专家', title: '主任医师', specialty: '神经内科资深专家门诊' },
          { id: 102739, name: '钱专家', title: '主任医师', specialty: '神经内科资深专家门诊' }
        ],
        27014: [ // 心血管内科资深专家门诊 (departmentId=27, subDepartmentId=14)
          { id: 102740, name: '冯专家', title: '主任医师', specialty: '心血管内科资深专家门诊' },
          { id: 102741, name: '韩专家', title: '主任医师', specialty: '心血管内科资深专家门诊' },
          { id: 102742, name: '杨专家', title: '主任医师', specialty: '心血管内科资深专家门诊' }
        ],
        27015: [ // 精神卫生科资深专家门诊 (departmentId=27, subDepartmentId=15)
          { id: 102743, name: '赵专家', title: '主任医师', specialty: '精神卫生科资深专家门诊' },
          { id: 102744, name: '孙专家', title: '主任医师', specialty: '精神卫生科资深专家门诊' },
          { id: 102745, name: '周专家', title: '主任医师', specialty: '精神卫生科资深专家门诊' }
        ],
        27016: [ // 内分泌科资深专家门诊 (departmentId=27, subDepartmentId=16)
          { id: 102746, name: '李专家', title: '主任医师', specialty: '内分泌科资深专家门诊' },
          { id: 102747, name: '王专家', title: '主任医师', specialty: '内分泌科资深专家门诊' },
          { id: 102748, name: '张专家', title: '主任医师', specialty: '内分泌科资深专家门诊' }
        ],
        // 医疗美容科各专科门诊的医生数据（通过 specialtyId 访问）
        19001: [ // 整形外科门诊
          { id: 101901, name: '赵主任', title: '主任医师', specialty: '整形外科门诊' },
          { id: 101902, name: '钱医生', title: '副主任医师', specialty: '整形外科门诊' },
          { id: 101903, name: '孙医生', title: '主治医师', specialty: '整形外科门诊' }
        ],
        19002: [ // 脱发及毛发移植专科门诊
          { id: 101904, name: '李主任', title: '主任医师', specialty: '脱发及毛发移植专科门诊' },
          { id: 101905, name: '周医生', title: '副主任医师', specialty: '脱发及毛发移植专科门诊' },
          { id: 101906, name: '吴医生', title: '主治医师', specialty: '脱发及毛发移植专科门诊' }
        ],
        19003: [ // 面部皮肤激光美容专科门诊
          { id: 101907, name: '郑主任', title: '主任医师', specialty: '面部皮肤激光美容专科门诊' },
          { id: 101908, name: '王医生', title: '副主任医师', specialty: '面部皮肤激光美容专科门诊' },
          { id: 101909, name: '刘医生', title: '主治医师', specialty: '面部皮肤激光美容专科门诊' }
        ],
        19004: [ // 体表肿物（整形外科）专科门诊
          { id: 101910, name: '陈主任', title: '主任医师', specialty: '体表肿物（整形外科）专科门诊' },
          { id: 101911, name: '杨医生', title: '副主任医师', specialty: '体表肿物（整形外科）专科门诊' },
          { id: 101912, name: '黄医生', title: '主治医师', specialty: '体表肿物（整形外科）专科门诊' }
        ],
        19005: [ // 抽脂塑形（整形外科）专科门诊
          { id: 101913, name: '胡主任', title: '主任医师', specialty: '抽脂塑形（整形外科）专科门诊' },
          { id: 101914, name: '高医生', title: '副主任医师', specialty: '抽脂塑形（整形外科）专科门诊' },
          { id: 101915, name: '罗医生', title: '主治医师', specialty: '抽脂塑形（整形外科）专科门诊' }
        ],
        19006: [ // 腋臭（整形外科）专科门诊
          { id: 101916, name: '马主任', title: '主任医师', specialty: '腋臭（整形外科）专科门诊' },
          { id: 101917, name: '贾医生', title: '副主任医师', specialty: '腋臭（整形外科）专科门诊' },
          { id: 101918, name: '邓医生', title: '主治医师', specialty: '腋臭（整形外科）专科门诊' }
        ],
        19007: [ // 注射微整（整形外科）专科门诊
          { id: 101919, name: '姚主任', title: '主任医师', specialty: '注射微整（整形外科）专科门诊' },
          { id: 101920, name: '曹医生', title: '副主任医师', specialty: '注射微整（整形外科）专科门诊' },
          { id: 101921, name: '袁医生', title: '主治医师', specialty: '注射微整（整形外科）专科门诊' }
        ],
        19008: [ // 乳房整形美容（整形外科）专科门诊
          { id: 101922, name: '谢主任', title: '主任医师', specialty: '乳房整形美容（整形外科）专科门诊' },
          { id: 101923, name: '秦医生', title: '副主任医师', specialty: '乳房整形美容（整形外科）专科门诊' },
          { id: 101924, name: '何医生', title: '主治医师', specialty: '乳房整形美容（整形外科）专科门诊' }
        ],
        19009: [ // 整形美容中心门诊
          { id: 101925, name: '段主任', title: '主任医师', specialty: '整形美容中心门诊' },
          { id: 101926, name: '雷医生', title: '副主任医师', specialty: '整形美容中心门诊' },
          { id: 101927, name: '谷医生', title: '主治医师', specialty: '整形美容中心门诊' }
        ],
        19010: [ // 体表肿物（整形美容）专科门诊
          { id: 101928, name: '毕主任', title: '主任医师', specialty: '体表肿物（整形美容）专科门诊' },
          { id: 101929, name: '汤医生', title: '副主任医师', specialty: '体表肿物（整形美容）专科门诊' },
          { id: 101930, name: '窦医生', title: '主治医师', specialty: '体表肿物（整形美容）专科门诊' }
        ],
        19011: [ // 抽脂塑形（整形美容）专科门诊
          { id: 101931, name: '安主任', title: '主任医师', specialty: '抽脂塑形（整形美容）专科门诊' },
          { id: 101932, name: '常医生', title: '副主任医师', specialty: '抽脂塑形（整形美容）专科门诊' },
          { id: 101933, name: '乐医生', title: '主治医师', specialty: '抽脂塑形（整形美容）专科门诊' }
        ],
        19012: [ // 腋臭（整形美容）专科门诊
          { id: 101934, name: '于主任', title: '主任医师', specialty: '腋臭（整形美容）专科门诊' },
          { id: 101935, name: '时医生', title: '副主任医师', specialty: '腋臭（整形美容）专科门诊' },
          { id: 101936, name: '傅医生', title: '主治医师', specialty: '腋臭（整形美容）专科门诊' }
        ],
        19013: [ // 注射微整（整形美容）专科门诊
          { id: 101937, name: '皮主任', title: '主任医师', specialty: '注射微整（整形美容）专科门诊' },
          { id: 101938, name: '卞医生', title: '副主任医师', specialty: '注射微整（整形美容）专科门诊' },
          { id: 101939, name: '齐医生', title: '主治医师', specialty: '注射微整（整形美容）专科门诊' }
        ],
        19014: [ // 乳房整形美容（整形美容）专科门诊
          { id: 101940, name: '康主任', title: '主任医师', specialty: '乳房整形美容（整形美容）专科门诊' },
          { id: 101941, name: '伍医生', title: '副主任医师', specialty: '乳房整形美容（整形美容）专科门诊' },
          { id: 101942, name: '余医生', title: '主治医师', specialty: '乳房整形美容（整形美容）专科门诊' }
        ],
        19015: [ // 激光美容专科门诊
          { id: 101943, name: '元主任', title: '主任医师', specialty: '激光美容专科门诊' },
          { id: 101944, name: '卜医生', title: '副主任医师', specialty: '激光美容专科门诊' },
          { id: 101945, name: '顾医生', title: '主治医师', specialty: '激光美容专科门诊' }
        ],
        19016: [ // 光子嫩肤（整形美容）专科门诊
          { id: 101946, name: '孟主任', title: '主任医师', specialty: '光子嫩肤（整形美容）专科门诊' },
          { id: 101947, name: '平医生', title: '副主任医师', specialty: '光子嫩肤（整形美容）专科门诊' },
          { id: 101948, name: '宁医生', title: '主治医师', specialty: '光子嫩肤（整形美容）专科门诊' }
        ],
        19017: [ // 毛发移植专科门诊
          { id: 101949, name: '景主任', title: '主任医师', specialty: '毛发移植专科门诊' },
          { id: 101950, name: '牛医生', title: '副主任医师', specialty: '毛发移植专科门诊' },
          { id: 101951, name: '柴医生', title: '主治医师', specialty: '毛发移植专科门诊' }
        ],
        19018: [ // 女性私密整形专科门诊
          { id: 101952, name: '温主任', title: '主任医师', specialty: '女性私密整形专科门诊' },
          { id: 101953, name: '支医生', title: '副主任医师', specialty: '女性私密整形专科门诊' },
          { id: 101954, name: '柯医生', title: '主治医师', specialty: '女性私密整形专科门诊' }
        ],
        19019: [ // 私密（整形美容）专科门诊
          { id: 101955, name: '昝主任', title: '主任医师', specialty: '私密（整形美容）专科门诊' },
          { id: 101956, name: '管医生', title: '副主任医师', specialty: '私密（整形美容）专科门诊' },
          { id: 101957, name: '卢医生', title: '主治医师', specialty: '私密（整形美容）专科门诊' }
        ]
      },
      // 专科门诊的医生数据（消化内科的专科门诊）
      specialtyDoctors: {
        1: [ // 消化内科门诊
          { id: 100137, name: '张明', title: '主任医师', specialty: '消化内科门诊' },
          { id: 100138, name: '李华', title: '副主任医师', specialty: '消化内科门诊' },
          { id: 100139, name: '王强', title: '主治医师', specialty: '消化内科门诊' }
        ],
        2: [ // 自身免疫性胰腺炎（内科）专科门诊
          { id: 100140, name: '赵敏', title: '主任医师', specialty: '自身免疫性胰腺炎（内科）专科门诊' },
          { id: 100141, name: '陈建国', title: '副主任医师', specialty: '自身免疫性胰腺炎（内科）专科门诊' },
          { id: 100142, name: '刘芳', title: '主治医师', specialty: '自身免疫性胰腺炎（内科）专科门诊' }
        ],
        3: [ // 食管胃静脉曲张（内科）专科门诊
          { id: 100143, name: '周伟', title: '主任医师', specialty: '食管胃静脉曲张（内科）专科门诊' },
          { id: 100144, name: '吴丽', title: '副主任医师', specialty: '食管胃静脉曲张（内科）专科门诊' },
          { id: 100145, name: '郑强', title: '主治医师', specialty: '食管胃静脉曲张（内科）专科门诊' }
        ],
        4: [ // 脂肪肝专科门诊
          { id: 100146, name: '孙立', title: '主任医师', specialty: '脂肪肝专科门诊' },
          { id: 100147, name: '马静', title: '副主任医师', specialty: '脂肪肝专科门诊' },
          { id: 100148, name: '钱勇', title: '主治医师', specialty: '脂肪肝专科门诊' }
        ],
        5: [ // 克罗恩病、溃疡性结肠炎专科门诊
          { id: 100149, name: '冯军', title: '主任医师', specialty: '克罗恩病、溃疡性结肠炎专科门诊' },
          { id: 100150, name: '韩梅', title: '副主任医师', specialty: '克罗恩病、溃疡性结肠炎专科门诊' },
          { id: 100151, name: '杨波', title: '主治医师', specialty: '克罗恩病、溃疡性结肠炎专科门诊' }
        ],
        6: [ // 胃食管反流病外科治疗专科门诊
          { id: 100152, name: '朱文', title: '主任医师', specialty: '胃食管反流病外科治疗专科门诊' },
          { id: 100153, name: '林雪', title: '副主任医师', specialty: '胃食管反流病外科治疗专科门诊' },
          { id: 100154, name: '何刚', title: '主治医师', specialty: '胃食管反流病外科治疗专科门诊' }
        ],
        7: [ // 心血管内科门诊
          { id: 100155, name: '陈建国', title: '主任医师', specialty: '心血管内科门诊' },
          { id: 100156, name: '刘芳', title: '副主任医师', specialty: '心血管内科门诊' },
          { id: 100157, name: '周伟', title: '主治医师', specialty: '心血管内科门诊' },
          { id: 100158, name: '吴丽', title: '主任医师', specialty: '心血管内科门诊' }
        ],
        8: [ // 心脏起搏器专科门诊
          { id: 100159, name: '郑强', title: '主任医师', specialty: '心脏起搏器专科门诊' },
          { id: 100160, name: '孙立', title: '副主任医师', specialty: '心脏起搏器专科门诊' },
          { id: 100161, name: '马静', title: '主治医师', specialty: '心脏起搏器专科门诊' }
        ],
        9: [ // 房颤专科门诊
          { id: 100162, name: '钱勇', title: '主任医师', specialty: '房颤专科门诊' },
          { id: 100163, name: '冯军', title: '副主任医师', specialty: '房颤专科门诊' },
          { id: 100164, name: '韩梅', title: '主治医师', specialty: '房颤专科门诊' }
        ],
        10: [ // 脉动脉高压专科门诊
          { id: 100165, name: '杨波', title: '主任医师', specialty: '脉动脉高压专科门诊' },
          { id: 100166, name: '朱文', title: '副主任医师', specialty: '脉动脉高压专科门诊' },
          { id: 100167, name: '林雪', title: '主治医师', specialty: '脉动脉高压专科门诊' }
        ],
        11: [ // 心脏瓣膜病（内科）专科门诊
          { id: 100168, name: '何刚', title: '主任医师', specialty: '心脏瓣膜病（内科）专科门诊' },
          { id: 100169, name: '罗敏', title: '副主任医师', specialty: '心脏瓣膜病（内科）专科门诊' },
          { id: 100170, name: '徐亮', title: '主治医师', specialty: '心脏瓣膜病（内科）专科门诊' }
        ],
        12: [ // 血液科门诊
          { id: 100171, name: '冯军', title: '主任医师', specialty: '血液科门诊' },
          { id: 100172, name: '韩梅', title: '副主任医师', specialty: '血液科门诊' },
          { id: 100173, name: '杨波', title: '主治医师', specialty: '血液科门诊' },
          { id: 100174, name: '朱文', title: '主任医师', specialty: '血液科门诊' }
        ],
        13: [ // 血液骨髓移植门诊
          { id: 100175, name: '林雪', title: '主任医师', specialty: '血液骨髓移植门诊' },
          { id: 100176, name: '何刚', title: '副主任医师', specialty: '血液骨髓移植门诊' },
          { id: 100177, name: '罗敏', title: '主治医师', specialty: '血液骨髓移植门诊' }
        ],
        14: [ // 血液骨髓移植/CAR-T门诊
          { id: 100178, name: '徐亮', title: '主任医师', specialty: '血液骨髓移植/CAR-T门诊' },
          { id: 100179, name: '高红', title: '副主任医师', specialty: '血液骨髓移植/CAR-T门诊' },
          { id: 100180, name: '谢军', title: '主治医师', specialty: '血液骨髓移植/CAR-T门诊' }
        ],
        15: [ // 血液、淋巴瘤门诊
          { id: 100181, name: '唐丽', title: '主任医师', specialty: '血液、淋巴瘤门诊' },
          { id: 100182, name: '邓强', title: '副主任医师', specialty: '血液、淋巴瘤门诊' },
          { id: 100183, name: '许静', title: '主治医师', specialty: '血液、淋巴瘤门诊' }
        ],
        16: [ // 白血病专科门诊
          { id: 100184, name: '曹勇', title: '主任医师', specialty: '白血病专科门诊' },
          { id: 100185, name: '袁文', title: '副主任医师', specialty: '白血病专科门诊' },
          { id: 100186, name: '田梅', title: '主治医师', specialty: '白血病专科门诊' },
          { id: 100187, name: '宋刚', title: '主任医师', specialty: '白血病专科门诊' }
        ],
        17: [ // CAR-T专科门诊
          { id: 100188, name: '潘明', title: '主任医师', specialty: 'CAR-T专科门诊' },
          { id: 100189, name: '方丽', title: '副主任医师', specialty: 'CAR-T专科门诊' },
          { id: 100190, name: '石强', title: '主治医师', specialty: 'CAR-T专科门诊' }
        ],
        18: [ // 代谢与遗传性疾病门诊
          { id: 100191, name: '姚静', title: '主任医师', specialty: '代谢与遗传性疾病门诊' },
          { id: 100192, name: '胡军', title: '副主任医师', specialty: '代谢与遗传性疾病门诊' },
          { id: 100193, name: '范红', title: '主治医师', specialty: '代谢与遗传性疾病门诊' }
        ],
        19: [ // 肾脏病中心门诊
          { id: 100194, name: '朱文', title: '主任医师', specialty: '肾脏病中心门诊' },
          { id: 100195, name: '林雪', title: '副主任医师', specialty: '肾脏病中心门诊' },
          { id: 100196, name: '何刚', title: '主治医师', specialty: '肾脏病中心门诊' },
          { id: 100197, name: '罗敏', title: '主任医师', specialty: '肾脏病中心门诊' }
        ],
        20: [ // 风湿免疫肾病专科门诊
          { id: 100198, name: '徐亮', title: '主任医师', specialty: '风湿免疫肾病专科门诊' },
          { id: 100199, name: '高红', title: '副主任医师', specialty: '风湿免疫肾病专科门诊' },
          { id: 100200, name: '谢军', title: '主治医师', specialty: '风湿免疫肾病专科门诊' }
        ],
        21: [ // 腹透专科门诊
          { id: 100201, name: '唐丽', title: '主任医师', specialty: '腹透专科门诊' },
          { id: 100202, name: '邓强', title: '副主任医师', specialty: '腹透专科门诊' },
          { id: 100203, name: '许静', title: '主治医师', specialty: '腹透专科门诊' }
        ],
        22: [ // 神经内科门诊
          { id: 100204, name: '徐亮', title: '主任医师', specialty: '神经内科门诊' },
          { id: 100205, name: '高红', title: '副主任医师', specialty: '神经内科门诊' },
          { id: 100206, name: '谢军', title: '主治医师', specialty: '神经内科门诊' },
          { id: 100207, name: '唐丽', title: '主任医师', specialty: '神经内科门诊' }
        ],
        23: [ // 记忆障碍专科门诊
          { id: 100208, name: '邓强', title: '主任医师', specialty: '记忆障碍专科门诊' },
          { id: 100209, name: '许静', title: '副主任医师', specialty: '记忆障碍专科门诊' },
          { id: 100210, name: '曹勇', title: '主治医师', specialty: '记忆障碍专科门诊' }
        ],
        24: [ // 睡眠障碍（神内）专科门诊
          { id: 100211, name: '袁文', title: '主任医师', specialty: '睡眠障碍（神内）专科门诊' },
          { id: 100212, name: '田梅', title: '副主任医师', specialty: '睡眠障碍（神内）专科门诊' },
          { id: 100213, name: '宋刚', title: '主治医师', specialty: '睡眠障碍（神内）专科门诊' }
        ],
        25: [ // 帕金森与神经程控专科门诊
          { id: 100214, name: '潘明', title: '主任医师', specialty: '帕金森与神经程控专科门诊' },
          { id: 100215, name: '方丽', title: '副主任医师', specialty: '帕金森与神经程控专科门诊' },
          { id: 100216, name: '石强', title: '主治医师', specialty: '帕金森与神经程控专科门诊' },
          { id: 100217, name: '姚静', title: '主任医师', specialty: '帕金森与神经程控专科门诊' }
        ],
        26: [ // 癫痫专科门诊
          { id: 100218, name: '胡军', title: '主任医师', specialty: '癫痫专科门诊' },
          { id: 100219, name: '范红', title: '副主任医师', specialty: '癫痫专科门诊' },
          { id: 100220, name: '卢勇', title: '主治医师', specialty: '癫痫专科门诊' }
        ],
        27: [ // 内分泌科门诊
          { id: 100221, name: '邓强', title: '主任医师', specialty: '内分泌科门诊' },
          { id: 100222, name: '许静', title: '副主任医师', specialty: '内分泌科门诊' },
          { id: 100223, name: '曹勇', title: '主治医师', specialty: '内分泌科门诊' },
          { id: 100224, name: '袁文', title: '主任医师', specialty: '内分泌科门诊' }
        ],
        28: [ // 体重管理（内分泌科）门诊
          { id: 100225, name: '田梅', title: '主任医师', specialty: '体重管理（内分泌科）门诊' },
          { id: 100226, name: '宋刚', title: '副主任医师', specialty: '体重管理（内分泌科）门诊' },
          { id: 100227, name: '潘明', title: '主治医师', specialty: '体重管理（内分泌科）门诊' }
        ],
        29: [ // 肾上腺疾病（内科）门诊
          { id: 100228, name: '方丽', title: '主任医师', specialty: '肾上腺疾病（内科）门诊' },
          { id: 100229, name: '石强', title: '副主任医师', specialty: '肾上腺疾病（内科）门诊' },
          { id: 100230, name: '姚静', title: '主治医师', specialty: '肾上腺疾病（内科）门诊' }
        ],
        30: [ // 风湿免疫科门诊
          { id: 100231, name: '袁文', title: '主任医师', specialty: '风湿免疫科门诊' },
          { id: 100232, name: '田梅', title: '副主任医师', specialty: '风湿免疫科门诊' },
          { id: 100233, name: '宋刚', title: '主治医师', specialty: '风湿免疫科门诊' },
          { id: 100234, name: '潘明', title: '主任医师', specialty: '风湿免疫科门诊' }
        ],
        31: [ // 自身炎症性疾病专科门诊
          { id: 100235, name: '方丽', title: '主任医师', specialty: '自身炎症性疾病专科门诊' },
          { id: 100236, name: '石强', title: '副主任医师', specialty: '自身炎症性疾病专科门诊' },
          { id: 100237, name: '姚静', title: '主治医师', specialty: '自身炎症性疾病专科门诊' }
        ],
        32: [ // 白塞病专科门诊
          { id: 100238, name: '胡军', title: '主任医师', specialty: '白塞病专科门诊' },
          { id: 100239, name: '范红', title: '副主任医师', specialty: '白塞病专科门诊' },
          { id: 100240, name: '卢勇', title: '主治医师', specialty: '白塞病专科门诊' }
        ],
        33: [ // 系统性硬化症专科门诊
          { id: 100241, name: '邓强', title: '主任医师', specialty: '系统性硬化症专科门诊' },
          { id: 100242, name: '许静', title: '副主任医师', specialty: '系统性硬化症专科门诊' },
          { id: 100243, name: '曹勇', title: '主治医师', specialty: '系统性硬化症专科门诊' },
          { id: 100244, name: '袁文', title: '主任医师', specialty: '系统性硬化症专科门诊' }
        ],
        34: [ // 结缔组织病相关间质性肺病门诊
          { id: 100245, name: '田梅', title: '主任医师', specialty: '结缔组织病相关间质性肺病门诊' },
          { id: 100246, name: '宋刚', title: '副主任医师', specialty: '结缔组织病相关间质性肺病门诊' },
          { id: 100247, name: '潘明', title: '主治医师', specialty: '结缔组织病相关间质性肺病门诊' }
        ],
        35: [ // 呼吸内科门诊
          { id: 100248, name: '孙立', title: '主任医师', specialty: '呼吸内科门诊' },
          { id: 100249, name: '马静', title: '副主任医师', specialty: '呼吸内科门诊' },
          { id: 100250, name: '钱勇', title: '主治医师', specialty: '呼吸内科门诊' }
        ],
        36: [ // 老年内科门诊
          { id: 100251, name: '潘明', title: '主任医师', specialty: '老年内科门诊' },
          { id: 100252, name: '方丽', title: '副主任医师', specialty: '老年内科门诊' },
          { id: 100253, name: '石强', title: '主治医师', specialty: '老年内科门诊' },
          { id: 100254, name: '姚静', title: '主任医师', specialty: '老年内科门诊' }
        ],
        37: [ // 普内科门诊
          { id: 100255, name: '胡军', title: '主任医师', specialty: '普内科门诊' },
          { id: 100256, name: '范红', title: '副主任医师', specialty: '普内科门诊' },
          { id: 100257, name: '卢勇', title: '主治医师', specialty: '普内科门诊' }
        ],
      }
    }
  },
  computed: {
    displayTitle() {
      // 如果有专科门诊名称，显示专科门诊名称，否则显示子科室名称
      return this.specialtyName || this.subDepartmentName || '科室'
    },
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
      try {
        // 如果年份或月份未初始化，使用明天的日期
        if (!this.selectedYear || !this.selectedMonth) {
          const tomorrow = new Date()
          tomorrow.setDate(tomorrow.getDate() + 1)
          return [tomorrow.getDate()]
        }
        
        // 验证月份范围
        if (this.selectedMonth < 1 || this.selectedMonth > 12) {
          return [1]
        }
        
        const daysInMonth = new Date(this.selectedYear, this.selectedMonth, 0).getDate()
        const days = []
        const tomorrow = new Date()
        tomorrow.setDate(tomorrow.getDate() + 1)
        
        let minDay = 1
        if (this.selectedYear === tomorrow.getFullYear() && 
            this.selectedMonth === tomorrow.getMonth() + 1) {
          minDay = tomorrow.getDate()
        }
        
        for (let i = minDay; i <= daysInMonth; i++) {
          days.push(i)
        }
        
        // 确保至少有一个日期可选
        if (days.length === 0) {
          days.push(minDay > 0 ? minDay : 1)
        }
        
        return days
      } catch (error) {
        console.error('计算可用日期时出错:', error)
        // 返回默认日期
        const tomorrow = new Date()
        tomorrow.setDate(tomorrow.getDate() + 1)
        return [tomorrow.getDate()]
      }
    },
    canSubmit() {
      return (
        this.selectedDoctor &&
        this.selectedDate &&
        this.selectedTimeSlot &&
        this.selectedPatientId
      )
    }
  },
  watch: {
    selectedMonth(newVal, oldVal) {
      // 避免初始化时触发
      if (oldVal === null || oldVal === undefined) {
        return
      }
      // 当月份改变时，检查日期是否有效
      if (this.selectedYear && newVal) {
        const maxDay = new Date(this.selectedYear, newVal, 0).getDate()
        if (this.selectedDay && this.selectedDay > maxDay) {
          this.selectedDay = maxDay
        }
        this.updateDate()
      }
    },
    selectedYear(newVal, oldVal) {
      // 避免初始化时触发
      if (oldVal === null || oldVal === undefined) {
        return
      }
      if (newVal && this.selectedMonth) {
        this.updateDate()
      }
    },
    selectedDate(newDate, oldDate) {
      if (!newDate) {
        this.doctors = []
        this.doctorQuotas = {}
        this.selectedDoctor = null
        this.selectedTimeSlot = ''
        return
      }
      if (newDate === oldDate) {
        return
      }
      this.selectedDoctor = null
      this.selectedTimeSlot = ''
      void this.loadDoctors()
    }
  },
  mounted() {
    // 从路由查询参数获取信息
    this.departmentId = parseInt(this.$route.query.departmentId) || 1
    this.departmentName = this.$route.query.departmentName || '内科'
    this.subDepartmentId = parseInt(this.$route.query.subDepartmentId) || 1
    this.subDepartmentName = this.$route.query.subDepartmentName || ''
    this.specialtyId = this.$route.query.specialtyId ? parseInt(this.$route.query.specialtyId) : null
    this.specialtyName = this.$route.query.specialtyName || ''
    this.loadPatients()
    window.addEventListener('focus', this.loadPatients)
    
    console.log('页面加载参数:', {
      departmentId: this.departmentId,
      subDepartmentId: this.subDepartmentId,
      subDepartmentName: this.subDepartmentName,
      specialtyId: this.specialtyId,
      specialtyName: this.specialtyName
    })
    
    // 初始化日期（明天）
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    this.selectedYear = tomorrow.getFullYear()
    this.selectedMonth = tomorrow.getMonth() + 1
    this.selectedDay = tomorrow.getDate()
    
    this.$nextTick(() => {
      const year = this.selectedYear
      const month = String(this.selectedMonth).padStart(2, '0')
      const day = String(this.selectedDay).padStart(2, '0')
      this.selectedDate = `${year}-${month}-${day}`
      // 医生列表由 selectedDate 的 watch 触发 loadDoctors（含 date 参数）
    })
  },
  beforeUnmount() {
    window.removeEventListener('focus', this.loadPatients)
  },
  methods: {
    // 判断是否为专家号：主任医师 + 资深专家门诊全员专家
    isExpertDoctor(doctor) {
      if (!doctor || !doctor.title) return false
      const title = doctor.title
      // 资深专家门诊（departmentId = 27）下的医生全部视为专家号
      if (this.departmentId === 27) return true
      // 仅“主任医师”视为专家号，排除“副主任医师”
      return title.includes('主任医师') && !title.includes('副主任医师')
    },

    // 加载每个医生在当前日期的号源总数和剩余数
    async loadDoctorQuotas() {
      try {
        if (!this.selectedDate || !this.doctors || this.doctors.length === 0) {
          this.doctorQuotas = {}
          return
        }

        const timeSlotCount = this.timeSlots.length

        const getDefaultPerSlot = (doctor) => {
          // 与后端逻辑保持一致：
          // 专家号：每天总号源 40 -> 两个时间段，每段 20
          // 普通号：每天总号源 80 -> 两个时间段，每段 40
          return this.isExpertDoctor(doctor) ? 20 : 40
        }

        const quotas = {}

        await Promise.all(
          this.doctors.map(async (doctor) => {
            try {
              const resp = await axios.get('/api/appointment-slots', {
                params: {
                  doctor_id: doctor.id,
                  date: this.selectedDate
                }
              })

              if (resp.data.status === 'success' && Array.isArray(resp.data.slots) && resp.data.slots.length > 0) {
                let total = 0
                let remaining = 0
                resp.data.slots.forEach(slot => {
                  total += slot.total_count
                  remaining += slot.available_count
                })
                quotas[doctor.id] = { total, remaining }
              } else {
                const perSlot = getDefaultPerSlot(doctor)
                const total = perSlot * timeSlotCount
                quotas[doctor.id] = { total, remaining: total }
              }
            } catch (e) {
              console.error('加载医生号源信息失败:', e)
              const perSlot = getDefaultPerSlot(doctor)
              const total = perSlot * timeSlotCount
              quotas[doctor.id] = { total, remaining: total }
            }
          })
        )

        this.doctorQuotas = quotas
      } catch (error) {
        console.error('加载医生号源总数时出错:', error)
      }
    },

    // 更新日期
    updateDate() {
      if (!this.selectedYear || !this.selectedMonth || !this.selectedDay) {
        return
      }
      
      try {
        const year = this.selectedYear
        const month = String(this.selectedMonth).padStart(2, '0')
        const day = String(this.selectedDay).padStart(2, '0')
        this.selectedDate = `${year}-${month}-${day}`
        
        // 如果选择的日期小于最小日期，调整日期
        const minDate = new Date()
        minDate.setDate(minDate.getDate() + 1)
        minDate.setHours(0, 0, 0, 0)
        const selectedDateObj = new Date(this.selectedDate)
        selectedDateObj.setHours(0, 0, 0, 0)
        
        if (selectedDateObj < minDate) {
          this.$nextTick(() => {
            this.selectedYear = minDate.getFullYear()
            this.selectedMonth = minDate.getMonth() + 1
            this.selectedDay = minDate.getDate()
            const newYear = minDate.getFullYear()
            const newMonth = String(minDate.getMonth() + 1).padStart(2, '0')
            const newDay = String(minDate.getDate()).padStart(2, '0')
            this.selectedDate = `${newYear}-${newMonth}-${newDay}`
          })
        }

        this.selectedTimeSlot = ''
      } catch (error) {
        console.error('更新日期时出错:', error)
      }
    },
    async loadDoctors() {
      this.loadingDoctors = true
      this.doctorsLoadError = ''
      this.doctors = []
      try {
        const params = { department_id: this.departmentId }
        if (this.subDepartmentId != null && !Number.isNaN(this.subDepartmentId)) {
          params.sub_department_id = this.subDepartmentId
        }
        if (this.specialtyId != null && !Number.isNaN(this.specialtyId)) {
          params.specialty_id = this.specialtyId
        }
        if (this.selectedDate) {
          params.date = this.selectedDate
        }
        const { data } = await axios.get('/api/doctors', { params })
        if (data.status === 'error') {
          this.doctorsLoadError = data.message || '加载医生列表失败'
          this.doctors = []
        } else {
          this.doctors = (data.doctors || []).map((d) => ({
            id: d.id,
            name: d.name,
            title: d.title,
            specialty: d.specialty
          }))
          if (this.doctors.length === 0) {
            this.doctorsLoadError =
              '该日无门诊出诊安排（周末或非排班日），请更换就诊日期后再选医生'
          }
        }
        if (this.selectedDate) {
          await this.loadDoctorQuotas()
        }
      } catch (error) {
        console.error('加载医生时出错:', error)
        this.doctorsLoadError =
          (error.response && error.response.data && error.response.data.message) ||
          error.message ||
          '网络错误，无法加载医生'
        this.doctors = []
      } finally {
        this.loadingDoctors = false
      }
    },
    
    selectDoctor(doctor) {
      this.selectedDoctor = doctor
      // 如果已选择日期，自动加载号源
      if (this.selectedDate) {
        this.loadSlotAvailability()
      }
      // 清空已选择的时段
      this.selectedTimeSlot = ''
    },
    
    selectTimeSlot(slot) {
      // 检查号源是否可用
      if (this.getSlotAvailability(slot) === 0) {
        this.showMessage('该时段号源已满，请选择其他时段', 'warning', 2000)
        return
      }
      this.selectedTimeSlot = slot
    },
    
    // 获取时段的可用号源数量
    getSlotAvailability(slot) {
      return this.slotAvailability[slot] !== undefined ? this.slotAvailability[slot] : null
    },
    
    // 加载号源信息
    async loadSlotAvailability() {
      if (!this.selectedDoctor || !this.selectedDate) {
        this.slotAvailability = {}
        return
      }
      
      this.loadingSlots = true
      try {
        const response = await axios.get('/api/appointment-slots', {
          params: {
            doctor_id: this.selectedDoctor.id,
            date: this.selectedDate
          }
        })
        
        if (response.data.status === 'success') {
          // 初始化所有时段为null（未查询到）
          const availability = {}
          this.timeSlots.forEach(slot => {
            availability[slot] = null
          })
          
          // 更新查询到的号源信息
          response.data.slots.forEach(slot => {
            availability[slot.time_slot] = slot.available_count
          })
          
          this.slotAvailability = availability
        } else {
          console.error('加载号源失败:', response.data.message)
          this.slotAvailability = {}
        }
      } catch (error) {
        console.error('加载号源时出错:', error)
        // 如果出错，设置为null表示未知状态（不阻止用户操作）
        const availability = {}
        this.timeSlots.forEach(slot => {
          availability[slot] = null
        })
        this.slotAvailability = availability
      } finally {
        this.loadingSlots = false
      }
    },
    
    async loadPatients() {
      try {
        const response = await axios.get('/api/patients')
        if (response.data.status === 'success') {
          const list = response.data.data || []
      this.patients = list
      if (list.length === 0) {
        this.selectedPatientId = null
      } else if (!list.find(p => p.id === this.selectedPatientId)) {
        this.selectedPatientId = list[0].id
          }
        } else {
          this.patients = []
          this.selectedPatientId = null
        }
      } catch (error) {
        console.error('获取就诊人列表失败:', error)
        this.patients = []
        this.selectedPatientId = null
      }
    },
    selectPatient(id) {
      this.selectedPatientId = id
    },
    goToPatientManager() {
      this.$router.push({ name: 'PatientManager' })
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
    
    async confirmAppointment() {
      if (!this.canSubmit) {
        this.showMessage('请先选择医生、时间段与就诊人', 'warning', 2000)
        return
      }
      const patient = this.patients.find(p => p.id === this.selectedPatientId)
      if (!patient) {
        this.showMessage('请先添加就诊人', 'warning', 2000)
        return
      }
      // 检查号源是否可用
      if (this.getSlotAvailability(this.selectedTimeSlot) === 0) {
        this.showMessage('该时段号源已满，请选择其他时段', 'warning', 2000)
        return
      }
      
      const appointmentData = {
        department: this.departmentName,
        subDepartment: this.subDepartmentName,
        specialty: this.specialtyName,
        doctor: this.selectedDoctor.name,
        doctorId: this.selectedDoctor.id, // 添加医生ID
        doctorTitle: this.selectedDoctor.title,
        date: this.selectedDate,
        timeSlot: this.selectedTimeSlot,
        patientName: patient.name,
        patientPhone: patient.phone,
        patientIdCard: patient.idCard,
        departmentId: this.departmentId,
        subDepartmentId: this.subDepartmentId,
        specialtyId: this.specialtyId
      }
      try {
        const response = await axios.post('/api/appointment', appointmentData)
        if (response.data.status === 'error') {
          this.showMessage(response.data.message || '预约失败，请稍后重试', 'error', 3000)
          return
        }
        const appointmentId = response.data.appointmentId || 'A' + Date.now()
        this.showMessage(`预约成功！预约号：${appointmentId}`, 'success', 3500)
        // 重新加载号源，更新显示
        await this.loadSlotAvailability()
        // 清空选择
        this.selectedTimeSlot = ''
        // 延迟跳转到挂号记录页（与 axios baseURL 一致，避免误以为回到首页且看不到记录）
        setTimeout(() => {
          this.$router.push({ name: 'AppointmentHistory', query: { booked: '1' } })
        }, 2800)
      } catch (error) {
        if (error.response && error.response.status === 401) {
          this.showMessage('请先登录患者账号后再预约', 'error', 2500)
          this.$router.push({ path: '/login', query: { redirect: this.$route.fullPath } })
          return
        }
        const errorMsg = error.response?.data?.message || '预约失败，请稍后重试'
        this.showMessage(errorMsg, 'error', 3000)
        await this.loadSlotAvailability()
      }
    },
    
    goBack() {
      // 皮肤科、精神科卫生科、中医科、麻醉科、疼痛科、全科医疗科、康复医学科、病理科、营养科、临床药学、专科护理、高压氧、资深专家门诊：从医生页返回时回到子科室选择（细分科室列表）
      if (this.departmentId === 13 || this.departmentId === 14 || this.departmentId === 15 || this.departmentId === 16 || this.departmentId === 18 || this.departmentId === 20 || this.departmentId === 21 || this.departmentId === 22 || this.departmentId === 23 || this.departmentId === 24 || this.departmentId === 25 || this.departmentId === 26 || this.departmentId === 27) {
        this.$router.push({
          name: 'AppointmentSubDepartment',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            openSub: 'true'
          }
        })
        return
      }

      // 其他科室：如果有专科门诊信息，返回到专科门诊选择页面
      if (this.specialtyId) {
        this.$router.push({
          name: 'AppointmentSpecialty',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            subDepartmentId: this.subDepartmentId,
            subDepartmentName: this.subDepartmentName
          }
        })
      } else {
        // 否则返回到子科室选择页面
        this.$router.push({
          name: 'AppointmentSubDepartment',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName
          }
        })
      }
    }
  }
}
</script>

<style scoped>
.appointment-doctor {
  max-width: 1000px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.appointment-container {
  position: relative;
  z-index: 1;
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
  position: relative;
  z-index: 100;
  pointer-events: auto;
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

.date-time-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.date-picker label,
.time-slots label {
  display: block;
  margin-bottom: 0.5rem;
  color: #333;
  font-weight: 600;
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
  position: relative;
  z-index: 1;
  user-select: none;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.time-slot.disabled {
  background: #e0e0e0;
  color: #999;
  cursor: not-allowed;
  opacity: 0.6;
}

.time-slot.disabled:hover {
  background: #e0e0e0;
  border-color: transparent;
}

.slot-time {
  font-weight: 600;
  font-size: 1rem;
}

.slot-count {
  font-size: 0.75rem;
  margin-top: 0.2rem;
}

.available-count {
  color: #4CAF50;
  font-weight: 500;
}

.full-count {
  color: #f44336;
  font-weight: 500;
}

.loading-count {
  color: #999;
  font-size: 0.7rem;
  font-style: italic;
}

.time-slot:hover:not(.disabled),
.time-slot.active:not(.disabled) {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  z-index: 2;
}

.time-slot.active:not(.disabled) .slot-count {
  color: rgba(255, 255, 255, 0.9);
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

.doctor-availability {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.quota-line {
  font-size: 0.85rem;
  color: #374151;
}

.quota-line.pending {
  color: #9ca3af;
}

.quota-remaining {
  font-weight: 600;
  color: #16a34a;
}

.quota-total {
  color: #6b7280;
  margin-left: 0.15rem;
}

.level-tag {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.level-tag.expert {
  background: #fee2e2;
  color: #b91c1c;
}

.level-tag.normal {
  background: #e0f2fe;
  color: #0369a1;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mini-btn {
  padding: 0.4rem 0.8rem;
  border: 1px solid #667eea;
  background: white;
  color: #667eea;
  border-radius: 6px;
  cursor: pointer;
}

.no-patient {
  background: #f9fafb;
  border: 1px dashed #cbd5e1;
  padding: 1rem;
  border-radius: 10px;
  text-align: center;
}

.primary-btn {
  padding: 0.6rem 1.2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.patient-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.patient-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.patient-card.active {
  border-color: #667eea;
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.15);
}

.patient-name {
  font-weight: 700;
  margin-bottom: 0.3rem;
}

.patient-meta {
  color: #555;
  font-size: 0.9rem;
}

.available {
  color: #28a745;
  font-weight: 600;
}

.submit-section {
  text-align: center;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #f0f0f0;
}

.next-btn {
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

.next-btn:hover {
  opacity: 0.9;
}

.no-doctors {
  text-align: center;
  padding: 2rem;
  color: #999;
  background: #f8f9fa;
  border-radius: 10px;
}

.doctor-card {
  position: relative;
  z-index: 1;
  pointer-events: auto;
}

.header-section {
  position: relative;
  z-index: 100;
}

.time-slot {
  position: relative;
  z-index: 1;
  pointer-events: auto;
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
