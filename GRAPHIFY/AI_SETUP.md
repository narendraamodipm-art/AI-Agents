# 🧠 AI Code Analysis Setup Guide

GRAPHIFY now includes **AI-powered code architecture analysis** using Claude or Mistral to explain code to beginners!

---

## ✨ What AI Analysis Does

When you click **"Analyze Architecture"**, the AI:

1. **Reads Your Code** - Analyzes the structure and logic
2. **Explains Simply** - Uses beginner-friendly language
3. **Breaks Down Components** - Lists each class/function/table
4. **Shows Relationships** - Explains how parts work together
5. **Provides Examples** - Uses real-world analogies
6. **Walks Through Flow** - Step-by-step execution explanation

### Example Output:

```
📝 What This Code Does
├─ A simple data manager that stores and retrieves user information
├─ Like a digital address book that you can search and update
└─ Perfect for beginners learning object-oriented programming

📦 Main Components
├─ UserManager class: The main container for all operations
├─ add_user() function: Adds a new person to the system
├─ get_user() function: Finds and returns a specific person
└─ delete_user() function: Removes a person from the system

🔗 How They Work Together
├─ User Manager stores all users in a list
├─ When you ask for a user, it searches through the list
├─ It returns the matching user or says "not found"
└─ All operations modify the central user list

⏭️ Step-by-Step Flow
├─ Step 1: Create a UserManager with empty list
├─ Step 2: Call add_user() to add someone
├─ Step 3: Call get_user() to retrieve them
├─ Step 4: Call delete_user() to remove them
└─ Step 5: List is updated each time

... and more!
```

---

## 🚀 Setup (Choose One)

### Option 1: Use Claude (Recommended for Beginners)

#### Step 1: Get Claude API Key

1. Visit: **https://console.anthropic.com/**
2. Sign up or log in
3. Click **"API Keys"**
4. Create a new API key
5. Copy the key

#### Step 2: Set Environment Variable

Create a `.env.local` file in your GRAPHIFY folder:

```bash
# .env.local
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
```

Or set via command line:
```bash
export ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
```

#### Step 3: Restart GRAPHIFY

```bash
npm run dev
```

✅ Claude is now ready!

---

### Option 2: Use Mistral (Free Alternative)

#### Step 1: Get Mistral API Key

1. Visit: **https://console.mistral.ai/**
2. Sign up or log in
3. Go to **"API Keys"**
4. Create a new API key
5. Copy the key

#### Step 2: Set Environment Variable

Add to `.env.local`:

```bash
# .env.local
MISTRAL_API_KEY=your_mistral_key_here
```

Or:
```bash
export MISTRAL_API_KEY=your_mistral_key_here
```

#### Step 3: Restart GRAPHIFY

```bash
npm run dev
```

✅ Mistral is now ready!

---

## 💻 How to Use

### 1. **Select AI Model**
   - Click **✨ Claude** or **🚀 Mistral** button
   - Choose based on which API key you configured

### 2. **Paste or Upload Code**
   - Paste code directly OR
   - Upload a file (.py, .js, .java, etc.)

### 3. **Select Language**
   - Click language button (Python, JavaScript, Java, etc.)

### 4. **Click "Analyze Architecture"**
   - Wait for AI to process (5-15 seconds)
   - Read the detailed explanation!

### 5. **Copy or Share**
   - Use the "Copy" button to save analysis
   - Share with beginners or teammates

---

## 🎯 Example: Python Analysis

### Input Code:
```python
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, x):
        self.result += x
        return self.result
    
    def subtract(self, x):
        self.result -= x
        return self.result

calc = Calculator()
print(calc.add(5))      # 5
print(calc.subtract(2)) # 3
```

### AI Output (Simplified):
```
📝 What This Code Does
Like a calculator app that remembers the answer.
Each time you add or subtract, it remembers the new total.

📦 Main Components
- Calculator class: The main calculator
- add(): Adds numbers and updates total
- subtract(): Subtracts numbers and updates total
- result: Stores the current number

🔗 How They Work Together
1. Calculator starts with result = 0
2. When add(5) is called, result becomes 5
3. When subtract(2) is called, result becomes 3
4. The result stays in memory for next operation

⏭️ Step-by-Step Flow
Step 1: Create calc = Calculator() → result starts at 0
Step 2: calc.add(5) → adds 5 → result = 5
Step 3: calc.subtract(2) → subtracts 2 → result = 3
Result is shown each time

🌍 Real-World Analogy
Like a cash register:
- Start with $0
- Add cash → Total increases
- Subtract change → Total decreases
- Register remembers the total between transactions

📚 Key Concepts
- Class: A blueprint for creating objects
- Method: A function inside a class
- self: Refers to the current object
- __init__: Special method that runs when object is created
```

---

## 🔄 Comparing Claude vs Mistral

| Feature | Claude | Mistral |
|---------|--------|---------|
| **Explanations** | Very detailed | Clear & concise |
| **Speed** | 5-10 seconds | 3-7 seconds |
| **Beginner-Friendly** | Excellent | Good |
| **Cost** | Pay per API call | Pay per API call |
| **Free Trial** | Limited credits | Limited credits |

**Recommendation**: Start with Claude for best explanations!

---

## ⚙️ Troubleshooting

### "API Key Not Found"
```
Error: ANTHROPIC_API_KEY not configured
```
**Solution:**
1. Check `.env.local` file exists
2. Verify API key is correct (no spaces)
3. Restart the dev server
4. Check you're using the right provider

### "API Rate Limit"
```
Error: Rate limit exceeded
```
**Solution:**
- Wait a few seconds before next analysis
- Upgrade your API plan

### "Code Not Analyzing"
```
Error: Failed to analyze code
```
**Solution:**
1. Ensure code is pasted (not empty)
2. Check code syntax is valid
3. Ensure API key is valid
4. Try simpler code first

### "Slow Response"
- Claude is usually slower (5-10s)
- Mistral is faster (3-7s)
- Switch between models to test

---

## 📊 Cost & Usage

### Claude Pricing (Sonnet model)
- **Input**: $3 per 1M tokens
- **Output**: $15 per 1M tokens
- Analyzing 100 lines = ~1,000 tokens
- **Cost**: ~$0.005 per analysis

### Mistral Pricing (Medium model)
- **Input**: $2.70 per 1M tokens
- **Output**: $8.10 per 1M tokens
- **Cost**: ~$0.003 per analysis

### Free Options
- Claude: $5 free trial credit
- Mistral: Free tier available

---

## 🎓 For Beginners

### Start With:
1. **Small Python code** (5-10 lines)
2. **Simple classes** (Calculator, Person, etc.)
3. **Basic functions** (add, multiply, etc.)

### Then Try:
1. **JavaScript classes**
2. **Java methods**
3. **SQL queries**
4. **HTML structure**

### Advanced:
1. **Complex architectures**
2. **Multi-file projects**
3. **Design patterns**

---

## 🚀 Getting Started

```bash
# 1. Create .env.local
cp .env.example .env.local

# 2. Add your API key to .env.local
# ANTHROPIC_API_KEY=sk-ant-xxxxx
# or
# MISTRAL_API_KEY=xxxxx

# 3. Restart dev server
npm run dev

# 4. Go to http://localhost:3000

# 5. Select AI model and paste code

# 6. Click "Analyze Architecture"

# 7. Read the AI explanation!
```

---

## 📚 Learn More

- **Claude API**: https://docs.anthropic.com/
- **Mistral API**: https://docs.mistral.ai/
- **GRAPHIFY README**: See README.md

---

## ✨ Features

✅ Claude AI explanations  
✅ Mistral AI alternative  
✅ Beginner-friendly output  
✅ Step-by-step walkthroughs  
✅ Real-world analogies  
✅ Copy analysis to clipboard  
✅ Works with all supported languages  
✅ No code changes needed - just paste!  

---

**Ready to analyze code with AI?** 🧠✨

Set up your API key and start learning!
