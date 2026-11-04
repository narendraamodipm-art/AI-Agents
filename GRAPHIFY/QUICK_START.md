# 🚀 GRAPHIFY Quick Start Guide

Get **GRAPHIFY** running in 3 minutes!

## 📋 Prerequisites

- **Node.js** 16 or higher ([Download](https://nodejs.org/))
- **npm** (comes with Node.js)

Check your versions:
```bash
node --version  # v16+
npm --version   # v7+
```

---

## ⚡ Installation & Setup

### Step 1: Navigate to GRAPHIFY
```bash
cd /Users/nkuma55/Documents/Practice/Multi-Agent/GRAPHIFY
```

### Step 2: Install Dependencies
```bash
npm install
```
This downloads all packages (~500MB). Takes 2-3 minutes.

### Step 3: Start Development Server
```bash
npm run dev
```

### Step 4: Open in Browser
Visit: **http://localhost:3000**

You should see the GRAPHIFY interface!

---

## ✅ Verify Installation

After running `npm run dev`, you should see:
```
> graphify@1.0.0 dev
> next dev

  ▲ Next.js 14.0.0
  - Local:        http://localhost:3000
```

If you see errors:
1. Check Node.js version: `node --version`
2. Delete `node_modules`: `rm -rf node_modules`
3. Reinstall: `npm install`
4. Restart: `npm run dev`

---

## 🎯 First Graph - Step by Step

### Step 1: Paste Sample Code
Copy this Python code:
```python
class DataAnalyzer:
    def __init__(self, data):
        self.data = data
    
    def analyze(self):
        return self.analyze_stats()
    
    def analyze_stats(self):
        return len(self.data)

import pandas as pd
from numpy import array
```

### Step 2: Select Language
Click the **Python** button

### Step 3: Paste Code
Paste the code into the text area on the left

### Step 4: Generate Graph
Click **"Generate Graph"** button

### Step 5: Explore!
You should see:
- ✅ Interactive graph on the right
- ✅ Statistics panel showing entities found
- ✅ Color-coded nodes for different types

---

## 🎨 Try Other Languages

### JavaScript Example
```javascript
class UserManager {
  constructor(users) {
    this.users = users;
  }

  getUser(id) {
    return this.users.find(u => u.id === id);
  }

  addUser(user) {
    this.users.push(user);
  }
}

import { useState } from 'react';
import axios from 'axios';
```

### Java Example
```java
package com.example.app;

import java.util.*;

public class Calculator {
  public int add(int a, int b) {
    return a + b;
  }

  public static void main(String[] args) {
    System.out.println("Ready");
  }
}
```

### HTML Example
```html
<!DOCTYPE html>
<html>
<head>
  <title>My Page</title>
</head>
<body>
  <div id="app">
    <h1 class="title">Hello World</h1>
    <p class="content">Welcome</p>
  </div>
</body>
</html>
```

---

## 🎮 Interactive Features

### Zoom & Pan
- **Scroll**: Zoom in/out
- **Click & Drag**: Pan around
- **Double Click**: Reset view

### Download Graph
- Click **"Download Graph"** button
- Saves as `graph-[language].json`
- Can be imported into other tools

### Copy Code
- Click **"Copy"** button
- Code copied to clipboard
- Useful for sharing

### Upload Files
- Click **"Upload File"** button
- Select `.py`, `.js`, `.java`, `.html`, `.rs` file
- Language auto-detected from file extension

---

## 📊 Understanding the Output

### Graph Visualization
- **Central Node** (top): Language indicator
- **Connected Nodes**: Extracted entities
- **Lines**: Relationships between entities
- **Colors**: Entity types

### Statistics Panel
Shows:
- **Language**: Detected language
- **Total Entities**: Number of items found
- **By Type**: Breakdown (classes, functions, imports, etc.)

### Entity Types by Language

**Python**
- 📦 Class
- ⚙️ Function
- 📥 Import

**JavaScript**
- 📦 Class
- ⚙️ Function
- 📥 Import

**Java**
- 📦 Class
- 🔧 Method
- 📥 Import

**HTML**
- 🏷️ Element
- 🎯 ID
- 🏷️ Class

**Rust**
- 🏗️ Struct
- ⚙️ Function
- 💻 Implementation

---

## ⚙️ Available Commands

```bash
# Development
npm run dev              # Start dev server on port 3000

# Production
npm run build           # Build optimized version
npm run start           # Start production server

# Quality
npm run lint            # Check code quality with ESLint
```

---

## 🐛 Troubleshooting

### Port 3000 Already in Use
```bash
# Use different port
npm run dev -- -p 3001
# Visit http://localhost:3001
```

### "Module not found" Error
```bash
# Clean reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Graph Not Generating
- Ensure code format matches language
- Check for syntax errors in code
- Try auto-detect feature
- Refresh browser

### Slow Performance
- Analyze smaller files
- Close browser tabs
- Check available RAM

---

## 📁 Project Structure

```
GRAPHIFY/
├── app/                    # Next.js app
│   ├── layout.jsx         # Root layout
│   ├── page.jsx           # Main page
│   └── globals.css        # Styles
├── components/            # React components
│   └── GraphVisualization.jsx
├── lib/                   # Utilities
│   ├── codeParser.js      # Parsers
│   └── graphUtils.js      # Graph gen
├── package.json
├── tailwind.config.js
├── postcss.config.js
└── next.config.js
```

---

## 🌐 Deployment

### Deploy to Vercel (1 Click)
1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import repository
4. Deploy!

### Deploy Anywhere
```bash
# Build
npm run build

# Run production
npm run start
```

---

## 💡 Pro Tips

✨ **Auto-Detect**: Use "Auto-Detect" button for automatic language detection

✨ **Upload Files**: Upload entire files instead of copy-pasting

✨ **Download**: Save graphs as JSON for later analysis

✨ **Multiple Languages**: Test with different programming languages

✨ **Share Results**: Download graph and share with team

---

## 📚 Learn More

- **Full Documentation**: See `README.md`
- **Code Analysis**: See `lib/codeParser.js`
- **Visualization**: See `components/GraphVisualization.jsx`

---

## 🎉 Next Steps

1. ✅ Run local version
2. ✅ Test with sample code
3. ✅ Try different languages
4. ✅ Download graph results
5. ✅ Deploy to production

---

## ❓ Need Help?

- Check browser console (F12) for errors
- Ensure code syntax is valid
- Try simpler code first
- Refresh the page

---

**Happy graphifying! 📊**

Questions? Check the full `README.md` for detailed information.
