# 🧠 GitIntel

> **Understand any GitHub repo's Issues and PRs instantly — including hidden discussion context and maintainer decisions.**

GitIntel is a context-aware intelligence engine designed to turn messy GitHub issue threads into structured, LLM-ready digests. It's built for contributors who need to understand a codebase's current challenges, constraints, and solved problems without digging through hundreds of comments manually.

---

## ✨ Features

- **💡 Context-Aware Ingestion**: Unlike Gitingest which captures files, GitIntel captures **intelligence**. It extracts the "why" from Issue and PR discussions.
- **🧠 AI Summarization**: Automatically extracts core architecture status, key maintainer decisions, and technical constraints using GPT-4o.
- **🔍 Neo-Brutalism Dashboard**: A premium, high-contrast UI inspired by Gitingest but with a fresh "Intel" lavender palette.
- **📦 LLM-Ready Exports**: One-click copy or download of a single text file containing all analyzed context.
- **🚀 GraphQL Powered**: Fetches data efficiently, including nested review comments and timeline events.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (Tested on 3.13)
- A GitHub Personal Access Token (PAT)
- An OpenAI API Key (optional, for intelligence summaries)

### 2. Installation

Clone the repository and install dependencies using a virtual environment:

```bash
git clone https://github.com/amaydixit11/GitIntel.git
cd GitIntel

# Create and activate venv
python -m venv venv
source venv/bin/activate  # On Linux/MacOS

# Build for Python 3.13 compatibility
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory:

```env
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Running the Server

```bash
python src/server/main.py
```

The app will be available at: `http://localhost:8000`

---

## 🎨 Design Philosophy

GitIntel uses a **Neo-Brutalism** design system:
- **Thick black borders** and playful box-shadows.
- **Lavender & Cyan** accent colors.
- **Interactive sparkles** for a modern, energetic feel.
- High-contrast typography using **Space Grotesk** and **Space Mono**.

---

## 🤝 Contributing

Contributions are welcome! If you have ideas for better extraction filters (e.g., AST-based code mapping), feel free to open an issue or PR.

## 📄 License

This project is licensed under the MIT License.
