'use client'

import { useState } from 'react'
import { Upload, Zap, Copy, Download, Maximize2, Minimize2 } from 'lucide-react'
import dynamic from 'next/dynamic'
import { detectLanguage } from '@/lib/codeParser'
import { createGraphFromStructure, generateStructureStats } from '@/lib/graphUtils'
import { analyzeSql, createGraphFromSql, generateSqlStats } from '@/lib/sqlAnalyzer'
import { createGraphFromLlm, generateLlmStats } from '@/lib/llmGraph'
import AIAnalysis from '@/components/AIAnalysis'
import Salahkar from '@/components/Salahkar'

const EXTENSION_LANGUAGES = {
  py: 'python', js: 'javascript', jsx: 'javascript', mjs: 'javascript', ts: 'typescript', tsx: 'typescript',
  java: 'java', c: 'c', h: 'c', cpp: 'cpp', cc: 'cpp', hpp: 'cpp', cs: 'csharp', go: 'go', rs: 'rust',
  php: 'php', rb: 'ruby', kt: 'kotlin', swift: 'swift', sql: 'sql', html: 'html', htm: 'html', css: 'css', sh: 'bash',
}

const LANGUAGE_NAMES = { javascript: 'JavaScript', typescript: 'TypeScript', cpp: 'C++', csharp: 'C#', sql: 'SQL', html: 'HTML', css: 'CSS', php: 'PHP' }
const formatLanguage = (lang) => LANGUAGE_NAMES[lang] || lang.charAt(0).toUpperCase() + lang.slice(1)

const GraphVisualization = dynamic(() => import('@/components/GraphVisualization'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-slate-900 rounded-xl">
      <div className="text-center">
        <div className="animate-spin text-indigo-400 text-4xl mb-2">⚙️</div>
        <p className="text-slate-400">Loading graph...</p>
      </div>
    </div>
  ),
})

export default function Home() {
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('python')
  const [graphData, setGraphData] = useState(null)
  const [stats, setStats] = useState(null)
  const [fileName, setFileName] = useState('')
  const [generating, setGenerating] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)

  const aiModel = 'mistral'

  // The language is never picked by hand: a quick local guess while typing, then Mistral's answer
  const handleCodeChange = (e) => {
    setCode(e.target.value)
    setLanguage(detectLanguage(e.target.value))
  }

  const postAnalyze = async (body) => {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.error || 'Unknown error')
    return data
  }

  // Used only if Mistral can't produce the graph: local SQL analysis, or the older structure call
  const generateFallbackGraph = async () => {
    if (language === 'sql') {
      const analysis = analyzeSql(code)
      setGraphData(createGraphFromSql(analysis))
      setStats(generateSqlStats(analysis))
      return
    }
    const data = await postAnalyze({ code, language, type: 'structure' })
    setGraphData(createGraphFromStructure(data.structure, language))
    setStats(generateStructureStats(data.structure))
  }

  const generateGraph = async () => {
    if (!code.trim()) {
      alert('Please paste or upload code first!')
      return
    }

    setGenerating(true)
    try {
      const { graph } = await postAnalyze({ code, language, type: 'graph' })
      if (graph.language && graph.language !== 'other' && graph.language !== 'unknown') {
        setLanguage(graph.language)
      }
      setGraphData(createGraphFromLlm(graph))
      setStats(generateLlmStats(graph))
    } catch (error) {
      console.error('LLM graph failed, using fallback:', error)
      try {
        await generateFallbackGraph()
      } catch (fallbackError) {
        alert('Failed to generate graph: ' + fallbackError.message)
      }
    } finally {
      setGenerating(false)
    }
  }

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        const content = event.target?.result || ''
        setCode(content)
        setFileName(file.name)

        // The file extension is the most reliable hint; fall back to reading the code
        const ext = file.name.split('.').pop()?.toLowerCase()
        setLanguage(EXTENSION_LANGUAGES[ext] || detectLanguage(content))
      }
      reader.readAsText(file)
    }
  }

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code)
    alert('Code copied to clipboard!')
  }

  const handleDownloadGraphPNG = async () => {
    if (!graphData) {
      alert('Generate a graph first!')
      return
    }

    try {
      // Dynamic import html2canvas
      const html2canvas = (await import('html2canvas')).default

      // Find graph container - try multiple selectors
      let graphContainer = document.querySelector('.react-flow__viewport')?.parentElement

      if (!graphContainer) {
        graphContainer = document.querySelector('[style*="background-to-br"]')
      }

      if (!graphContainer) {
        // Fallback: find the graph visualization div
        const allDivs = document.querySelectorAll('div[class*="rounded-xl"]')
        for (let div of allDivs) {
          if (div.querySelector('.react-flow__viewport')) {
            graphContainer = div
            break
          }
        }
      }

      if (!graphContainer) {
        alert('Could not find graph element! Please try downloading as JSON instead.')
        return
      }

      // Capture the graph as canvas
      const canvas = await html2canvas(graphContainer, {
        backgroundColor: '#0f172a',
        scale: 2,
        useCORS: true,
        logging: false,
        allowTaint: true,
      })

      // Convert to PNG and download
      const link = document.createElement('a')
      link.href = canvas.toDataURL('image/png')
      link.download = `graph-${language}-${Date.now()}.png`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      alert('Graph downloaded as PNG!')
    } catch (error) {
      console.error('Error downloading PNG:', error)
      alert('Failed to download graph as PNG. Error: ' + error.message)
    }
  }

  const handleDownloadGraphJSON = () => {
    if (!graphData) {
      alert('Generate a graph first!')
      return
    }
    const dataStr = JSON.stringify(graphData, null, 2)
    const element = document.createElement('a')
    element.setAttribute('href', 'data:text/json;charset=utf-8,' + encodeURIComponent(dataStr))
    element.setAttribute('download', `graph-${language}.json`)
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-slate-700 glass-effect">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-3xl">📊</div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">GRAPHIFY</h1>
              <p className="text-sm text-slate-400">Code to Knowledge Graph</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Zap className="w-4 h-4 text-yellow-400" />
            <span>Visualize Code Structure in Seconds</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Code Input Area */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Left Panel */}
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-semibold text-slate-300">
                  Code Input
                </label>
                {code.trim() && (
                  <span className="text-xs px-2 py-1 rounded-full bg-slate-800 border border-slate-600 text-slate-300">
                    🔍 Detected: <strong className="text-indigo-300">{language === 'unknown' ? 'Unknown' : formatLanguage(language)}</strong>
                  </span>
                )}
              </div>
              <div className="flex gap-2 mb-2">
                <label className="flex-1">
                  <div className="flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg cursor-pointer font-medium transition">
                    <Upload className="w-4 h-4" />
                    Upload File
                  </div>
                  <input
                    type="file"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
                <button
                  onClick={handleCopyCode}
                  disabled={!code}
                  className="px-4 py-2 rounded-lg font-medium bg-slate-700 hover:bg-slate-600 disabled:opacity-50 transition flex items-center gap-2"
                >
                  <Copy className="w-4 h-4" />
                  Copy
                </button>
              </div>

              {fileName && (
                <p className="text-xs text-slate-400 mb-2">📄 Uploaded: {fileName}</p>
              )}

              <textarea
                value={code}
                onChange={handleCodeChange}
                placeholder="Paste your code here or upload a file..."
                className="code-input w-full h-96 resize-none focus:outline-none focus:border-indigo-500 focus:border-2"
              />
            </div>

            <button
              onClick={generateGraph}
              disabled={generating || !code.trim()}
              className={`w-full text-lg py-3 font-bold flex items-center justify-center gap-2 rounded-lg transition ${
                generating || !code.trim()
                  ? 'btn-primary opacity-60 cursor-not-allowed'
                  : 'btn-primary hover:opacity-90'
              }`}
            >
              {generating ? (
                <>
                  <div className="animate-spin">⚙️</div>
                  Analyzing with LLM...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  Generate Graph
                </>
              )}
            </button>
          </div>

          {/* Right Panel - Stats */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                Code Statistics
              </label>
              <div className="glass-effect p-6 rounded-lg space-y-4 h-96 overflow-auto">
                {stats ? (
                  <>
                    <div className="grid grid-cols-2 gap-4 border-b border-slate-600 pb-4">
                      {stats.items.map((item) => (
                        <div key={item.label}>
                          <p className="text-slate-400 text-sm">{item.icon} {item.label}</p>
                          <p className={`text-3xl font-bold ${item.color}`}>{item.value}</p>
                          {item.detail && <p className="text-xs text-slate-400 mt-1">{item.detail}</p>}
                        </div>
                      ))}
                    </div>

                    {stats.issues.length > 0 && (
                      <div className="border-b border-slate-600 pb-4">
                        <p className="text-slate-400 text-sm font-semibold mb-2">⚠️ Issues Found</p>
                        <div className="space-y-1 text-xs">
                          {stats.issues.map((issue) => (
                            <div key={issue.name + issue.note} className="flex justify-between gap-2">
                              <span className="text-slate-300">{issue.name}</span>
                              <span className="bg-red-900 text-red-200 px-2 py-0.5 rounded whitespace-nowrap">{issue.note}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {stats.summary === null && (
                      <p className="text-xs text-slate-400">📝 Generating summary…</p>
                    )}

                    {stats.summary && (
                      <div>
                        <p className="text-slate-400 text-sm font-semibold mb-2">📝 Summary</p>
                        <p className="text-xs text-slate-300 leading-relaxed">{stats.summary}</p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="flex items-center justify-center h-full text-slate-400">
                    <div className="text-center">
                      <p className="text-3xl mb-2">📈</p>
                      <p>Statistics will appear here after generating a graph</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Graph Visualization */}
        {graphData && (
          <div className={`mb-6 ${fullscreen ? 'fixed inset-0 z-50 p-0 m-0' : ''}`}>
            <div className={`flex items-center justify-between mb-4 ${fullscreen ? 'p-4 bg-slate-950' : ''}`}>
              <h2 className="text-xl font-bold flex items-center gap-2">
                <span>📊</span> Knowledge Graph Visualization
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={() => setFullscreen(!fullscreen)}
                  className={`px-4 py-2 rounded-lg font-medium transition flex items-center gap-2 ${
                    fullscreen
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-indigo-600 hover:bg-indigo-700'
                  }`}
                  title={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}
                >
                  {fullscreen ? (
                    <>
                      <Minimize2 className="w-4 h-4" />
                      Exit Fullscreen
                    </>
                  ) : (
                    <>
                      <Maximize2 className="w-4 h-4" />
                      Fullscreen
                    </>
                  )}
                </button>
                <button
                  onClick={handleDownloadGraphPNG}
                  className="px-4 py-2 rounded-lg font-medium bg-green-600 hover:bg-green-700 transition flex items-center gap-2"
                  title="Download graph as PNG image"
                >
                  <Download className="w-4 h-4" />
                  📸 PNG
                </button>
                <button
                  onClick={handleDownloadGraphJSON}
                  className="px-4 py-2 rounded-lg font-medium bg-slate-700 hover:bg-slate-600 transition flex items-center gap-2"
                  title="Download graph data as JSON"
                >
                  <Download className="w-4 h-4" />
                  📄 JSON
                </button>
              </div>
            </div>
            <div
              className={`${
                fullscreen
                  ? 'fixed inset-0 top-20 rounded-none border-none'
                  : 'h-[600px] rounded-xl border border-slate-700'
              } overflow-hidden bg-slate-900`}
            >
              <GraphVisualization
                key={graphData.nodes.map((n) => n.id + n.data.label).join('|')}
                nodes={graphData.nodes}
                edges={graphData.edges}
              />
            </div>
          </div>
        )}

        {/* AI Analysis Section */}
        <div className="mb-8">
          <AIAnalysis code={code} language={language} aiModel={aiModel} onApplyCode={setCode} />
        </div>

        {/* SALAHKAR chat: refactors the code from the user's instructions */}
        <div className="mb-8">
          <Salahkar code={code} language={language} onApplyCode={setCode} />
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="glass-effect p-4 rounded-lg card-hover">
            <div className="text-2xl mb-2">🐍</div>
            <h3 className="font-semibold mb-1">Python</h3>
            <p className="text-sm text-slate-400">Classes, functions, imports</p>
          </div>
          <div className="glass-effect p-4 rounded-lg card-hover">
            <div className="text-2xl mb-2">⚡</div>
            <h3 className="font-semibold mb-1">JavaScript</h3>
            <p className="text-sm text-slate-400">Classes, functions, modules</p>
          </div>
          <div className="glass-effect p-4 rounded-lg card-hover">
            <div className="text-2xl mb-2">☕</div>
            <h3 className="font-semibold mb-1">Java</h3>
            <p className="text-sm text-slate-400">Classes, methods, packages</p>
          </div>
          <div className="glass-effect p-4 rounded-lg card-hover">
            <div className="text-2xl mb-2">🗄️</div>
            <h3 className="font-semibold mb-1">SQL</h3>
            <p className="text-sm text-slate-400">Tables, columns, functions</p>
          </div>
        </div>

        {/* Features */}
        <div className="glass-effect p-6 rounded-lg">
          <h2 className="text-lg font-bold mb-4">✨ Features</h2>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-slate-300">
            <li>✅ Support for all programming languages</li>
            <li>✅ Auto-detect language from code</li>
            <li>✅ Extract classes, functions, imports, variables</li>
            <li>✅ Interactive graph visualization with zoom & pan</li>
            <li>✅ Download graph as JSON for integration</li>
            <li>✅ Real-time code analysis</li>
            <li>✅ Color-coded by entity type</li>
            <li>✅ Upload files or paste code directly</li>
          </ul>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-700 mt-12 py-6 text-center text-sm text-slate-400">
        <p>Built with ❤️ using Next.js, React Flow & Tailwind CSS</p>
      </footer>
    </div>
  )
}
