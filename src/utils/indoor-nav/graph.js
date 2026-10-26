// Indoor navigation static graph (nodes + weighted edges).
// Coordinate system: image pixel space.
// - Same-floor walking edges weight: Euclidean distance
// - Elevator vertical connector weight: fixed (simulate waiting time)
// - Stairs vertical connector weight: fixed (simulate fatigue)

export const ELEVATOR_W = 50
export const STAIRS_W = 80

export function buildDemoGraph() {
  // Demo graph derived from your existing logical points, but converted to pixels.
  // You should replace/extend this with real coordinates collected from the floor images.
  //
  // Conventions:
  // - floor uses strings like '2F', '3F' (matches UI)
  // - x,y in [0..1000] (image pixels); current legacy coords were [0..100], so *10
  const px = (n) => Math.round((n ?? 0) * 10)

  const nodesArr = [
    // 2F key places
    { id: 'ELEVATOR_2F', name: '电梯(2F)', floor: '2F', x: px(54), y: px(37), type: 'lift' },
    { id: 'STAIRS_2F', name: '楼梯(2F)', floor: '2F', x: px(48), y: px(36), type: 'stairs' },
    { id: 'CASHIER_2F', name: '挂号收费处(2F)', floor: '2F', x: px(58), y: px(40), type: 'hub' },
    { id: 'ICU_2F', name: 'ICU(2F)', floor: '2F', x: px(70), y: px(46), type: 'hub' },
    { id: 'LAB_2F', name: '检验科(2F)', floor: '2F', x: px(62), y: px(42), type: 'hub' },
    { id: 'FUNC_2F', name: '功能检查区(2F)', floor: '2F', x: px(75), y: px(32), type: 'zone' },

    // 3F key places
    { id: 'ELEVATOR_3F', name: '电梯(3F)', floor: '3F', x: px(54), y: px(37), type: 'lift' },
    { id: 'STAIRS_3F', name: '楼梯(3F)', floor: '3F', x: px(48), y: px(36), type: 'stairs' },
    { id: 'CASHIER_3F', name: '挂号收费处(3F)', floor: '3F', x: px(58), y: px(36), type: 'hub' },
    { id: 'PATH_3F', name: '病理科(3F)', floor: '3F', x: px(62), y: px(38), type: 'hub' },
    { id: 'ENDOSCOPY_3F', name: '内镜中心(3F)', floor: '3F', x: px(76), y: px(25), type: 'dept' }
  ]

  const nodes = {}
  nodesArr.forEach((n) => { nodes[n.id] = n })

  const edges = {}
  const add = (a, b, w) => {
    if (!edges[a]) edges[a] = []
    edges[a].push({ to: b, w })
  }
  const linkWalk = (a, b) => {
    const na = nodes[a]
    const nb = nodes[b]
    if (!na || !nb) return
    const dx = na.x - nb.x
    const dy = na.y - nb.y
    const w = Math.max(5, Math.round(Math.sqrt(dx * dx + dy * dy)))
    add(a, b, w); add(b, a, w)
  }
  const linkFixed = (a, b, w) => { add(a, b, w); add(b, a, w) }

  // Same-floor walking (demo)
  linkWalk('ELEVATOR_2F', 'CASHIER_2F')
  linkWalk('CASHIER_2F', 'LAB_2F')
  linkWalk('LAB_2F', 'ICU_2F')
  linkWalk('ELEVATOR_2F', 'FUNC_2F')
  linkWalk('STAIRS_2F', 'ELEVATOR_2F')

  linkWalk('ELEVATOR_3F', 'CASHIER_3F')
  linkWalk('CASHIER_3F', 'PATH_3F')
  linkWalk('ELEVATOR_3F', 'ENDOSCOPY_3F')
  linkWalk('STAIRS_3F', 'ELEVATOR_3F')

  // Vertical connectors
  linkFixed('ELEVATOR_2F', 'ELEVATOR_3F', ELEVATOR_W)
  linkFixed('STAIRS_2F', 'STAIRS_3F', STAIRS_W)

  return { nodes, edges }
}

