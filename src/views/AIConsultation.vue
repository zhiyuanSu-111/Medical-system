<template>
  <div class="ai-consultation">
    <div class="consultation-container">
      <div class="header-section">
        <h1 class="page-title">AI问诊</h1>
        <div class="header-buttons">
          <button @click="showHistoryModal = true" class="history-btn">
            📋 对话历史
          </button>
          <button @click="createNewConversation" class="new-chat-btn">
            ➕ 创建新的对话
          </button>
        </div>
      </div>
      
      <!-- 对话历史弹窗 -->
      <div v-if="showHistoryModal" class="modal-overlay" @click="showHistoryModal = false">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h2>对话历史</h2>
            <button @click="showHistoryModal = false" class="close-btn">✕</button>
          </div>
          <div class="modal-body">
            <div v-if="conversationHistory.length === 0" class="no-history">
              <div class="no-history-icon">📝</div>
              <p>暂无历史记录</p>
              <p class="no-history-hint">开始新的对话后，历史记录将显示在这里</p>
            </div>
            <div v-else class="history-list">
              <div 
                v-for="(conversation, index) in conversationHistory" 
                :key="conversation.id"
                @click="selectConversation(conversation.id)"
                :class="['history-item', { active: currentConversationId === conversation.id }]"
              >
                <div class="history-item-header">
                  <span class="history-icon">💬</span>
                  <div class="history-item-content">
                    <span class="history-title-text">{{ conversation.title || `对话 ${index + 1}` }}</span>
                    <span class="history-time">{{ formatTime(conversation.updatedAt) }}</span>
                  </div>
                </div>
                <button 
                  @click.stop="showDeleteConfirm(conversation.id)"
                  class="delete-btn"
                  title="删除对话"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 删除确认对话框 -->
      <div v-if="showDeleteConfirmModal" class="modal-overlay" @click="cancelDelete">
        <div class="confirm-modal" @click.stop>
          <div class="confirm-header">
            <h3>确认删除</h3>
          </div>
          <div class="confirm-body">
            <div class="confirm-icon">⚠️</div>
            <p class="confirm-message">确定要删除这个对话吗？</p>
            <p class="confirm-hint">删除后无法恢复</p>
          </div>
          <div class="confirm-footer">
            <button @click="cancelDelete" class="cancel-btn">取消</button>
            <button @click="confirmDelete" class="confirm-delete-btn">确认删除</button>
          </div>
        </div>
      </div>
      
      <!-- 聊天区域 -->
      <div class="triage-panel">
        <h3>智能分诊引导</h3>
        <p class="triage-desc">请选择人群后，在人体图上点击大致不适部位，系统会继续追问并结合 AI 对话给出更精准的科室建议。</p>

        <div class="profile-tabs">
          <button
            v-for="profile in bodyProfiles"
            :key="profile.id"
            class="profile-tab-btn"
            :class="{ active: selectedProfile === profile.id }"
            @click="switchProfile(profile.id)"
          >
            {{ profile.icon }} {{ profile.label }}
          </button>
        </div>

        <div class="body-map-wrap">
          <div class="body-map-header">
            <strong>{{ currentProfileMeta.label }}人体图</strong>
            <div class="map-view-switch">
              <button
                class="map-view-btn"
                :class="{ active: selectedBodyView === 'front' }"
                @click="switchBodyView('front')"
              >
                正面
              </button>
              <button
                class="map-view-btn"
                :class="{ active: selectedBodyView === 'back' }"
                @click="switchBodyView('back')"
              >
                背面
              </button>
            </div>
          </div>
          <div class="body-map-canvas" :class="{ 'preset-map-canvas': usePresetBodyMap }" :style="presetCanvasStyle">
            <div v-if="!usePresetBodyMap" class="body-bg-ring"></div>
            <div v-if="!usePresetBodyMap" class="body-bg-ring inner"></div>
            <img
              v-if="!bodyImageUnavailable"
              :class="['body-figure', { 'full-layout': usePresetBodyMap }]"
              :style="presetFigureStyle"
              :src="currentBodyImage"
              :alt="`${currentProfileMeta.label}${selectedBodyView === 'front' ? '正面' : '背面'}人体图`"
              @error="onBodyImageError"
            />
            <div v-else class="body-image-missing">
              <div class="body-silhouette">{{ currentProfileMeta.silhouette }}</div>
              <p>未找到人体图资源，请将图片放入 `public/triage/` 目录。</p>
            </div>
            <button
              v-if="usePresetBodyMap"
              v-for="zone in currentBodyZones"
              :key="`hotspot-${selectedProfile}-${zone.id}`"
              class="body-zone-hotspot"
              :class="{ active: selectedBodyPart && selectedBodyPart.id === zone.id }"
              :style="getHotspotStyle(zone)"
              @click="selectBodyPart(zone)"
              :title="zone.label"
              :aria-label="zone.label"
            >
              <span class="sr-only">{{ zone.label }}</span>
            </button>
            <button
              v-else
              v-for="zone in currentBodyZones"
              :key="`${selectedProfile}-${zone.id}`"
              class="body-zone-callout"
              :class="[zone.side || (zone.x >= 50 ? 'right' : 'left'), { active: selectedBodyPart && selectedBodyPart.id === zone.id }]"
              :style="getZoneStyle(zone)"
              @click="selectBodyPart(zone)"
            >
              <span class="callout-label">{{ zone.label }}</span>
              <span class="callout-end-dot"></span>
              <span class="callout-line"></span>
            </button>
          </div>
        </div>

        <div v-if="selectedBodyPart && triageStage !== 'done'" class="followup-box">
          <div class="followup-question">
            {{ currentFollowupQuestion.question }}
          </div>
          <div class="followup-options">
            <button
              v-for="option in currentFollowupQuestion.options"
              :key="option"
              class="followup-option-btn"
              @click="answerFollowup(option)"
            >
              {{ option }}
            </button>
          </div>
        </div>

        <div v-if="triageStage === 'done' || recommendedDepartment" class="triage-result">
          <p>推荐挂号科室：<strong>{{ recommendedDepartment }}</strong></p>
          <p v-if="firstRecommendedDepartmentRaw" class="triage-recommended-first">
            第一个推荐科室：<strong>{{ firstRecommendedDepartmentRaw }}</strong>
            <span v-if="firstRecommendedDepartmentCanonical && firstRecommendedDepartmentCanonical !== firstRecommendedDepartmentRaw">
              （本院目录：<strong>{{ firstRecommendedDepartmentCanonical }}</strong>）
            </span>
          </p>
          <p class="triage-result-hint">可直接点击下方按钮进入挂号流程，也可继续和 AI 详细沟通病情。</p>
          <button class="go-appointment-btn" @click="goToRecommendedOrAppointment">
            一键前往挂号
          </button>
          <button
            v-if="firstRecommendedDepartmentCanonical"
            class="go-recommended-btn"
            @click="goToFirstRecommendedDepartment"
          >
            前往 {{ firstRecommendedDepartmentCanonical }} 挂号
          </button>
        </div>
      </div>

      <div class="consultation-box">
        <div class="chat-area" ref="chatArea">
          <div v-for="(message, index) in messages" :key="index" :class="['message', message.type]">
            <div class="message-content">
              <div class="message-avatar">{{ message.type === 'user' ? '👤' : '🤖' }}</div>
              <div class="message-text">
                {{ message.text }}
                <div v-if="message.file" class="file-info">
                  {{ message.file.name }} ({{ formatFileSize(message.file.size) }})
                </div>
              </div>
            </div>
          </div>
          <div v-if="isLoading" class="message ai">
            <div class="message-content">
              <div class="message-avatar">🤖</div>
              <div class="message-text loading">
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
                AI正在思考中...
              </div>
            </div>
          </div>
        </div>

        <div v-if="firstRecommendedDepartmentCanonical" class="chat-action-bar">
          <button class="go-recommended-btn" @click="goToFirstRecommendedDepartment">
            前往 {{ firstRecommendedDepartmentCanonical }} 挂号
          </button>
        </div>
        
        <div class="input-area">
          <button
            v-if="speechSupported"
            class="mic-btn"
            :class="{ recording: isRecording }"
            @click="toggleVoiceInput"
            :disabled="isLoading"
            :title="isRecording ? '停止语音输入' : '语音输入'"
          >
            {{ isRecording ? '停止' : '语音输入' }}
          </button>
          <label class="file-upload-btn" :class="{ 'has-file': uploadedFile }">
            <input
              type="file"
              ref="fileInput"
              @change="handleFileUpload"
              accept="image/*"
              style="display: none"
              :disabled="isLoading"
            />
            {{ uploadedFile ? uploadedFile.name : '图片上传' }}
          </label>
          <input 
            v-model="inputMessage" 
            @keyup.enter="sendMessage"
            type="text" 
            :placeholder="canInputFreeText ? '可继续补充症状、病史、用药情况...' : '请先完成上方人体部位选择与追问'"
            class="message-input"
            :disabled="isLoading || isRecording || !canInputFreeText"
          />
          <button @click="sendMessage" class="send-btn" :disabled="isLoading || !canInputFreeText">
            {{ isLoading ? '发送中...' : '发送' }}
          </button>
        </div>
        <div v-if="speechSupported" class="voice-hint">
          <span v-if="isRecording">正在聆听中…请说话</span>
          <span v-if="voiceError" class="voice-error">（{{ voiceError }}）</span>
        </div>
      </div>
      
      <div class="quick-questions" v-if="canInputFreeText">
        <h3>常见问题</h3>
        <div class="question-tags">
          <span 
            v-for="(question, index) in quickQuestions" 
            :key="index"
            @click="selectQuickQuestion(question)"
            class="question-tag"
          >
            {{ question }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

/**
 * 口语/简称 → 与本系统在线挂号目录一致的规范科室名。
 * 新增判定时只改这一处，normalizeDeptAlias 与界面说明会同步生效。
 */
const DEPARTMENT_CANONICAL_ALIASES = {
  心内科: '心血管内科',
  心脏内科: '心血管内科',
  循环内科: '心血管内科',
  冠心病科: '心血管内科',
  消内: '消化内科',
  消化内: '消化内科',
  呼内: '呼吸内科',
  呼吸内: '呼吸内科',
  神内: '神经内科',
  神外: '神经外科',
  肾内科: '肾脏病',
  肾病内科: '肾脏病',
  肾脏内科: '肾脏病',
  肾病科: '肾脏病',
  泌尿内科: '肾脏病',
  耳鼻喉科: '耳鼻咽喉科',
  耳鼻喉: '耳鼻咽喉科',
  小儿科: '儿科',
  儿童科: '儿科',
  儿内: '儿科',
  妇产: '妇产科',
  传染科: '感染病科',
  感染科: '感染病科',
  肝病科: '感染病科',
  心理科: '精神科卫生科',
  精神科: '精神科卫生科',
  精神心理科: '精神科卫生科',
  影像科: '医学影像科',
  放射科: '医学影像科',
  超声科: '医学影像科',
  核医学科: '医学影像科',
  医美科: '医疗美容科',
  整形美容科: '医疗美容科',
  变态反应科: '变态反应（过敏）科',
  过敏科: '变态反应（过敏）科',
  药学门诊: '临床药学',
  药剂科: '临床药学',
  护理门诊: '专科护理',
  手外: '骨科',
  手外科: '骨科',
  足踝: '骨科',
  足踝外科: '骨科'
}

export default {
  name: 'AIConsultation',
  computed: {
    canInputFreeText() {
      // 允许两种场景继续输入：
      // 1) 已选择人体部位并进入引导/追问
      // 2) 已完成推荐（无论是分诊流程完成，还是 AI 对话中直接推荐出科室）
      // 3) 从对话历史进入某段对话：只要该对话已有用户消息，就允许继续输入
      const hasUserMessage = Array.isArray(this.messages) && this.messages.some(m => m && m.type === 'user' && String(m.text || '').trim())
      return (
        Boolean(this.selectedBodyPart) ||
        this.triageStage === 'done' ||
        Boolean(this.recommendedDepartment) ||
        hasUserMessage
      )
    },
    currentFollowupQuestion() {
      return this.followupQuestions[this.followupIndex] || this.followupQuestions[this.followupQuestions.length - 1]
    },
    currentProfileMeta() {
      return this.bodyProfiles.find(item => item.id === this.selectedProfile) || this.bodyProfiles[0]
    },
    currentBodyZones() {
      const views = this.currentProfileMeta.views || {}
      return views[this.selectedBodyView] || []
    },
    currentBodyImage() {
      const key = `${this.selectedProfile}_${this.selectedBodyView}`
      const map = {
        male_front: '/triage/male_front.png',
        male_back: '/triage/male_back.png',
        female_front: '/triage/female_front.png',
        female_back: '/triage/female_back.png',
        child_front: '/triage/child_front.png',
        child_back: '/triage/child_back.png'
      }
      return map[key] || ''
    },
    usePresetBodyMap() {
      return true
    },
    currentBodyMapKey() {
      return `${this.selectedProfile}_${this.selectedBodyView}`
    },
    presetMapLayout() {
      const map = {
        male_front: { offsetX: 0, offsetY: 0, figureHeight: 100, figureTop: 50, hitScale: 1.5 },
        male_back: { offsetX: 0, offsetY: 0, figureHeight: 100, figureTop: 50, hitScale: 1.5 },
        female_front: { offsetX: 0, offsetY: 0, figureHeight: 100, figureTop: 50, hitScale: 1.5 },
        female_back: { offsetX: 0, offsetY: 0, figureHeight: 100, figureTop: 50, hitScale: 1.5 },
        child_front: { offsetX: 0, offsetY: 0, figureHeight: 88, figureTop: 50, hitScale: 1.7 },
        child_back: { offsetX: 0, offsetY: 0, figureHeight: 88, figureTop: 50, hitScale: 1.7 }
      }
      return map[this.currentBodyMapKey] || map.male_front
    },
    presetCanvasStyle() {
      return this.usePresetBodyMap
        ? {
            '--figure-height': `${this.presetMapLayout.figureHeight}%`,
            '--figure-top': `${this.presetMapLayout.figureTop}%`
          }
        : {}
    },
    presetFigureStyle() {
      return this.usePresetBodyMap
        ? {
            '--figure-height': `${this.presetMapLayout.figureHeight}%`,
            '--figure-top': `${this.presetMapLayout.figureTop}%`
          }
        : {}
    },
    presetMapHotspotOffset() {
      const layout = this.presetMapLayout || {}
      return {
        x: layout.offsetX || 0,
        y: layout.offsetY || 0
      }
    }
    ,
    /** AI 原文中「第一个推荐科室」片段（未做本院目录映射） */
    firstRecommendedDepartmentRaw() {
      if (!this.recommendedDepartment) return ''
      const first =
        String(this.recommendedDepartment)
          .split(/[\/、，,;；]/)[0]
          ?.replace(/\*\*/g, '')
          .trim() || ''
      if (!this._isPlausibleSingleDepartmentName(first)) return ''
      return first
    },
    /** 映射到本院挂号目录后的规范名（用于按钮文案与路由） */
    firstRecommendedDepartmentCanonical() {
      const raw = this.firstRecommendedDepartmentRaw
      if (!raw) return ''
      return this.normalizeDeptAlias(raw)
    }
  },
  data() {
    return {
      lastDeptMappingNoticeKey: '',
      messages: [
        {
          type: 'ai',
          text: '您好！我是AI问诊助手。请先在上方人体示意图选择不适部位，我会继续追问并推荐就诊科室。'
        }
      ],
      inputMessage: '',
      isLoading: false,
      // 语音输入（Web Speech API）
      speechSupported: false,
      isRecording: false,
      voiceError: '',
      recognition: null,
      // 文件上传
      uploadedFile: null,
      currentConversationId: null,
      conversationHistory: [],
      showHistoryModal: false,
      showDeleteConfirmModal: false,
      deleteTargetId: null,
      triageStage: 'idle',
      selectedBodyPart: null,
      followupIndex: 0,
      followupAnswers: {
        symptomType: '',
        duration: '',
        severity: ''
      },
      recommendedDepartment: '',
      selectedBodyView: 'front',
      bodyImageUnavailable: false,
      followupQuestions: [
        {
          key: 'symptomType',
          question: '请问主要不适类型是？',
          options: ['疼痛', '肿胀/包块', '发热', '功能受限', '其他']
        },
        {
          key: 'duration',
          question: '症状持续多久了？',
          options: ['<24小时', '1-3天', '1周内', '1周以上']
        },
        {
          key: 'severity',
          question: '当前不适程度如何？',
          options: ['轻度', '中度', '重度', '非常严重']
        }
      ],
      selectedProfile: 'male',
      bodyProfiles: [
        {
          id: 'male',
          label: '男性',
          icon: '👨',
          silhouette: '🧍‍♂️',
          views: {
            front: [
              { id: 'male-brain-front', label: '脑部', region: 'brain', icon: '🧠', x: 56, y: 10, side: 'right', hitX: 52, hitY: 9.6, hitW: 106, hitH: 96, hitRadius: '48%' },
              { id: 'male-chest-front', label: '胸部', region: 'chest', icon: '🫁', x: 58, y: 27, side: 'right', hitX: 52, hitY: 26.5, hitW: 108, hitH: 84, hitRadius: '45%' },
              { id: 'male-upper-limb-front', label: '上肢', region: 'upper_limb', icon: '💪', x: 60, y: 39, side: 'right', hitX: 61.5, hitY: 39, hitW: 62, hitH: 118, hitRadius: '999px', hitRotate: -10 },
              { id: 'male-hand-front', label: '手', region: 'hand', icon: '✋', x: 60, y: 55, side: 'right', hitX: 66, hitY: 54.5, hitW: 68, hitH: 78, hitRadius: '40%' },
              { id: 'male-abdomen-front', label: '腹部', region: 'abdomen', icon: '🩺', x: 48, y: 42, side: 'left', hitX: 51, hitY: 41.5, hitW: 98, hitH: 92, hitRadius: '42%' },
              { id: 'male-genital-front', label: '男性生殖部', region: 'pelvis_male', icon: '⚕️', x: 48, y: 54, side: 'left', hitX: 51, hitY: 54.5, hitW: 70, hitH: 56, hitRadius: '45%' },
              { id: 'male-lower-limb-front', label: '下肢', region: 'lower_limb', icon: '🦵', x: 46, y: 74, side: 'left', hitX: 49, hitY: 73.5, hitW: 96, hitH: 190, hitRadius: '999px' },
              { id: 'male-foot-front', label: '脚', region: 'foot', icon: '🦶', x: 47, y: 93, side: 'left', hitX: 49, hitY: 92.8, hitW: 82, hitH: 52, hitRadius: '40%' }
            ],
            back: [
              { id: 'male-brain-back', label: '脑部', region: 'brain', icon: '🧠', x: 79, y: 12, side: 'right', hitX: 50, hitY: 10.5, hitW: 106, hitH: 96, hitRadius: '48%' },
              { id: 'male-back-back', label: '背部', region: 'back', icon: '🦴', x: 78, y: 30, side: 'right', hitX: 50, hitY: 31, hitW: 108, hitH: 120, hitRadius: '42%' },
              { id: 'male-upper-limb-back', label: '上肢', region: 'upper_limb', icon: '💪', x: 79, y: 43, side: 'right', hitX: 61, hitY: 39.5, hitW: 64, hitH: 120, hitRadius: '999px', hitRotate: -9 },
              { id: 'male-hand-back', label: '手', region: 'hand', icon: '✋', x: 83, y: 55, side: 'right', hitX: 66, hitY: 54, hitW: 70, hitH: 78, hitRadius: '40%' },
              { id: 'male-neck-back', label: '颈部', region: 'neck', icon: '🦴', x: 18, y: 20, side: 'left', hitX: 50, hitY: 18, hitW: 72, hitH: 44, hitRadius: '999px' },
              { id: 'male-abdomen-back', label: '腹部', region: 'abdomen', icon: '🩺', x: 13, y: 44, side: 'left', hitX: 49.5, hitY: 41.8, hitW: 94, hitH: 88, hitRadius: '44%' },
              { id: 'male-hip-back', label: '臀部', region: 'buttock', icon: '🦴', x: 13, y: 54, side: 'left', hitX: 49.5, hitY: 54.2, hitW: 88, hitH: 64, hitRadius: '45%' },
              { id: 'male-lower-limb-back', label: '下肢', region: 'lower_limb', icon: '🦵', x: 18, y: 74, side: 'left', hitX: 49, hitY: 73.5, hitW: 96, hitH: 190, hitRadius: '999px' },
              { id: 'male-foot-back', label: '脚', region: 'foot', icon: '🦶', x: 17, y: 88, side: 'left', hitX: 49, hitY: 92.8, hitW: 82, hitH: 52, hitRadius: '40%' }
            ]
          }
        },
        {
          id: 'female',
          label: '女性',
          icon: '👩',
          silhouette: '🧍‍♀️',
          views: {
            front: [
              { id: 'female-brain-front', label: '脑部', region: 'brain', icon: '🧠', x: 81, y: 12, side: 'right', hitX: 50, hitY: 10.8, hitW: 104, hitH: 96, hitRadius: '48%' },
              { id: 'female-chest-front', label: '胸部', region: 'chest', icon: '🫁', x: 77, y: 30, side: 'right', hitX: 51.5, hitY: 28, hitW: 106, hitH: 86, hitRadius: '45%' },
              { id: 'female-upper-limb-front', label: '上肢', region: 'upper_limb', icon: '💪', x: 78, y: 42, side: 'right', hitX: 60.5, hitY: 40, hitW: 62, hitH: 116, hitRadius: '999px', hitRotate: -10 },
              { id: 'female-hand-front', label: '手', region: 'hand', icon: '✋', x: 84, y: 57, side: 'right', hitX: 65.5, hitY: 55, hitW: 68, hitH: 80, hitRadius: '40%' },
              { id: 'female-abdomen-front', label: '腹部', region: 'abdomen', icon: '🩺', x: 16, y: 44, side: 'left', hitX: 50.5, hitY: 41.1, hitW: 98, hitH: 88, hitRadius: '42%' },
              { id: 'female-genital-front', label: '女性生殖部', region: 'pelvis_female', icon: '⚕️', x: 9, y: 55, side: 'left', hitX: 50.5, hitY: 52.4, hitW: 74, hitH: 60, hitRadius: '45%' },
              { id: 'female-lower-limb-front', label: '下肢', region: 'lower_limb', icon: '🦵', x: 18, y: 74, side: 'left', hitX: 49.5, hitY: 74, hitW: 94, hitH: 186, hitRadius: '999px' },
              { id: 'female-foot-front', label: '脚', region: 'foot', icon: '🦶', x: 18, y: 88, side: 'left', hitX: 46.8, hitY: 92.8, hitW: 80, hitH: 54, hitRadius: '40%' }
            ],
            back: [
              { id: 'female-brain-back', label: '脑部', region: 'brain', icon: '🧠', x: 78, y: 12, side: 'right', hitX: 50, hitY: 10.8, hitW: 104, hitH: 96, hitRadius: '48%' },
              { id: 'female-chest-back', label: '胸部', region: 'chest', icon: '🫁', x: 75, y: 30, side: 'right', hitX: 51, hitY: 30, hitW: 102, hitH: 88, hitRadius: '43%' },
              { id: 'female-upper-limb-back', label: '上肢', region: 'upper_limb', icon: '💪', x: 76, y: 42, side: 'right', hitX: 60.5, hitY: 40, hitW: 62, hitH: 116, hitRadius: '999px', hitRotate: -10 },
              { id: 'female-hand-back', label: '手', region: 'hand', icon: '✋', x: 80, y: 55, side: 'right', hitX: 65.5, hitY: 54.5, hitW: 66, hitH: 78, hitRadius: '40%' },
              { id: 'female-neck-back', label: '颈部', region: 'neck', icon: '🦴', x: 18, y: 20, side: 'left', hitX: 50, hitY: 18.5, hitW: 70, hitH: 44, hitRadius: '999px' },
              { id: 'female-abdomen-back', label: '腹部', region: 'abdomen', icon: '🩺', x: 12, y: 44, side: 'left', hitX: 50, hitY: 41.8, hitW: 94, hitH: 84, hitRadius: '42%' },
              { id: 'female-hip-back', label: '臀部', region: 'buttock', icon: '🦴', x: 12, y: 54, side: 'left', hitX: 50, hitY: 53.2, hitW: 86, hitH: 64, hitRadius: '45%' },
              { id: 'female-lower-limb-back', label: '下肢', region: 'lower_limb', icon: '🦵', x: 18, y: 74, side: 'left', hitX: 49.5, hitY: 74, hitW: 92, hitH: 184, hitRadius: '999px' },
              { id: 'female-foot-back', label: '脚', region: 'foot', icon: '🦶', x: 17, y: 88, side: 'left', hitX: 46.8, hitY: 92.8, hitW: 78, hitH: 54, hitRadius: '40%' }
            ]
          }
        },
        {
          id: 'child',
          label: '儿童',
          icon: '🧒',
          silhouette: '🧒',
          views: {
            front: [
              { id: 'child-brain-front', label: '脑部', region: 'brain', icon: '🧠', x: 80, y: 12, side: 'right', hitX: 50, hitY: 14.5, hitW: 92, hitH: 82, hitRadius: '48%' },
              { id: 'child-chest-front', label: '胸部', region: 'chest_child', icon: '🫁', x: 75, y: 30, side: 'right', hitX: 51, hitY: 31.5, hitW: 94, hitH: 78, hitRadius: '45%' },
              { id: 'child-upper-limb-front', label: '上肢', region: 'upper_limb', icon: '💪', x: 74, y: 42, side: 'right', hitX: 59.5, hitY: 43, hitW: 58, hitH: 106, hitRadius: '999px', hitRotate: -9 },
              { id: 'child-hand-front', label: '手', region: 'hand', icon: '✋', x: 77, y: 55, side: 'right', hitX: 64, hitY: 57, hitW: 62, hitH: 72, hitRadius: '40%' },
              { id: 'child-abdomen-front', label: '腹部', region: 'abdomen_child', icon: '🩺', x: 13, y: 44, side: 'left', hitX: 50, hitY: 46, hitW: 90, hitH: 80, hitRadius: '42%' },
              { id: 'child-genital-front', label: '儿童生殖部', region: 'pelvis_child', icon: '⚕️', x: 8, y: 55, side: 'left', hitX: 52.6, hitY: 55.9, hitW: 66, hitH: 52, hitRadius: '44%', hitShiftX: -26.5 },
              { id: 'child-lower-limb-front', label: '下肢', region: 'limb_child', icon: '🦵', x: 16, y: 74, side: 'left', hitX: 47.5, hitY: 67.9, hitW: 68, hitH: 118.8, hitRadius: '999px' },
              { id: 'child-foot-front', label: '脚', region: 'foot', icon: '🦶', x: 16, y: 88, side: 'left', hitX: 46.5, hitY: 84.6, hitW: 72, hitH: 50, hitRadius: '40%' }
            ],
            back: [
              { id: 'child-brain-back', label: '脑部', region: 'brain', icon: '🧠', x: 79, y: 12, side: 'right', hitX: 50, hitY: 14.5, hitW: 92, hitH: 82, hitRadius: '48%' },
              { id: 'child-chest-back', label: '胸部', region: 'chest_child', icon: '🫁', x: 74, y: 30, side: 'right', hitX: 51, hitY: 33, hitW: 92, hitH: 80, hitRadius: '44%' },
              { id: 'child-upper-limb-back', label: '上肢', region: 'upper_limb', icon: '💪', x: 74, y: 42, side: 'right', hitX: 59.5, hitY: 43, hitW: 58, hitH: 106, hitRadius: '999px', hitRotate: -9 },
              { id: 'child-hand-back', label: '手', region: 'hand', icon: '✋', x: 77, y: 55, side: 'right', hitX: 64, hitY: 57, hitW: 62, hitH: 72, hitRadius: '40%' },
              { id: 'child-neck-back', label: '颈部', region: 'neck', icon: '🦴', x: 18, y: 20, side: 'left', hitX: 50, hitY: 22, hitW: 62, hitH: 40, hitRadius: '999px' },
              { id: 'child-abdomen-back', label: '腹部', region: 'abdomen_child', icon: '🩺', x: 13, y: 44, side: 'left', hitX: 50, hitY: 46, hitW: 86, hitH: 78, hitRadius: '42%', hitShiftY: -10 },
              { id: 'child-hip-back', label: '臀部', region: 'buttock', icon: '🦴', x: 13, y: 54, side: 'left', hitX: 50, hitY: 59, hitW: 76, hitH: 58, hitRadius: '44%', hitShiftX: 5, hitShiftY: -10 },
              { id: 'child-lower-limb-back', label: '下肢', region: 'limb_child', icon: '🦵', x: 17, y: 74, side: 'left', hitX: 47.5, hitY: 69.8, hitW: 76, hitH: 133.2, hitRadius: '999px' },
              { id: 'child-foot-back', label: '脚', region: 'foot', icon: '🦶', x: 17, y: 88, side: 'left', hitX: 46.5, hitY: 84.6, hitW: 70, hitH: 50, hitRadius: '40%' }
            ]
          }
        }
      ],
      quickQuestions: [
        '头痛',
        '发烧',
        '咳嗽',
        '胃痛',
        '失眠',
        '疲劳'
      ]
    }
  },
  async mounted() {
    await this.loadConversationHistory()
    this.initSpeechRecognition()
    // 每次进入页面都开启全新对话，不自动恢复上一次推荐或聊天内容
    // 历史记录仍可在“对话历史”弹窗中手动查看/切换
    this.createNewConversation()
  },
  methods: {
    sanitizeDepartmentCandidate(name) {
      let s = String(name || '')
        .replace(/\*\*/g, '')
        .replace(/\s+/g, '')
        .trim()
      if (!s) return ''

      // 去掉模型常见的引导词，避免把“建议尽快就诊呼吸内科”当成科室名
      const LEADING_HINT_RE = /^(?:请|建议(?:您|你|患者)?|可(?:先|优先|考虑)?|宜|优先|首先|先|尽快|及时|立即|前往|到|去|往|至|就诊|挂号|就医|诊|挂)+/
      while (LEADING_HINT_RE.test(s)) {
        s = s.replace(LEADING_HINT_RE, '').trim()
      }
      return s
    },
    parseDbTimestamp(ts) {
      if (!ts) return null
      const s = String(ts).trim()
      // SQLite CURRENT_TIMESTAMP: "YYYY-MM-DD HH:mm:ss"（UTC）
      if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(s)) {
        return new Date(s.replace(' ', 'T') + 'Z')
      }
      // "YYYY-MM-DDTHH:mm:ss"（无时区标记时按 UTC 处理，避免固定差 8 小时）
      if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(s)) {
        return new Date(s + 'Z')
      }
      // 其他情况交给浏览器解析（含 ISO 8601 带 Z/时区偏移）
      const d = new Date(s)
      return Number.isNaN(d.getTime()) ? null : d
    },
    rehydrateConversationState() {
      // 从已加载的对话消息中尽可能恢复“推荐科室/完成状态”
      try {
        if (!Array.isArray(this.messages) || this.messages.length === 0) return
        // 从后往前找：优先取最新的 AI 推荐
        for (let i = this.messages.length - 1; i >= 0; i--) {
          const m = this.messages[i]
          if (!m || m.type !== 'ai') continue
          const dept = this.extractRecommendedDepartment(m.text)
          if (dept) {
            this.recommendedDepartment = dept
            this.triageStage = 'done'
            return
          }
        }
      } catch (e) {
        // ignore
      }
    },
    /**
     * 是否为像科室/门诊的片段（过滤「检查明确原因」等就诊动作描述）。
     */
    _isPlausibleSingleDepartmentName(s) {
      const t = this.sanitizeDepartmentCandidate(s)
      if (!t || t.length > 24) return false
      const compact = t.replace(/\s+/g, '')
      if (DEPARTMENT_CANONICAL_ALIASES[compact]) return true
      if (/(?:建议|尽快|及时|立即|就诊|挂号|前往|可考虑|优先|首选|首先|请)/.test(t)) return false
      if (/检查明确|明确原因|完善检查|对症处理|进一步检查/.test(t)) return false
      if (/原因|病因|排除|复查观察|注意休息/.test(t) && !/(?:科|门诊|中心)/.test(t)) return false
      if (/^(检查|化验|复查|观察)(?!科)/.test(t)) return false
      return (
        /(科|中心|门诊|诊部|诊室)$/.test(t) ||
        /^(急诊|内科|外科|妇科|产科|儿科)(?:科)?$/.test(t)
      )
    },
    /** 支持「呼吸内科/心血管内科」等组合，任一段不合法则整体不通过 */
    isPlausibleDepartmentName(s) {
      const raw = String(s || '').trim().replace(/\*\*/g, '')
      if (!raw) return false
      const parts = raw.split(/[\/、，,;；]/).map((p) => p.trim()).filter(Boolean)
      const chunks = parts.length ? parts : [raw]
      return chunks.every((p) => this._isPlausibleSingleDepartmentName(p))
    },
    _finalizeDepartmentExtract(candidate) {
      const d = String(candidate || '').trim()
      if (!d) return ''
      return this.isPlausibleDepartmentName(d) ? d : ''
    },
    extractRecommendedDepartment(text) {
      if (!text) return ''
      const s = String(text)
      // 单科推荐名合理上限（本院目录最长约十字；过长多为整句误匹配）
      const MAX_SINGLE_DEPT_LEN = 15
      // 更长科室名必须写在「内科」等短后缀之前，否则会出现「经+内科」误匹配成「经内科」
      const DEPT_SUFFIX =
        '(?:神经内科|神经外科|心血管内科|消化内科|呼吸内科|内分泌科|风湿免疫科|老年医学科|普内科|心内科|肾内科|血液科|肾脏病|' +
        '耳鼻咽喉科|耳鼻喉科|康复医学科|全科医疗科|精神科卫生科|感染病科|医学影像科|资深专家门诊|医疗美容科|多学科协作诊治|专科护理|临床医学|' +
        '内科|外科|儿科|妇科|急诊科|骨科|皮肤科|口腔科|眼科|疼痛科|肿瘤科|麻醉科|营养科|病理科|高压氧|生殖医学|门诊)'
      const FALSE_DEPT_FRAGMENTS = new Set(['经内科', '神内科', '及内科', '的内科', '是内科'])

      const pickFirstDept = (raw) => {
        const cleaned = String(raw || '')
          .replace(/[（(].*?[）)]/g, '') // 去掉括号解释
          .replace(/[\u26A0-\u26FF]/g, '') // 去掉警告符号等
          .trim()
        if (!cleaned) return ''
        // 只取第一个候选科室
        return cleaned
          .split(/[\/、，,;；或]/)[0]
          .trim()
          .replace(/^(?:挂|挂号|至|到|去|就诊)+/, '')
          .trim()
      }

      /** 在长串或误匹配结果中再抽一次「短科室名」（避免 /g 一次 exec 吞掉整句后无法继续匹配） */
      const refineDeptChunk = (raw) => {
        let d = pickFirstDept(raw)
        if (!d) return ''
        if (d.length <= MAX_SINGLE_DEPT_LEN) return d
        const fromStart = new RegExp(`^([\\u4e00-\\u9fa5\\d]{1,12}${DEPT_SUFFIX})`)
        const hits = []
        for (let i = 0; i < d.length; i++) {
          const m = d.slice(i).match(fromStart)
          if (!m) continue
          const x = pickFirstDept(m[1])
          if (!x || x.length > MAX_SINGLE_DEPT_LEN || FALSE_DEPT_FRAGMENTS.has(x)) continue
          hits.push({ dept: x, len: x.length, index: i })
        }
        if (!hits.length) return ''
        // 同一长句里多个「xx科」碎片时，取最短名（通常是真正科室），同长度则取更靠后的片段（多紧跟在「挂」后）
        hits.sort((a, b) => a.len - b.len || b.index - a.index)
        return hits[0].dept
      }

      // 1) 优先 Markdown 加粗 **神经内科**（模型常用，且不会被整句前缀污染）
      const boldRe = /\*\*([^*]{1,48})\*\*/g
      let boldBest = { index: Infinity, dept: '' }
      let bm
      while ((bm = boldRe.exec(s)) !== null) {
        const chunk = bm[1].trim()
        if (!chunk || chunk.length > MAX_SINGLE_DEPT_LEN + 6) continue
        if (!/(?:科|门诊|诊)/.test(chunk)) continue
        const dept = refineDeptChunk(chunk)
        if (dept && bm.index < boldBest.index) boldBest = { index: bm.index, dept }
      }
      if (boldBest.dept) {
        const v = this._finalizeDepartmentExtract(boldBest.dept)
        if (v) return v
      }

      const normalized = s.replace(/\*\*/g, '').replace(/\*/g, '')

      // 常见表述：推荐挂号科室：xx / 建议首选挂xx / 建议先挂xx / 建议挂xx / 可考虑挂xx
      const patterns = [
        /推荐(?:挂号)?科室[：:\s]*([^\n。；;]+)/g,
        /建议(?:优先)?(?:挂号|就诊)[：:\s]*([^\n。；;]+)/g,
        // 兼容：建议您首先挂xx / 建议你先挂xx / 建议患者优先挂号xx
        /建议(?:您|你|患者)?(?:\s*)?(?:首选|优先|首先|先)?(?:\s*)?(?:挂号|挂|就诊)[：:\s]*([^\n。；;]+)/g,
        // 兜底：允许“建议”与“挂/挂号”之间夹少量字（如“建议您首先挂”）
        /建议.{0,6}?(?:首选|优先|首先|先)?(?:\s*)?(?:挂号|挂|就诊)[：:\s]*([^\n。；;]+)/g,
        /首选(?:挂号|就诊)?[：:\s]*([^\n。；;]+)/g,
        /可考虑(?:挂号|就诊)?[：:\s]*([^\n。；;]+)/g
      ]

      let best = { index: Infinity, dept: '' }
      for (const re of patterns) {
        re.lastIndex = 0
        let m
        while ((m = re.exec(normalized))) {
          const dept = refineDeptChunk(m[1])
          if (!dept) continue
          if (m.index < best.index) best = { index: m.index, dept }
          break
        }
      }

      // 全文扫描：旧逻辑用「从左起第一个匹配」会把整句吞到第一个「xx科」；改为收集后只保留合理长度的候选，再按出现顺序取第一个
      const deptNameRegex = new RegExp(
        `([^\\s，,。；;\\n]{2,18}?${DEPT_SUFFIX})`,
        'g'
      )
      const scanHits = []
      let dm
      deptNameRegex.lastIndex = 0
      while ((dm = deptNameRegex.exec(normalized)) !== null) {
        const dept = refineDeptChunk(dm[1])
        if (dept && dept.length <= MAX_SINGLE_DEPT_LEN) {
          scanHits.push({ index: dm.index, dept })
        }
      }
      scanHits.sort((a, b) => a.index - b.index)
      const scanPick = scanHits[0]

      if (scanPick) {
        const choices = []
        if (!best.dept || best.index > scanPick.index) {
          choices.push(scanPick.dept, best.dept)
        } else if (best.index < scanPick.index) {
          choices.push(best.dept, scanPick.dept)
        } else {
          const shorter = best.dept.length <= scanPick.dept.length ? best.dept : scanPick.dept
          const longer = shorter === best.dept ? scanPick.dept : best.dept
          choices.push(shorter, longer)
        }
        for (const c of choices) {
          if (!c) continue
          const v = this._finalizeDepartmentExtract(c)
          if (v) return v
        }
      }

      if (best.dept) {
        const v = this._finalizeDepartmentExtract(best.dept)
        if (v) return v
      }

      const fallback = normalized.match(
        new RegExp(`([^\\s，,。；;]{2,12}${DEPT_SUFFIX})`)
      )
      return this._finalizeDepartmentExtract(refineDeptChunk(fallback?.[1] || '') || '')
    },
    getZoneStyle(zone) {
      return {
        top: `${zone.y}%`,
        '--anchor-x': `${zone.x}%`,
        '--label-size': `${zone.fontSize || 20}px`
      }
    },
    getHotspotStyle(zone) {
      const looseHitScale = this.usePresetBodyMap ? (this.presetMapLayout.hitScale || 1.35) : 1.2
      return {
        left: `${(zone.hitX ?? zone.x) + this.presetMapHotspotOffset.x}%`,
        top: `${(zone.hitY ?? zone.y) + this.presetMapHotspotOffset.y}%`,
        '--hit-w': `${zone.hitW || zone.hitSize || 46}px`,
        '--hit-h': `${zone.hitH || zone.hitSize || 46}px`,
        '--hit-radius': zone.hitRadius || '50%',
        '--hit-rotate': `${zone.hitRotate || 0}deg`,
        '--hit-shift-x': `${zone.hitShiftX || 0}px`,
        '--hit-shift-y': `${zone.hitShiftY || 0}px`,
        '--hit-scale': looseHitScale
      }
    },
    onBodyImageError() {
      this.bodyImageUnavailable = true
    },
    switchBodyView(view) {
      if (this.selectedBodyView === view) return
      this.selectedBodyView = view
      this.bodyImageUnavailable = false
      this.selectedBodyPart = null
      this.triageStage = 'idle'
      this.followupIndex = 0
      this.recommendedDepartment = ''
    },
    switchProfile(profileId) {
      if (this.selectedProfile === profileId) return
      this.selectedProfile = profileId
      this.selectedBodyView = 'front'
      this.bodyImageUnavailable = false
      this.selectedBodyPart = null
      this.triageStage = 'idle'
      this.followupIndex = 0
      this.recommendedDepartment = ''
    },
    selectBodyPart(part) {
      this.selectedBodyPart = part
      this.triageStage = 'followup'
      this.followupIndex = 0
      this.followupAnswers = {
        symptomType: '',
        duration: '',
        severity: ''
      }
      this.messages.push({
        type: 'user',
        text: `就诊人群：${this.currentProfileMeta.label}；视图：${this.selectedBodyView === 'front' ? '正面' : '背面'}；不适部位：${part.label}`
      })
      this.messages.push({
        type: 'ai',
        text: `已记录：${this.currentProfileMeta.label}，不适部位为${part.label}。${this.followupQuestions[0].question}`
      })
      this.saveConversationHistory()
      this.$nextTick(() => this.scrollToBottom())
    },
    answerFollowup(option) {
      if (this.triageStage !== 'followup') return
      const q = this.currentFollowupQuestion
      this.followupAnswers[q.key] = option
      this.messages.push({
        type: 'user',
        text: `${q.question}${option}`
      })

      if (this.followupIndex < this.followupQuestions.length - 1) {
        this.followupIndex += 1
        const nextQ = this.currentFollowupQuestion
        this.messages.push({
          type: 'ai',
          text: nextQ.question
        })
      } else {
        this.finishTriage()
      }

      this.saveConversationHistory()
      this.$nextTick(() => this.scrollToBottom())
    },
    finishTriage() {
      this.triageStage = 'done'
      this.recommendedDepartment = this.recommendDepartment()
      this.messages.push({
        type: 'ai',
        text: `根据当前引导信息，建议优先挂号：${this.recommendedDepartment}。如出现剧烈疼痛、高热或呼吸困难，请优先前往急诊。你也可以继续补充症状，我会进一步分析。`
      })
      this.appendDepartmentMappingAssistantNoticeIfNeeded()
    },
    recommendDepartment() {
      const part = this.selectedBodyPart?.region
      const severe = this.followupAnswers.severity === '非常严重' || this.followupAnswers.severity === '重度'
      if (severe) return '急诊科'
      const mapping = {
        brain: '神经内科/神经外科',
        head: '神经内科/耳鼻喉科',
        neck: '骨科/耳鼻喉科',
        chest: '呼吸内科/心血管内科',
        abdomen: '消化内科',
        back: '骨科',
        hand: '骨科/手外科',
        foot: '骨科/足踝外科',
        buttock: '骨科/疼痛科',
        upper_limb: '骨科',
        lower_limb: '骨科',
        pelvis_male: '泌尿外科',
        pelvis_female: '妇科',
        pelvis_child: '儿科/小儿外科',
        whole_body: '全科医疗科',
        head_child: '儿科',
        chest_child: '儿科/小儿呼吸科',
        abdomen_child: '儿科/小儿消化科',
        ent_child: '儿科/耳鼻喉科',
        skin_child: '儿科/皮肤科',
        limb_child: '儿科/骨科',
        whole_child: '儿科'
      }
      return mapping[part] || '全科医疗科'
    },
    goToAppointment() {
      this.$router.push('/appointment')
    },
    /** 取 AI 推荐字符串中第一个科室片段（原文，未映射） */
    pickFirstRecommendedDeptKey() {
      const raw = this.firstRecommendedDepartmentRaw
      if (raw) return raw
      const r = this.recommendedDepartment
      if (!r) return ''
      return (
        String(r)
          .split(/[\/、，,;；]/)[0]
          ?.replace(/\*\*/g, '')
          .trim() || ''
      )
    },
    /** 将口语/简称统一为挂号映射表中的规范名称 */
    normalizeDeptAlias(name) {
      let s = this.sanitizeDepartmentCandidate(name)
      if (!s) return ''
      return DEPARTMENT_CANONICAL_ALIASES[s] || s
    },
    /** 对话中补充一条说明，避免用户疑惑「心内科」与目录不一致 */
    appendDepartmentMappingAssistantNoticeIfNeeded() {
      this.$nextTick(() => {
        const raw = this.firstRecommendedDepartmentRaw
        const can = this.firstRecommendedDepartmentCanonical
        if (!raw || !can) return
        const rawKey = raw.replace(/\*\*/g, '').replace(/\s+/g, '')
        if (!rawKey || rawKey === can.replace(/\s+/g, '')) return
        if (!DEPARTMENT_CANONICAL_ALIASES[rawKey]) return
        const key = `${raw}→${can}`
        if (this.lastDeptMappingNoticeKey === key) return
        this.lastDeptMappingNoticeKey = key
        this.messages.push({
          type: 'ai',
          text: `说明：您提到的「${raw}」在本院在线挂号目录中的对应科室为「${can}」，下方「前往 ${can} 挂号」将带您进入该科室流程。`
        })
        this.saveConversationHistory()
        this.$nextTick(() => this.scrollToBottom())
      })
    },
    /** 绿色「一键前往挂号」：有推荐则直达对应流程，否则进挂号首页 */
    goToRecommendedOrAppointment() {
      if (this.pickFirstRecommendedDeptKey()) {
        return this.goToFirstRecommendedDepartment()
      }
      return this.goToAppointment()
    },
    goToFirstRecommendedDepartment() {
      let first = this.normalizeDeptAlias(this.pickFirstRecommendedDeptKey())
      if (!first) return this.goToAppointment()

      // 内科各子科室：与手工挂号一致，需带「默认专科门诊」才能进入医生页（见 AppointmentSubDepartment → AppointmentSpecialty）
      const internalSubDeptRoute = {
        消化内科: { subDepartmentId: 1, specialtyId: 1, specialtyName: '消化内科门诊' },
        心血管内科: { subDepartmentId: 2, specialtyId: 7, specialtyName: '心血管内科门诊' },
        呼吸内科: { subDepartmentId: 3, specialtyId: 35, specialtyName: '呼吸内科门诊' },
        血液科: { subDepartmentId: 4, specialtyId: 12, specialtyName: '血液科门诊' },
        肾脏病: { subDepartmentId: 5, specialtyId: 19, specialtyName: '肾脏病中心门诊' },
        神经内科: { subDepartmentId: 6, specialtyId: 22, specialtyName: '神经内科门诊' },
        内分泌科: { subDepartmentId: 7, specialtyId: 27, specialtyName: '内分泌科门诊' },
        风湿免疫科: { subDepartmentId: 8, specialtyId: 30, specialtyName: '风湿免疫科门诊' },
        老年医学科: { subDepartmentId: 9, specialtyId: 36, specialtyName: '老年内科门诊' },
        普内科: { subDepartmentId: 10, specialtyId: 37, specialtyName: '普内科门诊' }
      }

      // 外科各子科室：带默认专科 ID（与 AppointmentSpecialty 首项一致；无专科数据时会回退到外科子科室医生表）
      const surgerySubDeptRoute = {
        肝胆胰外科: { subDepartmentId: 1, specialtyId: 101, specialtyName: '普外科/肝胆胰外科普通门诊' },
        胃肠外科: { subDepartmentId: 2, specialtyId: 201, specialtyName: '胃肠肿瘤、疝门诊' },
        甲状腺外科: { subDepartmentId: 3, specialtyId: 301, specialtyName: '甲状腺外科门诊' },
        乳腺外科: { subDepartmentId: 4, specialtyId: 401, specialtyName: '乳腺外科门诊' },
        肿瘤外科: { subDepartmentId: 5, specialtyId: 501, specialtyName: '肿瘤外科门诊' },
        结直肠外科: { subDepartmentId: 6, specialtyId: 601, specialtyName: '结直肠（肛肠）外科门诊' },
        骨科: { subDepartmentId: 7, specialtyId: 701, specialtyName: '骨科门诊（四肢骨折/骨髓炎/未分类/换药/骨质疏松）' },
        泌尿外科: { subDepartmentId: 8, specialtyId: 801, specialtyName: '泌尿外科门诊' },
        神经外科: { subDepartmentId: 9, specialtyId: 901, specialtyName: '神经外科门诊' },
        普胸外科: { subDepartmentId: 10, specialtyId: 1001, specialtyName: '普胸外科门诊' },
        心脏大血管外科: { subDepartmentId: 11, specialtyId: 1101, specialtyName: '心脏大血管外科门诊' },
        血管外科: { subDepartmentId: 12, specialtyId: 1201, specialtyName: '血管外科门诊' }
      }

      // 与 Appointment.vue 一致：先选专科门诊的顶层科室（进入专科列表，比停在首页少步数）
      const directSpecialtyDept = {
        多学科协作诊治: { departmentId: 3, departmentName: '多学科协作诊治' },
        多学科: { departmentId: 3, departmentName: '多学科协作诊治' },
        感染病科: { departmentId: 4, departmentName: '感染病科' },
        耳鼻咽喉科: { departmentId: 6, departmentName: '耳鼻咽喉科' },
        眼科: { departmentId: 7, departmentName: '眼科' }
      }

      // 其余进入「子科室选择」的顶层科室（与 Appointment.vue selectDepartment 一致）
      const mainDeptMap = {
        内科: { departmentId: 1, departmentName: '内科' },
        外科: { departmentId: 2, departmentName: '外科' },
        肿瘤科: { departmentId: 5, departmentName: '肿瘤科' },
        口腔科: { departmentId: 8, departmentName: '口腔科' },
        妇产科: { departmentId: 9, departmentName: '妇产科' },
        生殖医学: { departmentId: 10, departmentName: '生殖医学' },
        儿科: { departmentId: 11, departmentName: '儿科' },
        '变态反应（过敏）科': { departmentId: 12, departmentName: '变态反应（过敏）科' },
        皮肤科: { departmentId: 13, departmentName: '皮肤科' },
        精神科卫生科: { departmentId: 14, departmentName: '精神科卫生科' },
        中医科: { departmentId: 15, departmentName: '中医科' },
        麻醉科: { departmentId: 16, departmentName: '麻醉科' },
        医学影像科: { departmentId: 17, departmentName: '医学影像科' },
        疼痛科: { departmentId: 18, departmentName: '疼痛科' },
        医疗美容科: { departmentId: 19, departmentName: '医疗美容科' },
        全科医疗科: { departmentId: 20, departmentName: '全科医疗科' },
        康复医学科: { departmentId: 21, departmentName: '康复医学科' },
        病理科: { departmentId: 22, departmentName: '病理科' },
        营养科: { departmentId: 23, departmentName: '营养科' },
        临床药学: { departmentId: 24, departmentName: '临床药学' },
        专科护理: { departmentId: 25, departmentName: '专科护理' },
        高压氧: { departmentId: 26, departmentName: '高压氧' },
        资深专家门诊: { departmentId: 27, departmentName: '资深专家门诊' },
        急诊科: null
      }

      const pushDoctor = (q) =>
        this.$router.push({
          name: 'AppointmentDoctor',
          query: q
        })

      const pushSpecialty = (q) =>
        this.$router.push({
          name: 'AppointmentSpecialty',
          query: q
        })

      const pushSubDept = (q) =>
        this.$router.push({
          name: 'AppointmentSubDepartment',
          query: q
        })

      if (mainDeptMap[first] === null) {
        return this.goToAppointment()
      }

      // 肿瘤科下属：进专科列表（与手工流程一致）
      if (first === '肿瘤内科') {
        return pushSpecialty({
          departmentId: 5,
          departmentName: '肿瘤科',
          subDepartmentId: 1,
          subDepartmentName: '肿瘤内科'
        })
      }
      if (first === '放疗科') {
        return pushSpecialty({
          departmentId: 5,
          departmentName: '肿瘤科',
          subDepartmentId: 2,
          subDepartmentName: '放疗科'
        })
      }

      // 妇产：妇科/产科直达专科列表（避免只到科室入口）
      if (first === '妇科') {
        return pushSpecialty({
          departmentId: 9,
          departmentName: '妇产科',
          subDepartmentId: 1,
          subDepartmentName: '妇科'
        })
      }
      if (first === '产科') {
        return pushSpecialty({
          departmentId: 9,
          departmentName: '妇产科',
          subDepartmentId: 2,
          subDepartmentName: '产科'
        })
      }

      const directSpec = directSpecialtyDept[first]
      if (directSpec) {
        return pushSpecialty({
          departmentId: directSpec.departmentId,
          departmentName: directSpec.departmentName,
          subDepartmentId: 0,
          subDepartmentName: directSpec.departmentName
        })
      }

      const internalRoute = internalSubDeptRoute[first]
      if (internalRoute) {
        return pushDoctor({
          departmentId: 1,
          departmentName: '内科',
          subDepartmentId: internalRoute.subDepartmentId,
          subDepartmentName: first,
          specialtyId: internalRoute.specialtyId,
          specialtyName: internalRoute.specialtyName
        })
      }

      const surgeryRoute = surgerySubDeptRoute[first]
      if (surgeryRoute) {
        return pushDoctor({
          departmentId: 2,
          departmentName: '外科',
          subDepartmentId: surgeryRoute.subDepartmentId,
          subDepartmentName: first,
          specialtyId: surgeryRoute.specialtyId,
          specialtyName: surgeryRoute.specialtyName
        })
      }

      if (mainDeptMap[first]) {
        return pushSubDept({
          departmentId: mainDeptMap[first].departmentId,
          departmentName: mainDeptMap[first].departmentName
        })
      }

      return this.goToAppointment()
    },
    initSpeechRecognition() {
      try {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition
        if (!SR) {
          this.speechSupported = false
          return
        }
        this.speechSupported = true
        const rec = new SR()
        rec.lang = 'zh-CN'
        rec.continuous = false
        rec.interimResults = true
        rec.maxAlternatives = 1

        rec.onstart = () => {
          this.voiceError = ''
          this.isRecording = true
        }
        rec.onend = () => {
          this.isRecording = false
        }
        rec.onerror = (e) => {
          this.voiceError = e?.error ? `语音识别失败：${e.error}` : '语音识别失败'
          this.isRecording = false
        }
        rec.onresult = (event) => {
          let transcript = ''
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const res = event.results[i]
            transcript += (res[0]?.transcript || '')
          }
          if (transcript) {
            this.inputMessage = transcript.trim()
          }
        }

        this.recognition = rec
      } catch (e) {
        this.speechSupported = false
      }
    },

    toggleVoiceInput() {
      if (!this.speechSupported || !this.recognition) return
      this.voiceError = ''
      try {
        if (this.isRecording) {
          this.recognition.stop()
          this.isRecording = false
        } else {
          this.inputMessage = ''
          this.recognition.start()
        }
      } catch (e) {
        // start 在短时间重复调用可能抛异常
        this.voiceError = '语音功能暂时不可用，请稍后再试'
        this.isRecording = false
      }
    },

    // 创建新对话
    createNewConversation() {
      const newId = Date.now().toString()
      const newConversation = {
        id: newId,
        title: '新对话',
        messages: [
          {
            type: 'ai',
            text: '您好！我是AI问诊助手。请先在上方人体示意图选择不适部位，我会继续追问并推荐就诊科室。'
          }
        ],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      
      this.conversationHistory.unshift(newConversation)
      this.currentConversationId = newId
      this.messages = [...newConversation.messages]
      this.triageStage = 'idle'
      this.selectedBodyPart = null
      this.selectedBodyView = 'front'
      this.followupIndex = 0
      this.followupAnswers = {
        symptomType: '',
        duration: '',
        severity: ''
      }
      this.recommendedDepartment = ''
      this.lastDeptMappingNoticeKey = ''

      this.$nextTick(() => {
        this.scrollToBottom()
      })
    },
    
    // 加载对话
    loadConversation(conversationId) {
      const conversation = this.conversationHistory.find(c => c.id === conversationId)
      if (conversation) {
        this.currentConversationId = conversationId
        this.messages = [...conversation.messages]
        // 切换对话时，恢复分诊/推荐状态，确保按钮与输入框状态一致
        this.rehydrateConversationState()
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      }
    },
    
    // 选择对话（从历史弹窗中选择）
    selectConversation(conversationId) {
      this.loadConversation(conversationId)
      this.showHistoryModal = false
    },
    
    // 显示删除确认对话框
    showDeleteConfirm(conversationId) {
      this.deleteTargetId = conversationId
      this.showDeleteConfirmModal = true
    },
    
    // 取消删除
    cancelDelete() {
      this.showDeleteConfirmModal = false
      this.deleteTargetId = null
    },
    
    // 确认删除
    async confirmDelete() {
      if (!this.deleteTargetId) {
        this.cancelDelete()
        return
      }
      
      try {
        const response = await axios.delete(`/api/consultation-history/${this.deleteTargetId}`)
        
        if (response.data.status === 'success') {
          // 从本地列表中移除
        const index = this.conversationHistory.findIndex(c => c.id === this.deleteTargetId)
        if (index !== -1) {
          this.conversationHistory.splice(index, 1)
          }
          
          // 如果删除的是当前对话，加载其他对话或创建新对话
          if (this.currentConversationId === this.deleteTargetId) {
            if (this.conversationHistory.length > 0) {
              this.loadConversation(this.conversationHistory[0].id)
            } else {
              this.createNewConversation()
            }
          }
          
      this.cancelDelete()
        } else {
          alert(response.data.message || '删除失败')
        }
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.message || '删除失败'
        alert(errorMsg)
      }
    },
    
    // 保存对话历史到数据库
    async saveConversationHistory() {
      if (!this.currentConversationId) return
      
      // 更新当前对话
      const currentConversation = this.conversationHistory.find(c => c.id === this.currentConversationId)
      if (currentConversation) {
        currentConversation.messages = [...this.messages]
        currentConversation.updatedAt = new Date().toISOString()
        // 更新标题（使用第一条用户消息）
        const firstUserMessage = this.messages.find(m => m.type === 'user')
        if (firstUserMessage) {
          const text = firstUserMessage.text || ''
          currentConversation.title = text.length > 20 ? text.substring(0, 20) + '...' : text
        }
      }

      // 没有任何用户输入的“空对话”不落库（避免产生大量“新对话”垃圾记录）
      const hasUserMessage = Array.isArray(this.messages) && this.messages.some(m => m && m.type === 'user' && String(m.text || '').trim())
      if (!hasUserMessage) return
      
      try {
        // 保存到数据库
        await axios.post('/api/consultation-history', {
          id: this.currentConversationId,
          title: currentConversation?.title || '新对话',
          messages: this.messages
        })
      } catch (error) {
        console.error('保存对话历史失败:', error)
      }
    },
    
    // 从数据库加载对话历史
    async loadConversationHistory() {
      try {
        const response = await axios.get('/api/consultation-history')
        if (response.data.status === 'success') {
          this.conversationHistory = response.data.data || []
          // 按更新时间排序（最新的在前）
          this.conversationHistory.sort((a, b) => {
            const bd = this.parseDbTimestamp(b.updatedAt) || new Date(0)
            const ad = this.parseDbTimestamp(a.updatedAt) || new Date(0)
            return bd - ad
          })
        } else {
          this.conversationHistory = []
        }
      } catch (error) {
        console.error('加载对话历史失败:', error)
        this.conversationHistory = []
      }
    },
    
    // 格式化时间
    formatTime(timeString) {
      const date = this.parseDbTimestamp(timeString) || new Date(timeString)
      if (Number.isNaN(date.getTime())) return ''
      const now = new Date()
      const diff = now - date
      const minutes = Math.floor(diff / 60000)
      const hours = Math.floor(diff / 3600000)
      const days = Math.floor(diff / 86400000)
      
      if (minutes < 1) return '刚刚'
      if (minutes < 60) return `${minutes}分钟前`
      if (hours < 24) return `${hours}小时前`
      if (days < 7) return `${days}天前`
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
    },
    
    // 格式化文件大小
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    },
    
    // 处理文件选择
    handleFileSelect(event) {
      const file = event.target.files[0]
      if (file) {
        // 检查文件大小（限制10MB）
        if (file.size > 10 * 1024 * 1024) {
          alert('文件大小不能超过10MB')
          this.$refs.fileInput.value = ''
          return
        }
        this.uploadedFile = file
      }
    },
    
    async sendMessage() {
      // 如果没有输入消息也没有上传文件，不发送
      if ((!this.inputMessage.trim() && !this.uploadedFile) || this.isLoading) return
      if (!this.canInputFreeText) return
      // 录音中不发送，避免半句触发
      if (this.isRecording) return
      
      // 确保有当前对话
      if (!this.currentConversationId) {
        this.createNewConversation()
      }
      
      const userMessage = this.inputMessage.trim() || (this.uploadedFile ? `已上传文件：${this.uploadedFile.name}` : '')
      this.messages.push({
        type: 'user',
        text: userMessage,
        file: this.uploadedFile ? {
          name: this.uploadedFile.name,
          size: this.uploadedFile.size,
          type: this.uploadedFile.type
        } : null
      })
      
      // 立即保存用户消息
      this.saveConversationHistory()
      
      const messageToSend = this.inputMessage.trim()
      const fileToUpload = this.uploadedFile
      // 点击发送后立即清空输入框和已选图片，按钮恢复可再次上传
      this.inputMessage = ''
      this.uploadedFile = null
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
      this.isLoading = true
      
      // 滚动到底部
      this.$nextTick(() => {
        this.scrollToBottom()
      })
      
      try {
        // 准备表单数据（附带本轮之前的对话，避免模型只看到单句而重复追问）
        const formData = new FormData()
        formData.append('message', userMessage)
        const priorForHistory = this.messages.slice(0, -1)
        const historyPayload = priorForHistory
          .filter((m) => m && (m.type === 'user' || m.type === 'ai') && String(m.text || '').trim())
          .map((m) => ({
            role: m.type === 'user' ? 'user' : 'assistant',
            content: String(m.text || '').trim()
          }))
          .slice(-40)
        formData.append('history', JSON.stringify(historyPayload))
        if (fileToUpload) {
          formData.append('file', fileToUpload)
        }
        
        // 调用后端API
        const response = await axios.post('/api/ai-consultation', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        if (response.data.status === 'success') {
          const aiText = response.data.response || '抱歉，我暂时无法理解您的问题，请详细描述您的症状。'
          this.messages.push({
            type: 'ai',
            text: aiText
          })

          // 如果 AI 在对话中直接给出科室推荐，也同步到上方分诊结果区，展示跳转按钮
          const dept = this.extractRecommendedDepartment(aiText)
          if (dept) {
            this.recommendedDepartment = dept
            this.triageStage = 'done'
            this.appendDepartmentMappingAssistantNoticeIfNeeded()
          }
        } else {
          // 显示后端返回的错误信息
          this.messages.push({
            type: 'ai',
            text: response.data.response || '抱歉，服务暂时不可用，请稍后再试。'
          })
        }
      } catch (error) {
        console.error('API调用错误:', error)
        
        // 如果后端返回了错误响应，显示后端返回的错误信息
        if (error.response && error.response.data && error.response.data.response) {
          this.messages.push({
            type: 'ai',
            text: error.response.data.response
          })
        } else if (error.response && error.response.status === 500) {
          // 服务器错误
          this.messages.push({
            type: 'ai',
            text: '服务器错误，请稍后再试。如果症状紧急，请直接前往医院就诊。'
          })
        } else if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
          // 连接被拒绝，可能是后端服务器未运行
          this.messages.push({
            type: 'ai',
            text: '无法连接到服务器，请确保后端服务已启动。'
          })
        } else {
          // 其他网络错误
          this.messages.push({
            type: 'ai',
            text: '网络连接出现问题，请检查网络后重试。如果症状紧急，请直接前往医院就诊。'
          })
        }
      } finally {
        this.isLoading = false
        // 保存完整的对话记录
        this.saveConversationHistory()
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      }
    },
    
    selectQuickQuestion(question) {
      this.inputMessage = question
      this.sendMessage()
    },
    
    handleFileUpload(event) {
      const file = event.target.files[0]
      if (file) {
        // 仅允许图片
        if (!file.type || !file.type.startsWith('image/')) {
          alert('仅支持上传图片文件')
          if (this.$refs.fileInput) {
            this.$refs.fileInput.value = ''
          }
          return
        }
        // 检查文件大小（限制10MB）
        if (file.size > 10 * 1024 * 1024) {
          alert('文件大小不能超过10MB')
          return
        }
        this.uploadedFile = file
      }
    },
    
    removeFile() {
      this.uploadedFile = null
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
    
    scrollToBottom() {
      const chatArea = this.$refs.chatArea
      if (chatArea) {
        chatArea.scrollTop = chatArea.scrollHeight
      }
    },
    
    getMockResponse(message) {
      // 模拟AI回复
      const responses = {
        '头痛': '头痛可能由多种原因引起，如紧张性头痛、偏头痛等。建议您注意休息，保持充足睡眠，如果症状持续或加重，请及时就医。',
        '发烧': '发烧是身体对抗感染的正常反应。建议多休息、多喝水，体温超过38.5°C可考虑服用退烧药。如持续高烧或伴有其他严重症状，请及时就医。',
        '咳嗽': '咳嗽可能是感冒、过敏或其他呼吸道疾病的症状。建议多喝水，避免刺激性食物，保持室内空气流通。如咳嗽持续超过一周，建议就医检查。',
        '胃痛': '胃痛可能与饮食不当、胃炎、胃溃疡等有关。建议规律饮食，避免辛辣刺激食物，少食多餐。如症状严重或持续，请及时就医。',
        '失眠': '失眠可能与压力、生活习惯、环境等因素有关。建议保持规律的作息时间，睡前避免使用电子设备，营造舒适的睡眠环境。如长期失眠，建议咨询医生。',
        '疲劳': '疲劳可能与工作压力、睡眠不足、营养不均衡等有关。建议保证充足睡眠，均衡饮食，适当运动。如疲劳持续且影响日常生活，建议就医检查。'
      }
      
      for (const key in responses) {
        if (message.includes(key)) {
          return responses[key]
        }
      }
      
      return '感谢您的咨询。根据您的描述，建议您注意休息，观察症状变化。如果症状持续或加重，请及时到医院就诊，进行专业检查。'
    }
  }
}
</script>

<style scoped>
.ai-consultation {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  color: white;
  text-align: center;
  font-size: 2.5rem;
  margin-bottom: 2rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.consultation-box {
  background: white;
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.triage-panel {
  background: white;
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  padding: 1.25rem;
  margin-bottom: 1rem;
}

.triage-panel h3 {
  color: #667eea;
  margin: 0 0 0.5rem;
}

.triage-desc {
  color: #666;
  margin: 0 0 1rem;
}

.profile-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-bottom: 0.9rem;
}

.profile-tab-btn {
  border: 1px solid #dbe0ff;
  background: #f5f7ff;
  color: #4a5bb8;
  border-radius: 999px;
  padding: 0.45rem 0.85rem;
  cursor: pointer;
}

.profile-tab-btn.active {
  color: white;
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.body-map-wrap {
  border: 1px solid #dfe6ee;
  background: linear-gradient(180deg, #f3f6fa 0%, #eef3f8 100%);
  border-radius: 12px;
  padding: 0.8rem;
}

.body-map-header {
  display: flex;
  justify-content: space-between;
  gap: 0.6rem;
  align-items: center;
  margin-bottom: 0.6rem;
}

.map-view-switch {
  display: inline-flex;
  gap: 0.4rem;
}

.map-view-btn {
  border: 1px solid #dbe0ff;
  background: #fff;
  color: #5a67b9;
  border-radius: 999px;
  padding: 0.25rem 0.7rem;
  cursor: pointer;
}

.map-view-btn.active {
  border-color: #667eea;
  color: #fff;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.body-map-hint {
  color: #7a82a8;
  font-size: 0.9rem;
}

.body-map-canvas {
  --side-offset: 4%;
  --label-width: 190px;
  --end-dot-size: 8px;
  position: relative;
  height: 540px;
  border-radius: 10px;
  background:
    linear-gradient(rgba(105, 124, 150, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(105, 124, 150, 0.06) 1px, transparent 1px),
    #f2f5f8;
  background-size: 28px 28px, 28px 28px, auto;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.55);
}

.body-map-canvas.preset-map-canvas {
  height: auto;
  aspect-ratio: 1439 / 1080;
  background: #f2f5f8;
}

.body-bg-ring {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 78%;
  height: 88%;
  transform: translate(-50%, -50%);
  border: 5px dotted rgba(90, 210, 239, 0.72);
  border-radius: 50%;
  opacity: 0.45;
}

.body-bg-ring.inner {
  width: 58%;
  height: 68%;
  border: none;
  background:
    radial-gradient(circle at center, rgba(157, 201, 235, 0.16) 0 60%, transparent 62%),
    radial-gradient(circle at center, rgba(157, 201, 235, 0.1) 0 72%, transparent 74%);
}

.body-figure {
  position: absolute;
  left: 50%;
  top: 50%;
  height: 95%;
  max-width: 40%;
  transform: translate(-50%, -50%);
  object-fit: contain;
  z-index: 2;
  border-radius: 10px;
  box-shadow: 0 6px 18px rgba(82, 116, 143, 0.08);
  filter: saturate(0.95) contrast(0.97) brightness(0.995);
  mix-blend-mode: multiply;
}

.body-figure.full-layout {
  left: 50%;
  top: var(--figure-top, 50%);
  width: 100%;
  height: var(--figure-height, 100%);
  max-width: 100%;
  transform: translate(-50%, -50%);
  object-fit: contain;
  border-radius: 0;
  box-shadow: none;
  filter: none;
  mix-blend-mode: normal;
}

.body-image-missing {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #5f6a95;
  z-index: 2;
}

.body-silhouette {
  font-size: 8rem;
  opacity: 0.3;
  user-select: none;
}

.body-zone-callout {
  position: absolute;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  border: none;
  background: transparent;
  padding: 0;
  color: #697684;
  cursor: pointer;
  white-space: nowrap;
  z-index: 3;
}

.body-zone-hotspot {
  position: absolute;
  transform: translate(calc(-50% + var(--hit-shift-x, 0px)), calc(-50% + var(--hit-shift-y, 0px))) rotate(var(--hit-rotate, 0deg));
  width: max(calc(var(--hit-w, 46px) * var(--hit-scale, 1)), 56px);
  height: max(calc(var(--hit-h, 46px) * var(--hit-scale, 1)), 56px);
  border: none;
  border-radius: var(--hit-radius, 50%);
  background: transparent;
  cursor: pointer;
  z-index: 4;
}

.body-zone-hotspot::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  border: 2px solid rgba(30, 168, 202, 0);
  background: rgba(30, 168, 202, 0);
  transition: all 0.2s ease;
}

.body-zone-hotspot:hover::before {
  border-color: rgba(30, 168, 202, 0.45);
  background: rgba(30, 168, 202, 0.12);
}

.body-zone-hotspot.active::before {
  border-color: #1ea8ca;
  background: rgba(30, 168, 202, 0.2);
  box-shadow: 0 0 0 4px rgba(30, 168, 202, 0.15);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.body-zone-callout.left {
  left: var(--side-offset);
}

.body-zone-callout.right {
  right: var(--side-offset);
  flex-direction: row-reverse;
}

.callout-end-dot {
  width: var(--end-dot-size);
  height: var(--end-dot-size);
  border-radius: 50%;
  background: #8dc4d8;
  flex-shrink: 0;
  margin: 0 4px;
  transition: all 0.2s ease;
}

.callout-line {
  width: clamp(40px, 24vw, 420px);
  height: 1px;
  background: #a8b3be;
  margin: 0 2px;
  transition: all 0.2s ease;
}

.body-zone-callout.left .callout-line {
  width: clamp(
    78px,
    calc(var(--anchor-x, 30%) - var(--side-offset) - var(--label-width) - var(--end-dot-size) - 6px),
    520px
  );
}

.body-zone-callout.right .callout-line {
  width: clamp(
    78px,
    calc((100% - var(--anchor-x, 70%)) - var(--side-offset) - var(--label-width) - var(--end-dot-size) - 6px),
    520px
  );
}

.callout-label {
  font-size: var(--label-size, 20px);
  color: #667380;
  letter-spacing: 0.5px;
  transition: all 0.2s ease;
  width: var(--label-width);
}

.body-zone-callout.left .callout-label {
  text-align: left;
}

.body-zone-callout.right .callout-label {
  text-align: right;
}

.body-zone-callout:hover .callout-line {
  background: #85cde3;
}

.body-zone-callout:hover .callout-end-dot {
  background: #6fc6e3;
}

.body-zone-callout:hover .callout-label {
  color: #4f6f83;
}

.body-zone-callout.active .callout-label {
  color: #1798bb;
  font-weight: 600;
}

.body-zone-callout.active .callout-line {
  background: #64bfd8;
}

.body-zone-callout.active .callout-end-dot {
  background: #1ea8ca;
  box-shadow: 0 0 0 3px rgba(30, 168, 202, 0.2);
}

.followup-box {
  margin-top: 1rem;
  background: #f7f9ff;
  border: 1px solid #e8ecff;
  border-radius: 12px;
  padding: 0.9rem;
}

.followup-question {
  font-weight: 600;
  margin-bottom: 0.6rem;
  color: #2f3a7a;
}

.followup-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.followup-option-btn {
  border: 1px solid #d8defa;
  background: white;
  border-radius: 999px;
  padding: 0.45rem 0.8rem;
  cursor: pointer;
  color: #4a5bb8;
}

.followup-option-btn:hover {
  background: #eef1ff;
}

.triage-result {
  margin-top: 1rem;
  background: #f6ffed;
  border: 1px solid #d9f7be;
  border-radius: 12px;
  padding: 0.9rem;
  color: #2a5e1a;
}

.triage-result-hint {
  color: #5b7f50;
  margin: 0.4rem 0 0.8rem;
}

.triage-recommended-first {
  margin: 0.2rem 0 0.6rem;
  color: #4f6f83;
}

.go-appointment-btn {
  border: none;
  border-radius: 999px;
  padding: 0.55rem 1rem;
  color: #fff;
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  cursor: pointer;
}

.go-recommended-btn {
  margin-top: 0.6rem;
  border: none;
  border-radius: 999px;
  padding: 0.55rem 1rem;
  color: #fff;
  background: linear-gradient(135deg, #2f8cff 0%, #1362d9 100%);
  cursor: pointer;
}

.go-recommended-btn:hover {
  filter: brightness(1.03);
}

.chat-action-bar {
  padding: 0 1.5rem 1rem;
}

.chat-area {
  height: 650px;
  overflow-y: auto;
  padding: 1.5rem;
  background: #f8f9fa;
}

.message {
  margin-bottom: 1.5rem;
}

.message-content {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.message.user .message-content {
  flex-direction: row-reverse;
}

.message-avatar {
  font-size: 2rem;
  flex-shrink: 0;
}

.message-text {
  background: white;
  padding: 1rem 1.5rem;
  border-radius: 15px;
  max-width: 70%;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  line-height: 1.6;
}

.message.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.file-info {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 0.9rem;
  opacity: 0.9;
}

.message.user .file-info {
  border-top-color: rgba(255, 255, 255, 0.3);
}

.input-area {
  display: flex;
  padding: 1rem;
  gap: 1rem;
  background: white;
  border-top: 1px solid #eee;
}

.mic-btn {
  padding: 0.8rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: opacity 0.3s;
  white-space: nowrap;
}

.mic-btn:hover {
  opacity: 0.9;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.mic-btn.recording {
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%);
}

.mic-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.voice-hint {
  padding: 0.5rem 1rem 1rem;
  font-size: 0.9rem;
  color: #888;
}

.voice-error {
  color: #ff4d4f;
}

.message-input {
  flex: 1;
  padding: 0.8rem 1rem;
  border: 2px solid #eee;
  border-radius: 25px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.3s;
}

.message-input:focus {
  border-color: #667eea;
}

.file-upload-btn {
  padding: 0.8rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: all 0.3s;
  white-space: nowrap;
}

.file-upload-btn:hover {
  opacity: 0.9;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.file-upload-btn.has-file {
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
}

.file-upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.send-btn {
  padding: 0.8rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.3s;
}

.send-btn:hover {
  opacity: 0.9;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.file-upload-btn {
  padding: 0.8rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: opacity 0.3s;
  white-space: nowrap;
}

.file-upload-btn:hover {
  opacity: 0.9;
}

.file-upload-btn.has-file {
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
}

.file-upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.file-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.8rem 1rem;
  background: #f0f7ff;
  border-top: 1px solid #e6f7ff;
  border-bottom: 1px solid #e6f7ff;
}

.file-name {
  font-size: 0.9rem;
  color: #1890ff;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-file-btn {
  background: none;
  border: none;
  color: #ff4d4f;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.remove-file-btn:hover {
  background: rgba(255, 77, 79, 0.1);
}

.quick-questions {
  margin-top: 2rem;
  background: white;
  border-radius: 15px;
  padding: 1.5rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.quick-questions h3 {
  color: #667eea;
  margin-bottom: 1rem;
}

.question-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
}

.question-tag {
  padding: 0.5rem 1rem;
  background: #f0f0f0;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 0.9rem;
}

.question-tag:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-2px);
}

.loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #999;
}

.loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #667eea;
  animation: loading-bounce 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes loading-bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.message-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.new-chat-btn {
  padding: 0.8rem 1.5rem;
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 10px rgba(102, 126, 234, 0.2);
}

.new-chat-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.header-buttons {
  display: flex;
  gap: 1rem;
}

.history-btn {
  padding: 0.8rem 1.5rem;
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 10px rgba(102, 126, 234, 0.2);
}

.history-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

/* 弹窗样式 */
.modal-overlay {
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

.modal-content {
  background: white;
  border-radius: 15px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
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

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 2px solid #f0f0f0;
}

.modal-header h2 {
  color: #667eea;
  margin: 0;
  font-size: 1.5rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #999;
  cursor: pointer;
  padding: 0.5rem;
  line-height: 1;
  border-radius: 5px;
  transition: all 0.3s;
}

.close-btn:hover {
  background: #f0f0f0;
  color: #667eea;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.no-history {
  text-align: center;
  padding: 3rem 1rem;
  color: #999;
}

.no-history-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-history p {
  margin: 0.5rem 0;
  font-size: 1rem;
}

.no-history-hint {
  font-size: 0.9rem;
  color: #bbb;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.history-item:hover {
  background: #e9ecef;
  transform: translateX(5px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.history-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.history-item-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
  min-width: 0;
}

.history-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.history-item-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.history-title-text {
  font-weight: 600;
  font-size: 1rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-time {
  font-size: 0.85rem;
  opacity: 0.8;
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.5rem;
  border-radius: 5px;
  transition: all 0.3s;
  opacity: 0.7;
  flex-shrink: 0;
}

.delete-btn:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

.history-item.active .delete-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 删除确认对话框样式 */
.confirm-modal {
  background: white;
  border-radius: 15px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s;
  overflow: hidden;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .body-map-canvas {
    --label-width: 92px;
  }

  .body-map-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .body-map-canvas {
    height: 470px;
  }

  .body-map-canvas.preset-map-canvas {
    height: auto;
  }

  .callout-line {
    width: 90px;
    margin: 0 6px;
  }

  .callout-label {
    font-size: 13px;
    letter-spacing: 0;
  }

  .callout-end-dot {
    width: 8px;
    height: 8px;
  }

  .body-zone-hotspot {
    width: max(calc(var(--hit-w, 46px) * 0.9), 48px);
    height: max(calc(var(--hit-h, 46px) * 0.9), 48px);
  }

  .header-section {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .header-buttons {
    flex-direction: column;
  }
  
  .new-chat-btn,
  .history-btn {
    width: 100%;
  }
  
  .modal-content {
    width: 95%;
    max-height: 90vh;
  }
  
  .confirm-modal {
    width: 95%;
  }
  
  .confirm-footer {
    flex-direction: column;
  }
  
  .cancel-btn,
  .confirm-delete-btn {
    width: 100%;
  }
}
</style>
