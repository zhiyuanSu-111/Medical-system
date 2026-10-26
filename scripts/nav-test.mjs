import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const root = path.resolve(__dirname, '..')

const nodesPath = path.join(root, 'src', 'data', 'indoor', 'nodes.json')
const edgesPath = path.join(root, 'src', 'data', 'indoor', 'edges.json')
const outDir = path.join(root, 'test-output', 'nav')

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf-8'))
}

function buildGraphFromJson(nodesArr, edgesArr) {
  const nodes = {}
  for (const n of nodesArr || []) {
    if (!n || !n.id) continue
    nodes[n.id] = n
  }
  const edges = {}
  const add = (a, b, w, kind) => {
    if (!edges[a]) edges[a] = []
    edges[a].push({ to: b, w, kind })
  }
  for (const e of edgesArr || []) {
    if (!e || !e.from || !e.to) continue
    const w = typeof e.weight === 'number' ? e.weight : 1
    const kind = e.kind || 'walk'
    add(e.from, e.to, w, kind)
    add(e.to, e.from, w, kind)
  }
  return { nodes, edges }
}

function edgeKindBetween(edges, aId, bId) {
  const list = edges?.[aId] || []
  const hit = list.find((e) => e && e.to === bId)
  return hit?.kind || ''
}

function floorSwitchCount(nodes, pathIds) {
  let c = 0
  for (let i = 0; i < pathIds.length - 1; i++) {
    const a = nodes[pathIds[i]]
    const b = nodes[pathIds[i + 1]]
    if (a?.floor && b?.floor && a.floor !== b.floor) c += 1
  }
  return c
}

function kindStats(edges, pathIds) {
  const stats = { walk: 0, stairs: 0, elevator: 0, other: 0 }
  for (let i = 0; i < pathIds.length - 1; i++) {
    const a = pathIds[i]
    const b = pathIds[i + 1]
    const kind = edgeKindBetween(edges, a, b) || edgeKindBetween(edges, b, a) || 'walk'
    if (kind === 'walk') stats.walk += 1
    else if (kind === 'stairs') stats.stairs += 1
    else if (kind === 'elevator') stats.elevator += 1
    else stats.other += 1
  }
  return stats
}

function pickByNameContains(nodesArr, needle) {
  const n = String(needle || '').trim()
  if (!n) return null
  return (nodesArr || []).find((x) => String(x?.name || '').includes(n)) || null
}

function safeCsvCell(v) {
  const s = String(v ?? '')
  if (/[,"\n]/.test(s)) return `"${s.replaceAll('"', '""')}"`
  return s
}

function writeCsv(p, rows) {
  const header = Object.keys(rows[0] || {})
  const lines = [header.join(',')]
  for (const r of rows) {
    lines.push(header.map((k) => safeCsvCell(r[k])).join(','))
  }
  fs.writeFileSync(p, lines.join('\n'), 'utf-8')
}

function randInt(max) {
  return Math.floor(Math.random() * max)
}

async function main() {
  const nodesArr = readJson(nodesPath)
  const edgesArr = readJson(edgesPath)
  const { nodes, edges } = buildGraphFromJson(nodesArr, edgesArr)

  const aStarMod = await import(pathToFileURL(path.join(root, 'src', 'utils', 'indoor-nav', 'astar.js')).href)
  const aStar = aStarMod?.aStar
  if (typeof aStar !== 'function') {
    throw new Error('无法加载 aStar()，请检查 src/utils/indoor-nav/astar.js 导出')
  }

  const allowedFloors = new Set(['1F', '2F', '3F', '4F'])
  const candidates = nodesArr.filter((n) => n && allowedFloors.has(n.floor))
  const ids = candidates.map((n) => n.id)

  // 典型用例（用于截图/论文描述）
  const caseSameFloorA = pickByNameContains(candidates, '1F门诊入口')
  const caseSameFloorB = pickByNameContains(candidates, '1F门诊收费')
  const caseElevatorA = pickByNameContains(candidates, '1F客梯（A1、A2）')
  const caseElevatorB = pickByNameContains(candidates, '4F_lift') // 兜底：可能没这个 name
  const caseStairsA = pickByNameContains(candidates, '1F门诊收费旁楼梯')
  const caseStairsB = pickByNameContains(candidates, '2F口腔科科旁楼梯2')

  const fixedCases = []
  if (caseSameFloorA?.id && caseSameFloorB?.id) {
    fixedCases.push({ label: '同层步行', startId: caseSameFloorA.id, endId: caseSameFloorB.id })
  }
  if (caseElevatorA?.id) {
    // 找一个 2F/3F/4F 的客梯 A1A2 作为终点（跨层电梯）
    const elevTargets = candidates.filter((n) => /客梯（A1、A2）/.test(String(n.name || '')) && n.floor !== nodes[caseElevatorA.id]?.floor)
    if (elevTargets.length) {
      fixedCases.push({ label: '跨层电梯', startId: caseElevatorA.id, endId: elevTargets[0].id })
    }
  }
  if (caseStairsA?.id && caseStairsB?.id) {
    fixedCases.push({ label: '跨层楼梯', startId: caseStairsA.id, endId: caseStairsB.id })
  }

  const randomCases = []
  const RANDOM_N = 30
  for (let i = 0; i < RANDOM_N; i++) {
    const a = ids[randInt(ids.length)]
    let b = ids[randInt(ids.length)]
    if (a === b) b = ids[(randInt(ids.length - 1) + 1) % ids.length]
    randomCases.push({ label: `随机${i + 1}`, startId: a, endId: b })
  }

  const cases = [...fixedCases, ...randomCases]
  const rows = []
  let ok = 0

  for (const tc of cases) {
    const start = nodes[tc.startId]
    const end = nodes[tc.endId]
    const res = aStar(nodes, edges, tc.startId, tc.endId)
    const success = Array.isArray(res?.path) && res.path.length >= 2 && Number.isFinite(res.cost) && res.cost !== Infinity
    if (success) ok += 1
    const switches = success ? floorSwitchCount(nodes, res.path) : 0
    const ks = success ? kindStats(edges, res.path) : { walk: 0, stairs: 0, elevator: 0, other: 0 }

    rows.push({
      case: tc.label,
      startName: start?.name || tc.startId,
      startFloor: start?.floor || '',
      endName: end?.name || tc.endId,
      endFloor: end?.floor || '',
      success: success ? 'PASS' : 'FAIL',
      cost: success ? res.cost : '',
      pathNodes: success ? res.path.length : 0,
      floorSwitches: switches,
      edges_walk: ks.walk,
      edges_elevator: ks.elevator,
      edges_stairs: ks.stairs,
      edges_other: ks.other
    })
  }

  const summary = {
    generatedAt: new Date().toISOString(),
    nodeCount: Object.keys(nodes).length,
    edgeCountDirected: Object.values(edges).reduce((acc, arr) => acc + (arr?.length || 0), 0),
    testCount: rows.length,
    passCount: ok,
    passRate: rows.length ? ok / rows.length : 0,
    fixedCases
  }

  fs.mkdirSync(outDir, { recursive: true })
  fs.writeFileSync(path.join(outDir, 'nav_test_summary.json'), JSON.stringify(summary, null, 2), 'utf-8')
  fs.writeFileSync(path.join(outDir, 'nav_test_results.json'), JSON.stringify(rows, null, 2), 'utf-8')
  writeCsv(path.join(outDir, 'nav_test_results.csv'), rows)

  console.log('=== indoor-nav test done ===')
  console.log(summary)
  console.log('outputs:', outDir)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})

