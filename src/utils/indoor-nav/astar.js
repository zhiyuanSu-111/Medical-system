// A* pathfinding on a weighted graph (adjacency list).
// nodes: { [id]: { id, floor, x, y, type, name } }
// edges: { [id]: Array<{ to: string, w: number }> }

function heuristic(a, b) {
  // Euclidean distance in pixel space (works for image coordinate system).
  const dx = (a.x ?? 0) - (b.x ?? 0)
  const dy = (a.y ?? 0) - (b.y ?? 0)
  return Math.sqrt(dx * dx + dy * dy)
}

export function aStar(nodes, edges, startId, goalId) {
  if (!startId || !goalId) return { path: [], cost: Infinity }
  if (startId === goalId) return { path: [startId], cost: 0 }
  if (!nodes[startId] || !nodes[goalId]) return { path: [], cost: Infinity }

  const open = new Set([startId])
  const cameFrom = {}

  const g = {}
  const f = {}
  Object.keys(nodes).forEach((id) => {
    g[id] = Infinity
    f[id] = Infinity
  })

  g[startId] = 0
  f[startId] = heuristic(nodes[startId], nodes[goalId])

  const lowestFInOpen = () => {
    let best = null
    let bestVal = Infinity
    open.forEach((id) => {
      const v = f[id]
      if (v < bestVal) {
        bestVal = v
        best = id
      }
    })
    return best
  }

  while (open.size) {
    const current = lowestFInOpen()
    if (!current) break
    if (current === goalId) {
      const path = [current]
      let cur = current
      while (cameFrom[cur]) {
        cur = cameFrom[cur]
        path.unshift(cur)
      }
      return { path, cost: g[current] }
    }

    open.delete(current)
    const nbrs = edges[current] || []
    for (const e of nbrs) {
      const to = e?.to
      if (!to || !nodes[to]) continue
      const wRaw = e?.w
      const w = (typeof wRaw === 'number' && Number.isFinite(wRaw) && wRaw > 0) ? wRaw : 1
      const currentG = typeof g[current] === 'number' ? g[current] : Infinity
      const toG = typeof g[to] === 'number' ? g[to] : Infinity
      const tentative = currentG + w
      if (tentative < toG) {
        cameFrom[to] = current
        g[to] = tentative
        f[to] = tentative + heuristic(nodes[to], nodes[goalId])
        open.add(to)
      }
    }
  }

  return { path: [], cost: Infinity }
}

