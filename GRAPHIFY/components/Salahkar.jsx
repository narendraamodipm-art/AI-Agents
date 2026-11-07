'use client'

import { useEffect, useRef, useState } from 'react'
import { Loader, Copy, Check, Send, RotateCcw } from 'lucide-react'

const SUGGESTIONS = [
  'Remove unused code',
  'Improve variable and function names',
  'Add comments for beginners',
  'Add error handling',
  'Make it faster',
  'Explain what this code does',
]

export default function Salahkar({ code, language, onApplyCode }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copiedIndex, setCopiedIndex] = useState(null)
  const [appliedIndex, setAppliedIndex] = useState(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  // Each request works on SALAHKAR's latest version, so follow-ups build on earlier changes
  const latestCode = [...messages].reverse().find((m) => m.code)?.code
  const workingCode = latestCode || code

  const send = async (text) => {
    const content = text.trim()
    if (!content || loading) return
    if (!workingCode.trim()) {
      setError('Paste some code in the editor first.')
      return
    }

    const nextMessages = [...messages, { role: 'user', content }]
    setMessages(nextMessages)
    setInput('')
    setError('')
    setLoading(true)

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'chat',
          code: workingCode,
          language,
          messages: nextMessages.map(({ role, content: body }) => ({ role, content: body })),
        }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'SALAHKAR could not answer')

      setMessages([...nextMessages, { role: 'assistant', content: data.reply, code: data.code }])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send(input)
    }
  }

  const handleCopy = (index, text) => {
    navigator.clipboard.writeText(text)
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  const handleApply = (index, text) => {
    onApplyCode(text)
    setAppliedIndex(index)
    setTimeout(() => setAppliedIndex(null), 2000)
  }

  const resetChat = () => {
    setMessages([])
    setError('')
  }

  return (
    <div className="glass-effect p-6 rounded-lg">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <span>🧑‍🏫</span> SALAHKAR
        </h2>
        {messages.length > 0 && (
          <button
            onClick={resetChat}
            className="flex items-center gap-1 px-3 py-1 text-sm bg-slate-700 hover:bg-slate-600 rounded transition"
            title="Start over from the code in the editor"
          >
            <RotateCcw className="w-4 h-4" />
            New chat
          </button>
        )}
      </div>
      <p className="text-sm text-slate-400 mb-4">
        Your AI code advisor. Tell it how to change the code and it rewrites it for you.
        {latestCode && ' Working on its latest version.'}
      </p>

      <div ref={scrollRef} className="bg-slate-950 border border-slate-700 rounded-lg p-4 h-96 overflow-y-auto space-y-4 mb-3">
        {messages.length === 0 && !loading && (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 gap-3">
            <p className="text-3xl">💬</p>
            <p className="text-sm">Ask SALAHKAR to refactor the code in the editor. Try one of these:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => send(suggestion)}
                  disabled={!code.trim()}
                  className="px-3 py-1 text-xs rounded-full bg-slate-800 border border-slate-600 hover:bg-slate-700 disabled:opacity-50 transition"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[90%] rounded-lg px-4 py-3 text-sm ${
                message.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-200 border border-slate-700'
              }`}
            >
              {message.role === 'assistant' && <p className="text-xs font-semibold text-emerald-400 mb-1">🧑‍🏫 SALAHKAR</p>}
              {message.content && <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>}

              {message.code && (
                <div className="mt-3">
                  <div className="flex justify-end gap-2 mb-2">
                    <button
                      onClick={() => handleCopy(index, message.code)}
                      className="flex items-center gap-1 px-2 py-1 text-xs bg-slate-700 hover:bg-slate-600 rounded transition"
                    >
                      {copiedIndex === index ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                      {copiedIndex === index ? 'Copied!' : 'Copy'}
                    </button>
                    <button
                      onClick={() => handleApply(index, message.code)}
                      className="px-2 py-1 text-xs bg-emerald-700 hover:bg-emerald-600 rounded transition"
                    >
                      {appliedIndex === index ? '✓ Applied' : 'Use in Editor'}
                    </button>
                  </div>
                  <pre className="bg-slate-950 border border-slate-700 rounded p-3 max-h-72 overflow-auto text-xs font-mono text-slate-300">
                    {message.code}
                  </pre>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Loader className="w-4 h-4 animate-spin" />
            SALAHKAR is thinking…
          </div>
        )}
      </div>

      {error && <p className="text-sm text-red-400 mb-2">⚠️ {error}</p>}

      <div className="flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={code.trim() ? 'e.g. "Split main() into smaller functions" (Enter to send, Shift+Enter for a new line)' : 'Paste code in the editor first…'}
          rows={2}
          className="flex-1 resize-none bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
        />
        <button
          onClick={() => send(input)}
          disabled={loading || !input.trim() || !code.trim()}
          className="px-4 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 disabled:text-slate-400 text-white font-semibold flex items-center gap-2 transition"
        >
          <Send className="w-4 h-4" />
          Send
        </button>
      </div>
    </div>
  )
}
