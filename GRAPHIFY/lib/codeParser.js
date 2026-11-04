export const detectLanguage = (code) => {
  const patterns = {
    sql: /^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH)\s+/im,
    python: /^(import|from|def|class|@|\bif __name__|async def)/m,
    javascript: /^(import|export|const|let|var|function|=>|class|async|await)/m,
    java: /^(import|package|public|private|class|interface|@Override)/m,
    html: /^<!DOCTYPE|<html|<head|<body|<div|<span/m,
    rust: /^(fn|mod|use|impl|struct|enum|trait|async)/m,
    holand: /^(program|procedure|variable|input|output|if|while)/m,
  }

  for (const [lang, pattern] of Object.entries(patterns)) {
    if (pattern.test(code.trim())) {
      return lang
    }
  }
  return 'unknown'
}

export const parseCode = (code, language) => {
  const parser = {
    sql: parseSQL,
    python: parsePython,
    javascript: parseJavaScript,
    java: parseJava,
    html: parseHTML,
    rust: parseRust,
    holand: parseHoland,
  }

  return (parser[language] || parseUnknown)(code)
}

const parsePython = (code) => {
  const entities = []
  const relationships = []
  let nodeId = 0

  const classRegex = /^class\s+(\w+)(?:\(([^)]*)\))?:/gm
  const funcRegex = /^\s{0,4}def\s+(\w+)\s*\(([^)]*)\):/gm
  const importRegex = /^(?:import|from)\s+([\w.]+)/gm

  let match

  while ((match = classRegex.exec(code)) !== null) {
    const className = match[1]
    const parent = match[2] || ''
    entities.push({
      id: `python-class-${nodeId++}`,
      label: className,
      type: 'class',
      language: 'python',
      metadata: { parent: parent.split(',')[0]?.trim() || 'object' },
    })
  }

  funcRegex.lastIndex = 0
  while ((match = funcRegex.exec(code)) !== null) {
    const funcName = match[1]
    const params = match[2].split(',').length
    entities.push({
      id: `python-func-${nodeId++}`,
      label: funcName,
      type: 'function',
      language: 'python',
      metadata: { params },
    })
  }

  importRegex.lastIndex = 0
  while ((match = importRegex.exec(code)) !== null) {
    const moduleName = match[1]
    entities.push({
      id: `python-import-${nodeId++}`,
      label: moduleName,
      type: 'import',
      language: 'python',
    })
  }

  return { entities, relationships, language: 'python' }
}

const parseJavaScript = (code) => {
  const entities = []
  let nodeId = 0

  const classRegex = /class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{/g
  const funcRegex = /(?:const|let|function)\s+(\w+)\s*=?\s*(?:\(([^)]*)\))?\s*(?:=>)?/g
  const importRegex = /import\s+(?:{([^}]+)}|\*|(\w+))\s+from\s+['"](.*)['"]/g

  let match

  while ((match = classRegex.exec(code)) !== null) {
    entities.push({
      id: `js-class-${nodeId++}`,
      label: match[1],
      type: 'class',
      language: 'javascript',
      metadata: { extends: match[2] || 'none' },
    })
  }

  funcRegex.lastIndex = 0
  while ((match = funcRegex.exec(code)) !== null) {
    if (match[1] && !match[1].includes('{')) {
      entities.push({
        id: `js-func-${nodeId++}`,
        label: match[1],
        type: 'function',
        language: 'javascript',
      })
    }
  }

  importRegex.lastIndex = 0
  while ((match = importRegex.exec(code)) !== null) {
    const items = match[1] || match[2] || match[3]
    entities.push({
      id: `js-import-${nodeId++}`,
      label: match[3],
      type: 'import',
      language: 'javascript',
      metadata: { items: items.split(',').length },
    })
  }

  return { entities, relationships: [], language: 'javascript' }
}

const parseJava = (code) => {
  const entities = []
  let nodeId = 0

  const classRegex = /(?:public|private)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?/g
  const methodRegex = /(?:public|private|protected)?\s*\w+\s+(\w+)\s*\([^)]*\)/g
  const importRegex = /import\s+([\w.]+);/g

  let match

  while ((match = classRegex.exec(code)) !== null) {
    entities.push({
      id: `java-class-${nodeId++}`,
      label: match[1],
      type: 'class',
      language: 'java',
      metadata: { extends: match[2] || 'Object' },
    })
  }

  methodRegex.lastIndex = 0
  while ((match = methodRegex.exec(code)) !== null) {
    entities.push({
      id: `java-method-${nodeId++}`,
      label: match[1],
      type: 'method',
      language: 'java',
    })
  }

  importRegex.lastIndex = 0
  while ((match = importRegex.exec(code)) !== null) {
    entities.push({
      id: `java-import-${nodeId++}`,
      label: match[1].split('.').pop(),
      type: 'import',
      language: 'java',
      metadata: { fullPath: match[1] },
    })
  }

  return { entities, relationships: [], language: 'java' }
}

const parseHTML = (code) => {
  const entities = []
  let nodeId = 0

  const tagRegex = /<(\w+)(?:\s+[^>]*)?>|<(\w+)(?:\s+[^>]*)?\/>/gi
  const idRegex = /id=["']([^"']+)["']/g
  const classRegex = /class=["']([^"']+)["']/g

  const tagsSet = new Set()
  let match

  while ((match = tagRegex.exec(code)) !== null) {
    const tag = (match[1] || match[2]).toLowerCase()
    if (!tagsSet.has(tag)) {
      tagsSet.add(tag)
      entities.push({
        id: `html-tag-${nodeId++}`,
        label: tag.toUpperCase(),
        type: 'element',
        language: 'html',
      })
    }
  }

  const idSet = new Set()
  idRegex.lastIndex = 0
  while ((match = idRegex.exec(code)) !== null) {
    if (!idSet.has(match[1])) {
      idSet.add(match[1])
      entities.push({
        id: `html-id-${nodeId++}`,
        label: `#${match[1]}`,
        type: 'identifier',
        language: 'html',
      })
    }
  }

  return { entities, relationships: [], language: 'html' }
}

const parseRust = (code) => {
  const entities = []
  let nodeId = 0

  const structRegex = /struct\s+(\w+)/g
  const fnRegex = /fn\s+(\w+)\s*\(/g
  const implRegex = /impl\s+(\w+)/g
  const useRegex = /use\s+([\w:]+);/g

  let match

  while ((match = structRegex.exec(code)) !== null) {
    entities.push({
      id: `rust-struct-${nodeId++}`,
      label: match[1],
      type: 'struct',
      language: 'rust',
    })
  }

  fnRegex.lastIndex = 0
  while ((match = fnRegex.exec(code)) !== null) {
    entities.push({
      id: `rust-fn-${nodeId++}`,
      label: match[1],
      type: 'function',
      language: 'rust',
    })
  }

  implRegex.lastIndex = 0
  while ((match = implRegex.exec(code)) !== null) {
    entities.push({
      id: `rust-impl-${nodeId++}`,
      label: match[1],
      type: 'implementation',
      language: 'rust',
    })
  }

  useRegex.lastIndex = 0
  while ((match = useRegex.exec(code)) !== null) {
    entities.push({
      id: `rust-use-${nodeId++}`,
      label: match[1],
      type: 'import',
      language: 'rust',
    })
  }

  return { entities, relationships: [], language: 'rust' }
}

const parseHoland = (code) => {
  const entities = []
  let nodeId = 0

  const programRegex = /program\s+(\w+)/gi
  const procRegex = /procedure\s+(\w+)/gi
  const varRegex = /variable\s+(\w+)/gi

  let match

  while ((match = programRegex.exec(code)) !== null) {
    entities.push({
      id: `holand-program-${nodeId++}`,
      label: match[1],
      type: 'program',
      language: 'holand',
    })
  }

  procRegex.lastIndex = 0
  while ((match = procRegex.exec(code)) !== null) {
    entities.push({
      id: `holand-proc-${nodeId++}`,
      label: match[1],
      type: 'procedure',
      language: 'holand',
    })
  }

  varRegex.lastIndex = 0
  while ((match = varRegex.exec(code)) !== null) {
    entities.push({
      id: `holand-var-${nodeId++}`,
      label: match[1],
      type: 'variable',
      language: 'holand',
    })
  }

  return { entities, relationships: [], language: 'holand' }
}

const parseSQL = (code) => {
  const entities = []
  let nodeId = 0

  const tableRegex = /(?:FROM|INTO|UPDATE|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|FULL JOIN)\s+(\w+)/gi
  const selectRegex = /SELECT\s+([\w\s,.*]+)\s+FROM/gi
  const insertRegex = /INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)/gi
  const createRegex = /CREATE\s+(?:TABLE|VIEW|INDEX|DATABASE)\s+(\w+)/gi
  const functionRegex = /(?:COUNT|SUM|AVG|MAX|MIN|UPPER|LOWER|CONCAT)\s*\(/gi

  let match

  // Extract tables
  const tablesSet = new Set()
  tableRegex.lastIndex = 0
  while ((match = tableRegex.exec(code)) !== null) {
    const tableName = match[1].trim()
    if (!tablesSet.has(tableName)) {
      tablesSet.add(tableName)
      entities.push({
        id: `sql-table-${nodeId++}`,
        label: tableName,
        type: 'table',
        language: 'sql',
        metadata: { type: 'table' },
      })
    }
  }

  // Extract columns from SELECT
  selectRegex.lastIndex = 0
  while ((match = selectRegex.exec(code)) !== null) {
    const columns = match[1].split(',').map(c => c.trim())
    columns.slice(0, 3).forEach((col) => {
      if (col && col !== '*') {
        entities.push({
          id: `sql-col-${nodeId++}`,
          label: col.split('.').pop(),
          type: 'column',
          language: 'sql',
        })
      }
    })
  }

  // Extract columns from INSERT
  insertRegex.lastIndex = 0
  while ((match = insertRegex.exec(code)) !== null) {
    const columns = match[2].split(',').map(c => c.trim())
    columns.forEach((col) => {
      if (col) {
        entities.push({
          id: `sql-col-${nodeId++}`,
          label: col,
          type: 'column',
          language: 'sql',
        })
      }
    })
  }

  // Extract CREATE objects
  createRegex.lastIndex = 0
  while ((match = createRegex.exec(code)) !== null) {
    entities.push({
      id: `sql-create-${nodeId++}`,
      label: match[1],
      type: 'schema',
      language: 'sql',
    })
  }

  // Extract functions
  const functionsSet = new Set()
  functionRegex.lastIndex = 0
  while ((match = functionRegex.exec(code)) !== null) {
    const func = match[0].replace(/\s*\($/, '')
    if (!functionsSet.has(func)) {
      functionsSet.add(func)
      entities.push({
        id: `sql-func-${nodeId++}`,
        label: func,
        type: 'function',
        language: 'sql',
      })
    }
  }

  return { entities, relationships: [], language: 'sql' }
}

const parseUnknown = (code) => {
  const entities = []
  const lines = code.split('\n').slice(0, 10)

  lines.forEach((line, idx) => {
    if (line.trim().length > 0) {
      entities.push({
        id: `unknown-${idx}`,
        label: line.trim().substring(0, 50),
        type: 'line',
        language: 'unknown',
      })
    }
  })

  return { entities, relationships: [], language: 'unknown' }
}
