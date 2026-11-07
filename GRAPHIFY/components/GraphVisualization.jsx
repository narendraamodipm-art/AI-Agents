'use client'

import { useCallback, useState, useEffect } from 'react'
import ReactFlow, {
  ReactFlowProvider,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  useReactFlow,
  useViewport,
} from 'reactflow'
import { Maximize, Zap } from 'lucide-react'
import 'reactflow/dist/style.css'

const MAX_ZOOM = 5
const ZOOM_PRESETS = [0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5]

function GraphContent({ nodes, edges }) {
  const [graphNodes, setNodes, onNodesChange] = useNodesState(nodes || [])
  const [graphEdges, setEdges, onEdgesChange] = useEdgesState(edges || [])
  const { fitView, zoomTo } = useReactFlow()
  const { zoom } = useViewport()
  const [layoutApplied, setLayoutApplied] = useState(false)

  // Auto-fit graph when it loads
  useEffect(() => {
    if (graphNodes.length > 0) {
      setTimeout(() => {
        fitView({ padding: 0.15, duration: 600 })
      }, 150)
    }
  }, [graphNodes.length, fitView])

  const onConnect = useCallback(
    (connection) => setEdges((eds) => [...eds, connection]),
    [setEdges]
  )

  const handleFitScreen = useCallback(() => {
    fitView({ padding: 0.15, duration: 800 })
  }, [fitView])

  const handleAutoLayout = useCallback(() => {
    // Hierarchical tree layout
    const nodesCopy = JSON.parse(JSON.stringify(graphNodes))
    const edgesCopy = graphEdges

    // Build parent-child relationships
    const childrenMap = {}
    const parentMap = {}

    edgesCopy.forEach((edge) => {
      if (!childrenMap[edge.source]) childrenMap[edge.source] = []
      childrenMap[edge.source].push(edge.target)
      if (!parentMap[edge.target]) parentMap[edge.target] = []
      parentMap[edge.target].push(edge.source)
    })

    // Find root (node with no parents or 'root' node)
    let rootId = 'root'
    const hasNodeWithId = nodesCopy.some((n) => n.id === 'root')
    if (!hasNodeWithId) {
      rootId = nodesCopy.find((n) => !parentMap[n.id])?.id || nodesCopy[0].id
    }

    // Calculate depth using DFS
    const depthMap = {}
    const visited = new Set()

    const dfs = (nodeId, depth) => {
      if (visited.has(nodeId)) return
      visited.add(nodeId)
      depthMap[nodeId] = depth

      const children = childrenMap[nodeId] || []
      children.forEach((childId) => {
        dfs(childId, depth + 1)
      })
    }

    dfs(rootId, 0)

    // Assign remaining unvisited nodes
    nodesCopy.forEach((node) => {
      if (!depthMap[node.id]) {
        depthMap[node.id] = 0
      }
    })

    // Group by depth level
    const levels = {}
    nodesCopy.forEach((node) => {
      const depth = depthMap[node.id]
      if (!levels[depth]) levels[depth] = []
      levels[depth].push(node)
    })

    // Position nodes
    const verticalGap = 150
    const horizontalGap = 200

    Object.entries(levels).forEach(([depth, nodes]) => {
      const y = parseInt(depth) * verticalGap
      const levelWidth = (nodes.length - 1) * horizontalGap
      const startX = -levelWidth / 2

      nodes.forEach((node, idx) => {
        node.position = {
          x: startX + idx * horizontalGap,
          y: y,
        }
      })
    })

    setNodes(nodesCopy)
    console.log('Layout applied:', depthMap)

    // Fit view
    setTimeout(() => {
      fitView({ padding: 0.15, duration: 1000 })
    }, 100)
  }, [graphNodes, graphEdges, setNodes, fitView])

  return (
    <div className="w-full h-full relative">
      {/* Control Buttons */}
      <div className="absolute top-4 left-4 z-10 flex gap-3">
        <button
          onClick={handleFitScreen}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition shadow-lg"
          title="Fit graph to screen"
        >
          <Maximize className="w-4 h-4" />
          Fit Screen
        </button>
        <button
          onClick={handleAutoLayout}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition shadow-lg"
          title="Auto-arrange nodes in hierarchical flow"
        >
          <Zap className="w-4 h-4" />
          Auto Layout
        </button>
        <select
          value=""
          onChange={(e) => zoomTo(Number(e.target.value), { duration: 400 })}
          className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium border border-slate-600 shadow-lg cursor-pointer"
          title="Zoom level"
        >
          <option value="" disabled>
            🔍 {Math.round(zoom * 100)}%
          </option>
          {ZOOM_PRESETS.map((level) => (
            <option key={level} value={level}>
              {level * 100}%
            </option>
          ))}
        </select>
      </div>

      {/* React Flow */}
      <ReactFlow
        nodes={graphNodes}
        edges={graphEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        minZoom={0.1}
        maxZoom={MAX_ZOOM}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
      >
        <Background color="#334155" gap={16} variant="dots" />
        <Controls
          position="bottom-right"
          showZoom={true}
          showFitView={true}
          showInteractive={true}
          style={{
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid rgba(148, 163, 184, 0.3)',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)',
          }}
          ariaLabel="React Flow Controls"
        />
      </ReactFlow>
    </div>
  )
}

export default function GraphVisualization({ nodes, edges }) {
  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-900 to-slate-950 rounded-xl overflow-hidden border border-slate-700">
      <ReactFlowProvider>
        <GraphContent nodes={nodes} edges={edges} />
      </ReactFlowProvider>
    </div>
  )
}
