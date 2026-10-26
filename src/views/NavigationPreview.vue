<template>
  <div class="preview-page">
    <h1 class="page-title">院内导航</h1>

    <div class="layout">
      <section class="map-pane">
        <div class="toolbar">
          <div class="floor-tabs">
            <button type="button" :class="['tab', { active: currentFloor === '1F' }]" @click="setFloor('1F')">1F</button>
            <button type="button" :class="['tab', { active: currentFloor === '2F' }]" @click="setFloor('2F')">2F</button>
            <button type="button" :class="['tab', { active: currentFloor === '3F' }]" @click="setFloor('3F')">3F</button>
            <button type="button" :class="['tab', { active: currentFloor === '4F' }]" @click="setFloor('4F')">4F</button>
          </div>
          <div class="toolbar-actions">
            <label class="check">
              <input type="checkbox" v-model="showAllNodes" />
              <span>显示全部节点</span>
            </label>
          </div>
        </div>

        <div v-if="floorSwitchBanner" class="floor-switch-banner" role="status" aria-live="polite">
          {{ floorSwitchBanner }}
        </div>

        <div ref="mapEl" class="leaflet-map"></div>
      </section>

      <aside class="panel">
        <div class="card">
          <div class="title">路径规划</div>
          <div class="row">
            <label>起点</label>
            <div class="start-mode">
              <label class="radio">
                <input type="radio" value="free" v-model="startMode" />
                <span>地图选点</span>
              </label>
              <label class="radio">
                <input type="radio" value="node" v-model="startMode" />
                <span>从节点选择</span>
              </label>
            </div>
            <div v-if="startMode === 'node'">
              <select v-model="startId">
                <option value="">请选择起点</option>
                <option v-for="n in nodeOptions" :key="n.id" :value="n.id">{{ n.name }}（{{ n.floor }}）</option>
              </select>
            </div>
            <div v-else class="free-start-hint">
              <div class="hint">在地图上单击任意位置设置起点。</div>
            </div>
          </div>
          <div class="row">
            <label>终点</label>
            <select v-model="endId">
              <option value="">请选择终点</option>
              <option v-for="n in nodeOptions" :key="n.id" :value="n.id">{{ n.name }}（{{ n.floor }}）</option>
            </select>
          </div>
          <div class="actions">
            <button class="primary" :disabled="!canPlan" @click="planRoute">规划路线</button>
            <button class="primary" :disabled="routePathIds.length < 2 || isAnimating" @click="playRouteAnimation">开始导航动画</button>
            <button class="ghost" :disabled="!isAnimating" @click="stopRouteAnimation">停止动画</button>
            <button class="ghost" :disabled="!startId && !freeStartPoint && !endId" @click="clearRoute">清空</button>
          </div>
          <div v-if="error" class="error">{{ error }}</div>
          <div v-if="routePolicyHint" class="hint">{{ routePolicyHint }}</div>
          <div v-if="floorSwitchNotices.length" class="floor-switch-notices">
            <div class="notice-title">楼层切换提示</div>
            <div v-for="(t, idx) in floorSwitchNotices" :key="t + idx" class="notice-item">
              {{ idx + 1 }}. {{ t }}
            </div>
          </div>
        </div>

        <div class="card">
          <div class="title">路线结果</div>
          <div v-if="!routePathIds.length" class="hint">请选择起点终点后规划。</div>
          <div v-else class="hint">路径节点：{{ routePathIds.length }} 个</div>
          <div class="steps">
            <div v-for="(id, idx) in routePathIds" :key="id + idx" class="step">
              {{ idx + 1 }}. {{ effectiveNodesForRouting[id]?.name || id }}（{{ effectiveNodesForRouting[id]?.floor }}）
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script>
import L from 'leaflet'
import { aStar } from '../utils/indoor-nav/astar'
import nodesData from '../data/indoor/nodes.json'
import edgesData from '../data/indoor/edges.json'

const VIRTUAL_START_ID = '__virtual_start__'
const ANIMATION_TICK_MS = 28
const ANIMATION_PROGRESS_STEP = 0.075

function buildGraphFromJson(nodesArr, edgesArr) {
  const nodes = {}
  ;(nodesArr || []).forEach((n) => {
    if (!n || !n.id) return
    nodes[n.id] = n
  })

  const edges = {}
  const add = (a, b, w, kind) => {
    if (!edges[a]) edges[a] = []
    edges[a].push({ to: b, w, kind })
  }
  ;(edgesArr || []).forEach((e) => {
    if (!e || !e.from || !e.to) return
    const w = typeof e.weight === 'number' ? e.weight : 1
    add(e.from, e.to, w, e.kind || 'walk')
    add(e.to, e.from, w, e.kind || 'walk')
  })
  return { nodes, edges }
}

function ensureAdjacentFloorVerticalBackbone(nodesMap, edgesMap) {
  const nextEdges = cloneEdgesMap(edgesMap || {})
  const floors = ['1F', '2F', '3F', '4F']
  const byFloor = {}
  Object.values(nodesMap || {}).forEach((n) => {
    if (!n?.id || !n?.floor) return
    if (!byFloor[n.floor]) byFloor[n.floor] = []
    byFloor[n.floor].push(n)
  })

  const addBi = (a, b, w, kind) => {
    if (!a || !b) return
    if (!nextEdges[a]) nextEdges[a] = []
    if (!nextEdges[b]) nextEdges[b] = []
    if (!nextEdges[a].some((e) => e?.to === b)) nextEdges[a].push({ to: b, w, kind, inferred: true, backbone: true })
    if (!nextEdges[b].some((e) => e?.to === a)) nextEdges[b].push({ to: a, w, kind, inferred: true, backbone: true })
  }

  const familyOfLift = (n) => {
    if (n?.type !== 'lift') return ''
    const name = String(n?.name || '').toUpperCase()
    if (/(A1.*A2|A2.*A1)/.test(name)) return 'A1A2'
    if (/(A3.*A4|A4.*A3)/.test(name)) return 'A3A4'
    if (/扶梯/.test(name)) return 'ESCALATOR'
    if (/货梯/.test(name)) return 'FREIGHT'
    return ''
  }

  const pickNearestByName = (list, needleRe) => {
    const pool = (list || []).filter((n) => needleRe.test(String(n?.name || '')))
    if (!pool.length) return null
    // 选“更像垂直交通”的优先：lift/stairs > 其他；同类取第一个即可（采集数据中同名通常唯一）
    pool.sort((a, b) => {
      const sa = (a.type === 'lift' || a.type === 'stairs') ? 0 : 1
      const sb = (b.type === 'lift' || b.type === 'stairs') ? 0 : 1
      return sa - sb
    })
    return pool[0]
  }

  for (let i = 0; i < floors.length - 1; i++) {
    const f1 = floors[i]
    const f2 = floors[i + 1]
    const list1 = byFloor[f1] || []
    const list2 = byFloor[f2] || []
    if (!list1.length || !list2.length) continue

    // 电梯（按家族连通相邻楼层）
    const lifts1 = list1.filter((n) => n?.type === 'lift')
    const lifts2 = list2.filter((n) => n?.type === 'lift')
    ;['A1A2', 'A3A4', 'ESCALATOR', 'FREIGHT'].forEach((fam) => {
      const a = lifts1.find((n) => familyOfLift(n) === fam)
      const b = lifts2.find((n) => familyOfLift(n) === fam)
      if (a && b) addBi(a.id, b.id, 50, 'elevator')
    })

    // 楼梯：优先连 “A3客梯旁楼梯” 与 “通往住院部楼梯”，保证最基础跨层链路存在
    const stairs1 = list1.filter((n) => n?.type === 'stairs')
    const stairs2 = list2.filter((n) => n?.type === 'stairs')
    const a3_1 = pickNearestByName(stairs1, /A3.*客梯.*楼梯/i)
    const a3_2 = pickNearestByName(stairs2, /A3.*客梯.*楼梯/i)
    if (a3_1 && a3_2) addBi(a3_1.id, a3_2.id, 80, 'stairs')
    const ward1 = pickNearestByName(stairs1, /通往住院部楼梯/i)
    const ward2 = pickNearestByName(stairs2, /通往住院部楼梯/i)
    if (ward1 && ward2) addBi(ward1.id, ward2.id, 80, 'stairs')
  }

  return nextEdges
}

function cloneEdgesMap(edgesMap) {
  const next = {}
  Object.keys(edgesMap || {}).forEach((from) => {
    next[from] = (edgesMap[from] || []).map((e) => ({ ...e }))
  })
  return next
}

function distBetween(a, b) {
  const dx = (a?.x ?? 0) - (b?.x ?? 0)
  const dy = (a?.y ?? 0) - (b?.y ?? 0)
  return Math.sqrt(dx * dx + dy * dy)
}

function inferSupplementalWalkEdges(nodesMap, edgesMap) {
  const nextEdges = cloneEdgesMap(edgesMap)
  const byFloor = {}
  Object.values(nodesMap || {}).forEach((n) => {
    if (!n?.id || !n?.floor || n.id === VIRTUAL_START_ID) return
    if (!byFloor[n.floor]) byFloor[n.floor] = []
    byFloor[n.floor].push(n)
  })

  const addBidirectional = (aId, bId, w) => {
    if (!nextEdges[aId]) nextEdges[aId] = []
    if (!nextEdges[bId]) nextEdges[bId] = []
    const hasAB = nextEdges[aId].some((e) => e?.to === bId)
    const hasBA = nextEdges[bId].some((e) => e?.to === aId)
    if (!hasAB) nextEdges[aId].push({ to: bId, w, kind: 'walk', inferred: true })
    if (!hasBA) nextEdges[bId].push({ to: aId, w, kind: 'walk', inferred: true })
  }

  const isTransitNode = (n) => ['hub', 'turn', 'entrance', 'lift'].includes(n?.type)
  const isRoomNode = (n) => n?.type === 'room'

  Object.values(byFloor).forEach((list) => {
    if (list.length < 2) return
    const nearest = []
    list.forEach((n) => {
      let best = Infinity
      list.forEach((m) => {
        if (m.id === n.id) return
        best = Math.min(best, distBetween(n, m))
      })
      if (Number.isFinite(best)) nearest.push(best)
    })
    nearest.sort((a, b) => a - b)
    const medianNearest = nearest[Math.floor(nearest.length / 2)] || 320
    const maxTransitLink = Math.max(320, Math.round(medianNearest * 2.6))
    const maxAnyLink = Math.max(260, Math.round(medianNearest * 1.9))

    list.forEach((fromNode) => {
      const sorted = list
        .filter((toNode) => toNode.id !== fromNode.id)
        .map((toNode) => ({ toNode, d: distBetween(fromNode, toNode) }))
        .sort((a, b) => a.d - b.d)
      const transitCandidates = sorted.filter((x) => isTransitNode(x.toNode) && x.d <= maxTransitLink)
      // room 节点只补“到公共节点”的最近连线，避免把科室当走廊中转
      const picks = isRoomNode(fromNode)
        ? transitCandidates.slice(0, 1)
        : (() => {
            const anyCandidate = sorted.find((x) => x.d <= maxAnyLink)
            return anyCandidate ? [...transitCandidates.slice(0, 3), anyCandidate] : transitCandidates.slice(0, 3)
          })()
      picks.forEach(({ toNode, d }) => {
        // 房间与房间之间不额外补边，避免穿科室抄近路
        if (isRoomNode(fromNode) && isRoomNode(toNode)) return
        const w = Math.max(5, Math.round(d))
        addBidirectional(fromNode.id, toNode.id, w)
      })
    })
  })

  return nextEdges
}

function buildVirtualCorridorGraph(baseNodesMap, baseEdgesMap, floorSizeByFloor = {}) {
  const nextNodes = { ...(baseNodesMap || {}) }
  const nextEdges = cloneEdgesMap(baseEdgesMap || {})
  const GRID_STEP = 240
  const ROOM_BUFFER = 260
  const NON_ROOM_JOIN_RADIUS = 320
  const ROOM_JOIN_RADIUS = 420

  const addBidirectional = (aId, bId, w, kind = 'walk') => {
    if (!nextEdges[aId]) nextEdges[aId] = []
    if (!nextEdges[bId]) nextEdges[bId] = []
    if (!nextEdges[aId].some((e) => e?.to === bId)) nextEdges[aId].push({ to: bId, w, kind, inferred: true })
    if (!nextEdges[bId].some((e) => e?.to === aId)) nextEdges[bId].push({ to: aId, w, kind, inferred: true })
  }

  const byFloor = {}
  Object.values(baseNodesMap || {}).forEach((n) => {
    if (!n?.id || !n?.floor || n.id === VIRTUAL_START_ID) return
    if (!byFloor[n.floor]) byFloor[n.floor] = []
    byFloor[n.floor].push(n)
  })

  Object.keys(byFloor).forEach((floor) => {
    const size = floorSizeByFloor?.[floor]
    if (!size?.w || !size?.h) return
    const floorNodes = byFloor[floor]
    const roomNodes = floorNodes.filter((n) => n.type === 'room')
    const nonRoomNodes = floorNodes.filter((n) => n.type !== 'room')
    const gridByKey = {}
    const floorGridNodes = []

    for (let x = GRID_STEP / 2; x <= size.w - GRID_STEP / 2; x += GRID_STEP) {
      for (let y = GRID_STEP / 2; y <= size.h - GRID_STEP / 2; y += GRID_STEP) {
        const tooCloseToRoom = roomNodes.some((r) => distBetween({ x, y }, r) < ROOM_BUFFER)
        if (tooCloseToRoom) continue
        const id = `__grid__${floor}__${Math.round(x)}__${Math.round(y)}`
        const node = { id, name: `走廊点(${floor})`, floor, x, y, type: 'turn', virtual: true }
        nextNodes[id] = node
        floorGridNodes.push(node)
        gridByKey[`${Math.round(x)}_${Math.round(y)}`] = id
      }
    }

    const dirs = [[GRID_STEP, 0], [0, GRID_STEP]]
    floorGridNodes.forEach((n) => {
      dirs.forEach(([dx, dy]) => {
        const nx = Math.round(n.x + dx)
        const ny = Math.round(n.y + dy)
        const nid = gridByKey[`${nx}_${ny}`]
        if (!nid) return
        const w = Math.max(5, Math.round(Math.sqrt(dx * dx + dy * dy)))
        addBidirectional(n.id, nid, w, 'walk')
      })
    })

    nonRoomNodes.forEach((n) => {
      const nearby = floorGridNodes
        .map((g) => ({ g, d: distBetween(n, g) }))
        .filter((x) => x.d <= NON_ROOM_JOIN_RADIUS)
        .sort((a, b) => a.d - b.d)
        .slice(0, 3)
      nearby.forEach(({ g, d }) => addBidirectional(n.id, g.id, Math.max(5, Math.round(d)), 'walk'))
    })

    // room 仅与最近走廊点连 1 条“出入口边”，能进出但不鼓励穿科室中转
    roomNodes.forEach((n) => {
      const nearest = floorGridNodes
        .map((g) => ({ g, d: distBetween(n, g) }))
        .filter((x) => x.d <= ROOM_JOIN_RADIUS)
        .sort((a, b) => a.d - b.d)[0]
      if (!nearest) return
      const w = Math.max(5, Math.round(nearest.d) + 900)
      addBidirectional(n.id, nearest.g.id, w, 'walk')
    })
  })

  return { nodes: nextNodes, edges: nextEdges }
}

function buildConnectedComponents(nodesMap, edgesMap) {
  const ids = Object.keys(nodesMap || {})
  const visited = new Set()
  const comps = []
  ids.forEach((id) => {
    if (visited.has(id)) return
    const queue = [id]
    visited.add(id)
    const comp = []
    while (queue.length) {
      const cur = queue.shift()
      comp.push(cur)
      const nbrs = edgesMap?.[cur] || []
      nbrs.forEach((e) => {
        const to = e?.to
        if (!to || !nodesMap[to] || visited.has(to)) return
        visited.add(to)
        queue.push(to)
      })
    }
    comps.push(comp)
  })
  return comps
}

function ensureGlobalReachability(nodesMap, edgesMap) {
  const nextEdges = cloneEdgesMap(edgesMap || {})
  const isVertical = (n) => n?.type === 'lift' || n?.type === 'stairs'
  const isPublic = (n) => n?.type !== 'room'
  const floorOrder = ['1F', '2F', '3F', '4F']
  const floorIndex = (f) => floorOrder.indexOf(f)
  const familyOf = (n) => {
    if (!n || !isVertical(n)) return ''
    const name = String(n.name || '').toUpperCase()
    if (/(A1.*A2|A2.*A1)/.test(name)) return 'A1A2'
    if (/(A3.*A4|A4.*A3)/.test(name)) return 'A3A4'
    if (/扶梯/.test(name)) return 'ESCALATOR'
    if (/货梯/.test(name)) return 'FREIGHT'
    return `${n.type}:${name.replace(/[^\w\u4e00-\u9fa5]/g, '')}`
  }
  const addBi = (a, b, w, kind = 'walk') => {
    if (!nextEdges[a]) nextEdges[a] = []
    if (!nextEdges[b]) nextEdges[b] = []
    if (!nextEdges[a].some((e) => e?.to === b)) nextEdges[a].push({ to: b, w, kind, inferred: true, global: true })
    if (!nextEdges[b].some((e) => e?.to === a)) nextEdges[b].push({ to: a, w, kind, inferred: true, global: true })
  }

  let guard = 0
  while (guard < 200) {
    guard += 1
    const comps = buildConnectedComponents(nodesMap, nextEdges)
    if (comps.length <= 1) break
    const compNodes = comps.map((ids) => ids.map((id) => nodesMap?.[id]).filter(Boolean))
    let best = null

    for (let i = 0; i < compNodes.length; i++) {
      for (let j = i + 1; j < compNodes.length; j++) {
        const A = compNodes[i]
        const B = compNodes[j]
        for (const a of A) {
          for (const b of B) {
            if (!a?.id || !b?.id) continue
            const sameFloor = a.floor === b.floor
            const fiA = floorIndex(a.floor)
            const fiB = floorIndex(b.floor)
            const floorGap = Math.abs((fiA < 0 ? 0 : fiA) - (fiB < 0 ? 0 : fiB))
            const d = distBetween(a, b)
            let pri = 9
            let kind = 'walk'
            let w = Math.max(5, Math.round(d))

            if (sameFloor && isPublic(a) && isPublic(b)) {
              pri = 0
            } else if (sameFloor) {
              pri = 1
              w += 240
            } else if (isVertical(a) && isVertical(b) && floorGap <= 1 && familyOf(a) === familyOf(b)) {
              pri = 2
              kind = a.type === 'stairs' || b.type === 'stairs' ? 'stairs' : 'elevator'
              w = kind === 'stairs' ? 80 : 50
            } else if (isPublic(a) && isPublic(b) && floorGap <= 1) {
              pri = 3
              kind = 'walk'
              w += 600
            } else {
              continue
            }

            const score = pri * 100000 + w
            if (!best || score < best.score) best = { aId: a.id, bId: b.id, w, kind, score }
          }
        }
      }
    }

    if (!best) break
    addBi(best.aId, best.bId, best.w, best.kind)
  }
  return nextEdges
}

function ensurePairReachability(nodesMap, edgesMap, startId, endId) {
  const nextEdges = cloneEdgesMap(edgesMap || {})
  const addBi = (a, b, w, kind = 'walk') => {
    if (!nextEdges[a]) nextEdges[a] = []
    if (!nextEdges[b]) nextEdges[b] = []
    if (!nextEdges[a].some((e) => e?.to === b)) nextEdges[a].push({ to: b, w, kind, inferred: true, rescue: true })
    if (!nextEdges[b].some((e) => e?.to === a)) nextEdges[b].push({ to: a, w, kind, inferred: true, rescue: true })
  }
  const isVertical = (n) => n?.type === 'lift' || n?.type === 'stairs'
  const isPublic = (n) => n?.type !== 'room'
  const floorIndex = (f) => ['1F', '2F', '3F', '4F'].indexOf(f)
  const familyOf = (n) => {
    if (!n || !isVertical(n)) return ''
    const name = String(n.name || '').toUpperCase()
    if (/(A1.*A2|A2.*A1)/.test(name)) return 'A1A2'
    if (/(A3.*A4|A4.*A3)/.test(name)) return 'A3A4'
    if (/扶梯/.test(name)) return 'ESCALATOR'
    if (/货梯/.test(name)) return 'FREIGHT'
    return `${n.type}:${name.replace(/[^\w\u4e00-\u9fa5]/g, '')}`
  }

  const pickCandidates = (ids = [], anchorId = '') => {
    const anchor = nodesMap?.[anchorId]
    const list = ids
      .map((id) => nodesMap?.[id])
      .filter(Boolean)
      .sort((a, b) => {
        const sa = (isPublic(a) ? 0 : 1) + (isVertical(a) ? 0 : 1)
        const sb = (isPublic(b) ? 0 : 1) + (isVertical(b) ? 0 : 1)
        if (sa !== sb) return sa - sb
        const da = anchor ? distBetween(a, anchor) : 0
        const db = anchor ? distBetween(b, anchor) : 0
        return da - db
      })
    return list.slice(0, 120)
  }

  let guard = 0
  while (guard < 3) {
    guard += 1
    const comps = buildConnectedComponents(nodesMap, nextEdges)
    const compIndex = {}
    comps.forEach((arr, idx) => arr.forEach((id) => { compIndex[id] = idx }))
    const sIdx = compIndex[startId]
    const eIdx = compIndex[endId]
    if (sIdx == null || eIdx == null || sIdx === eIdx) break

    const fromCandidates = pickCandidates(comps[sIdx], startId)
    const toCandidates = pickCandidates(comps[eIdx], endId)
    let best = null

    for (const a of fromCandidates) {
      for (const b of toCandidates) {
        const sameFloor = a.floor === b.floor
        const bothVertical = isVertical(a) && isVertical(b)
        const bothPublic = isPublic(a) && isPublic(b)
        const d = distBetween(a, b)
        const fiA = floorIndex(a.floor)
        const fiB = floorIndex(b.floor)
        const floorGap = Math.abs((fiA < 0 ? 0 : fiA) - (fiB < 0 ? 0 : fiB))

        let priority = 9
        let kind = 'walk'
        let w = Math.max(5, Math.round(d))
        if (sameFloor && bothPublic) {
          priority = 0
          kind = 'walk'
        } else if (sameFloor) {
          priority = 1
          kind = 'walk'
          w += 300
        } else if (bothVertical && floorGap <= 1 && familyOf(a) === familyOf(b)) {
          priority = 2
          kind = a.type === 'stairs' || b.type === 'stairs' ? 'stairs' : 'elevator'
          w = kind === 'stairs' ? 80 : 50
        } else {
          continue
        }
        const score = priority * 100000 + w
        if (!best || score < best.score) best = { aId: a.id, bId: b.id, w, kind, score }
      }
    }
    if (!best) break
    addBi(best.aId, best.bId, best.w, best.kind)
  }
  return nextEdges
}

export default {
  name: 'NavigationPreview',
  data() {
    const { nodes, edges } = buildGraphFromJson(nodesData, edgesData)
    const withBackbone = ensureAdjacentFloorVerticalBackbone(nodes, edges)
    return {
      nodes,
      edges: ensureGlobalReachability(nodes, withBackbone),
      currentFloor: '1F',
      showAllNodes: true,
      showNodeMarkers: true,
      startMode: 'free', // free | node
      startId: '',
      endId: '',
      freeStartPoint: null, // { floor, x, y }
      routePathIds: [],
      runtimeNodesMap: null,
      error: '',
      routePolicyHint: '',
      floorSwitchNotices: [],
      floorSwitchBanner: '',
      _floorSwitchBannerTimer: null,
      isAnimating: false,
      animationProgress: 0,
      animationSegmentIndex: 0,
      animationCurrentFloor: '',
      animationVisitedIds: [],
      _animationTimer: null,
      _movingMarker: null,
      _activeSegmentLine: null,
      _onWindowResize: null,

      _map: null,
      _imgLayer: null,
      _nodeLayer: null,
      _routeLayer: null,
      imageSizeByFloor: {},
      floorViewInitialized: {},

      floorplanByFloor: {
        '1F': new URL('../assets/floorplans/floors/1F.jpg', import.meta.url).href,
        '2F': new URL('../assets/floorplans/floors/2F.jpg', import.meta.url).href,
        '3F': new URL('../assets/floorplans/floors/3F.jpg', import.meta.url).href,
        '4F': new URL('../assets/floorplans/floors/4F.jpg', import.meta.url).href
      }
    }
  },
  computed: {
    nodeOptions() {
      return Object.values(this.nodes).filter((n) => ['1F', '2F', '3F', '4F'].includes(n.floor))
    },
    floorNodes() {
      return this.nodeOptions.filter((n) => n.floor === this.currentFloor)
    },
    canPlan() {
      const hasStart = this.startMode === 'node' ? Boolean(this.startId) : Boolean(this.freeStartPoint)
      return hasStart && Boolean(this.endId)
    },
    nodesForRouting() {
      if (this.startMode !== 'free' || !this.freeStartPoint) return this.nodes
      return {
        ...this.nodes,
        [VIRTUAL_START_ID]: {
          id: VIRTUAL_START_ID,
          name: '起点',
          floor: this.freeStartPoint.floor,
          x: this.freeStartPoint.x,
          y: this.freeStartPoint.y,
          type: 'hub'
        }
      }
    },
    effectiveNodesForRouting() {
      return this.runtimeNodesMap || this.nodesForRouting
    }
  },
  watch: {
    showAllNodes() { this.renderNodes() },
    showNodeMarkers() { this.renderNodes() },
    startMode(next) {
      // 切换起点模式时，清理另一种模式的值，避免“看似有值但实际无效”
      this.error = ''
      if (next === 'free') {
        this.startId = ''
      } else {
        this.freeStartPoint = null
      }
      this.stopRouteAnimation(true)
      this.routePathIds = []
      this.runtimeNodesMap = null
      this.floorSwitchNotices = []
      this.renderRoute()
      this.renderNodes()
    },
    async currentFloor() {
      const needFit = !this.floorViewInitialized?.[this.currentFloor]
      await this.setBaseLayer(needFit)
      this.renderNodes()
      this.renderRoute()
    }
  },
  mounted() {
    this.initMap()
    this._onWindowResize = () => {
      if (!this._map) return
      this._map.invalidateSize(false)
      this.renderRoute()
      this.renderNodes()
    }
    window.addEventListener('resize', this._onWindowResize)
  },
  beforeUnmount() {
    this.stopRouteAnimation(true)
    this.clearFloorSwitchBanner()
    if (this._onWindowResize) {
      window.removeEventListener('resize', this._onWindowResize)
      this._onWindowResize = null
    }
    if (this._map) this._map.remove()
    this._map = null
  },
  methods: {
    isVerticalVisitPolicySatisfied(pathIds, nodesMap) {
      const ids = Array.isArray(pathIds) ? pathIds : []
      if (!ids.length) return true
      const perFloorVerticalIds = {}
      ids.forEach((id) => {
        const n = nodesMap?.[id]
        if (!n?.floor) return
        const isVertical = n.type === 'lift' || n.type === 'stairs'
        if (!isVertical) return
        if (!perFloorVerticalIds[n.floor]) perFloorVerticalIds[n.floor] = new Set()
        perFloorVerticalIds[n.floor].add(id)
      })
      return Object.values(perFloorVerticalIds).every((set) => set.size <= 1)
    },
    ensurePreferElevatorEdges(edgesMap, nodesMap, startId, endId) {
      const start = nodesMap?.[startId]
      const end = nodesMap?.[endId]
      if (!start?.floor || !end?.floor || start.floor === end.floor) return edgesMap

      const normLiftFamily = (n) => {
        if (n?.type !== 'lift') return ''
        const name = String(n?.name || '').toUpperCase()
        if (/(A1.*A2|A2.*A1)/.test(name)) return 'A1A2'
        if (/(A3.*A4|A4.*A3)/.test(name)) return 'A3A4'
        if (/扶梯/.test(name)) return 'ESCALATOR'
        if (/货梯/.test(name)) return 'FREIGHT'
        return name.replace(/[^\w\u4e00-\u9fa5]/g, '')
      }
      const dist = (a, b) => {
        const dx = (a?.x ?? 0) - (b?.x ?? 0)
        const dy = (a?.y ?? 0) - (b?.y ?? 0)
        return Math.sqrt(dx * dx + dy * dy)
      }

      const startLifts = Object.values(nodesMap || {}).filter((n) => n?.type === 'lift' && n.floor === start.floor)
      const endLifts = Object.values(nodesMap || {}).filter((n) => n?.type === 'lift' && n.floor === end.floor)
      if (!startLifts.length || !endLifts.length) return edgesMap

      // 选“同一组电梯”中综合最近的一组（起点到该组 + 终点到该组）
      let best = null
      const byFamilyEnd = {}
      endLifts.forEach((n) => {
        const fam = normLiftFamily(n)
        if (!fam) return
        if (!byFamilyEnd[fam]) byFamilyEnd[fam] = []
        byFamilyEnd[fam].push(n)
      })
      startLifts.forEach((sLift) => {
        const fam = normLiftFamily(sLift)
        const endPool = fam ? (byFamilyEnd[fam] || []) : []
        const endPick = (endPool.length ? endPool : endLifts)
          .map((eLift) => ({ eLift, d: dist(eLift, end) }))
          .sort((a, b) => a.d - b.d)[0]?.eLift
        if (!endPick) return
        const score = dist(sLift, start) + dist(endPick, end)
        if (!best || score < best.score) best = { sLift, eLift: endPick, fam, score }
      })
      if (!best?.sLift || !best?.eLift) return edgesMap

      const nextEdges = cloneEdgesMap(edgesMap || {})
      const addBi = (a, b, w, kind = 'walk') => {
        if (!nextEdges[a]) nextEdges[a] = []
        if (!nextEdges[b]) nextEdges[b] = []
        if (!nextEdges[a].some((e) => e?.to === b)) nextEdges[a].push({ to: b, w, kind, inferred: true, preferElevator: true })
        if (!nextEdges[b].some((e) => e?.to === a)) nextEdges[b].push({ to: a, w, kind, inferred: true, preferElevator: true })
      }

      // 强制“先到电梯”：给 startId ↔ startLift 一条低成本 walk 边（若原图缺边也能走到电梯区域）
      // 同理 endId ↔ endLift，保证下电梯后能快速到终点。
      const wStart = Math.max(5, Math.round(dist(start, best.sLift) * 0.8))
      const wEnd = Math.max(5, Math.round(dist(end, best.eLift) * 0.8))
      addBi(startId, best.sLift.id, wStart, 'walk')
      addBi(endId, best.eLift.id, wEnd, 'walk')

      // 若已选择“客梯家族”（A1A2/A3A4），则硬约束：路径不再经过其他类型电梯（扶梯/货梯等）
      const selectedLiftFamily = normLiftFamily(best.sLift)
      const lockPassengerLiftFamily = selectedLiftFamily === 'A1A2' || selectedLiftFamily === 'A3A4'

      // 进一步抑制跨层时“走楼梯捷径”：把所有 stairs 边再加一层惩罚
      Object.keys(nextEdges).forEach((from) => {
        nextEdges[from] = (nextEdges[from] || []).map((e) => {
          if ((e?.kind || 'walk') !== 'stairs') return e
          const base = typeof e?.w === 'number' ? e.w : 1
          return { ...e, w: base + 300000 }
        }).map((e) => {
          const base = typeof e?.w === 'number' ? e.w : 1
          if (!lockPassengerLiftFamily) return e
          const fromNode = nodesMap?.[from]
          const toNode = nodesMap?.[e?.to]
          const fromLiftFamily = normLiftFamily(fromNode)
          const toLiftFamily = normLiftFamily(toNode)
          const touchLift = fromNode?.type === 'lift' || toNode?.type === 'lift'
          const touchNonSelectedLift = touchLift && (
            (fromNode?.type === 'lift' && fromLiftFamily && fromLiftFamily !== selectedLiftFamily) ||
            (toNode?.type === 'lift' && toLiftFamily && toLiftFamily !== selectedLiftFamily)
          )
          if (!touchNonSelectedLift) return e
          // 近乎禁用：客梯锁定后，不再允许借道扶梯/货梯等其他电梯类型
          return { ...e, w: base + 2000000 }
        })
      })

      return nextEdges
    },
    toggleNodeMarkers() {
      this.showNodeMarkers = !this.showNodeMarkers
    },
    clearFloorSwitchBanner() {
      if (this._floorSwitchBannerTimer) {
        clearTimeout(this._floorSwitchBannerTimer)
        this._floorSwitchBannerTimer = null
      }
      this.floorSwitchBanner = ''
    },
    showFloorSwitchBanner(text) {
      const t = String(text || '').trim()
      if (!t) return
      this.floorSwitchBanner = t
      if (this._floorSwitchBannerTimer) clearTimeout(this._floorSwitchBannerTimer)
      this._floorSwitchBannerTimer = setTimeout(() => {
        this.floorSwitchBanner = ''
        this._floorSwitchBannerTimer = null
      }, 4500)
    },
    edgeKindBetween(aId, bId) {
      const list = this.edges?.[aId] || []
      const hit = list.find((e) => e && e.to === bId)
      return hit?.kind || ''
    },
    buildFloorSwitchNotices(pathIds) {
      const ids = Array.isArray(pathIds) ? pathIds : []
      const tips = []
      for (let i = 0; i < ids.length - 1; i++) {
        const aId = ids[i]
        const bId = ids[i + 1]
        const a = this.nodes[aId]
        const b = this.nodes[bId]
        if (!a || !b) continue
        if (!a.floor || !b.floor) continue
        if (a.floor === b.floor) continue
        const kind = this.edgeKindBetween(aId, bId) || this.edgeKindBetween(bId, aId)
        const via = kind === 'elevator' ? '电梯' : (kind === 'stairs' ? '楼梯' : '连通点')
        tips.push(`即将从 ${a.floor} 切换到 ${b.floor}（请通过${via}：${a.name} → ${b.name}）`)
      }
      return tips
    },
    async initMap() {
      this._map = L.map(this.$refs.mapEl, {
        crs: L.CRS.Simple,
        zoomControl: true,
        minZoom: -3,
        maxZoom: 6
      })
      this._nodeLayer = L.layerGroup().addTo(this._map)
      this._routeLayer = L.layerGroup().addTo(this._map)

      await this.setBaseLayer(true)

      this.renderNodes()
      this.renderRoute()

      // 起点“地图任意点”模式：点击底图设置起点
      this._map.on('click', (e) => {
        if (this.startMode !== 'free') return
        const x = e?.latlng?.lng
        const y = e?.latlng?.lat
        if (!Number.isFinite(x) || !Number.isFinite(y)) return
        this.freeStartPoint = { floor: this.currentFloor, x, y }
        this.stopRouteAnimation(true)
        this.routePathIds = []
        this.runtimeNodesMap = null
        this.floorSwitchNotices = []
        this.error = ''
        this.renderRoute()
        this.renderNodes()
      })
      // 任何缩放/拖拽后都重绘一次，确保路线与节点始终贴合底图
      this._map.on('zoomend moveend resize', () => {
        this.renderRoute()
        this.renderNodes()
      })
    },
    resolveFloorUrl(floor = this.currentFloor) {
      return this.floorplanByFloor[floor] || this.floorplanByFloor['1F']
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
    async ensureImageSize(floor = this.currentFloor) {
      if (this.imageSizeByFloor[floor]?.w && this.imageSizeByFloor[floor]?.h) {
        return this.imageSizeByFloor[floor]
      }
      const url = this.resolveFloorUrl(floor)
      const size = await this.loadImageSize(url)
      this.imageSizeByFloor = {
        ...this.imageSizeByFloor,
        [floor]: size
      }
      return size
    },
    async setBaseLayer(needFitBounds = false) {
      if (!this._map) return
      const url = this.resolveFloorUrl(this.currentFloor)
      const size = await this.ensureImageSize(this.currentFloor)
      const bounds = [[0, 0], [size.h, size.w]]
      // 复用同一个 ImageOverlay，避免多次 remove/add 后出现底图缩放不同步
      if (!this._imgLayer) {
        this._imgLayer = L.imageOverlay(url, bounds).addTo(this._map)
      } else {
        this._imgLayer.setUrl(url)
        this._imgLayer.setBounds(bounds)
      }
      // 同步当前楼层的视图约束，防止切层后出现“点位在缩放、底图不跟随”的错位感
      this._map.setMaxBounds(bounds)
      if (needFitBounds) {
        // 严格按底图边界贴合，优先保证节点与底图坐标 1:1 对齐
        this._map.invalidateSize(false)
        this._map.fitBounds(bounds, { padding: [0, 0], animate: false })
        this.floorViewInitialized = {
          ...(this.floorViewInitialized || {}),
          [this.currentFloor]: true
        }
      } else {
        // 非首次加载不重置缩放，保留用户当前视角，避免导航后缩放体验异常
        this._map.invalidateSize(false)
        this._map.panInsideBounds(bounds, { animate: false })
      }
    },
    setFloor(floor) {
      this.currentFloor = floor
    },
    renderNodes() {
      if (!this._nodeLayer) return
      this._nodeLayer.clearLayers()

      const source = this.showAllNodes ? this.floorNodes : this.floorNodes.filter((n) => n.id === this.startId || n.id === this.endId)
      // showNodeMarkers=true：节点圆点 + tooltip（原行为）
      // showNodeMarkers=false：只显示文字标签（避免节点遮挡科室名称）
      if (this.showNodeMarkers) {
        source.forEach((n) => {
          const visited = this.animationVisitedIds.includes(n.id)
          const fill = n.type === 'lift' ? '#0ea5e9' : (n.type === 'stairs' ? '#f97316' : '#6366f1')
          L.circleMarker([n.y, n.x], {
            radius: visited ? 7 : 5.5,
            color: '#0f172a',
            weight: visited ? 2.6 : 1.8,
            fillColor: fill,
            fillOpacity: visited ? 1 : 0.95
          }).addTo(this._nodeLayer).bindTooltip(n.name, { direction: 'top' })
        })
        return
      }

      const escapeHtml = (s) =>
        String(s || '')
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#39;')

      source.forEach((n) => {
        const visited = this.animationVisitedIds.includes(n.id)
        const kindClass = n.type === 'lift' ? 'label-lift' : (n.type === 'stairs' ? 'label-stairs' : 'label-room')
        const visitedClass = visited ? 'label-visited' : ''
        const html = `<div class="node-label ${kindClass} ${visitedClass}">${escapeHtml(n.name)}</div>`
        const icon = L.divIcon({
          className: 'node-label-icon',
          html,
          iconSize: null
        })
        L.marker([n.y, n.x], { icon, interactive: false }).addTo(this._nodeLayer)
      })
    },
    renderRoute() {
      if (!this._routeLayer) return
      this._routeLayer.clearLayers()

      const allNodes = this.effectiveNodesForRouting
      const s = this.startMode === 'node' ? allNodes[this.startId] : allNodes[VIRTUAL_START_ID]
      const e = allNodes[this.endId]
      if (s && s.floor === this.currentFloor) {
        L.circleMarker([s.y, s.x], { radius: 8, color: '#2563eb', weight: 3, fillOpacity: 0 }).addTo(this._routeLayer).bindTooltip('起点', { permanent: true })
      }
      if (e && e.floor === this.currentFloor) {
        L.circleMarker([e.y, e.x], { radius: 8, color: '#f97316', weight: 3, fillOpacity: 0 }).addTo(this._routeLayer).bindTooltip('终点', { permanent: true })
      }

      if (!this.routePathIds.length) return
      // 逐段绘制路线，避免跨楼层过滤后出现“丢线/断线”的视觉问题
      for (let i = 0; i < this.routePathIds.length - 1; i++) {
        const a = allNodes[this.routePathIds[i]]
        const b = allNodes[this.routePathIds[i + 1]]
        if (!a || !b) continue
        if (a.floor !== this.currentFloor || b.floor !== this.currentFloor) continue
        L.polyline([[a.y, a.x], [b.y, b.x]], {
          color: '#1d4ed8',
          weight: 7,
          opacity: 0.92,
          lineJoin: 'round',
          noClip: true
        }).addTo(this._routeLayer)
      }

      // 给路径节点补可视锚点，便于确认路线是完整连续的
      this.routePathIds.forEach((id) => {
        const n = allNodes[id]
        if (!n || n.floor !== this.currentFloor) return
        L.circleMarker([n.y, n.x], {
          radius: 4,
          color: '#1e3a8a',
          weight: 1.5,
          fillColor: '#dbeafe',
          fillOpacity: 0.95
        }).addTo(this._routeLayer)
      })

      if (this.isAnimating) {
        this.renderAnimationFrame()
      }
    },
    buildEdgesWithVirtualStart(nodesMap, edgesMap) {
      if (this.startMode !== 'free' || !this.freeStartPoint) return edgesMap
      const start = nodesMap[VIRTUAL_START_ID]
      if (!start) return edgesMap

      const sameFloor = Object.values(nodesMap).filter((n) => n && n.id && n.floor === start.floor && n.id !== VIRTUAL_START_ID)
      if (!sameFloor.length) return edgesMap

      const dist = (a, b) => {
        const dx = (a.x ?? 0) - (b.x ?? 0)
        const dy = (a.y ?? 0) - (b.y ?? 0)
        return Math.sqrt(dx * dx + dy * dy)
      }

      const candidates = sameFloor
        .map((n) => ({ id: n.id, d: dist(start, n) }))
        .sort((a, b) => a.d - b.d)

      const entranceCandidates = sameFloor
        .filter((n) => n.type === 'entrance')
        .map((n) => ({ id: n.id, d: dist(start, n) }))
        .sort((a, b) => a.d - b.d)

      const nearestEntrance = entranceCandidates[0] || null
      const nearestInner = candidates.find((c) => nodesMap[c.id]?.type !== 'entrance') || null
      const floorSize = this.imageSizeByFloor?.[start.floor] || null
      const isNearMapEdge = Boolean(
        floorSize?.w && floorSize?.h && (
          start.x <= floorSize.w * 0.08 ||
          start.x >= floorSize.w * 0.92 ||
          start.y <= floorSize.h * 0.08 ||
          start.y >= floorSize.h * 0.86
        )
      )
      const nearestOutpatientEntrance = entranceCandidates.find((c) => {
        const n = nodesMap[c.id]
        return /门诊入口/.test(String(n?.name || ''))
      }) || null

      // 室外起点启发式：位于 1F 且更靠近入口点
      const isOutdoorStart = Boolean(
        start.floor === '1F' &&
        nearestEntrance &&
        nearestEntrance.d <= 620 &&
        (!nearestInner || nearestEntrance.d <= nearestInner.d * 1.18)
      )

      const nearestAny = candidates[0] || null
      const nearestAnyNode = nearestAny ? nodesMap[nearestAny.id] : null
      const nearestAnyIsEntrance = nearestAnyNode?.type === 'entrance'

      // 仅在“明显像室外起点”时才强制先走入口：
      // 1) 最近点本身就是入口；2) 最近入口距离足够近，且显著优于最近室内点
      const forceEntranceFirst = Boolean(
        start.floor === '1F' &&
        nearestEntrance &&
        (
          isNearMapEdge ||
          nearestAnyIsEntrance ||
          (
            nearestEntrance.d <= 360 &&
            (!nearestInner || nearestEntrance.d <= nearestInner.d * 0.72)
          )
        )
      )

      // 室外起点：强制先连最近入口；室内起点：连最近若干节点
      const preferredEntrance = nearestOutpatientEntrance || nearestEntrance
      const picked = (forceEntranceFirst || isOutdoorStart) && preferredEntrance ? [preferredEntrance] : candidates.slice(0, 4)
      if (!picked.length) return edgesMap

      const nextEdges = { ...(edgesMap || {}) }
      const add = (from, to, w) => {
        if (!nextEdges[from]) nextEdges[from] = []
        // 去重
        if ((nextEdges[from] || []).some((e) => e && e.to === to)) return
        nextEdges[from] = [...nextEdges[from], { to, w, kind: 'walk' }]
      }

      picked.forEach((p) => {
        const w = Math.max(5, Math.round(p.d))
        add(VIRTUAL_START_ID, p.id, w)
        add(p.id, VIRTUAL_START_ID, w)
      })

      this.routePolicyHint = (forceEntranceFirst || isOutdoorStart) && preferredEntrance
        ? `起点规则：先进入最近入口（${nodesMap[preferredEntrance.id]?.name || '入口'}）再进行院内导航。`
        : ''

      return nextEdges
    },
    applyRoutePreference(edgesMap, nodesMap) {
      const nextEdges = {}
      const isRoomLike = (n) => n?.type === 'room'
      const isCorridorLike = (n) => {
        const t = n?.type
        if (['hub', 'turn', 'entrance'].includes(t)) return true
        const name = String(n?.name || '')
        return /(走廊|导诊台|大厅|入口|收费|通道|连廊|候诊|前台)/.test(name)
      }
      const normalizedLiftFamily = (n) => {
        if (n?.type !== 'lift') return ''
        const name = String(n?.name || '').toUpperCase()
        if (/(A1.*A2|A2.*A1)/.test(name)) return 'A1A2'
        if (/(A3.*A4|A4.*A3)/.test(name)) return 'A3A4'
        if (/扶梯/.test(name)) return 'ESCALATOR'
        if (/货梯/.test(name)) return 'FREIGHT'
        return name.replace(/[^\w\u4e00-\u9fa5]/g, '')
      }
      Object.keys(edgesMap || {}).forEach((from) => {
        nextEdges[from] = (edgesMap[from] || []).map((e) => {
          const base = typeof e?.w === 'number' ? e.w : 1
          const kind = e?.kind || 'walk'
          const fromNode = nodesMap?.[from]
          const toNode = nodesMap?.[e?.to]
          const touchStairsNode = fromNode?.type === 'stairs' || toNode?.type === 'stairs'
          const touchLiftNode = fromNode?.type === 'lift' || toNode?.type === 'lift'
          const touchRoomLike = isRoomLike(fromNode) || isRoomLike(toNode)
          const bothRoomLike = isRoomLike(fromNode) && isRoomLike(toNode)
          const corridorLikePass = isCorridorLike(fromNode) || isCorridorLike(toNode)
          const liftFamilyFrom = normalizedLiftFamily(fromNode)
          const liftFamilyTo = normalizedLiftFamily(toNode)
          const isLiftToLiftWalk = kind === 'walk' && fromNode?.type === 'lift' && toNode?.type === 'lift'
          let w = base
          if (kind === 'stairs') {
            // 强化惩罚跨层楼梯，除非没有其他路，否则不会选
            w = base + 9000
          } else if (kind === 'elevator') {
            // 电梯/扶梯不做过强全局偏置，主要由“就近 + 同层步行成本”决定
            w = Math.max(5, base - 25)
          }

          // 经过楼梯节点抬高代价，避免为图上捷径而穿楼梯区绕行
          if (touchStairsNode) {
            w += 1200
          }

          // 经过电梯/扶梯节点的小幅奖励，鼓励“就近换层”
          if (touchLiftNode) {
            w = Math.max(5, w - 120)
          }

          // 禁止“扶梯 -> 客梯”串联绕行：不同电梯家族之间步行换乘增加高惩罚
          if (isLiftToLiftWalk && liftFamilyFrom && liftFamilyTo && liftFamilyFrom !== liftFamilyTo) {
            w += 1500
          }

          // 尽量少穿科室：将 room 相关边抬高，促使路线优先走公共节点与走廊
          if (touchRoomLike && kind === 'walk') {
            w += 2200
          }
          if (bothRoomLike && kind === 'walk') {
            w += 6000
          }

          // 走廊/导诊台/入口等公共通道节点给小幅奖励
          if (corridorLikePass && kind === 'walk') {
            w = Math.max(8, w - 120)
          }
          return {
            ...e,
            w
          }
        })
      })
      return nextEdges
    },
    applySameFloorNoVerticalPolicy(edgesMap, nodesMap, startId, endId) {
      const start = nodesMap?.[startId]
      const end = nodesMap?.[endId]
      if (!start?.floor || !end?.floor || start.floor !== end.floor) return edgesMap
      const protectedIds = new Set([startId, endId])
      const nextEdges = {}
      Object.keys(edgesMap || {}).forEach((from) => {
        nextEdges[from] = (edgesMap[from] || []).map((e) => {
          const to = e?.to
          const kind = e?.kind || 'walk'
          const fromNode = nodesMap?.[from]
          const toNode = nodesMap?.[to]
          const fromVertical = fromNode?.type === 'lift' || fromNode?.type === 'stairs'
          const toVertical = toNode?.type === 'lift' || toNode?.type === 'stairs'
          const touchVertical = fromVertical || toVertical
          let w = typeof e?.w === 'number' ? e.w : 1

          // 同层路径原则：非必要不经过电梯/楼梯（从惩罚升级为“近乎禁用”）
          if (touchVertical && !protectedIds.has(from) && !protectedIds.has(to)) {
            w += 120000
          }
          // 同层时跨层边几乎不可选（除非无路）
          if ((kind === 'elevator' || kind === 'stairs') && !protectedIds.has(from) && !protectedIds.has(to)) {
            w += 180000
          }
          return { ...e, w }
        })
      })
      return nextEdges
    },
    applyCrossFloorDirectPolicy(edgesMap, nodesMap, startId, endId) {
      const start = nodesMap?.[startId]
      const end = nodesMap?.[endId]
      if (!start?.floor || !end?.floor || start.floor === end.floor) return edgesMap
      const floorOrder = ['1F', '2F', '3F', '4F']
      const startIdx = floorOrder.indexOf(start.floor)
      const endIdx = floorOrder.indexOf(end.floor)
      const lo = Math.min(startIdx, endIdx)
      const hi = Math.max(startIdx, endIdx)
      const protectedIds = new Set([startId, endId])
      const nextEdges = {}
      const liftFamily = (n) => {
        if (n?.type !== 'lift') return ''
        const name = String(n?.name || '').toUpperCase()
        if (/(A1.*A2|A2.*A1)/.test(name)) return 'A1A2'
        if (/(A3.*A4|A4.*A3)/.test(name)) return 'A3A4'
        if (/扶梯/.test(name)) return 'ESCALATOR'
        if (/货梯/.test(name)) return 'FREIGHT'
        return name.replace(/[^\w\u4e00-\u9fa5]/g, '')
      }

      Object.keys(edgesMap || {}).forEach((from) => {
        nextEdges[from] = (edgesMap[from] || []).map((e) => {
          const to = e?.to
          const kind = e?.kind || 'walk'
          const fromNode = nodesMap?.[from]
          const toNode = nodesMap?.[to]
          let w = typeof e?.w === 'number' ? e.w : 1
          const fromFloorIdx = floorOrder.indexOf(fromNode?.floor)
          const toFloorIdx = floorOrder.indexOf(toNode?.floor)
          const sameFloor = fromNode?.floor && toNode?.floor && fromNode.floor === toNode.floor
          const onIntermediateFloor = sameFloor && fromFloorIdx > lo && fromFloorIdx < hi
          const fromVertical = fromNode?.type === 'lift' || fromNode?.type === 'stairs'
          const toVertical = toNode?.type === 'lift' || toNode?.type === 'stairs'

          // 跨层路线尽量直达：强烈惩罚中间楼层的同层步行
          if (kind === 'walk' && onIntermediateFloor && !protectedIds.has(from) && !protectedIds.has(to)) {
            w += 9000
          }
          // 非必要不走楼梯（跨层场景）
          if (kind === 'stairs' && !protectedIds.has(from) && !protectedIds.has(to)) {
            w += 1800
          }
          // 避免不同电梯组在中间楼层换乘
          if (kind === 'walk' && fromVertical && toVertical && !protectedIds.has(from) && !protectedIds.has(to)) {
            const f1 = liftFamily(fromNode)
            const f2 = liftFamily(toNode)
            if (f1 && f2 && f1 !== f2) w += 5000
          }
          // 鼓励电梯垂直边
          if (kind === 'elevator') {
            w = Math.max(5, w - 30)
          }
          // 避免“反方向楼层折返”
          if ((kind === 'elevator' || kind === 'stairs') && fromFloorIdx >= 0 && toFloorIdx >= 0) {
            const direction = Math.sign(endIdx - startIdx)
            const stepDir = Math.sign(toFloorIdx - fromFloorIdx)
            if (direction !== 0 && stepDir !== 0 && stepDir !== direction) {
              w += 6000
            }
          }
          return { ...e, w }
        })
      })
      return nextEdges
    },
    applyDestinationFloorFastArrivalPolicy(edgesMap, nodesMap, startId, endId) {
      const start = nodesMap?.[startId]
      const end = nodesMap?.[endId]
      if (!start?.floor || !end?.floor || start.floor === end.floor) return edgesMap
      const targetFloor = end.floor
      const protectedIds = new Set([startId, endId])
      const isRoomLike = (n) => n?.type === 'room'
      const isCorridorLike = (n) => {
        const t = n?.type
        if (['hub', 'turn', 'entrance'].includes(t)) return true
        const name = String(n?.name || '')
        return /(走廊|导诊台|大厅|入口|收费|通道|连廊|候诊|前台)/.test(name)
      }
      const distToEnd = (n) => {
        const dx = (n?.x ?? 0) - (end?.x ?? 0)
        const dy = (n?.y ?? 0) - (end?.y ?? 0)
        return Math.sqrt(dx * dx + dy * dy)
      }

      const nextEdges = {}
      Object.keys(edgesMap || {}).forEach((from) => {
        nextEdges[from] = (edgesMap[from] || []).map((e) => {
          const to = e?.to
          const kind = e?.kind || 'walk'
          const fromNode = nodesMap?.[from]
          const toNode = nodesMap?.[to]
          let w = typeof e?.w === 'number' ? e.w : 1
          const bothOnTargetFloor = fromNode?.floor === targetFloor && toNode?.floor === targetFloor

          if (!bothOnTargetFloor || kind !== 'walk') {
            return { ...e, w }
          }

          const fromIsEnd = from === endId
          const toIsEnd = to === endId
          const touchRoomLike = isRoomLike(fromNode) || isRoomLike(toNode)
          const touchCorridor = isCorridorLike(fromNode) || isCorridorLike(toNode)
          const fromDist = distToEnd(fromNode)
          const toDist = distToEnd(toNode)
          const movingAway = toDist > fromDist + 18

          // 目标楼层上避免“穿科室绕路”：除终点外，room 边强惩罚
          if (touchRoomLike && !fromIsEnd && !toIsEnd) {
            w += 9000
          }

          // 奖励走廊/大厅/导诊台等公共通道
          if (touchCorridor && !fromIsEnd && !toIsEnd) {
            w = Math.max(5, w - 260)
          }

          // 到达目标楼层后优先“逼近终点”，抑制先远离再折返
          if (movingAway && !protectedIds.has(from) && !protectedIds.has(to)) {
            w += 2600
          } else if (!movingAway && !fromIsEnd && !toIsEnd) {
            w = Math.max(5, w - 120)
          }

          return { ...e, w }
        })
      })
      return nextEdges
    },
    applySingleVerticalPerFloorPolicy(edgesMap, nodesMap, startId, endId) {
      const start = nodesMap?.[startId]
      const end = nodesMap?.[endId]
      if (!start?.floor || !end?.floor) return edgesMap
      const floorOrder = ['1F', '2F', '3F', '4F']
      const startIdx = floorOrder.indexOf(start.floor)
      const endIdx = floorOrder.indexOf(end.floor)
      if (startIdx < 0 || endIdx < 0) return edgesMap

      const isVertical = (n) => n?.type === 'lift' || n?.type === 'stairs'
      const familyOf = (n) => {
        if (!n || !isVertical(n)) return ''
        const name = String(n.name || '').toUpperCase()
        if (/(A1.*A2|A2.*A1)/.test(name)) return 'A1A2'
        if (/(A3.*A4|A4.*A3)/.test(name)) return 'A3A4'
        if (/扶梯/.test(name)) return 'ESCALATOR'
        if (/货梯/.test(name)) return 'FREIGHT'
        return `${n.type}:${name.replace(/[^\w\u4e00-\u9fa5]/g, '')}`
      }
      const dist = (a, b) => {
        const dx = (a?.x ?? 0) - (b?.x ?? 0)
        const dy = (a?.y ?? 0) - (b?.y ?? 0)
        return Math.sqrt(dx * dx + dy * dy)
      }
      const verticalByFloor = {}
      Object.values(nodesMap || {}).forEach((n) => {
        if (!n?.id || !isVertical(n)) return
        if (!verticalByFloor[n.floor]) verticalByFloor[n.floor] = []
        verticalByFloor[n.floor].push(n)
      })
      const nearest = (list, anchor, filterFn = null) => {
        const pool = (list || []).filter((n) => !filterFn || filterFn(n))
        if (!pool.length) return null
        return pool
          .map((n) => ({ n, d: distBetween(n, anchor) }))
          .sort((a, b) => a.d - b.d)[0]?.n || null
      }

      const preferredByFloor = {}
      const lo = Math.min(startIdx, endIdx)
      const hi = Math.max(startIdx, endIdx)
      const startFloorVerticals = verticalByFloor[start.floor] || []

      // 跨层场景：优先选择“电梯家族”，并挑选离起点与终点都更近的那一组，减少绕路。
      const isCrossFloor = start.floor !== end.floor
      let preferredSeed = null
      let preferredType = 'lift'
      let preferredFamily = ''

      const startLifts = startFloorVerticals.filter((n) => n?.type === 'lift')
      const endFloorVerticals = verticalByFloor[end.floor] || []
      const endLifts = endFloorVerticals.filter((n) => n?.type === 'lift')

      if (isCrossFloor && startLifts.length && endLifts.length) {
        const best = { score: Infinity, seed: null, family: '' }
        const byFamilyEnd = {}
        endLifts.forEach((n) => {
          const fam = familyOf(n)
          if (!fam) return
          if (!byFamilyEnd[fam]) byFamilyEnd[fam] = []
          byFamilyEnd[fam].push(n)
        })
        startLifts.forEach((sLift) => {
          const fam = familyOf(sLift)
          if (!fam || !byFamilyEnd[fam]?.length) return
          const endBest = byFamilyEnd[fam]
            .map((eLift) => ({ eLift, d: dist(eLift, end) }))
            .sort((a, b) => a.d - b.d)[0]?.eLift
          if (!endBest) return
          const score = dist(sLift, start) + dist(endBest, end)
          if (score < best.score) {
            best.score = score
            best.seed = sLift
            best.family = fam
          }
        })
        if (best.seed) {
          preferredSeed = best.seed
          preferredType = 'lift'
          preferredFamily = best.family
        }
      }

      if (!preferredSeed) {
        const startLift = nearest(startFloorVerticals, start, (n) => n.type === 'lift')
        const startStairs = nearest(startFloorVerticals, start, (n) => n.type === 'stairs')
        preferredSeed = (isCrossFloor ? (startLift || null) : (startLift || startStairs || null))
        preferredType = (isCrossFloor ? 'lift' : (preferredSeed?.type || 'lift'))
        preferredFamily = familyOf(preferredSeed)
      }

      for (let idx = lo; idx <= hi; idx++) {
        const floor = floorOrder[idx]
        const list = verticalByFloor[floor] || []
        if (!list.length) continue
        let chosen = null
        if (idx === startIdx) {
          // 起点本身若在垂直交通节点上，强制该层只保留该节点，避免同层串联多个电梯/楼梯
          if (isVertical(start)) {
            chosen = list.find((n) => n.id === start.id) || null
          }
          if (!chosen) {
            chosen = nearest(list, start, (n) => n.type === preferredType && (!preferredFamily || familyOf(n) === preferredFamily))
          }
        } else if (idx === endIdx) {
          // 终点本身若在垂直交通节点上，强制该层只保留该节点
          if (isVertical(end)) {
            chosen = list.find((n) => n.id === end.id) || null
          }
          if (!chosen) {
            chosen = nearest(list, end, (n) => n.type === preferredType && (!preferredFamily || familyOf(n) === preferredFamily))
          }
        } else {
          const anchor = preferredByFloor[floorOrder[idx - 1]] || preferredSeed || start
          chosen = nearest(list, anchor, (n) => n.type === preferredType && (!preferredFamily || familyOf(n) === preferredFamily))
        }
        // 强约束：跨层链路必须同一家族，不做跨家族兜底选择
        if (chosen) preferredByFloor[floor] = chosen.id
      }

      const selectedVerticalByFloor = {}
      Object.entries(preferredByFloor).forEach(([floor, id]) => {
        if (id) selectedVerticalByFloor[floor] = id
      })
      const selectedVerticalIds = new Set(Object.values(selectedVerticalByFloor))
      const protectedIds = new Set([startId, endId, ...selectedVerticalIds])
      const shouldDropVerticalNode = (nodeId) => {
        if (!nodeId) return false
        if (nodeId === startId || nodeId === endId) return false
        const n = nodesMap?.[nodeId]
        if (!n || !isVertical(n)) return false
        if (preferredFamily && familyOf(n) !== preferredFamily) return true
        const selected = selectedVerticalByFloor[n.floor]
        if (!selected) return false
        return nodeId !== selected
      }

      const nextEdges = {}
      Object.keys(edgesMap || {}).forEach((from) => {
        const fromDropped = shouldDropVerticalNode(from)
        if (fromDropped) {
          nextEdges[from] = []
          return
        }
        nextEdges[from] = (edgesMap[from] || []).filter((e) => {
          const to = e?.to
          return !shouldDropVerticalNode(to)
        }).map((e) => {
          const to = e?.to
          const kind = e?.kind || 'walk'
          const fromNode = nodesMap?.[from]
          const toNode = nodesMap?.[to]
          const fromVertical = isVertical(fromNode)
          const toVertical = isVertical(toNode)
          let w = typeof e?.w === 'number' ? e.w : 1
          const selectedFromFloor = selectedVerticalByFloor[fromNode?.floor || '']
          const selectedToFloor = selectedVerticalByFloor[toNode?.floor || '']
          const fromIsUnselectedVertical = fromVertical && selectedFromFloor && from !== selectedFromFloor
          const toIsUnselectedVertical = toVertical && selectedToFloor && to !== selectedToFloor

          // 硬约束：每层仅允许一个垂直交通节点参与路径（无论货梯/客梯/扶梯/楼梯）
          if (fromIsUnselectedVertical || toIsUnselectedVertical) {
            w += 1500000
          }

          if ((fromVertical || toVertical) && !protectedIds.has(from) && !protectedIds.has(to)) {
            w += 420000
          }

          // 同层出现两个不同垂直交通节点时，直接近乎禁用
          if (kind === 'walk' && fromVertical && toVertical) {
            if (from !== to && (!selectedVerticalIds.has(from) || !selectedVerticalIds.has(to))) {
              w += 1800000
            }
          }
          if ((kind === 'elevator' || kind === 'stairs') && fromVertical && toVertical) {
            const ff = familyOf(fromNode)
            const tf = familyOf(toNode)
            if (ff && tf && ff !== tf) w += 2000000
          }
          if (kind === 'stairs' && preferredType === 'lift' && !protectedIds.has(from) && !protectedIds.has(to)) {
            w += 220000
          }
          if (kind === 'elevator' && preferredType === 'stairs' && !protectedIds.has(from) && !protectedIds.has(to)) {
            w += 220000
          }
          return { ...e, w }
        })
      })
      return nextEdges
    },
    async planRoute() {
      try {
        this.error = ''
        this.routePolicyHint = ''
        // 规划前确保四层尺寸都可用，避免虚拟走廊仅在当前楼层生成
        await Promise.all(['1F', '2F', '3F', '4F'].map((f) => this.ensureImageSize(f)))
        const nodesMap = this.nodesForRouting
        const realStartId = this.startMode === 'node' ? this.startId : VIRTUAL_START_ID
        if (!realStartId || !this.endId) return
        if (realStartId === this.endId) {
          this.error = '起点和终点不能相同'
          this.routePathIds = []
          this.runtimeNodesMap = null
          this.floorSwitchNotices = []
          this.renderRoute()
          return
        }

        const withVirtualStart = this.buildEdgesWithVirtualStart(nodesMap, this.edges)
        const withSupplementalEdges = inferSupplementalWalkEdges(nodesMap, withVirtualStart)
        const virtualGraph = buildVirtualCorridorGraph(nodesMap, withSupplementalEdges, this.imageSizeByFloor)
        const preferredEdges = this.applyRoutePreference(virtualGraph.edges, virtualGraph.nodes)
        const sameFloorPolicyEdges = this.applySameFloorNoVerticalPolicy(preferredEdges, virtualGraph.nodes, realStartId, this.endId)
        const crossFloorPolicyEdges = this.applyCrossFloorDirectPolicy(sameFloorPolicyEdges, virtualGraph.nodes, realStartId, this.endId)
        const destinationFastArrivalEdges = this.applyDestinationFloorFastArrivalPolicy(crossFloorPolicyEdges, virtualGraph.nodes, realStartId, this.endId)
        const strictEdges = this.applySingleVerticalPerFloorPolicy(destinationFastArrivalEdges, virtualGraph.nodes, realStartId, this.endId)
        const preferElevatorEdges = this.ensurePreferElevatorEdges(strictEdges, virtualGraph.nodes, realStartId, this.endId)

        // 分级求解：先严格策略，再逐步放宽，最后再做连通兜底，避免“策略过严导致误报无路”
        const edgeCandidates = [
          preferElevatorEdges, // 严格：同层/跨层/电梯偏好
          crossFloorPolicyEdges, // 中等：保留跨层方向性约束
          preferredEdges, // 宽松：仅保留基础偏好
          virtualGraph.edges // 最宽松：原图 + 虚拟走廊
        ]
        let res = { path: [], cost: Infinity }
        let usedEdges = edgeCandidates[0]
        let finalEdgesForRoute = usedEdges
        for (const candidate of edgeCandidates) {
          const r = aStar(virtualGraph.nodes, candidate, realStartId, this.endId)
          if (r.path.length && r.cost !== Infinity && this.isVerticalVisitPolicySatisfied(r.path, virtualGraph.nodes)) {
            res = r
            usedEdges = candidate
            finalEdgesForRoute = candidate
            break
          }
        }

        // 仍失败时，启用“成分补桥”再求解，确保跨楼层尽可能可达
        if (!res.path.length || res.cost === Infinity) {
          const rescued = ensurePairReachability(virtualGraph.nodes, usedEdges, realStartId, this.endId)
          const rescuedResult = aStar(virtualGraph.nodes, rescued, realStartId, this.endId)
          if (rescuedResult.path.length && rescuedResult.cost !== Infinity && this.isVerticalVisitPolicySatisfied(rescuedResult.path, virtualGraph.nodes)) {
            res = rescuedResult
          } else {
            res = { path: [], cost: Infinity }
          }
          finalEdgesForRoute = rescued
        }

        // 终点强校验：最终路径必须落在用户选择的终点，避免误停在中间公共点
        if (res.path.length && res.path[res.path.length - 1] !== this.endId) {
          const tailStartId = res.path[res.path.length - 1]
          const tail = aStar(virtualGraph.nodes, finalEdgesForRoute, tailStartId, this.endId)
          if (tail.path.length && tail.cost !== Infinity) {
            res = {
              path: [...res.path, ...tail.path.slice(1)],
              cost: Number.isFinite(res.cost) && Number.isFinite(tail.cost) ? (res.cost + tail.cost) : res.cost
            }
          }
        }
        if (!res.path.length || res.cost === Infinity) {
          this.error = '未找到可达路径，请检查节点采集是否严重缺失'
          this.routePathIds = []
          this.runtimeNodesMap = null
          this.floorSwitchNotices = []
          this.renderRoute()
          return
        }
        if (res.path[res.path.length - 1] !== this.endId) {
          const endName = virtualGraph.nodes?.[this.endId]?.name || this.endId
          this.error = `路径未能到达所选终点（${endName}），请重试或更换终点`
          this.routePathIds = []
          this.runtimeNodesMap = null
          this.floorSwitchNotices = []
          this.renderRoute()
          return
        }
        this.runtimeNodesMap = virtualGraph.nodes
        this.routePathIds = res.path
        this.floorSwitchNotices = this.buildFloorSwitchNotices(this.routePathIds)
        const s = virtualGraph.nodes[realStartId]
        if (s && ['1F', '2F', '3F', '4F'].includes(s.floor)) this.currentFloor = s.floor
        this.stopRouteAnimation(true)
        this.renderRoute()
      } catch (e) {
        const msg = e?.message || String(e || '路径规划失败')
        this.error = `路径规划失败：${msg}`
        this.routePathIds = []
        this.runtimeNodesMap = null
        this.floorSwitchNotices = []
        this.stopRouteAnimation(true)
        this.renderRoute()
      }
    },
    async playRouteAnimation() {
      if (this.routePathIds.length < 2) return
      this.stopRouteAnimation(true)
      this.isAnimating = true
      this.animationSegmentIndex = 0
      this.animationProgress = 0
      this.animationVisitedIds = [this.routePathIds[0]]
      const start = this.effectiveNodesForRouting[this.routePathIds[0]]
      this.animationCurrentFloor = start?.floor || this.currentFloor
      if (this.animationCurrentFloor && this.animationCurrentFloor !== this.currentFloor) {
        this.currentFloor = this.animationCurrentFloor
        await this.$nextTick()
      }
      this.renderNodes()
      this.renderRoute()
      this.scheduleAnimationTick()
    },
    stopRouteAnimation(silent = false) {
      if (this._animationTimer) {
        clearTimeout(this._animationTimer)
        this._animationTimer = null
      }
      this.isAnimating = false
      this.animationProgress = 0
      this.animationSegmentIndex = 0
      this.animationCurrentFloor = ''
      this.animationVisitedIds = []
      this.clearFloorSwitchBanner()
      if (!silent) {
        this.renderNodes()
        this.renderRoute()
      } else if (this._routeLayer) {
        this.renderRoute()
      }
    },
    scheduleAnimationTick() {
      if (!this.isAnimating) return
      this._animationTimer = setTimeout(async () => {
        await this.stepAnimation()
      }, ANIMATION_TICK_MS)
    },
    async stepAnimation() {
      if (!this.isAnimating) return
      if (this.animationSegmentIndex >= this.routePathIds.length - 1) {
        this.stopRouteAnimation()
        return
      }
      const fromId = this.routePathIds[this.animationSegmentIndex]
      const toId = this.routePathIds[this.animationSegmentIndex + 1]
      const allNodes = this.effectiveNodesForRouting
      const from = allNodes[fromId]
      const to = allNodes[toId]
      if (!from || !to) {
        this.stopRouteAnimation()
        return
      }

      // 跨楼层时，先平滑切换楼层后继续动画
      if (from.floor !== to.floor) {
        const kind = this.edgeKindBetween(fromId, toId) || this.edgeKindBetween(toId, fromId)
        const via = kind === 'elevator' ? '电梯' : (kind === 'stairs' ? '楼梯' : '连通点')
        this.showFloorSwitchBanner(`楼层切换：请通过${via}从 ${from.floor} 前往 ${to.floor}`)
        this.animationVisitedIds = Array.from(new Set([...this.animationVisitedIds, fromId]))
        this.renderNodes()
        this.renderRoute()
        this.animationSegmentIndex += 1
        this.animationProgress = 0
        this.animationCurrentFloor = to.floor
        if (to.floor !== this.currentFloor) {
          this.currentFloor = to.floor
          await new Promise((resolve) => setTimeout(resolve, 280))
        }
        this.animationVisitedIds = Array.from(new Set([...this.animationVisitedIds, toId]))
        this.renderNodes()
        this.renderRoute()
        this.scheduleAnimationTick()
        return
      }

      this.animationCurrentFloor = from.floor
      this.animationProgress = Math.min(1, this.animationProgress + ANIMATION_PROGRESS_STEP)
      if (this.animationProgress >= 1) {
        this.animationVisitedIds = Array.from(new Set([...this.animationVisitedIds, toId]))
        this.animationSegmentIndex += 1
        this.animationProgress = 0
      }
      this.renderNodes()
      this.renderRoute()
      this.scheduleAnimationTick()
    },
    renderAnimationFrame() {
      if (!this.isAnimating || this.animationSegmentIndex >= this.routePathIds.length - 1) return
      const allNodes = this.effectiveNodesForRouting
      const from = allNodes[this.routePathIds[this.animationSegmentIndex]]
      const to = allNodes[this.routePathIds[this.animationSegmentIndex + 1]]
      if (!from || !to || from.floor !== this.currentFloor || to.floor !== this.currentFloor) return

      const lat = from.y + (to.y - from.y) * this.animationProgress
      const lng = from.x + (to.x - from.x) * this.animationProgress
      L.circleMarker([lat, lng], {
        radius: 9,
        color: '#1d4ed8',
        weight: 3,
        fillColor: '#bfdbfe',
        fillOpacity: 0.95
      }).addTo(this._routeLayer).bindTooltip('导航中', { direction: 'top' })

      L.polyline([[from.y, from.x], [lat, lng]], {
        color: '#1d4ed8',
        weight: 8,
        opacity: 0.95
      }).addTo(this._routeLayer)
    },
    clearRoute() {
      this.stopRouteAnimation(true)
      this.startId = ''
      this.freeStartPoint = null
      this.endId = ''
      this.routePathIds = []
      this.runtimeNodesMap = null
      this.error = ''
      this.routePolicyHint = ''
      this.floorSwitchNotices = []
      this.clearFloorSwitchBanner()
      this.renderRoute()
      this.renderNodes()
    }
  }
}
</script>

<style scoped>
.preview-page { max-width: 1350px; margin: 0 auto; }
.page-title { color: #fff; text-align: center; margin-bottom: 1rem; }
.layout { display: grid; grid-template-columns: 2fr 1fr; gap: 1rem; }
.map-pane,.card { background:#fff; border-radius:14px; box-shadow:0 8px 24px rgba(0,0,0,.15); }
.map-pane { padding: .9rem; }
.toolbar { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:.6rem; margin-bottom:.6rem; }
.toolbar-actions { display:inline-flex; align-items:center; gap:.6rem; flex-wrap:wrap; }
.segmented { display:inline-flex; border:1px solid #d1d5db; border-radius:10px; overflow:hidden; }
.seg-btn { border:none; background:#fff; padding:.45rem .75rem; cursor:pointer; font-weight:800; }
.seg-btn.active { background:#eef2ff; color:#3730a3; }
.floor-tabs { display:inline-flex; gap:.4rem; margin-left:.5rem; }
.tab { border:1px solid #d1d5db; background:#f8fafc; border-radius:10px; padding:.35rem .6rem; cursor:pointer; font-weight:800; }
.tab.active { background:#111827; color:#fff; border-color:#111827; }
.check { display:inline-flex; align-items:center; gap:.35rem; font-weight:800; font-size:.85rem; }
.floor-switch-banner {
  margin: 0 0 .6rem;
  border-radius: 12px;
  padding: .55rem .75rem;
  font-weight: 900;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  color: #9a3412;
}
.leaflet-map { width:100%; height:680px; border:1px solid #e5e7eb; border-radius:12px; overflow:hidden; }
:deep(.leaflet-container img),
:deep(.leaflet-image-layer) {
  max-width: none !important;
  max-height: none !important;
}
.panel { display:flex; flex-direction:column; gap:.8rem; }
.card { padding:.9rem; }
.title { font-weight:900; color:#4338ca; margin-bottom:.6rem; }
.row { display:flex; flex-direction:column; gap:.35rem; margin:.45rem 0; }
select { height:36px; border:1px solid #d1d5db; border-radius:10px; padding:0 .5rem; }
.actions { display:flex; gap:.5rem; margin-top:.6rem; }
.primary,.ghost { border-radius:10px; padding:.5rem .8rem; font-weight:800; cursor:pointer; }
.primary { border:none; color:#fff; background:linear-gradient(135deg,#667eea,#764ba2); }
.primary:disabled,.ghost:disabled { opacity:.5; cursor:not-allowed; }
.ghost { border:1px solid #d1d5db; background:#fff; }
.error { color:#b91c1c; font-weight:800; margin-top:.5rem; }
.hint { color:#6b7280; font-size:.9rem; }
.hint.strong { color:#0f172a; font-weight: 900; }
.start-mode { display:flex; gap:.75rem; align-items:center; flex-wrap:wrap; }
.radio { display:inline-flex; align-items:center; gap:.35rem; font-weight:900; color:#111827; }
.free-start-hint { margin-top: .35rem; }
.floor-switch-notices { margin-top: .75rem; border-top: 1px dashed #e5e7eb; padding-top: .75rem; }
.notice-title { font-weight: 900; color: #9a3412; margin-bottom: .4rem; }
.notice-item { font-size: .9rem; color: #111827; background:#fff7ed; border:1px solid #fed7aa; border-radius:10px; padding:.35rem .5rem; margin:.3rem 0; }
.steps { margin-top:.6rem; max-height:420px; overflow:auto; display:flex; flex-direction:column; gap:.3rem; }
.step { font-size:.9rem; color:#111827; background:#f8fafc; border:1px solid #e5e7eb; border-radius:8px; padding:.35rem .45rem; }

/* 仅显示文字标签（不显示节点圆点时） */
.node-label-icon { background: transparent; border: none; }
.node-label {
  font-weight: 900;
  font-size: 12px;
  line-height: 1;
  white-space: nowrap;
  transform: translate(-50%, -50%);
  padding: 6px 8px;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  /* 房间/节点标签用更浅底色，类似高德/百度底图的“浅底+深字” */
  background: rgba(248, 250, 252, 0.94);
  color: #0f172a;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.12);
}
.node-label.label-room { border-color: rgba(99, 102, 241, 0.35); }
.node-label.label-lift { border-color: rgba(14, 165, 233, 0.35); }
.node-label.label-stairs { border-color: rgba(249, 115, 22, 0.35); }
.node-label.label-visited { background: rgba(240, 253, 244, 0.95); border-color: rgba(34, 197, 94, 0.35); }
@media (max-width: 980px) { .layout { grid-template-columns: 1fr; } .leaflet-map { height:520px; } }
</style>

