# 📊 GRAPHIFY - Code to Knowledge Graph Visualizer

Transform your code into beautiful, interactive knowledge graphs! **GRAPHIFY** analyzes source code and creates stunning visual representations of classes, functions, imports, and their relationships.

## 🎯 Features

✨ **Multi-Language Support**
- 🐍 Python
- ⚡ JavaScript / TypeScript
- ☕ Java
- 🌐 HTML
- 🦀 Rust
- 🎯 Holand (custom language support)

✨ **Powerful Analysis**
- Extract classes, functions, methods, imports
- Analyze code structure and entities
- Auto-detect programming language
- Generate statistics and metrics

✨ **Beautiful Visualization**
- Interactive React Flow graphs
- Zoom, pan, and drag to explore
- Color-coded by entity type
- Real-time updates

✨ **Developer Friendly**
- Upload files or paste code
- Download graph as JSON
- Copy code to clipboard
- Responsive design

---

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- npm or yarn

### Installation

```bash
# Clone or navigate to GRAPHIFY
cd GRAPHIFY

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit **http://localhost:3000** in your browser

---

## 💻 Usage

### 1. **Select Language**
Click on one of the language buttons or use "Auto-Detect" to automatically identify the language.

### 2. **Input Code**
- **Paste Code**: Directly paste your code in the text area
- **Upload File**: Upload a `.py`, `.js`, `.java`, `.html`, `.rs`, or `.hol` file

### 3. **Generate Graph**
Click "Generate Graph" to analyze and visualize your code.

### 4. **Explore**
- **Zoom**: Use mouse wheel or zoom controls
- **Pan**: Click and drag to move around
- **Statistics**: View code metrics on the right panel
- **Download**: Export the graph as JSON

---

## 📐 Architecture

```
GRAPHIFY/
├── app/
│   ├── layout.jsx          # Root layout
│   ├── page.jsx            # Main page (UI & state)
│   └── globals.css         # Global styles
│
├── components/
│   └── GraphVisualization.jsx  # React Flow graph
│
├── lib/
│   ├── codeParser.js       # Language parsers
│   └── graphUtils.js       # Graph generation
│
├── package.json
├── tailwind.config.js
├── postcss.config.js
├── next.config.js
├── jsconfig.json
└── README.md
```

---

## 🔧 How It Works

### Code Parsing Pipeline

```
User Input (Code)
    ↓
Language Detection (auto or manual)
    ↓
Language-Specific Parser
    ↓
Extract Entities (classes, functions, imports, etc.)
    ↓
Generate Graph Nodes & Edges
    ↓
React Flow Visualization
    ↓
Display with Statistics
```

### Supported Entities by Language

**Python**
- Classes (with inheritance)
- Functions & Methods
- Imports & Modules

**JavaScript**
- Classes (with extends)
- Functions & Arrow Functions
- Imports & Exports

**Java**
- Classes & Interfaces
- Methods & Constructors
- Package Imports

**HTML**
- HTML Elements (tags)
- IDs (selectors)
- Classes

**Rust**
- Structs & Enums
- Functions
- Implementations
- Use statements

**Holand**
- Programs
- Procedures
- Variables

---

## 🎨 Visual Design

### Color Scheme
- **Background**: Dark gradient (slate-950 to slate-900)
- **Primary**: Indigo (#6366f1)
- **Accent**: Pink (#ec4899), Cyan (#06b6d4)
- **Language Colors**:
  - Python: Blue (#3776ab)
  - JavaScript: Yellow (#f1e05a)
  - Java: Blue (#007396)
  - HTML: Orange (#e34c26)
  - Rust: Red (#ce422b)

### Entity Type Colors
- **Classes**: Pink (#ec4899)
- **Functions**: Cyan (#06b6d4)
- **Methods**: Amber (#f59e0b)
- **Imports**: Purple (#8b5cf6)
- **Structs**: Green (#10b981)
- **Variables**: Cyan (#0891b2)

---

## 📊 Code Parsing Examples

### Python

```python
class DataProcessor:
    def __init__(self, data):
        self.data = data
    
    def process(self):
        return self.data.upper()

import pandas as pd
from sklearn.model_selection import train_test_split
```

**Extracted Entities:**
- Class: `DataProcessor`
- Function: `__init__`, `process`
- Import: `pandas`, `sklearn.model_selection`

### JavaScript

```javascript
class APIClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  async fetchData(endpoint) {
    return await fetch(this.baseURL + endpoint);
  }
}

import { useState } from 'react';
```

**Extracted Entities:**
- Class: `APIClient`
- Function: `constructor`, `fetchData`
- Import: `react`

---

## 🔍 Statistics & Metrics

After analyzing code, you get:
- **Total Entities**: Number of extracted items
- **By Type**: Breakdown by entity type (classes, functions, imports, etc.)
- **Language**: Detected/selected language
- **Complexity**: Visual representation of code structure

---

## 📱 Responsive Design

- ✅ Desktop (1920px+)
- ✅ Laptop (1024px+)
- ✅ Tablet (768px+)
- ✅ Mobile (responsive layout)

---

## 🛠️ Technology Stack

| Technology | Purpose |
|-----------|---------|
| **Next.js 14** | React framework |
| **React 18** | UI library |
| **React Flow** | Graph visualization |
| **Tailwind CSS 3** | Styling |
| **Lucide React** | Icons |
| **Zustand** | State management |

---

## 📦 Deployment

### Vercel (Recommended)
```bash
# Push to GitHub
git push origin main

# Connect to Vercel
# Automatic deployment on push
```

### Docker
```bash
docker build -t graphify .
docker run -p 3000:3000 graphify
```

### Self-Hosted
```bash
npm run build
npm run start
```

---

## 🎓 Code Quality

- ✅ Modular architecture
- ✅ Clean separation of concerns
- ✅ Reusable components
- ✅ Type-safe patterns
- ✅ Responsive design
- ✅ Accessible UI

---

## 🚀 Future Enhancements

- [ ] Support for more languages (Go, Python async, Ruby, PHP)
- [ ] Graph export formats (SVG, PNG, XML)
- [ ] Dependency analysis
- [ ] Code metrics dashboard
- [ ] Dark/light theme toggle
- [ ] Real-time collaboration
- [ ] Browser storage for recent graphs
- [ ] Custom graph layouts

---

## 🐛 Troubleshooting

### "No entities found"
- Check that code format matches selected language
- Ensure proper syntax in the code
- Try auto-detect feature

### Graph not rendering
- Refresh the page
- Check browser console for errors
- Ensure sufficient code for analysis

### Performance issues
- Analyze smaller code files
- Use simpler language parser
- Check system resources

---

## 📝 License

MIT - Feel free to use and modify!

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Add new language parsers
- Improve visualization
- Fix bugs
- Add features

---

## 📞 Support

- 📖 Read documentation
- 💬 Check examples
- 🐛 Report issues

---

## 🎉 Getting Started

```bash
# 1. Install dependencies
npm install

# 2. Start dev server
npm run dev

# 3. Open http://localhost:3000

# 4. Paste code and click "Generate Graph"

# Happy graphifying! 📊
```

---

**Made with ❤️ using Next.js + React Flow + Tailwind CSS**

*Transform your code into beautiful knowledge graphs!*
