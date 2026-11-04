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

function findUnusedNames(code) {
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
7. If the code is already clean, return it unchanged and write "- No changes needed" under CHANGES.
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
Change nothing else: keep every other name, line and behaviour exactly as it is.

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
