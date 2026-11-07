import { Anthropic } from '@anthropic-ai/sdk'

const claudeClient = new Anthropic()

// API endpoints
const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'

const prompt = (code, language) => `Analyze this ${language.toUpperCase()} code and provide:

1. **📊 CODE FLOW** - How the code executes step-by-step
2. **🔗 DEPENDENCIES** - Which functions/classes depend on each other
3. **📞 FUNCTION CALLS** - Which function calls which (show the chain)
4. **⚙️ WHAT EACH DOES** - Brief description of each function/class
5. **📝 SUMMARY** (80-100 words) - Overview of entire code purpose and architecture

Format:

## 📊 CODE FLOW
Start → [Step 1] → [Step 2] → [Step 3] → End

## 🔗 DEPENDENCIES
- Component A depends on: Component B, Component C
- Component B depends on: Component D
(Show what needs what)

## 📞 FUNCTION CALLS
main() calls:
  └─ init()
     └─ setup()
  └─ process()
     └─ validate()
     └─ transform()
(Show the call chain)

## ⚙️ COMPONENTS
- **ClassName/FunctionName**: What it does (one line)
- **ClassName/FunctionName**: What it does (one line)

## 📝 SUMMARY (80-100 words)
[One paragraph explaining the overall purpose, architecture, and how components work together. Make it understandable for beginners.]

CODE:
\`\`\`${language}
${code}
\`\`\`

Be concise and visual. Use arrows and indentation.`

// Cheap static scan so the small model doesn't have to spot unused names on its own
const ENTRY_POINTS = new Set(['main', '__init__', 'constructor', 'render', 'setup'])

// Comments, docstrings and plain strings mention names without using them (e.g. require('path')),
// so drop them before counting. f-strings and `template` strings stay: they can reference variables.
function stripComments(code) {
  return code
    .replace(/("""|''')[\s\S]*?\1/g, '')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|\s)(#|\/\/).*$/gm, '$1')
    .replace(/(?<![fFrRbB\w])(["'])(?:\\.|(?!\1)[^\\\n])*\1/g, '""')
}

function findUnusedNames(rawCode) {
  const code = stripComments(rawCode)
  const countRefs = (name) => (code.match(new RegExp(`\\b${name}\\b`, 'g')) || []).length

  const definedFunctions = [
    ...code.matchAll(/^\s*(?:async\s+)?def\s+(\w+)/gm),
    ...code.matchAll(/^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)/gm),
  ].map((m) => m[1])

  const unusedFunctions = [...new Set(definedFunctions)].filter(
    (name) => !ENTRY_POINTS.has(name) && !name.startsWith('__') && countRefs(name) <= definedFunctions.filter((n) => n === name).length
  )

  const importedNames = []
  for (const m of code.matchAll(/^\s*import\s+([\w., ]+?)\s*$/gm)) {
    m[1].split(',').forEach((part) => importedNames.push(part.trim().split(/\s+as\s+/).pop().split('.')[0]))
  }
  for (const m of code.matchAll(/^\s*from\s+[\w.]+\s+import\s+([\w, ]+?)\s*$/gm)) {
    m[1].split(',').forEach((part) => importedNames.push(part.trim().split(/\s+as\s+/).pop()))
  }
  // Count uses outside the import lines, so "from datetime import datetime" doesn't count as a use
  const codeWithoutImports = code.replace(/^\s*(?:import|from)\s.*$/gm, '')
  const unusedImports = [...new Set(importedNames.filter(Boolean))].filter(
    (name) => !new RegExp(`\\b${name}\\b`).test(codeWithoutImports)
  )

  // A variable is unused when every mention of it is an assignment (x = ..., self.x = ...)
  const assignedVariables = [...code.matchAll(/^\s*(?:const\s+|let\s+|var\s+)?([A-Za-z_]\w*)\s*=(?!=)/gm)].map((m) => m[1])
  const unusedVariables = [...new Set(assignedVariables)].filter(
    (name) => name !== '_' && countRefs(name) <= assignedVariables.filter((n) => n === name).length
  )

  const assignedAttributes = [...code.matchAll(/\b(?:self|this)\.(\w+)\s*=(?!=)/g)].map((m) => m[1])
  const unusedAttributes = [...new Set(assignedAttributes)].filter(
    (name) => (code.match(new RegExp(`\\.${name}\\b`, 'g')) || []).length <= assignedAttributes.filter((n) => n === name).length
  )

  return { unusedFunctions, unusedImports, unusedVariables, unusedAttributes }
}

function describeUnused(code) {
  const { unusedFunctions, unusedImports, unusedVariables, unusedAttributes } = findUnusedNames(code)
  return [
    unusedFunctions.length && `- Functions/methods never called: ${unusedFunctions.join(', ')}`,
    unusedImports.length && `- Imports never used: ${unusedImports.join(', ')}`,
    unusedVariables.length && `- Variables/constants assigned but never read: ${unusedVariables.join(', ')}`,
    unusedAttributes.length && `- Attributes assigned but never read: ${unusedAttributes.map((a) => `self.${a}`).join(', ')}`,
  ].filter(Boolean).join('\n')
}

const refactorPrompt = (code, language) => {
  const hints = describeUnused(code)

  return `You are a senior ${language} engineer. Refactor the code below.
${hints ? `\nA static scan already found these unused items. DELETE every one of them entirely (do not rename them):\n${hints}\n` : ''}
Rules:
1. Remove functions/methods/classes that are never called or used anywhere.
   Keep entry points: main(), constructors (e.g. __init__), code run at top level or under if __name__ == "__main__", and anything exported.
2. Remove duplicate functions (same name defined more than once, or the same logic written twice). Keep one version and update its callers.
3. Remove unused variables, unused parameters and unused imports.
4. Apply the standard ${language} naming convention to variables, functions, classes and constants
   (e.g. Python: snake_case functions/variables, PascalCase classes, UPPER_CASE constants; JavaScript/Java: camelCase, PascalCase classes).
   Replace unclear names (x, temp, data1, fn) with descriptive ones. Rename every usage consistently.
   Do NOT rename names that already follow the convention and are already descriptive.
5. Do NOT change what the code does. Do not add new features.
   Keep each function where it is: do not move functions into or out of classes.
6. The CHANGES list must describe only what you actually did in the refactored code.
   Never remove a parameter or variable that is read somewhere.
7. Add clear comments so a beginner can understand the code:
   - A short header comment at the top saying what the program does.
   - A docstring (Python) or doc comment (JavaScript/Java: /** ... */) on every class and function:
     what it does, its parameters and what it returns.
   - Short inline comments on lines whose purpose is not obvious (calculations, conditions, loops).
   Comments explain what the code does and why. Do not write comments about the refactoring itself
   (no "renamed from ..." or "removed ..."), and do not comment obvious lines like "x = 0".
8. If the code is already clean, only add the comments and write "- No changes needed besides comments" under CHANGES.
   Always include the REFACTORED CODE block.

Reply in exactly this format and nothing else:

## CHANGES
- <one line per change, e.g. "Removed unused function calc_tax()", "Renamed getData -> get_data">

## REFACTORED CODE
\`\`\`${language}
<the complete refactored code>
\`\`\`

CODE:
\`\`\`${language}
${code}
\`\`\``
}

const cleanupPrompt = (code, language, leftovers) => `This ${language} code still contains unused items:
${leftovers}

Delete each of them entirely (the definition, assignment or import line). If deleting one makes an import unused, delete that import too.
Change nothing else: keep every other name, line, comment and behaviour exactly as it is.

Reply in exactly this format and nothing else:

## CHANGES
- <one line per item removed>

## REFACTORED CODE
\`\`\`${language}
<the complete code>
\`\`\`

CODE:
\`\`\`${language}
${code}
\`\`\``

async function askMistralForRefactor(content) {
  const apiKey = process.env.MISTRAL_API_KEY

  if (!apiKey) {
    throw new Error('MISTRAL_API_KEY not configured')
  }

  const response = await fetch('https://api.mistral.ai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: 'ministral-8b-latest',
      messages: [{ role: 'user', content }],
      max_tokens: 4000,
      temperature: 0.1,
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || 'Mistral API error')
  }

  const data = await response.json()
  const text = (data.choices?.[0]?.message?.content || '').replace(/\r\n/g, '\n')
  const truncated = data.choices?.[0]?.finish_reason === 'length'

  // The code is after the "REFACTORED CODE" heading; fall back to the last fenced block anywhere
  const [changesSection, codeSection = ''] = text.split(/#*\s*\**REFACTORED CODE\**:?/i)
  const source = codeSection || text
  const blocks = [...source.matchAll(/```[^\n]*\n([\s\S]*?)(?:```|$)/g)]
  let refactored = blocks.length ? blocks[blocks.length - 1][1].trimEnd() : ''
  if (!refactored && codeSection.trim()) {
    refactored = codeSection.trim()   // model skipped the fences
  }
  if (!refactored) {
    console.error('Refactor reply had no code block. finish_reason:', data.choices?.[0]?.finish_reason, '\n', text.slice(0, 2000))
  }
  if (truncated) {
    throw new Error('The code is too long for one refactor (Mistral reply was cut off). Try a smaller piece of code.')
  }

  const changes = changesSection
    .split('\n')
    .filter((line) => /^\s*[-*]\s+/.test(line))
    .map((line) => line.replace(/^\s*[-*]\s+/, '').trim())

  return { refactored, changes }
}

async function refactorWithMistral(code, language) {
  const first = await askMistralForRefactor(refactorPrompt(code, language))

  if (!first.refactored) {
    throw new Error('Mistral did not return refactored code. Try again.')
  }

  // The small model often renames unused items instead of deleting them, so re-scan and clean up once
  const leftovers = describeUnused(first.refactored)
  if (!leftovers) {
    return first
  }

  const second = await askMistralForRefactor(cleanupPrompt(first.refactored, language, leftovers))
  if (!second.refactored) {
    return first
  }

  return { refactored: second.refactored, changes: [...first.changes, ...second.changes] }
}

async function analyzeWithClaude(code, language) {
  const message = await claudeClient.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 1500,
    messages: [
      {
        role: 'user',
        content: prompt(code, language),
      },
    ],
  })

  return message.content[0].type === 'text' ? message.content[0].text : ''
}

const structurePrompt = (code, language) => `Analyze this ${language.toUpperCase()} code and return ONLY valid JSON (no markdown, no explanation, start with { and end with }):

{
  "classes": [
    {
      "name": "ClassName",
      "functionCount": number,
      "functions": [
        {
          "name": "methodName",
          "loopCount": number,
          "description": "20-30 word description of what this function does"
        }
      ]
    }
  ],
  "functions": [
    {
      "name": "functionName",
      "loopCount": number,
      "description": "20-30 word description of what this function does"
    }
  ],
  "statistics": {
    "totalClasses": number,
    "totalFunctions": number,
    "totalLoops": number,
    "duplicateFunctions": [{"name": "functionName", "count": number}]
  },
  "summary": "100-120 word summary of the entire code purpose, architecture, and how components work together"
}

CODE:
\`\`\`${language}
${code}
\`\`\``

async function analyzeCodeStructureWithClaude(code, language) {
  try {
    const message = await claudeClient.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 2000,
      messages: [
        {
          role: 'user',
          content: structurePrompt(code, language),
        },
      ],
    })

    const text = message.content[0].type === 'text' ? message.content[0].text : '{}'
    try {
      return JSON.parse(text)
    } catch {
      return JSON.parse(text.replace(/```json\n?|\n?```/g, '').trim())
    }
  } catch (error) {
    console.log('Claude not available, trying Mistral...')
    return analyzeCodeStructureWithMistral(code, language)
  }
}

async function analyzeCodeStructureWithMistral(code, language) {
  const apiKey = process.env.MISTRAL_API_KEY
  if (!apiKey) {
    console.log('Mistral not configured, using regex fallback...')
    return analyzeCodeStructureWithRegex(code, language)
  }

  try {
    const response = await fetch('https://api.mistral.ai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: 'ministral-8b-latest',
        messages: [
          {
            role: 'user',
            content: structurePrompt(code, language),
          },
        ],
        max_tokens: 2000,
        temperature: 0.3,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      if (error.message?.includes('rate')) {
        console.log('Mistral rate limited, using regex fallback...')
        return analyzeCodeStructureWithRegex(code, language)
      }
      throw new Error(error.message || 'Mistral API error')
    }

    const data = await response.json()
    const text = data.choices[0].message.content
    try {
      return JSON.parse(text)
    } catch {
      return JSON.parse(text.replace(/```json\n?|\n?```/g, '').trim())
    }
  } catch (error) {
    console.log('Mistral error, falling back to regex:', error.message)
    return analyzeCodeStructureWithRegex(code, language)
  }
}

function analyzeCodeStructureWithRegex(code, language) {
  const classes = []
  const functions = []
  let totalLoops = 0

  const classRegex = /class\s+(\w+)/g
  const methodRegex = /def\s+(\w+)\s*\([^)]*\)/g
  const loopRegex = /for\s+\w+\s+in|while\s+/g
  const functionRegex = /^def\s+(\w+)\s*\(/gm

  let classMatch
  while ((classMatch = classRegex.exec(code)) !== null) {
    const className = classMatch[1]
    const classBody = code.substring(classMatch.index)
    const nextClass = classBody.search(/^class\s+\w+/m)
    const endIndex = nextClass > 0 ? classMatch.index + nextClass : code.length
    const classMethods = classBody.substring(0, endIndex - classMatch.index)

    const methods = []
    let methodMatch
    while ((methodMatch = methodRegex.exec(classMethods)) !== null) {
      const methodName = methodMatch[1]
      const methodBody = classMethods.substring(methodMatch.index)
      const nextMethod = methodBody.search(/\n\s{0,4}def\s+\w+/)
      const methodEnd = nextMethod > 0 ? methodMatch.index + nextMethod : methodBody.length
      const methodCode = methodBody.substring(0, methodEnd)

      const loopMatches = methodCode.match(loopRegex) || []
      methods.push({
        name: methodName,
        loopCount: loopMatches.length,
        description: `Method ${methodName} performs operations on the input parameters and returns a result.`,
      })
      totalLoops += loopMatches.length
    }

    if (methods.length > 0) {
      classes.push({
        name: className,
        functionCount: methods.length,
        functions: methods,
      })
    }
  }

  let funcMatch
  while ((funcMatch = functionRegex.exec(code)) !== null) {
    const funcName = funcMatch[1]
    if (!classes.some(cls => cls.functions.some(m => m.name === funcName))) {
      const funcBody = code.substring(funcMatch.index)
      const nextFunc = funcBody.search(/\n^def\s+\w+/)
      const funcEnd = nextFunc > 0 ? funcMatch.index + nextFunc : funcBody.length
      const funcCode = funcBody.substring(0, funcEnd)

      const loopMatches = funcCode.match(loopRegex) || []
      functions.push({
        name: funcName,
        loopCount: loopMatches.length,
        description: `Function ${funcName} processes input and returns computed results.`,
      })
      totalLoops += loopMatches.length
    }
  }

  return {
    classes,
    functions,
    statistics: {
      totalClasses: classes.length,
      totalFunctions: functions.length + classes.reduce((sum, c) => sum + c.functionCount, 0),
      totalLoops,
      duplicateFunctions: [],
    },
    summary: `This ${language} code contains ${classes.length} classes and ${functions.length} standalone functions. The classes define methods that handle various operations, while standalone functions provide utility functionality. There are ${totalLoops} loops total in the code, distributed across different methods and functions.`,
  }
}


async function analyzeWithMistral(code, language) {
  const apiKey = process.env.MISTRAL_API_KEY

  if (!apiKey) {
    throw new Error('MISTRAL_API_KEY not configured')
  }

  const response = await fetch('https://api.mistral.ai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: 'ministral-8b-latest',
      messages: [
        {
          role: 'user',
          content: prompt(code, language),
        },
      ],
      max_tokens: 1500,
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || 'Mistral API error')
  }

  const data = await response.json()
  return data.choices[0].message.content
}

async function analyzeWithGemini(code, language) {
  const apiKey = process.env.GOOGLE_API_KEY

  if (!apiKey) {
    throw new Error('GOOGLE_API_KEY not configured. Get one at https://aistudio.google.com/')
  }

  try {
    const response = await fetch(`${GEMINI_API_URL}?key=${apiKey}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: [
          {
            parts: [
              {
                text: prompt(code, language),
              },
            ],
          },
        ],
        generationConfig: {
          maxOutputTokens: 1000,
          temperature: 0.5,
        },
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      console.error('Gemini Error:', errorData)
      throw new Error(errorData.error?.message || `Gemini API error: ${response.status}`)
    }

    const data = await response.json()
    return data.candidates[0].content.parts[0].text
  } catch (error) {
    console.error('Gemini Analysis Error:', error)
    throw error
  }
}

async function analyzeWithGroq(code, language) {
  const apiKey = process.env.GROQ_API_KEY

  if (!apiKey) {
    throw new Error('GROQ_API_KEY not configured. Get one at https://console.groq.com/')
  }

  try {
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: 'llama-3.1-8b-instant',
        messages: [
          {
            role: 'user',
            content: prompt(code, language),
          },
        ],
        max_tokens: 1000,
        temperature: 0.5,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      console.error('GROQ Error:', errorData)

      if (response.status === 401) {
        throw new Error('Invalid GROQ API key. Check your .env.local file.')
      }
      if (response.status === 429) {
        throw new Error('GROQ rate limited. Try Claude or Mistral instead.')
      }

      throw new Error(errorData.error?.message || `GROQ API error: ${response.status}`)
    }

    const data = await response.json()
    return data.choices[0].message.content
  } catch (error) {
    console.error('GROQ Analysis Error:', error)
    throw error
  }
}

const graphPrompt = (code, language) => `You are a code analysis tool. First identify the programming language of the code
(a quick guess says "${language}", but trust the code itself). Then describe the code as a knowledge graph.

Return ONLY a JSON object with this shape:
{
  "language": "one of: python, javascript, typescript, java, c, cpp, csharp, go, rust, php, ruby, kotlin, swift, sql, html, css, bash, other",
  "nodes": [{"id": "unique_id", "label": "name shown on the graph", "type": "node type", "detail": "one short fact, e.g. '4 columns', '2 loops', 'returns the total'"}],
  "edges": [{"source": "node id", "target": "node id", "label": "relationship, e.g. contains, calls, reads, inserts into, inherits, imports"}],
  "stats": [{"label": "stat name", "value": 0}],
  "issues": [{"name": "the exact identifier from the code, e.g. saveToFile or path", "note": "the problem in a few words, e.g. never called, imported but never used, duplicate of calcFee"}],
  "summary": "80-100 words explaining what the code does, for a beginner"
}

Rules:
- Use the concepts that fit the language. Node types to use:
  Programming languages (Python, JavaScript, Java, C, Go, Rust, ...): file, class, function, method, import, constant
  SQL: file, table, view, cte, select, insert, update, delete, create (one node per statement, labelled like "INSERT customers")
  HTML: file, page, section, form, element, script, style
- Exactly one node has type "file": the whole code. Connect it to the top-level items with "contains".
- Add an edge for every real relationship: class contains method, function calls function,
  query reads table, insert/update/delete writes into a table, cte feeds a query.
- Every edge must use ids that exist in "nodes". At most 40 nodes.
- "stats": 3 to 6 counts that make sense for the language (SQL example: Tables, Columns, Rows inserted, Statements, Joins;
  Python example: Classes, Functions, Methods, Loops). Count exactly from the code.
- "issues": one entry per problem item: functions that are never called, unused imports/variables/constants/CTEs,
  duplicates. "name" is the identifier itself, never a category like "unused_import". Empty list if none.

CODE:
\`\`\`
${code}
\`\`\``

// The model's JSON can have dangling edges, duplicate ids or wrong types, so clean it before the UI sees it
function sanitizeGraph(raw) {
  const asText = (value, fallback = '') => (value === undefined || value === null ? fallback : String(value)).trim()

  const nodes = []
  const ids = new Set()
  for (const node of Array.isArray(raw?.nodes) ? raw.nodes : []) {
    const id = asText(node?.id)
    if (!id || ids.has(id)) continue
    ids.add(id)
    nodes.push({
      id,
      label: asText(node.label, id),
      type: asText(node.type, 'item').toLowerCase(),
      detail: asText(node.detail),
    })
    if (nodes.length >= 60) break
  }

  const edgeKeys = new Set()
  const edges = []
  for (const edge of Array.isArray(raw?.edges) ? raw.edges : []) {
    const source = asText(edge?.source)
    const target = asText(edge?.target)
    const key = `${source}->${target}`
    if (!ids.has(source) || !ids.has(target) || source === target || edgeKeys.has(key)) continue
    edgeKeys.add(key)
    edges.push({ source, target, label: asText(edge.label) })
  }

  const stats = (Array.isArray(raw?.stats) ? raw.stats : [])
    .map((s) => ({ label: asText(s?.label), value: Number(s?.value) }))
    .filter((s) => s.label && Number.isFinite(s.value))
    .slice(0, 6)

  // The model sometimes names an issue by its node id (e.g. "import_path"); show the node's label instead
  const labelById = new Map(nodes.map((n) => [n.id, n.label]))
  const issues = (Array.isArray(raw?.issues) ? raw.issues : [])
    .map((i) => ({ name: asText(i?.name), note: asText(i?.note) }))
    .map((i) => ({ ...i, name: labelById.get(i.name) || i.name }))
    .filter((i) => i.name)

  const language = asText(raw?.language).toLowerCase().replace(/[^a-z+#]/g, '')
  return { language: language || 'unknown', nodes, edges, stats, issues, summary: asText(raw?.summary) }
}

async function graphWithMistral(code, language) {
  const apiKey = process.env.MISTRAL_API_KEY

  if (!apiKey) {
    throw new Error('MISTRAL_API_KEY not configured')
  }

  const response = await fetch('https://api.mistral.ai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: 'ministral-8b-latest',
      messages: [{ role: 'user', content: graphPrompt(code, language) }],
      response_format: { type: 'json_object' },
      max_tokens: 4000,
      temperature: 0.1,
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || 'Mistral API error')
  }

  const data = await response.json()
  const text = data.choices?.[0]?.message?.content || ''
  let raw
  try {
    raw = JSON.parse(text)
  } catch {
    raw = JSON.parse(text.replace(/```json\n?|\n?```/g, '').trim())
  }

  const graph = sanitizeGraph(raw)
  if (graph.nodes.length === 0) {
    throw new Error('Mistral returned an empty graph')
  }
  graph.issues = mergeStaticIssues(graph.issues, code, graph.language)
  return graph
}

// The small model misses some unused items, so add whatever the static scan finds that it didn't mention.
// The scan only understands Python and JavaScript-style code.
function mergeStaticIssues(issues, code, language) {
  if (!['python', 'javascript', 'typescript'].includes(language)) return issues

  const { unusedFunctions, unusedImports, unusedVariables, unusedAttributes } = findUnusedNames(code)
  const found = [
    ...unusedFunctions.map((name) => ({ name, note: 'never called' })),
    ...unusedImports.map((name) => ({ name, note: 'imported but never used' })),
    ...unusedVariables.map((name) => ({ name, note: 'assigned but never used' })),
    ...unusedAttributes.map((name) => ({ name: `self.${name}`, note: 'assigned but never read' })),
  ]

  const mentioned = issues.map((i) => `${i.name} ${i.note}`)
  const isMentioned = (name) => {
    const bare = name.replace(/^self\./, '')
    return mentioned.some((text) => new RegExp(`\\b${bare}\\b`).test(text))
  }
  return [...issues, ...found.filter((issue) => !isMentioned(issue.name))]
}

const salahkarSystemPrompt = (code, language) => {
  // Same static scan as Refactor, so "remove unused code" requests don't depend on the model spotting everything
  const unused = ['python', 'javascript', 'typescript'].includes(language) ? describeUnused(code) : ''

  return `You are SALAHKAR, a friendly senior software engineer who refactors code on request.

The user's current ${language} code is:
\`\`\`
${code}
\`\`\`
${unused ? `\nA static scan found these unused items (use this if the user asks about unused code):\n${unused}\nIf you delete something, also delete anything that only it used, and never leave code that references a deleted name.\n` : ''}
How to reply:
- If the user asks for a change (refactor, rename, add comments, add error handling, optimise, convert, fix a bug...):
  1. Start with a short list of what you changed, one "- " bullet per change.
  2. Then give the COMPLETE updated code in exactly one fenced code block. Never give partial snippets or "..." placeholders.
- If the user only asks a question, answer briefly in plain words and do not include a code block.
- Make ONLY the changes the user asked for. Copy every other line exactly as it is: do not rewrite,
  restructure or modernise anything else (e.g. never change class syntax, loops or the program's output).
- Keep the existing behaviour unless the user asks to change it. Follow the language's naming conventions.
- Be concise.`
}

// Older replies already shaped the current code, so their code blocks are dropped to keep the prompt small
function trimChatHistory(messages) {
  return (Array.isArray(messages) ? messages : [])
    .filter((m) => (m?.role === 'user' || m?.role === 'assistant') && typeof m.content === 'string' && m.content.trim())
    .slice(-10)
    .map((m) => ({
      role: m.role,
      content: m.role === 'assistant' ? m.content.replace(/```[\s\S]*?(```|$)/g, '[updated code shown above]') : m.content,
    }))
}

async function chatWithSalahkar(code, language, messages) {
  const apiKey = process.env.MISTRAL_API_KEY

  if (!apiKey) {
    throw new Error('MISTRAL_API_KEY not configured')
  }

  const history = trimChatHistory(messages)
  if (history.length === 0 || history[history.length - 1].role !== 'user') {
    throw new Error('Type a message for SALAHKAR first')
  }

  const response = await fetch('https://api.mistral.ai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: 'ministral-8b-latest',
      messages: [{ role: 'system', content: salahkarSystemPrompt(code, language) }, ...history],
      max_tokens: 4000,
      temperature: 0.2,
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || 'Mistral API error')
  }

  const data = await response.json()
  const text = (data.choices?.[0]?.message?.content || '').replace(/\r\n/g, '\n')
  if (data.choices?.[0]?.finish_reason === 'length') {
    throw new Error('The reply was cut off because the code is too long. Try a smaller piece of code.')
  }

  // The last fenced block is the new code; everything else is the explanation
  const blocks = [...text.matchAll(/```[^\n]*\n([\s\S]*?)```/g)]
  const updatedCode = blocks.length ? blocks[blocks.length - 1][1].trimEnd() : ''
  const reply = text.replace(/```[^\n]*\n[\s\S]*?```/g, '').replace(/\n{3,}/g, '\n\n').trim()

  return { reply: reply || (updatedCode ? 'Here is the updated code.' : ''), code: updatedCode }
}

export async function POST(request) {
  try {
    const body = await request.json()
    const { code, language, aiModel, type } = body

    if (typeof code !== 'string' || !code || !language) {
      return Response.json(
        { error: 'Code and language are required' },
        { status: 400 }
      )
    }

    if (type === 'chat') {
      const { reply, code: updatedCode } = await chatWithSalahkar(code, language, body.messages)
      return Response.json({ success: true, reply, code: updatedCode })
    }

    if (type === 'graph') {
      const graph = await graphWithMistral(code, language)
      return Response.json({ success: true, graph, language })
    }

    if (type === 'refactor') {
      const { refactored, changes } = await refactorWithMistral(code, language)
      return Response.json({
        success: true,
        refactored,
        changes,
        language,
      })
    }

    if (type === 'structure') {
      const structure = await analyzeCodeStructureWithClaude(code, language)
      return Response.json({
        success: true,
        structure,
        language,
      })
    }

    let analysis = ''

    if (aiModel === 'gemini') {
      analysis = await analyzeWithGemini(code, language)
    } else if (aiModel === 'groq') {
      analysis = await analyzeWithGroq(code, language)
    } else if (aiModel === 'mistral') {
      analysis = await analyzeWithMistral(code, language)
    } else {
      analysis = await analyzeWithClaude(code, language)
    }

    return Response.json({
      success: true,
      analysis,
      language,
      aiModel,
    })
  } catch (error) {
    console.error('Analysis error:', error)
    return Response.json(
      { error: 'Failed to analyze code: ' + error.message },
      { status: 500 }
    )
  }
}
