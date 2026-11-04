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

    if (!code || !language) {
      return Response.json(
        { error: 'Code and language are required' },
        { status: 400 }
      )
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
