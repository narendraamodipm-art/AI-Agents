'use client'

import { useState } from 'react'
import { Loader, Copy, Check, Wand2 } from 'lucide-react'

export default function AIAnalysis({ code, language, aiModel, onApplyCode }) {
  const [analysis, setAnalysis] = useState('')
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')
  const [refactor, setRefactor] = useState(null)
  const [refactoring, setRefactoring] = useState(false)
  const [refactorCopied, setRefactorCopied] = useState(false)

  const handleRefactor = async () => {
    if (!code.trim()) {
      setError('Please paste code first!')
      return
    }

    setRefactoring(true)
    setError('')
    setRefactor(null)

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language, aiModel, type: 'refactor' }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Refactor failed')
      }

      setRefactor({ code: data.refactored, changes: data.changes || [] })
    } catch (err) {
      setError(err.message || 'Failed to refactor code')
      console.error('Refactor error:', err)
    } finally {
      setRefactoring(false)
    }
  }

  const handleCopyRefactor = () => {
    navigator.clipboard.writeText(refactor.code)
    setRefactorCopied(true)
    setTimeout(() => setRefactorCopied(false), 2000)
  }

  const handleAnalyze = async () => {
    if (!code.trim()) {
      setError('Please paste code first!')
      return
    }

    setLoading(true)
    setError('')
    setAnalysis('')

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          language,
          aiModel,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Analysis failed')
      }

      setAnalysis(data.analysis)
    } catch (err) {
      setError(err.message || 'Failed to analyze code')
      console.error('Analysis error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(analysis)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="glass-effect p-6 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <span>🧠</span> AI Code Architect
        </h2>
        <span className="text-sm text-slate-400">
          🚀 Mistral
        </span>
      </div>

      {error && (
        <div className="bg-red-900 border border-red-600 text-red-200 px-4 py-3 rounded-lg mb-4">
          <p className="font-semibold">Error:</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      <button
        onClick={handleAnalyze}
        disabled={loading || !code}
        className={`w-full mb-4 px-4 py-3 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
          loading || !code
            ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
            : 'bg-indigo-600 hover:bg-indigo-700 text-white'
        }`}
      >
        {loading ? (
          <>
            <Loader className="w-5 h-5 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <span>🧠</span>
            Analyze Architecture
          </>
        )}
      </button>

      <button
        onClick={handleRefactor}
        disabled={refactoring || !code}
        className={`w-full mb-4 px-4 py-3 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
          refactoring || !code
            ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
            : 'bg-emerald-600 hover:bg-emerald-700 text-white'
        }`}
      >
        {refactoring ? (
          <>
            <Loader className="w-5 h-5 animate-spin" />
            Refactoring...
          </>
        ) : (
          <>
            <Wand2 className="w-5 h-5" />
            Refactor Code
          </>
        )}
      </button>

      {refactor && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-lg">Refactored Code</h3>
            <div className="flex gap-2">
              <button
                onClick={handleCopyRefactor}
                className="flex items-center gap-1 px-3 py-1 text-sm bg-slate-700 hover:bg-slate-600 rounded transition"
              >
                {refactorCopied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                {refactorCopied ? 'Copied!' : 'Copy'}
              </button>
              {onApplyCode && (
                <button
                  onClick={() => onApplyCode(refactor.code)}
                  className="px-3 py-1 text-sm bg-emerald-700 hover:bg-emerald-600 rounded transition"
                >
                  Use in Editor
                </button>
              )}
            </div>
          </div>

          {refactor.changes.length > 0 && (
            <div className="mb-3 p-3 bg-slate-800 rounded-lg text-sm text-slate-300">
              <p className="font-semibold mb-2">🛠️ Changes made:</p>
              <ul className="space-y-1 text-xs list-disc list-inside">
                {refactor.changes.map((change, idx) => (
                  <li key={idx}>{change}</li>
                ))}
              </ul>
            </div>
          )}

          <pre className="bg-slate-950 border border-slate-700 rounded-lg p-4 max-h-96 overflow-auto text-sm text-slate-300 font-mono">
            {refactor.code}
          </pre>
        </div>
      )}

      {analysis && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-lg">Analysis Result</h3>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-3 py-1 text-sm bg-slate-700 hover:bg-slate-600 rounded transition"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copy
                </>
              )}
            </button>
          </div>

          <div className="bg-slate-950 border border-slate-700 rounded-lg p-4 max-h-96 overflow-y-auto prose prose-invert prose-sm">
            <div className="text-slate-300 whitespace-pre-wrap font-mono text-sm leading-relaxed">
              {analysis.split('\n').map((line, idx) => (
                <div key={idx} className="mb-1">
                  {line}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 p-3 bg-slate-800 rounded-lg text-sm text-slate-300">
            <p className="font-semibold mb-2">💡 Beginner Tips:</p>
            <ul className="space-y-1 text-xs">
              <li>✓ Read the "What This Code Does" section first</li>
              <li>✓ Look at the "Real-World Analogy" to understand the concept</li>
              <li>✓ Follow the "Step-by-Step Flow" to trace execution</li>
              <li>✓ Use "Key Concepts Explained" to learn new terms</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
