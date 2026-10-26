<template>
  <div class="appointment-specialty">
    <div class="appointment-container">
      <div class="header-section">
        <button @click="goBack" class="back-btn">← 返回</button>
        <h1 class="page-title">{{ subDepartmentName }} - 选择专科门诊</h1>
      </div>
      
      <div class="specialty-form">
        <div class="form-section">
          <h2>请选择专科门诊</h2>
          <div class="specialty-grid">
            <div 
              v-for="specialty in specialties" 
              :key="specialty.id"
              @click="selectSpecialty(specialty)"
              class="specialty-card"
            >
              <div class="specialty-icon">{{ specialty.icon }}</div>
              <h3>{{ specialty.name }}</h3>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AppointmentSpecialty',
  data() {
    return {
      departmentId: null,
      departmentName: '',
      subDepartmentId: null,
      subDepartmentName: '',
      specialties: []
    }
  },
  mounted() {
    // 从路由查询参数获取信息
    this.departmentId = parseInt(this.$route.query.departmentId)
    this.departmentName = this.$route.query.departmentName || '内科'
    this.subDepartmentId = parseInt(this.$route.query.subDepartmentId)
    this.subDepartmentName = this.$route.query.subDepartmentName || '消化内科'
    
    // 根据科室ID和子科室ID加载专科门诊
    if (this.departmentId === 3) {
      // 多学科协作诊治
      this.specialties = [
        { id: 3001, name: '多学科联合门诊', icon: '👥' }
      ]
    } else if (this.departmentId === 4) {
      // 感染病科
      this.specialties = [
        { id: 4001, name: '肝病/感染门诊', icon: '🦠' },
        { id: 4002, name: '乙肝临床治愈门诊', icon: '🧬' }
      ]
    } else if (this.departmentId === 6) {
      // 耳鼻咽喉科
      this.specialties = [
        { id: 6001, name: '耳鼻咽喉科门诊', icon: '👂' },
        { id: 6002, name: '耳聋门诊', icon: '🦻' },
        { id: 6003, name: '人工耳蜗植入/听力康复门诊', icon: '🦻' },
        { id: 6004, name: '中耳炎/胆脂瘤门诊', icon: '🩺' },
        { id: 6005, name: '鼻窦炎鼻息肉门诊', icon: '👃' },
        { id: 6006, name: '耳畸形与修复门诊', icon: '🧩' },
        { id: 6007, name: '教学门诊/耳鼻喉科', icon: '📚' }
      ]
    } else if (this.departmentId === 7) {
      // 眼科
      this.specialties = [
        { id: 7001, name: '眼科门诊', icon: '👁️' },
        { id: 7002, name: '眼科激光门诊', icon: '🔦' },
        { id: 7003, name: '角膜移植和干眼专科门诊', icon: '🩺' },
        { id: 7004, name: '青少年近视专科门诊', icon: '🧒' },
        { id: 7005, name: '白内障专科门诊', icon: '⚕️' },
        { id: 7006, name: '高度近视门诊', icon: '👓' },
        { id: 7007, name: '眼科近视激光门诊', icon: '🔦' },
        { id: 7008, name: '眼周肉毒素治疗专科门诊', icon: '💉' },
        { id: 7009, name: '老视矫正门诊', icon: '👓' }
      ]
    } else if (this.departmentId === 9) {
      // 妇产科
      if (this.subDepartmentId === 1) {
        // 妇科
        this.specialties = [
          { id: 9001, name: '妇科门诊', icon: '👩' }
        ]
      } else if (this.subDepartmentId === 2) {
        // 产科
        this.specialties = [
          { id: 9101, name: '早孕门诊（确认妊娠/孕12周前首次检查/先兆流产可能等）', icon: '🤰' },
          { id: 9102, name: '产科门诊', icon: '👶' },
          { id: 9103, name: '遗传咨询（产科）专科门诊', icon: '🧬' },
          { id: 9104, name: '产前诊断（产科）门诊', icon: '🔬' },
          { id: 9105, name: '产后门诊', icon: '🍼' },
          { id: 9106, name: '胎儿医学专科门诊', icon: '🧑‍⚕️' },
          { id: 9107, name: '妊娠合并肾脏病门诊', icon: '🧪' },
          { id: 9108, name: '母婴阻断专科门诊', icon: '🛡️' },
          { id: 9109, name: '母乳喂养专科门诊', icon: '🍼' },
          { id: 9110, name: '妊娠合并结缔组织病门诊', icon: '🦴' }
        ]
      }
    } else if (this.departmentId === 8) {
      // 口腔科
      if (this.subDepartmentId === 1) {
        this.specialties = [
          { id: 8001, name: '口腔内科门诊', icon: '🦷' }
        ]
      } else if (this.subDepartmentId === 2) {
        this.specialties = [
          { id: 8002, name: '口腔颌面部外科门诊', icon: '🔪' }
        ]
      } else if (this.subDepartmentId === 3) {
        this.specialties = [
          { id: 8003, name: '口腔修复科门诊', icon: '🦷' }
        ]
      } else if (this.subDepartmentId === 4) {
        this.specialties = [
          { id: 8004, name: '口腔正畸门诊', icon: '😁' },
          { id: 8005, name: '数字化正畸门诊', icon: '💻' }
        ]
      } else if (this.subDepartmentId === 5) {
        this.specialties = [
          { id: 8006, name: '口腔种植修复门诊', icon: '🦷' }
        ]
      } else if (this.subDepartmentId === 6) {
        this.specialties = [
          { id: 8007, name: '儿童早期错颌畸形专科门诊', icon: '🧒' }
        ]
      } else if (this.subDepartmentId === 7) {
        this.specialties = [
          { id: 8008, name: '儿童牙科门诊', icon: '🧒' }
        ]
      }
    } else if (this.departmentId === 5) {
      // 肿瘤科
      if (this.subDepartmentId === 1) {
        // 肿瘤内科
        this.specialties = [
          { id: 5001, name: '肿瘤内科门诊', icon: '🎗️' },
          { id: 5002, name: '神经内分泌肿瘤专科门诊', icon: '🧬' }
        ]
      } else if (this.subDepartmentId === 2) {
        // 放疗科
        this.specialties = [
          { id: 5101, name: '放疗科门诊', icon: '☢️' }
        ]
      }
    } else if (this.departmentId === 1) {
      // 内科的专科门诊
      if (this.subDepartmentId === 1) {
      // 消化内科的专科门诊
      this.specialties = [
        { id: 1, name: '消化内科门诊', icon: '🏥' },
        { id: 2, name: '自身免疫性胰腺炎（内科）专科门诊', icon: '🔬' },
        { id: 3, name: '食管胃静脉曲张（内科）专科门诊', icon: '💊' },
        { id: 4, name: '脂肪肝专科门诊', icon: '🫀' },
        { id: 5, name: '克罗恩病、溃疡性结肠炎专科门诊', icon: '🩺' },
        { id: 6, name: '胃食管反流病外科治疗专科门诊', icon: '⚕️' }
      ]
    } else if (this.subDepartmentId === 2) {
      // 心血管内科的专科门诊
      this.specialties = [
        { id: 7, name: '心血管内科门诊', icon: '❤️' },
        { id: 8, name: '心脏起搏器专科门诊', icon: '💓' },
        { id: 9, name: '房颤专科门诊', icon: '📊' },
        { id: 10, name: '脉动脉高压专科门诊', icon: '🩺' },
        { id: 11, name: '心脏瓣膜病（内科）专科门诊', icon: '🫀' }
      ]
    } else if (this.subDepartmentId === 3) {
      // 呼吸内科的专科门诊
      this.specialties = [
        { id: 35, name: '呼吸内科门诊', icon: '🫁' }
      ]
    } else if (this.subDepartmentId === 4) {
      // 血液科的专科门诊
      this.specialties = [
        { id: 12, name: '血液科门诊', icon: '🩸' },
        { id: 13, name: '血液骨髓移植门诊', icon: '🔬' },
        { id: 14, name: '血液骨髓移植/CAR-T门诊', icon: '🧬' },
        { id: 15, name: '血液、淋巴瘤门诊', icon: '🩺' },
        { id: 16, name: '白血病专科门诊', icon: '💊' },
        { id: 17, name: 'CAR-T专科门诊', icon: '⚕️' },
        { id: 18, name: '代谢与遗传性疾病门诊', icon: '🧪' }
      ]
    } else if (this.subDepartmentId === 5) {
      // 肾脏病的专科门诊
      this.specialties = [
        { id: 19, name: '肾脏病中心门诊', icon: '🏥' },
        { id: 20, name: '风湿免疫肾病专科门诊', icon: '🦴' },
        { id: 21, name: '腹透专科门诊', icon: '💊' }
      ]
    } else if (this.subDepartmentId === 6) {
      // 神经内科的专科门诊
      this.specialties = [
        { id: 22, name: '神经内科门诊', icon: '🧠' },
        { id: 23, name: '记忆障碍专科门诊', icon: '📝' },
        { id: 24, name: '睡眠障碍（神内）专科门诊', icon: '😴' },
        { id: 25, name: '帕金森与神经程控专科门诊', icon: '🫀' },
        { id: 26, name: '癫痫专科门诊', icon: '⚡' }
      ]
    } else if (this.subDepartmentId === 7) {
      // 内分泌科的专科门诊
      this.specialties = [
        { id: 27, name: '内分泌科门诊', icon: '⚕️' },
        { id: 28, name: '体重管理（内分泌科）门诊', icon: '⚖️' },
        { id: 29, name: '肾上腺疾病（内科）门诊', icon: '🩺' }
      ]
    } else if (this.subDepartmentId === 8) {
      // 风湿免疫科的专科门诊
      this.specialties = [
        { id: 30, name: '风湿免疫科门诊', icon: '🦴' },
        { id: 31, name: '自身炎症性疾病专科门诊', icon: '🔬' },
        { id: 32, name: '白塞病专科门诊', icon: '🩺' },
        { id: 33, name: '系统性硬化症专科门诊', icon: '💊' },
        { id: 34, name: '结缔组织病相关间质性肺病门诊', icon: '🫁' }
      ]
    } else if (this.subDepartmentId === 9) {
      // 老年医学科的专科门诊
      this.specialties = [
        { id: 36, name: '老年内科门诊', icon: '👴' }
      ]
    } else if (this.subDepartmentId === 10) {
      // 普内科的专科门诊
      this.specialties = [
        { id: 37, name: '普内科门诊', icon: '🏥' }
      ]
      }
    } else if (this.departmentId === 2) {
      // 外科的专科门诊
      if (this.subDepartmentId === 1) {
        // 肝胆胰外科的专科门诊
        this.specialties = [
          { id: 101, name: '普外科/肝胆胰外科普通门诊', icon: '🏥' },
          { id: 102, name: '肝胆胰外科门诊', icon: '🔪' },
          { id: 103, name: '肝胆胰介入放射诊治门诊', icon: '📷' }
        ]
      } else if (this.subDepartmentId === 2) {
        // 胃肠外科的专科门诊
        this.specialties = [
          { id: 201, name: '胃肠肿瘤、疝门诊', icon: '🎗️' },
          { id: 202, name: '胃肠甲状腺疝外科门诊', icon: '🍽️' },
          { id: 203, name: '胃肠、疝专科门诊', icon: '🩺' },
          { id: 204, name: '食管裂孔疝', icon: '🫁' },
          { id: 205, name: '减重外科专科门诊', icon: '⚖️' },
          { id: 206, name: '胃肠、疝、阑尾专科门诊', icon: '🔬' }
        ]
      } else if (this.subDepartmentId === 3) {
        // 甲状腺外科的专科门诊
        this.specialties = [
          { id: 301, name: '甲状腺外科门诊', icon: '🦋' }
        ]
      } else if (this.subDepartmentId === 4) {
        // 乳腺外科的专科门诊
        this.specialties = [
          { id: 401, name: '乳腺外科门诊', icon: '💗' }
        ]
      } else if (this.subDepartmentId === 5) {
        // 肿瘤外科的专科门诊
        this.specialties = [
          { id: 501, name: '肿瘤外科门诊', icon: '🎗️' },
          { id: 502, name: '胃肠甲状腺肿瘤门诊', icon: '🍽️' },
          { id: 503, name: '甲状腺肿瘤门诊', icon: '🦋' },
          { id: 504, name: '食管癌综合治疗专科门诊', icon: '🫁' },
          { id: 505, name: '胃肠后腹膜肿瘤门诊', icon: '🔬' }
        ]
      } else if (this.subDepartmentId === 6) {
        // 结直肠外科的专科门诊
        this.specialties = [
          { id: 601, name: '结直肠（肛肠）外科门诊', icon: '🩺' },
          { id: 602, name: '结直肠癌综合诊治门诊', icon: '🎗️' },
          { id: 603, name: '肠功能衰竭专科门诊', icon: '🔬' }
        ]
      } else if (this.subDepartmentId === 7) {
        // 骨科的专科门诊
        this.specialties = [
          { id: 701, name: '骨科门诊（四肢骨折/骨髓炎/未分类/换药/骨质疏松）', icon: '🦴' },
          { id: 702, name: '骨科关节外科（关节疾病/置换/翻修/保髋保膝/矫形）', icon: '🦵' },
          { id: 703, name: '骨科运动医学科（半月板/肩痛肩袖/韧带/肌腱病）', icon: '🏃' },
          { id: 704, name: '骨科脊柱外科（椎间盘突出/脊柱骨折/颈痛背痛腰痛/脊柱侧弯）', icon: '🧠' },
          { id: 705, name: '骨科手外科（腕手足疾患/肢体神经损伤/创面皮瓣修复）', icon: '✋' },
          { id: 706, name: '骨科骨与软组织肿瘤（四肢软组织肿块/骨关节肿瘤/脊柱肿瘤）', icon: '🎗️' },
          { id: 707, name: '骨科足踝外科（足痛/踝扭伤/扁平足/踇外翻/马蹄足）', icon: '🦶' },
          { id: 708, name: '髋关节疼痛专科门诊', icon: '🦵' }
        ]
      } else if (this.subDepartmentId === 8) {
        // 泌尿外科的专科门诊
        this.specialties = [
          { id: 801, name: '泌尿外科门诊', icon: '💧' }
        ]
      } else if (this.subDepartmentId === 9) {
        // 神经外科的专科门诊
        this.specialties = [
          { id: 901, name: '神经外科门诊', icon: '🧠' },
          { id: 902, name: '脑血管疾病专科门诊', icon: '🩸' },
          { id: 903, name: '神经损伤与修复专科门诊', icon: '🩹' },
          { id: 904, name: '三叉神经痛面肌抽搐专科门诊', icon: '🙂' },
          { id: 905, name: '垂体瘤专科门诊', icon: '🧬' },
          { id: 906, name: '神经脊柱脊髓专科门诊', icon: '🦴' },
          { id: 907, name: '神经外科意识障碍专科门诊', icon: '🛌' }
        ]
      } else if (this.subDepartmentId === 10) {
        // 普胸外科的专科门诊
        this.specialties = [
          { id: 1001, name: '普胸外科门诊', icon: '🫁' },
          { id: 1002, name: '食管肿瘤外科治疗专科门诊', icon: '🎗️' }
        ]
      } else if (this.subDepartmentId === 11) {
        // 心脏大血管外科的专科门诊
        this.specialties = [
          { id: 1101, name: '心脏大血管外科门诊', icon: '❤️' }
        ]
      } else if (this.subDepartmentId === 12) {
        // 血管外科的专科门诊
        this.specialties = [
          { id: 1201, name: '血管外科门诊', icon: '🩸' },
          { id: 1202, name: '淋巴水肿外科治疗专科门诊', icon: '🦵' }
        ]
      }
    } else if (this.departmentId === 10) {
      // 生殖医学 - 显示所有专科门诊
      this.specialties = [
        { id: 10001, name: '生殖医学门诊', icon: '👶' },
        { id: 10002, name: '生殖男科门诊', icon: '👨' },
        { id: 10003, name: '遗传咨询（生殖）专科门诊', icon: '🧬' }
      ]
    } else if (this.departmentId === 11) {
      // 儿科 - 显示所有专科门诊
      this.specialties = [
        { id: 11001, name: '儿内科门诊', icon: '🧒' },
        { id: 11002, name: '儿童生长发育门诊', icon: '📏' },
        { id: 11003, name: '儿童骨龄测评门诊', icon: '🦴' },
        { id: 11004, name: '儿童呼吸/过敏门诊', icon: '🫁' },
        { id: 11005, name: '儿童哮喘/咳嗽门诊', icon: '🫁' },
        { id: 11006, name: '儿童脱敏专科门诊', icon: '💉' },
        { id: 11007, name: '儿童消化专科门诊', icon: '🫁' },
        { id: 11008, name: '儿童肥胖专科门诊', icon: '⚖️' },
        { id: 11009, name: '儿童保健门诊', icon: '🏥' },
        { id: 11010, name: '儿童保健/高危儿保健门诊', icon: '🍼' },
        { id: 11011, name: '教学门诊/儿内科', icon: '📚' },
        { id: 11012, name: '儿童糖尿病门诊', icon: '💉' },
        { id: 11013, name: '儿童临床研究随访专科门诊', icon: '🔬' },
        { id: 11014, name: '儿童遗尿症肾脏病专科门诊', icon: '🩺' },
        { id: 11015, name: '儿童遗传病/罕见病门诊', icon: '🧬' }
      ]
    } else if (this.departmentId === 12) {
      // 变态反应（过敏）科 - 显示所有专科门诊
      this.specialties = [
        { id: 12001, name: '变态反应（过敏）科门诊', icon: '🤧' },
        { id: 12002, name: '猫毛过敏症专科门诊', icon: '🐱' }
      ]
    } else if (this.departmentId === 17) {
      // 医学影像科 - 根据子科室显示不同的专科门诊
      if (this.subDepartmentId === 1) {
        // 放射科
        this.specialties = [
          { id: 17001, name: '放射诊断门诊', icon: '📷' }
        ]
      } else if (this.subDepartmentId === 2) {
        // 超声医学
        this.specialties = [
          { id: 17002, name: '超声医学科门诊', icon: '🔊' },
          { id: 17003, name: '产科超声检查门诊', icon: '🤰' },
          { id: 17004, name: '妇科超声检查门诊', icon: '👩' }
        ]
      } else if (this.subDepartmentId === 3) {
        // 核医学科
        this.specialties = [
          { id: 17005, name: '核医学科门诊', icon: '☢️' }
        ]
      }
    } else if (this.departmentId === 19) {
      // 医疗美容科 - 根据子科室（整形外科/整形美容）显示不同的专科门诊
      if (this.subDepartmentId === 1) {
        // 整形外科
        this.specialties = [
          { id: 19001, name: '整形外科门诊', icon: '🩺' },
          { id: 19002, name: '脱发及毛发移植专科门诊', icon: '💇' },
          { id: 19003, name: '面部皮肤激光美容专科门诊', icon: '💡' },
          { id: 19004, name: '体表肿物（整形外科）专科门诊', icon: '🧬' },
          { id: 19005, name: '抽脂塑形（整形外科）专科门诊', icon: '⚖️' },
          { id: 19006, name: '腋臭（整形外科）专科门诊', icon: '💧' },
          { id: 19007, name: '注射微整（整形外科）专科门诊', icon: '💉' },
          { id: 19008, name: '乳房整形美容（整形外科）专科门诊', icon: '👙' }
        ]
      } else if (this.subDepartmentId === 2) {
        // 整形美容
        this.specialties = [
          { id: 19009, name: '整形美容中心门诊', icon: '✨' },
          { id: 19010, name: '体表肿物（整形美容）专科门诊', icon: '🧬' },
          { id: 19011, name: '抽脂塑形（整形美容）专科门诊', icon: '⚖️' },
          { id: 19012, name: '腋臭（整形美容）专科门诊', icon: '💧' },
          { id: 19013, name: '注射微整（整形美容）专科门诊', icon: '💉' },
          { id: 19014, name: '乳房整形美容（整形美容）专科门诊', icon: '👙' },
          { id: 19015, name: '激光美容专科门诊', icon: '💡' },
          { id: 19016, name: '光子嫩肤（整形美容）专科门诊', icon: '🌟' },
          { id: 19017, name: '毛发移植专科门诊', icon: '💇' },
          { id: 19018, name: '女性私密整形专科门诊', icon: '👩' },
          { id: 19019, name: '私密（整形美容）专科门诊', icon: '🔒' }
        ]
      }
    }
  },
  methods: {
    selectSpecialty(specialty) {
      // 跳转到医生选择页面
      this.$router.push({
        name: 'AppointmentDoctor',
        query: {
          departmentId: this.departmentId,
          departmentName: this.departmentName,
          subDepartmentId: this.subDepartmentId,
          subDepartmentName: this.subDepartmentName,
          specialtyId: specialty.id,
          specialtyName: specialty.name
        }
      })
    },
    
    goBack() {
      // 内科/外科/医学影像科/医疗美容科返回子科室，其余返回科室列表
      if (this.departmentId === 1 || this.departmentId === 2 || this.departmentId === 17 || this.departmentId === 19) {
        this.$router.push({
          name: 'AppointmentSubDepartment',
          query: {
            departmentId: this.departmentId,
            departmentName: this.departmentName,
            openSub: this.departmentId === 17 ? 'true' : undefined
          }
        })
      } else {
        this.$router.push({
          name: 'Appointment',
          query: { fromBack: 'true' }
        })
      }
    }
  }
}
</script>

<style scoped>
.appointment-specialty {
  max-width: 1000px;
  margin: 0 auto;
}

.header-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  position: relative;
  z-index: 100;
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
  z-index: 1;
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

.specialty-form {
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

.specialty-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.specialty-card {
  background: #f8f9fa;
  border: 2px solid transparent;
  border-radius: 10px;
  padding: 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  z-index: 1;
  pointer-events: auto;
}

.specialty-card:hover {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-5px);
}

.specialty-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.specialty-card h3 {
  font-size: 0.95rem;
  margin: 0;
  line-height: 1.4;
}
</style>
