export const createGraphFromEntities = (entities, language) => {
  const nodes = []
  const edges = []

  const colorMap = {
    sql: { bg: '#336791', text: '#ffffff' },
    python: { bg: '#3776ab', text: '#ffffff' },
    javascript: { bg: '#f1e05a', text: '#000000' },
    java: { bg: '#007396', text: '#ffffff' },
    html: { bg: '#e34c26', text: '#ffffff' },
    rust: { bg: '#ce422b', text: '#ffffff' },
    holand: { bg: '#6366f1', text: '#ffffff' },
    unknown: { bg: '#64748b', text: '#ffffff' },
  }

  const typeIcons = {
    class: '📦',
    function: '⚙️',
    method: '🔧',
    import: '📥',
    struct: '🏗️',
    implementation: '💻',
    element: '🏷️',
    identifier: '🎯',
    program: '🎮',
    procedure: '📋',
    variable: '📌',
    line: '📝',
    table: '🗂️',
    column: '📊',
    schema: '📈',
  }

  const typeColors = {
    class: '#ec4899',
    function: '#06b6d4',
    method: '#f59e0b',
    import: '#8b5cf6',
    struct: '#10b981',
    implementation: '#6366f1',
    element: '#ef5350',
    identifier: '#fbbf24',
    program: '#5b21b6',
    procedure: '#1e40af',
    variable: '#0891b2',
    line: '#78716c',
    table: '#336791',
    column: '#4a90e2',
    schema: '#50c878',
  }

  const colors = colorMap[language] || colorMap.unknown
  const spacing = 250
  const cols = Math.ceil(Math.sqrt(entities.length))

  entities.forEach((entity, idx) => {
    const row = Math.floor(idx / cols)
    const col = idx % cols

    const node = {
      id: entity.id,
      data: {
        label: `${typeIcons[entity.type] || '•'} ${entity.label}`,
      },
      position: {
        x: col * spacing,
        y: row * spacing,
      },
      style: {
        background: typeColors[entity.type] || colors.bg,
        color: '#ffffff',
        border: '2px solid rgba(255,255,255,0.2)',
        borderRadius: '8px',
        padding: '10px',
        fontWeight: '600',
        fontSize: '12px',
        minWidth: '120px',
        textAlign: 'center',
        boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
      },
    }

    nodes.push(node)
  })

  // Add central root node
  const rootNode = {
    id: 'root',
    data: { label: `🌐 ${language.toUpperCase()}` },
    position: { x: 400, y: -100 },
    style: {
      background: colors.bg,
      color: colors.text,
      border: '3px solid ' + typeColors.import,
      borderRadius: '12px',
      padding: '15px',
      fontWeight: 'bold',
      fontSize: '14px',
      minWidth: '150px',
      textAlign: 'center',
      boxShadow: '0 6px 12px rgba(0,0,0,0.4)',
    },
  }

  nodes.unshift(rootNode)

  // Connect all entities to root
  entities.forEach((entity) => {
    edges.push({
      id: `root-${entity.id}`,
      source: 'root',
      target: entity.id,
      animated: true,
      style: { stroke: 'rgba(148, 163, 184, 0.3)', strokeWidth: 2 },
      markerEnd: { type: 'arrowclosed' },
    })
  })

  return { nodes, edges }
}

export const getLanguageColor = (language) => {
  const colors = {
    sql: '#336791',
    python: '#3776ab',
    javascript: '#f1e05a',
    java: '#007396',
    html: '#e34c26',
    rust: '#ce422b',
    holand: '#6366f1',
    unknown: '#64748b',
  }
  return colors[language] || colors.unknown
}

export const getLanguageIcon = (language) => {
  const icons = {
    sql: '🗄️',
    python: '🐍',
    javascript: '⚡',
    java: '☕',
    html: '🌐',
    rust: '🦀',
    holand: '🎯',
    unknown: '❓',
  }
  return icons[language] || icons.unknown
}

export const getTypeColor = (type) => {
  const colors = {
    class: '#ec4899',
    function: '#06b6d4',
    method: '#f59e0b',
    import: '#8b5cf6',
    struct: '#10b981',
    implementation: '#6366f1',
    element: '#ef5350',
    identifier: '#fbbf24',
    program: '#5b21b6',
    procedure: '#1e40af',
    variable: '#0891b2',
    line: '#78716c',
  }
  return colors[type] || '#6366f1'
}

export const generateGraphStats = (entities, language) => {
  const stats = {
    totalEntities: entities.length,
    language,
    byType: {},
  }

  entities.forEach((entity) => {
    stats.byType[entity.type] = (stats.byType[entity.type] || 0) + 1
  })

  return stats
}

export const createGraphFromStructure = (structure, language) => {
  const nodes = []
  const edges = []

  const colorMap = {
    sql: { bg: '#336791', text: '#ffffff' },
    python: { bg: '#3776ab', text: '#ffffff' },
    javascript: { bg: '#f1e05a', text: '#000000' },
    java: { bg: '#007396', text: '#ffffff' },
    html: { bg: '#e34c26', text: '#ffffff' },
    rust: { bg: '#ce422b', text: '#ffffff' },
    holand: { bg: '#6366f1', text: '#ffffff' },
    unknown: { bg: '#64748b', text: '#ffffff' },
  }

  const colors = colorMap[language] || colorMap.unknown

  // Root node - centered at origin
  const rootNode = {
    id: 'root',
    data: { label: `📊 ${language.toUpperCase()} Code` },
    position: { x: 0, y: 0 },
    style: {
      background: colors.bg,
      color: colors.text,
      border: '3px solid #fbbf24',
      borderRadius: '12px',
      padding: '15px',
      fontWeight: 'bold',
      fontSize: '14px',
      minWidth: '180px',
      textAlign: 'center',
      boxShadow: '0 6px 12px rgba(0,0,0,0.4)',
    },
  }
  nodes.push(rootNode)

  // Calculate positions for classes in a circle around root
  const classes = structure.classes || []
  const functions = structure.functions || []
  const totalClasses = classes.length
  // Adaptive radius based on number of classes
  const classRadius = Math.max(300, Math.min(600, 100 + totalClasses * 80))
  const methodRadius = 180

  // Position classes around root in a circle
  classes.forEach((cls, classIdx) => {
    const angle = (classIdx / totalClasses) * Math.PI * 2
    const classX = Math.cos(angle) * classRadius
    const classY = Math.sin(angle) * classRadius

    const classId = `class-${cls.name}`
    const classNode = {
      id: classId,
      data: {
        label: `📦 ${cls.name}\n(${cls.functionCount} methods)`,
      },
      position: { x: classX, y: classY },
      style: {
        background: '#ec4899',
        color: '#ffffff',
        border: '2px solid rgba(255,255,255,0.3)',
        borderRadius: '8px',
        padding: '10px',
        fontWeight: '600',
        fontSize: '11px',
        minWidth: '140px',
        textAlign: 'center',
        boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
      },
    }
    nodes.push(classNode)

    edges.push({
      id: `root-${classId}`,
      source: 'root',
      target: classId,
      animated: true,
      style: { stroke: '#94a3b8', strokeWidth: 2 },
      markerEnd: { type: 'arrowclosed' },
    })

    // Position methods around their class
    const methods = cls.functions || []
    const methodsPerClass = methods.length
    methods.forEach((method, methodIdx) => {
      const methodAngle = (methodIdx / Math.max(methodsPerClass, 1)) * Math.PI * 2
      const methodX = classX + Math.cos(methodAngle) * methodRadius
      const methodY = classY + Math.sin(methodAngle) * methodRadius

      const methodId = `method-${cls.name}-${method.name}`
      const methodNode = {
        id: methodId,
        data: {
          label: `⚙️ ${method.name}\n(🔄 ${method.loopCount} loops)`,
          description: method.description,
        },
        position: { x: methodX, y: methodY },
        style: {
          background: '#06b6d4',
          color: '#ffffff',
          border: '2px solid rgba(255,255,255,0.2)',
          borderRadius: '8px',
          padding: '8px',
          fontWeight: '500',
          fontSize: '10px',
          minWidth: '130px',
          textAlign: 'center',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
        },
      }
      nodes.push(methodNode)

      edges.push({
        id: `${classId}-${methodId}`,
        source: classId,
        target: methodId,
        animated: true,
        style: { stroke: '#f59e0b', strokeWidth: 2 },
        markerEnd: { type: 'arrowclosed' },
      })
    })
  })

  // Position standalone functions in a circle below root
  const functionsRadius = 300
  functions.forEach((func, funcIdx) => {
    const totalFunctions = functions.length
    const angle = (funcIdx / Math.max(totalFunctions, 1)) * Math.PI * 2 - Math.PI / 2
    const funcX = Math.cos(angle) * functionsRadius
    const funcY = Math.sin(angle) * functionsRadius + 500

    const funcId = `func-${func.name}`
    const funcNode = {
      id: funcId,
      data: {
        label: `⚙️ ${func.name}\n(🔄 ${func.loopCount} loops)`,
        description: func.description,
      },
      position: { x: funcX, y: funcY },
      style: {
        background: '#10b981',
        color: '#ffffff',
        border: '2px solid rgba(255,255,255,0.2)',
        borderRadius: '8px',
        padding: '8px',
        fontWeight: '500',
        fontSize: '10px',
        minWidth: '130px',
        textAlign: 'center',
        boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
      },
    }
    nodes.push(funcNode)

    edges.push({
      id: `root-${funcId}`,
      source: 'root',
      target: funcId,
      animated: false,
      style: { stroke: '#8b5cf6', strokeWidth: 1.5 },
      markerEnd: { type: 'arrowclosed' },
    })
  })

  return { nodes, edges, structure }
}

export const generateStructureStats = (structure) => {
  return {
    totalClasses: structure.statistics?.totalClasses || 0,
    totalFunctions: structure.statistics?.totalFunctions || 0,
    totalLoops: structure.statistics?.totalLoops || 0,
    duplicateFunctions: structure.statistics?.duplicateFunctions || [],
    summary: structure.summary || '',
  }
}
