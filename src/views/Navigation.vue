<template>
  <div class="collector-page">
    <div class="collector-container">
      <h1 class="page-title">室内导航数据采集</h1>

      <section class="map-pane">
        <div class="map-topbar">
          <div class="topbar-left">
            <div class="segmented">
              <button type="button" :class="['seg-btn', { active: baseMapMode === 'floor' }]" @click="switchBase('floor')">
                楼层图
              </button>
              <button type="button" :class="['seg-btn', { active: baseMapMode === 'index' }]" @click="switchBase('index')">
                索引图
              </button>
            </div>

            <div v-if="baseMapMode === 'floor'" class="floor-tabs">
              <button v-for="f in floorList" :key="f" type="button" :class="['tab', { active: currentFloor === f }]" @click="setFloor(f)">
                {{ f }}
              </button>
            </div>
          </div>

          <div class="topbar-right">
            <label class="check">
              <input type="checkbox" v-model="showNodes" />
              <span>显示节点</span>
            </label>
            <button type="button" class="ghost-btn" @click="clearAll">清空采集数据</button>
          </div>
        </div>

        <div class="status-bar">
          <strong>当前模式：</strong>{{ modeLabel }}
          <span class="status-sep">|</span>
          <span>{{ modeHint }}</span>
        </div>
        <div v-if="actionMessage" class="action-bar">{{ actionMessage }}</div>

        <div class="leaflet-wrap">
          <div ref="mapEl" :class="['leaflet-map', mapCursorClass]"></div>
        </div>

        <div class="tool-panel">
          <div class="tool-title">采集工具</div>

          <div class="tool-row">
            <label class="check"><input type="radio" value="node" v-model="collectorMode" /> <span>采节点</span></label>
            <label class="check"><input type="radio" value="edge" v-model="collectorMode" /> <span>连边</span></label>
            <label class="check"><input type="radio" value="none" v-model="collectorMode" /> <span>关闭</span></label>
          </div>

          <div v-if="collectorMode === 'node'" class="tool-block">
            <div class="tool-row">
              <input class="mini-input" v-model.trim="newNodeName" placeholder="节点名称（如：挂号收费处）" />
              <select class="mini-select" v-model="newNodeType">
                <option value="room">room/诊室</option>
                <option value="hub">hub/公共点</option>
                <option value="lift">lift/电梯</option>
                <option value="stairs">stairs/楼梯</option>
                <option value="turn">turn/拐点</option>
                <option value="entrance">entrance/出入口</option>
              </select>
            </div>
            <div class="hint">在地图上点击一次，即可在当前楼层创建 1 个节点。</div>
          </div>

          <div v-if="collectorMode === 'edge'" class="tool-block">
            <div class="tool-row">
              <select class="mini-select" v-model="edgeKind">
                <option value="walk">walk/同层通行</option>
                <option value="elevator">elevator/电梯跨层</option>
                <option value="stairs">stairs/楼梯跨层</option>
              </select>
              <input class="mini-input short" v-model.number="edgeWeight" type="number" placeholder="权重(可选)" />
            </div>
            <div class="hint">依次点击两个节点：先 A 再 B，自动建立双向边。</div>
            <div class="hint" v-if="edgePickA">已选 A：{{ nodes[edgePickA]?.name || edgePickA }}，请点击节点 B</div>
          </div>

          <div class="tool-block">
            <div class="tool-row">
              <select class="mini-select" v-model="renameNodeId">
                <option value="">选择要重命名的节点</option>
                <option v-for="n in nodesOnFloorSorted" :key="n.id" :value="n.id">
                  {{ n.name }}（{{ n.type }}）
                </option>
              </select>
              <input class="mini-input" v-model.trim="renameNodeName" placeholder="新的节点名称" />
              <button type="button" class="ghost-btn" @click="renameSelectedNode" :disabled="!renameNodeId || !renameNodeName">
                保存重命名
              </button>
            </div>
            <div class="tool-row">
              <button type="button" class="ghost-btn" @click="autoRenameDuplicatesCurrentFloor">
                当前楼层重复名自动编号
              </button>
              <button type="button" class="ghost-btn" @click="autoRenameDuplicatesAllFloors">
                全楼层重复名自动编号
              </button>
            </div>
            <div class="hint">可直接在已采集节点上改名，无需重新采集；自动编号示例：楼梯-1、楼梯-2。</div>
          </div>

          <div class="tool-block">
            <div class="tool-row">
              <select class="mini-select" v-model="deleteNodeId">
                <option value="">选择要删除的节点</option>
                <option v-for="n in nodesOnFloorSorted" :key="`del-${n.id}`" :value="n.id">
                  {{ n.name }}（{{ n.type }}）
                </option>
              </select>
              <button type="button" class="ghost-btn danger-btn" @click="deleteSelectedNode" :disabled="!deleteNodeId">
                删除采集点
              </button>
            </div>
            <div class="hint">删除节点时会自动清理该点所有连边，避免路径数据异常。</div>
          </div>

          <div class="tool-row">
            <button type="button" class="primary-btn" @click="exportJson">导出 JSON</button>
            <button type="button" class="ghost-btn" @click="goPreview">查看导航效果</button>
            <button type="button" class="ghost-btn" @click="autoLinkAllFloorNodes">自动连线</button>
            <button type="button" class="ghost-btn" @click="resetCollector">重置当前模式状态</button>
            <button type="button" class="ghost-btn" @click="clearLocalCache">清空本地缓存</button>
          </div>
          <div class="hint">自动连线会按四层节点一次性补全边：先做同层连通，再自动补电梯/楼梯跨层边。</div>
          <div class="hint">采集数据会自动保存在当前浏览器（刷新不丢失）。</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import L from 'leaflet'

export default {
  name: 'Navigation',
  data() {
    return {
      baseMapMode: 'floor',
      floorList: ['1F', '2F', '3F', '4F'],
      currentFloor: '1F',
      showNodes: true,

      nodes: {},
      edges: {},

      collectorMode: 'node', // node | edge | none
      newNodeName: '',
      newNodeType: 'room',
      edgeKind: 'walk',
      edgeWeight: null,
      edgePickA: '',
      renameNodeId: '',
      renameNodeName: '',
      deleteNodeId: '',
      actionMessage: '',
      recentEdge: null,

      _map: null,
      _imgLayer: null,
      _nodeLayer: null,
      _hintLayer: null,
      _edgeFlashTimer: null,

      floorplanByFloor: {
        '1F': new URL('../assets/floorplans/floors/1F.jpg', import.meta.url).href,
        '2F': new URL('../assets/floorplans/floors/2F.jpg', import.meta.url).href,
        '3F': new URL('../assets/floorplans/floors/3F.jpg', import.meta.url).href,
        '4F': new URL('../assets/floorplans/floors/4F.jpg', import.meta.url).href
      },
      indexHref: new URL('../assets/floorplans/index/index.png', import.meta.url).href,
      imageSizeByFloor: {},
      indexImageSize: { w: 900, h: 1899 },
      activeImageSize: { w: 1000, h: 1000 }
    }
  },
  computed: {
    nodesList() {
      return Object.values(this.nodes || {})
    },
    nodesOnFloor() {
      return this.nodesList.filter((n) => n.floor === this.currentFloor)
    },
    nodesOnFloorSorted() {
      return [...this.nodesOnFloor].sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''), 'zh-Hans-CN'))
    },
    modeLabel() {
      if (this.collectorMode === 'node') return '采节点'
      if (this.collectorMode === 'edge') return '连边'
      return '关闭'
    },
    modeHint() {
      if (this.collectorMode === 'node') return '请先填写“节点名称”，再点击地图采集节点'
      if (this.collectorMode === 'edge') return this.edgePickA ? '已选择 A 节点，请点击 B 节点完成连边' : '请先点击 A 节点，再点击 B 节点'
      return '已关闭采集，当前不会写入数据'
    },
    mapCursorClass() {
      if (this.collectorMode === 'node') return 'cursor-crosshair'
      if (this.collectorMode === 'edge') return 'cursor-pointer'
      return 'cursor-default'
    }
  },
  mounted() {
    this.restoreLocalCache()
    this.initMap()
    this._edgeFlashTimer = setInterval(() => {
      if (this.recentEdge && Date.now() > this.recentEdge.expiresAt) {
        this.recentEdge = null
        this.renderNodes()
      }
    }, 300)
  },
  beforeUnmount() {
    if (this._edgeFlashTimer) clearInterval(this._edgeFlashTimer)
    if (this._map) this._map.remove()
    this._map = null
  },
  methods: {
    async initMap() {
      this._map = L.map(this.$refs.mapEl, {
        crs: L.CRS.Simple,
        zoomControl: true,
        minZoom: -8,
        maxZoom: 8,
        scrollWheelZoom: true,
        doubleClickZoom: true,
        touchZoom: true,
        boxZoom: true,
        keyboard: true,
        dragging: true,
        inertia: false
      })
      this._nodeLayer = L.layerGroup().addTo(this._map)
      this._hintLayer = L.layerGroup().addTo(this._map)

      await this.setBaseLayer(true)

      this._map.on('click', (e) => this.onMapClick(e))
    },
    async switchBase(mode) {
      this.baseMapMode = mode
      await this.setBaseLayer(true)
    },
    async setFloor(f) {
      this.currentFloor = f
      if (this.baseMapMode === 'floor') await this.setBaseLayer(true)
      this.renderNodes()
    },
    resolveBaseUrl(mode = this.baseMapMode, floor = this.currentFloor) {
      if (mode === 'index') return this.indexHref
      return this.floorplanByFloor[floor] || Object.values(this.floorplanByFloor)[0]
    },
    async loadImageSize(url) {
      return new Promise((resolve) => {
        const img = new Image()
        img.onload = () => {
          const w = Number(img.naturalWidth) || 1000
          const h = Number(img.naturalHeight) || 1000
          resolve({ w, h })
        }
        img.onerror = () => resolve({ w: 1000, h: 1000 })
        img.src = url
      })
    },
    async ensureImageSize(mode = this.baseMapMode, floor = this.currentFloor) {
      if (mode === 'index') {
        if (!this.indexImageSize?.w || !this.indexImageSize?.h) {
          this.indexImageSize = await this.loadImageSize(this.indexHref)
        }
        return this.indexImageSize
      }
      const floorKey = floor || this.currentFloor
      if (!this.imageSizeByFloor[floorKey]?.w || !this.imageSizeByFloor[floorKey]?.h) {
        const url = this.resolveBaseUrl('floor', floorKey)
        const size = await this.loadImageSize(url)
        this.imageSizeByFloor = {
          ...this.imageSizeByFloor,
          [floorKey]: size
        }
      }
      return this.imageSizeByFloor[floorKey]
    },
    async setBaseLayer(needFitBounds = false) {
      const url = this.resolveBaseUrl(this.baseMapMode, this.currentFloor)
      const size = await this.ensureImageSize(this.baseMapMode, this.currentFloor)
      this.activeImageSize = size
      const { w, h } = size
      const bounds = [[0, 0], [h, w]]
      if (this._imgLayer) this._imgLayer.remove()
      this._imgLayer = L.imageOverlay(url, bounds).addTo(this._map)
      if (needFitBounds) {
        this._map.fitBounds(bounds, { animate: false })
        // 使用真实底图边界，允许用户继续缩放与拖拽
        this._map.setMaxBounds(bounds)
      }
      this.renderNodes()
    },
    renderNodes() {
      if (!this._nodeLayer) return
      this._nodeLayer.clearLayers()
      this._hintLayer.clearLayers()

      if (!this.showNodes || this.baseMapMode !== 'floor') return
      for (const n of this.nodesOnFloor) {
        const fill = n.type === 'lift' ? '#0ea5e9' : (n.type === 'stairs' ? '#f97316' : '#6366f1')
        const marker = L.circleMarker([n.y, n.x], {
          radius: 6,
          color: '#111827',
          weight: 2,
          fillColor: fill,
          fillOpacity: 0.9
        }).addTo(this._nodeLayer).bindTooltip(n.name, { direction: 'top' })
        marker.on('click', () => this.onNodeClick(n.id))
      }

      if (this.collectorMode === 'edge' && this.edgePickA && this.nodes[this.edgePickA]) {
        const a = this.nodes[this.edgePickA]
        L.circleMarker([a.y, a.x], {
          radius: 10,
          color: '#ef4444',
          weight: 3,
          fillOpacity: 0
        }).addTo(this._hintLayer).bindTooltip('A', { permanent: true, direction: 'right' })
      }

      if (this.collectorMode === 'edge' && this.recentEdge) {
        const a = this.nodes[this.recentEdge.a]
        const b = this.nodes[this.recentEdge.b]
        if (a && b) {
          L.polyline([[a.y, a.x], [b.y, b.x]], {
            color: '#22c55e',
            weight: 5,
            opacity: 0.95
          }).addTo(this._hintLayer).bindTooltip('已创建边', { direction: 'center' })
        }
      }
    },
    onMapClick(e) {
      if (this.baseMapMode !== 'floor') return
      if (this.collectorMode !== 'node') return
      const name = (this.newNodeName || '').trim()
      if (!name) return
      const x = e.latlng.lng
      const y = e.latlng.lat
      const id = this.makeNodeId(this.currentFloor, this.newNodeType, name)
      this.nodes = {
        ...this.nodes,
        [id]: { id, name, floor: this.currentFloor, x, y, type: this.newNodeType }
      }
      this.persistLocalCache()
      this.actionMessage = `已创建节点：${name}（${this.currentFloor}）`
      this.renderNodes()
    },
    onNodeClick(id) {
      if (this.collectorMode !== 'edge') return
      if (!this.edgePickA) {
        this.edgePickA = id
        this.actionMessage = `已选 A 点：${this.nodes[id]?.name || id}，请点击 B 点`
        this.renderNodes()
        return
      }
      if (this.edgePickA === id) return
      const aId = this.edgePickA
      this.addEdge(aId, id, this.edgeKind, this.edgeWeight)
      this.recentEdge = { a: aId, b: id, expiresAt: Date.now() + 2000 }
      this.actionMessage = `已创建边：${this.nodes[aId]?.name || aId} ↔ ${this.nodes[id]?.name || id}`
      this.edgePickA = ''
      this.renderNodes()
    },
    makeNodeId(floor, type, name) {
      const safe = (name || '').trim().replace(/\s+/g, '_').replace(/[^\w\u4e00-\u9fa5]+/g, '')
      const ts = Date.now().toString(36)
      return `${floor}_${type}_${safe}_${ts}`
    },
    addEdge(a, b, kind, weight) {
      const na = this.nodes[a]
      const nb = this.nodes[b]
      if (!na || !nb) return
      const newEdges = { ...(this.edges || {}) }
      if (!newEdges[a]) newEdges[a] = []
      if (!newEdges[b]) newEdges[b] = []
      const exists = (from, to) => (newEdges[from] || []).some((e) => e.to === to)
      const w = this.computeEdgeWeight(na, nb, kind, weight)
      if (!exists(a, b)) newEdges[a] = [...newEdges[a], { to: b, w, kind }]
      if (!exists(b, a)) newEdges[b] = [...newEdges[b], { to: a, w, kind }]
      this.edges = newEdges
      this.persistLocalCache()
    },
    computeEdgeWeight(na, nb, kind, weight) {
      if (typeof weight === 'number' && !Number.isNaN(weight) && weight > 0) return weight
      if (kind === 'elevator') return 50
      if (kind === 'stairs') return 80
      const dx = (na.x ?? 0) - (nb.x ?? 0)
      const dy = (na.y ?? 0) - (nb.y ?? 0)
      return Math.max(5, Math.round(Math.sqrt(dx * dx + dy * dy)))
    },
    resetCollector() {
      this.newNodeName = ''
      this.newNodeType = 'room'
      this.edgeKind = 'walk'
      this.edgeWeight = null
      this.edgePickA = ''
      this.renameNodeId = ''
      this.renameNodeName = ''
      this.deleteNodeId = ''
      this.recentEdge = null
      this.actionMessage = '已重置当前采集模式状态'
      this.renderNodes()
    },
    renameSelectedNode() {
      const id = this.renameNodeId
      const nextName = String(this.renameNodeName || '').trim()
      if (!id || !nextName || !this.nodes[id]) return
      const oldName = this.nodes[id].name
      this.nodes = {
        ...this.nodes,
        [id]: {
          ...this.nodes[id],
          name: nextName
        }
      }
      this.persistLocalCache()
      this.renderNodes()
      this.actionMessage = `已重命名：${oldName} → ${nextName}`
      this.renameNodeName = ''
    },
    autoRenameDuplicatesCurrentFloor() {
      const count = this.autoRenameDuplicatesByFloors([this.currentFloor])
      this.actionMessage = `${this.currentFloor} 重复名称自动编号完成：更新 ${count} 个节点`
    },
    autoRenameDuplicatesAllFloors() {
      const count = this.autoRenameDuplicatesByFloors(this.floorList)
      this.actionMessage = `全楼层重复名称自动编号完成：更新 ${count} 个节点`
    },
    autoRenameDuplicatesByFloors(floors = []) {
      const floorSet = new Set(floors)
      const cloned = { ...this.nodes }
      let changed = 0

      for (const floor of floorSet) {
        const floorNodes = Object.values(cloned).filter((n) => n.floor === floor)
        const groups = {}
        floorNodes.forEach((n) => {
          const base = String(n.name || '').trim()
          if (!base) return
          const key = `${n.type}::${base}`
          if (!groups[key]) groups[key] = []
          groups[key].push(n)
        })
        Object.values(groups).forEach((arr) => {
          if (arr.length <= 1) return
          arr.sort((a, b) => (a.y - b.y) || (a.x - b.x))
          arr.forEach((n, idx) => {
            const base = String(n.name || '').trim().replace(/-\d+$/, '')
            const next = `${base}-${idx + 1}`
            if (n.name === next) return
            cloned[n.id] = {
              ...cloned[n.id],
              name: next
            }
            changed += 1
          })
        })
      }
      if (changed > 0) {
        this.nodes = cloned
        this.persistLocalCache()
        this.renderNodes()
      }
      return changed
    },
    deleteSelectedNode() {
      const id = this.deleteNodeId
      const node = this.nodes[id]
      if (!id || !node) return

      const nextNodes = { ...this.nodes }
      delete nextNodes[id]

      const nextEdges = {}
      Object.keys(this.edges || {}).forEach((from) => {
        if (from === id) return
        const kept = (this.edges[from] || []).filter((e) => e.to !== id)
        if (kept.length) nextEdges[from] = kept
      })

      this.nodes = nextNodes
      this.edges = nextEdges
      if (this.edgePickA === id) this.edgePickA = ''
      if (this.renameNodeId === id) {
        this.renameNodeId = ''
        this.renameNodeName = ''
      }
      this.deleteNodeId = ''
      this.persistLocalCache()
      this.renderNodes()
      this.actionMessage = `已删除节点：${node.name}（相关连边已清理）`
    },
    clearAll() {
      this.nodes = {}
      this.edges = {}
      this.resetCollector()
      this.persistLocalCache()
      this.actionMessage = '已清空采集数据（nodes / edges）'
    },
    exportJson() {
      const nodesOut = Object.values(this.nodes || {}).map((n) => ({
        id: n.id,
        name: n.name,
        floor: n.floor,
        x: Math.round((n.x ?? 0) * 100) / 100,
        y: Math.round((n.y ?? 0) * 100) / 100,
        type: n.type
      }))
      const edgesOut = []
      const seen = new Set()
      Object.keys(this.edges || {}).forEach((from) => {
        ;(this.edges[from] || []).forEach((e) => {
          const to = e.to
          const key = [from, to].sort().join('__')
          if (seen.has(key)) return
          seen.add(key)
          edgesOut.push({
            from,
            to,
            kind: e.kind || 'walk',
            weight: e.w
          })
        })
      })
      this.downloadJson('nodes.json', nodesOut)
      this.downloadJson('edges.json', edgesOut)
      this.actionMessage = `导出成功：nodes(${nodesOut.length})，edges(${edgesOut.length})`
    },
    goPreview() {
      this.$router.push('/navigation-preview')
    },
    persistLocalCache() {
      try {
        const payload = {
          version: 2,
          nodes: this.nodes || {},
          edges: this.edges || {},
          imageSizeByFloor: this.imageSizeByFloor || {},
          currentFloor: this.currentFloor,
          savedAt: Date.now()
        }
        localStorage.setItem('medical.indoor.collector.v1', JSON.stringify(payload))
      } catch (e) {
        // ignore localStorage errors
      }
    },
    restoreLocalCache() {
      try {
        const raw = localStorage.getItem('medical.indoor.collector.v1')
        if (!raw) return
        const data = JSON.parse(raw)
        if (!data || typeof data !== 'object') return
        if (data.nodes && typeof data.nodes === 'object') this.nodes = data.nodes
        if (data.edges && typeof data.edges === 'object') this.edges = data.edges
        if (data.imageSizeByFloor && typeof data.imageSizeByFloor === 'object') {
          this.imageSizeByFloor = data.imageSizeByFloor
        }
        if (data.currentFloor && this.floorList.includes(data.currentFloor)) this.currentFloor = data.currentFloor
        if ((data.version || 1) < 2) {
          this.migrateLegacyNodesFrom1000()
        }
      } catch (e) {
        // ignore malformed cache
      }
    },
    migrateLegacyNodesFrom1000() {
      const defaultBase = { w: 1000, h: 1000 }
      const migratedNodes = {}
      Object.values(this.nodes || {}).forEach((node) => {
        const n = { ...node }
        const floorSize = this.imageSizeByFloor?.[n.floor] || defaultBase
        const sx = floorSize.w / 1000
        const sy = floorSize.h / 1000
        n.x = Number((Number(n.x || 0) * sx).toFixed(2))
        n.y = Number((Number(n.y || 0) * sy).toFixed(2))
        migratedNodes[n.id] = n
      })
      this.nodes = migratedNodes
      this.actionMessage = '已将旧版 1000x1000 坐标迁移为真实图像尺寸坐标'
      this.persistLocalCache()
    },
    autoLinkAllFloorNodes() {
      let totalAdded = 0
      let crossAdded = 0
      for (const floor of this.floorList) {
        totalAdded += this.autoLinkByFloor(floor)
      }
      crossAdded = this.autoLinkCrossFloor()
      totalAdded += crossAdded
      this.actionMessage = `四层自动连线完成：同层新增 ${totalAdded - crossAdded} 条，跨层新增 ${crossAdded} 条，总计 ${totalAdded} 条`
      this.renderNodes()
    },
    autoLinkByFloor(floor) {
      const list = this.nodesList.filter((n) => n.floor === floor)
      if (list.length < 2) return 0

      const calcDist = (a, b) => {
        const dx = (a.x || 0) - (b.x || 0)
        const dy = (a.y || 0) - (b.y || 0)
        return Math.sqrt(dx * dx + dy * dy)
      }

      const pairDist = []
      for (let i = 0; i < list.length; i++) {
        for (let j = i + 1; j < list.length; j++) {
          pairDist.push({ a: list[i], b: list[j], d: calcDist(list[i], list[j]) })
        }
      }
      if (!pairDist.length) return 0
      pairDist.sort((x, y) => x.d - y.d)

      const nearest = []
      for (const n of list) {
        let best = Infinity
        for (const m of list) {
          if (m.id === n.id) continue
          best = Math.min(best, calcDist(n, m))
        }
        if (Number.isFinite(best)) nearest.push(best)
      }
      nearest.sort((a, b) => a - b)
      const medianNearest = nearest[Math.floor(nearest.length / 2)] || 0
      const maxLinkDistance = Math.max(60, Math.round(medianNearest * 2.2))

      // 先用并查集构造最小生成树，确保该层节点整体连通
      const parent = {}
      const find = (id) => {
        if (parent[id] !== id) parent[id] = find(parent[id])
        return parent[id]
      }
      const union = (a, b) => {
        const ra = find(a)
        const rb = find(b)
        if (ra === rb) return false
        parent[rb] = ra
        return true
      }
      list.forEach((n) => { parent[n.id] = n.id })

      let added = 0
      for (const pair of pairDist) {
        if (!union(pair.a.id, pair.b.id)) continue
        this.addEdge(pair.a.id, pair.b.id, 'walk', null)
        added += 1
      }

      // 在连通基础上，每个节点额外补 1 条就近边（距离不过远），提升路径灵活性
      const hasEdge = (from, to) => (this.edges[from] || []).some((e) => e.to === to)
      for (const n of list) {
        const candidates = list
          .filter((m) => m.id !== n.id)
          .map((m) => ({ id: m.id, d: calcDist(n, m) }))
          .sort((a, b) => a.d - b.d)
        const firstNearby = candidates.find((c) => c.d <= maxLinkDistance && !hasEdge(n.id, c.id))
        if (!firstNearby) continue
        this.addEdge(n.id, firstNearby.id, 'walk', null)
        added += 1
      }

      if (added > 0) this.persistLocalCache()
      return added
    },
    autoLinkCrossFloor() {
      const list = this.nodesList.filter((n) => n.type === 'lift' || n.type === 'stairs')
      if (list.length < 2) return 0
      const floorOrder = this.floorList.reduce((acc, f, i) => ({ ...acc, [f]: i }), {})
      const normName = (name) => String(name || '').toLowerCase().replace(/\s+/g, '').replace(/[^\w\u4e00-\u9fa5]/g, '')
      const calcDist = (a, b) => {
        const dx = (a.x || 0) - (b.x || 0)
        const dy = (a.y || 0) - (b.y || 0)
        return Math.sqrt(dx * dx + dy * dy)
      }
      const hasEdge = (from, to) => (this.edges[from] || []).some((e) => e.to === to)
      const linkedPairs = new Set()
      let added = 0

      const tryConnect = (a, b, kind) => {
        const key = [a.id, b.id].sort().join('__')
        if (linkedPairs.has(key)) return
        if (hasEdge(a.id, b.id)) {
          linkedPairs.add(key)
          return
        }
        this.addEdge(a.id, b.id, kind, null)
        linkedPairs.add(key)
        added += 1
      }

      // 优先同名同类型跨层连接（电梯井/楼梯井）
      const grouped = {}
      for (const n of list) {
        const key = `${n.type}::${normName(n.name)}`
        if (!grouped[key]) grouped[key] = []
        grouped[key].push(n)
      }
      Object.values(grouped).forEach((arr) => {
        if (arr.length < 2) return
        arr.sort((a, b) => (floorOrder[a.floor] ?? 99) - (floorOrder[b.floor] ?? 99))
        for (let i = 0; i < arr.length - 1; i++) {
          const a = arr[i]
          const b = arr[i + 1]
          if (a.floor === b.floor) continue
          tryConnect(a, b, a.type === 'lift' ? 'elevator' : 'stairs')
        }
      })

      // 对没同名的点，按相邻楼层最近邻补全（避免跨层断路）
      for (let i = 0; i < this.floorList.length - 1; i++) {
        const f1 = this.floorList[i]
        const f2 = this.floorList[i + 1]
        const aFloor = list.filter((n) => n.floor === f1)
        const bFloor = list.filter((n) => n.floor === f2)
        for (const a of aFloor) {
          const sameType = bFloor.filter((b) => b.type === a.type)
          if (!sameType.length) continue
          const nearest = sameType
            .map((b) => ({ b, d: calcDist(a, b) }))
            .sort((x, y) => x.d - y.d)[0]
          if (!nearest || nearest.d > 180) continue
          tryConnect(a, nearest.b, a.type === 'lift' ? 'elevator' : 'stairs')
        }
      }

      if (added > 0) this.persistLocalCache()
      return added
    },
    clearLocalCache() {
      try {
        localStorage.removeItem('medical.indoor.collector.v1')
        this.actionMessage = '已清空本地缓存'
      } catch (e) {
        // ignore
      }
    },
    downloadJson(filename, obj) {
      const blob = new Blob([JSON.stringify(obj, null, 2)], { type: 'application/json;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    }
  }
}
</script>

<style scoped>
.collector-page {
  max-width: 1300px;
  margin: 0 auto;
  padding: 1.5rem 0 2rem;
}

.page-title {
  color: white;
  text-align: center;
  font-size: 2.2rem;
  margin-bottom: 1.2rem;
}

.map-pane {
  background: white;
  border-radius: 16px;
  padding: 1rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.map-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.65rem;
}

.topbar-left,
.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.segmented {
  display: inline-flex;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  overflow: hidden;
  background: white;
}

.seg-btn {
  padding: 0.45rem 0.8rem;
  border: none;
  background: transparent;
  cursor: pointer;
  font-weight: 900;
  color: #374151;
}
.seg-btn.active {
  background: #eef2ff;
  color: #3730a3;
}

.floor-tabs {
  display: inline-flex;
  gap: 0.4rem;
}

.tab {
  padding: 0.42rem 0.7rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: #f8fafc;
  cursor: pointer;
  font-weight: 900;
}
.tab.active {
  background: #111827;
  color: white;
  border-color: #111827;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.55rem;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: white;
  font-weight: 900;
  font-size: 0.85rem;
}
.check input { accent-color: #6366f1; }

.status-bar {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 0.55rem 0.75rem;
  font-size: 0.9rem;
  font-weight: 800;
  color: #334155;
  margin-bottom: 0.65rem;
}
.status-sep { margin: 0 0.45rem; color: #94a3b8; }

.action-bar {
  margin-bottom: 0.65rem;
  background: #ecfeff;
  border: 1px solid #a5f3fc;
  color: #155e75;
  border-radius: 12px;
  padding: 0.5rem 0.75rem;
  font-weight: 900;
  font-size: 0.9rem;
}

.leaflet-wrap {
  position: relative;
}

.leaflet-map {
  width: 100%;
  height: 660px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  background: #f8fafc;
}

.cursor-default { cursor: default; }
.cursor-crosshair { cursor: crosshair; }
.cursor-pointer { cursor: copy; }

.tool-panel {
  margin-top: 0.9rem;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 0.85rem;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.tool-title {
  font-weight: 1000;
  color: #111827;
  margin-bottom: 0.5rem;
}

.tool-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
  margin: 0.35rem 0;
}

.tool-block {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 0.6rem;
}

.mini-input {
  height: 34px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 0 0.75rem;
  font-weight: 800;
  background: white;
  min-width: 240px;
}
.mini-input.short { min-width: 140px; }

.mini-select {
  height: 34px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 0 0.6rem;
  font-weight: 900;
  background: white;
}

.hint {
  color: #6b7280;
  font-weight: 800;
  font-size: 0.86rem;
  line-height: 1.4;
}

.primary-btn {
  padding: 0.55rem 0.95rem;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  font-weight: 900;
}

.ghost-btn {
  padding: 0.55rem 0.85rem;
  border-radius: 12px;
  border: 1px solid #d1d5db;
  background: white;
  cursor: pointer;
  font-weight: 900;
  color: #374151;
}

.danger-btn {
  border-color: #fecaca;
  color: #b91c1c;
  background: #fff7f7;
}
</style>

