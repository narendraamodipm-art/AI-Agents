// Draws the knowledge graph exactly as Mistral described it: nodes, edges, stats and issues

const TYPE_STYLE = {
  file: { icon: '📊', color: '#336791' },
  class: { icon: '📦', color: '#ec4899' },
  function: { icon: '⚙️', color: '#10b981' },
  method: { icon: '🔧', color: '#06b6d4' },
  import: { icon: '📥', color: '#64748b' },
  constant: { icon: '🔒', color: '#a16207' },
  variable: { icon: '🔤', color: '#a16207' },
  table: { icon: '🗄️', color: '#ec4899' },
  view: { icon: '👁️', color: '#8b5cf6' },
  cte: { icon: '🧩', color: '#8b5cf6' },
  select: { icon: '🔍', color: '#06b6d4' },
  insert: { icon: '➕', color: '#10b981' },
  update: { icon: '✏️', color: '#f59e0b' },
  delete: { icon: '🗑️', color: '#ef4444' },
  create: { icon: '🏗️', color: '#6366f1' },
  page: { icon: '📄', color: '#e34c26' },
  section: { icon: '🧱', color: '#f97316' },
  form: { icon: '📝', color: '#10b981' },
  element: { icon: '🔹', color: '#0ea5e9' },
  script: { icon: '📜', color: '#eab308' },
  style: { icon: '🎨', color: '#a855f7' },
}
const FALLBACK_COLORS = ['#0ea5e9', '#14b8a6', '#f43f5e', '#84cc16', '#d946ef', '#f97316']
const STAT_COLORS = ['text-pink-400', 'text-cyan-400', 'text-orange-400', 'text-emerald-400', 'text-purple-400', 'text-sky-400']

const styleFor = (type) => {
  if (TYPE_STYLE[type]) return TYPE_STYLE[type]
  const hash = [...type].reduce((sum, ch) => sum + ch.charCodeAt(0), 0)
  return { icon: '🔸', color: FALLBACK_COLORS[hash % FALLBACK_COLORS.length] }
}

const edgeColor = (label) => {
  const text = label.toLowerCase()
  if (/call/.test(text)) return '#a78bfa'
  if (/read|select|use|feed/.test(text)) return '#22d3ee'
  if (/insert|update|delete|write/.test(text)) return '#34d399'
  if (/inherit|extend|implement/.test(text)) return '#f472b6'
  return '#94a3b8'
}

// Layered layout: the file node on top, then each level of children below it (breadth-first)
function layoutLevels(graph) {
  const children = new Map(graph.nodes.map((n) => [n.id, []]))
  const hasParent = new Set()
  graph.edges.forEach((e) => {
    children.get(e.source).push(e.target)
    hasParent.add(e.target)
  })

  const roots = graph.nodes.filter((n) => n.type === 'file')
  const start = roots.length ? roots : graph.nodes.filter((n) => !hasParent.has(n.id))
  const level = new Map()
  const queue = (start.length ? start : graph.nodes.slice(0, 1)).map((n) => n.id)
  queue.forEach((id) => level.set(id, 0))

  while (queue.length) {
    const id = queue.shift()
    for (const child of children.get(id)) {
      if (!level.has(child)) {
        level.set(child, level.get(id) + 1)
        queue.push(child)
      }
    }
  }

  // Anything the edges don't reach goes on its own row at the bottom
  const deepest = Math.max(0, ...level.values())
  graph.nodes.forEach((n) => {
    if (!level.has(n.id)) level.set(n.id, deepest + 1)
  })
  return level
}

export function createGraphFromLlm(graph) {
  const level = layoutLevels(graph)
  const rows = new Map()
  graph.nodes.forEach((n) => {
    const row = level.get(n.id)
    rows.set(row, [...(rows.get(row) || []), n])
  })

  const nodes = []
  rows.forEach((rowNodes, row) => {
    rowNodes.forEach((n, i) => {
      const { icon, color } = styleFor(n.type)
      const isFile = n.type === 'file'
      nodes.push({
        id: n.id,
        data: { label: `${icon} ${n.label}${n.detail ? `\n${n.detail}` : ''}` },
        position: { x: (i - (rowNodes.length - 1) / 2) * 220, y: row * 170 },
        style: {
          background: color,
          color: '#ffffff',
          border: isFile ? '3px solid #fbbf24' : '2px solid rgba(255,255,255,0.25)',
          borderRadius: '8px',
          padding: isFile ? '14px' : '8px',
          fontWeight: '600',
          fontSize: isFile ? '14px' : '11px',
          minWidth: '150px',
          maxWidth: '200px',
          textAlign: 'center',
          whiteSpace: 'pre-line',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
        },
      })
    })
  })

  const edges = graph.edges.map((e) => ({
    id: `${e.source}->${e.target}`,
    source: e.source,
    target: e.target,
    label: e.label,
    animated: /call|read|feed/i.test(e.label),
    style: { stroke: edgeColor(e.label), strokeWidth: 2 },
    labelStyle: { fill: '#e2e8f0', fontSize: 10 },
    labelBgStyle: { fill: '#0f172a' },
    markerEnd: { type: 'arrowclosed' },
  }))

  return { nodes, edges }
}

export function generateLlmStats(graph) {
  return {
    items: graph.stats.map((s, i) => ({
      icon: '',
      label: s.label,
      value: s.value,
      color: STAT_COLORS[i % STAT_COLORS.length],
    })),
    issues: graph.issues,
    summary: graph.summary,
  }
}
