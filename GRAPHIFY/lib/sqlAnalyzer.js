// SQL has tables, statements and CTEs rather than classes, functions and loops,
// so SQL gets its own analyzer, graph and stats instead of the generic code structure.

const CONSTRAINT_WORDS = new Set(['PRIMARY', 'FOREIGN', 'CONSTRAINT', 'UNIQUE', 'CHECK', 'INDEX', 'KEY'])
const SQL_KEYWORDS = new Set(['SELECT', 'LATERAL', 'UNNEST', 'VALUES', 'DUAL'])

// Blank out comments and string contents so commas, semicolons and keywords inside them are ignored
function cleanSql(code) {
  return code
    .replace(/--.*$/gm, '')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/'(?:[^']|'')*'/g, "''")
}

// Split on commas that are not inside parentheses
function splitTopLevel(text) {
  const parts = []
  let depth = 0
  let current = ''
  for (const ch of text) {
    if (ch === '(') depth++
    if (ch === ')') depth--
    if (ch === ',' && depth === 0) {
      parts.push(current)
      current = ''
    } else {
      current += ch
    }
  }
  if (current.trim()) parts.push(current)
  return parts.map((p) => p.trim()).filter(Boolean)
}

// Return the text inside the parenthesis that opens at index `start`
function readParens(text, start) {
  let depth = 0
  for (let i = start; i < text.length; i++) {
    if (text[i] === '(') depth++
    if (text[i] === ')') {
      depth--
      if (depth === 0) return text.slice(start + 1, i)
    }
  }
  return text.slice(start + 1)
}

function tablesReadIn(text) {
  return [...text.matchAll(/\b(?:FROM|JOIN)\s+([A-Za-z_][\w.]*)/gi)]
    .map((m) => m[1])
    .filter((name) => !SQL_KEYWORDS.has(name.toUpperCase()))
}

// Pull "name AS (...)" CTE definitions off the front of a WITH statement
function extractCtes(statement) {
  const ctes = []
  if (!/^WITH\b/i.test(statement)) return { ctes, mainQuery: statement }

  let rest = statement.replace(/^WITH\s+(?:RECURSIVE\s+)?/i, '')
  let match
  while ((match = rest.match(/^([A-Za-z_]\w*)\s*(?:\([^)]*\)\s*)?AS\s*\(/i))) {
    const openIndex = match[0].length - 1
    const body = readParens(rest, openIndex)
    ctes.push({ name: match[1], body })
    rest = rest.slice(openIndex + body.length + 2).replace(/^\s*,\s*/, '')
  }
  return { ctes, mainQuery: rest }
}

export function analyzeSql(code) {
  const statements = cleanSql(code)
    .split(';')
    .map((s) => s.trim())
    .filter(Boolean)

  const tables = new Map()
  const queries = []
  const allCtes = []
  let joins = 0
  let aggregates = 0

  const touchTable = (name) => {
    const key = name.toLowerCase()
    if (!tables.has(key)) {
      tables.set(key, { name, columns: [], rowsInserted: 0, createdHere: false })
    }
    return tables.get(key)
  }

  statements.forEach((statement, index) => {
    joins += (statement.match(/\bJOIN\b/gi) || []).length
    aggregates += (statement.match(/\b(?:COUNT|SUM|AVG|MIN|MAX)\s*\(/gi) || []).length

    const createTable = statement.match(/^CREATE\s+(?:TEMP(?:ORARY)?\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][\w.]*)\s*\(/i)
    if (createTable) {
      const table = touchTable(createTable[1])
      table.createdHere = true
      table.columns = splitTopLevel(readParens(statement, createTable[0].length - 1))
        .map((def) => def.split(/\s+/)[0])
        .filter((word) => !CONSTRAINT_WORDS.has(word.toUpperCase()))
      queries.push({ id: `q${index}`, kind: 'CREATE', target: table.name, reads: [] })
      return
    }

    const createView = statement.match(/^CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+([A-Za-z_][\w.]*)\s+AS\s+([\s\S]*)$/i)
    if (createView) {
      queries.push({ id: `q${index}`, kind: 'VIEW', target: createView[1], reads: [...new Set(tablesReadIn(createView[2]))] })
      return
    }

    const insert = statement.match(/^INSERT\s+INTO\s+([A-Za-z_][\w.]*)/i)
    if (insert) {
      const table = touchTable(insert[1])
      const valuesPart = statement.split(/\bVALUES\b/i)[1]
      const rows = valuesPart ? splitTopLevel(valuesPart).length : 0
      table.rowsInserted += rows
      queries.push({ id: `q${index}`, kind: 'INSERT', target: table.name, rows, reads: [...new Set(tablesReadIn(statement))] })
      return
    }

    const update = statement.match(/^UPDATE\s+([A-Za-z_][\w.]*)/i)
    if (update) {
      touchTable(update[1])
      queries.push({ id: `q${index}`, kind: 'UPDATE', target: update[1], reads: [...new Set(tablesReadIn(statement))] })
      return
    }

    const remove = statement.match(/^DELETE\s+FROM\s+([A-Za-z_][\w.]*)/i)
    if (remove) {
      touchTable(remove[1])
      queries.push({ id: `q${index}`, kind: 'DELETE', target: remove[1], reads: [] })
      return
    }

    if (/^(?:WITH|SELECT)\b/i.test(statement)) {
      const { ctes, mainQuery } = extractCtes(statement)
      const cteNames = new Set(ctes.map((c) => c.name.toLowerCase()))
      const queryId = `q${index}`

      ctes.forEach((cte) => {
        allCtes.push({
          id: `${queryId}-cte-${cte.name}`,
          name: cte.name,
          queryId,
          body: cte.body.replace(/\s+/g, ' ').trim(),
          reads: [...new Set(tablesReadIn(cte.body))],
          usedBy: [],
        })
      })

      // A CTE is used if the main query or another CTE reads it
      const statementCtes = allCtes.filter((c) => c.queryId === queryId)
      statementCtes.forEach((cte) => {
        if (tablesReadIn(mainQuery).some((n) => n.toLowerCase() === cte.name.toLowerCase())) cte.usedBy.push(queryId)
        statementCtes.forEach((other) => {
          if (other !== cte && other.reads.some((n) => n.toLowerCase() === cte.name.toLowerCase())) cte.usedBy.push(other.id)
        })
      })

      queries.push({ id: queryId, kind: 'SELECT', reads: [...new Set(tablesReadIn(mainQuery))], cteNames })
    }
  })

  // Every read that isn't a CTE is a table, even if this script doesn't create it
  queries.forEach((q) => q.reads.forEach((name) => {
    if (!q.cteNames?.has(name.toLowerCase())) touchTable(name)
  }))
  allCtes.forEach((cte) => cte.reads.forEach((name) => {
    const isCte = allCtes.some((c) => c.queryId === cte.queryId && c.name.toLowerCase() === name.toLowerCase())
    if (!isCte) touchTable(name)
  }))

  const bodies = new Map()
  allCtes.forEach((cte) => {
    const key = `${cte.queryId}|${cte.body.toLowerCase()}`
    bodies.set(key, [...(bodies.get(key) || []), cte.name])
  })
  const duplicateCtes = [...bodies.values()].filter((names) => names.length > 1)

  return {
    tables: [...tables.values()],
    queries,
    ctes: allCtes,
    joins,
    aggregates,
    duplicateCtes,
    unusedCtes: allCtes.filter((c) => c.usedBy.length === 0).map((c) => c.name),
  }
}

const KIND_STYLE = {
  CREATE: { icon: '🏗️', color: '#6366f1' },
  INSERT: { icon: '➕', color: '#10b981' },
  UPDATE: { icon: '✏️', color: '#f59e0b' },
  DELETE: { icon: '🗑️', color: '#ef4444' },
  SELECT: { icon: '🔍', color: '#06b6d4' },
  VIEW: { icon: '👁️', color: '#8b5cf6' },
}

const nodeStyle = (background, extra = {}) => ({
  background,
  color: '#ffffff',
  border: '2px solid rgba(255,255,255,0.25)',
  borderRadius: '8px',
  padding: '8px',
  fontWeight: '600',
  fontSize: '11px',
  minWidth: '150px',
  textAlign: 'center',
  whiteSpace: 'pre-line',
  boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
  ...extra,
})

const edge = (source, target, label, stroke, animated = false) => ({
  id: `${source}->${target}`,
  source,
  target,
  label,
  animated,
  style: { stroke, strokeWidth: 2 },
  labelStyle: { fill: '#e2e8f0', fontSize: 10 },
  labelBgStyle: { fill: '#0f172a' },
  markerEnd: { type: 'arrowclosed' },
})

// Layout: root on top, tables in a row, CTEs below them, then statements at the bottom
export function createGraphFromSql(analysis) {
  const nodes = []
  const edges = []
  const tableId = (name) => `table-${name.toLowerCase()}`
  const rowX = (index, count, gap) => (index - (count - 1) / 2) * gap

  nodes.push({
    id: 'root',
    data: { label: '📊 SQL Script' },
    position: { x: 0, y: -220 },
    style: nodeStyle('#336791', { border: '3px solid #fbbf24', fontSize: '14px', minWidth: '180px', padding: '14px' }),
  })

  analysis.tables.forEach((table, i) => {
    const details = [
      table.columns.length ? `${table.columns.length} columns` : null,
      table.rowsInserted ? `${table.rowsInserted} rows` : null,
    ].filter(Boolean).join(' · ')
    nodes.push({
      id: tableId(table.name),
      data: { label: `🗄️ ${table.name}${details ? `\n${details}` : ''}` },
      position: { x: rowX(i, analysis.tables.length, 230), y: 0 },
      style: nodeStyle('#ec4899', table.createdHere ? {} : { border: '2px dashed rgba(255,255,255,0.6)' }),
    })
    edges.push(edge('root', tableId(table.name), table.createdHere ? 'creates' : 'uses', '#94a3b8'))
  })

  analysis.ctes.forEach((cte, i) => {
    const unused = cte.usedBy.length === 0
    nodes.push({
      id: cte.id,
      data: { label: `🧩 ${cte.name}${unused ? '\n⚠️ never used' : ''}` },
      position: { x: rowX(i, analysis.ctes.length, 230), y: 220 },
      style: nodeStyle(unused ? '#7f1d1d' : '#8b5cf6'),
    })
    cte.reads.forEach((name) => {
      const source = analysis.ctes.find((c) => c.queryId === cte.queryId && c.name.toLowerCase() === name.toLowerCase())
      edges.push(edge(source ? source.id : tableId(name), cte.id, 'reads', '#a78bfa', true))
    })
  })

  const visibleQueries = analysis.queries.filter((q) => q.kind !== 'CREATE')
  let selectNumber = 0
  visibleQueries.forEach((q, i) => {
    const style = KIND_STYLE[q.kind]
    let label = `${style.icon} ${q.kind} ${q.target || ''}`.trim()
    if (q.kind === 'INSERT' && q.rows) label += `\n${q.rows} rows`
    if (q.kind === 'SELECT') label = `${style.icon} SELECT query ${++selectNumber}`

    nodes.push({
      id: q.id,
      data: { label },
      position: { x: rowX(i, visibleQueries.length, 210), y: analysis.ctes.length ? 440 : 240 },
      style: nodeStyle(style.color),
    })

    // Write edges also run table -> statement so Auto Layout keeps statements below their tables
    if (q.target && q.kind !== 'VIEW') {
      const writeLabel = { INSERT: 'inserted by', UPDATE: 'updated by', DELETE: 'deleted by' }[q.kind]
      edges.push(edge(tableId(q.target), q.id, writeLabel, style.color))
    }
    q.reads.forEach((name) => {
      const cte = analysis.ctes.find((c) => c.queryId === q.id && c.name.toLowerCase() === name.toLowerCase())
      edges.push(edge(cte ? cte.id : tableId(name), q.id, 'reads', '#22d3ee', true))
    })
  })

  return { nodes, edges }
}

export function generateSqlStats(analysis) {
  const countKind = (kind) => analysis.queries.filter((q) => q.kind === kind).length
  const queryBreakdown = ['CREATE', 'INSERT', 'UPDATE', 'DELETE', 'SELECT', 'VIEW']
    .map((kind) => [kind, countKind(kind)])
    .filter(([, count]) => count > 0)
    .map(([kind, count]) => `${count} ${kind}`)
    .join(' · ')

  const issues = [
    ...analysis.unusedCtes.map((name) => ({ name, note: 'unused CTE' })),
    ...analysis.duplicateCtes.map((names) => ({ name: names.join(' = '), note: 'duplicate CTEs' })),
  ]

  return {
    items: [
      { icon: '🗄️', label: 'Tables', value: analysis.tables.length, color: 'text-pink-400' },
      { icon: '📋', label: 'Columns', value: analysis.tables.reduce((sum, t) => sum + t.columns.length, 0), color: 'text-cyan-400' },
      { icon: '➕', label: 'Rows Inserted', value: analysis.tables.reduce((sum, t) => sum + t.rowsInserted, 0), color: 'text-emerald-400' },
      { icon: '🧾', label: 'Statements', value: analysis.queries.length, detail: queryBreakdown, color: 'text-orange-400' },
      { icon: '🧩', label: 'CTEs', value: analysis.ctes.length, color: 'text-purple-400' },
      { icon: '🔗', label: 'Joins', value: analysis.joins, color: 'text-sky-400' },
    ],
    issues,
    summary: '',
  }
}
