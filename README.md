# Orchify
[![PyPI version](https://img.shields.io/pypi/v/orchify.svg)](https://pypi.org/project/orchify) [![Python versions](https://img.shields.io/pypi/pyversions/orchify.svg)](https://pypi.org/project/orchify)

AI-driven Dockerfile and .dockerignore generator for **any** Python project.

---

## 🚀 Overview

Orchify is a command-line tool that uses AI agents (via Agno and the Model Context Protocol) to:

1. **Scan** a Python project and analyze its structure, dependencies, and entrypoints.
2. **Generate** a production-grade, multi-stage **Dockerfile** and corresponding **.dockerignore**—tailored to the project—without manual template editing.

Whether you're containerizing a microservice, a Flask app, or a complex multi-package repository, Orchify will craft best-practice container configurations in seconds.

---

## 🔧 Features

- **Framework Agnostic**: Works with plain Python scripts, Flask, FastAPI, Django, and more.
- **AI-Powered**: Leverages Anthropic Claude or OpenAI GPT models to write idiomatic Dockerfiles.
- **Two-Step Workflow**: `scan` → `gen` for clear separation of analysis and generation.
- **Production-Ready**: Generates multi-stage builds, non-root users, cache optimizations.
- **Customizable**: Override prompts, model choices, output paths via CLI flags.

---

## 📦 Installation

```bash
pip install orchify
```

Or from source:

```bash
git clone https://github.com/yourusername/Orchify.git
cd Orchify
docker run -it --rm \
  -v "$PWD":/workspace \
  python:3.11-slim bash -c "pip install -e ."
```

---

## 🔨 Usage

Orchify exposes three primary commands via the `orchify` CLI:

### 1. `hello`

A sanity-check command:

```bash
orchify hello
# 👋 Welcome to Orchify!
```

### 2. `scan`

Analyze your project and write out `orchify.json` metadata.

```bash
orchify scan \
  --dir /path/to/your/project \
  --prompt "Summarize my project for Dockerfile generation"
```

**Options:**

- `-d, --dir` <path>: Project directory (default: current directory).
- `-p, --prompt` <text>: Custom AI analysis prompt.

### 3. `gen`

Generate `Dockerfile` and `.dockerignore` based on the scan metadata.

```bash
orchify gen \
  --model-id claude-3-7-sonnet-latest \
  --output Dockerfile
```

**Options:**

- `-m, --model-id` <model>: Anthropic/OpenAI model to use.
- `-o, --output` <path>: Path for the generated Dockerfile (default: `Dockerfile`).

---

## ⚙️ Configuration

Orchify uses environment variables to authenticate with AI providers:

| Variable             | Description                      |
|----------------------|----------------------------------|
| `ANTHROPIC_API_KEY`  | Your Anthropic Claude API token. |
| `OPENAI_API_KEY`     | Your OpenAI API key (optional).  |

Set them in your shell or `.env` before running commands.

---

## 🛠️ Development

From your dev clone:

```bash
# Install editable
pip install -e .

# Run tests
pytest tests/

# Lint & format
flake8 orchify tests
black orchify tests
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repo.
2. Create a feature branch: `git checkout -b feature/awesome`.
3. Commit your changes and push.
4. Open a Pull Request.

Please adhere to the existing code style and add tests for any new functionality.

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.