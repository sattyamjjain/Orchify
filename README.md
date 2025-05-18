# Orchify
[![PyPI version](https://img.shields.io/pypi/v/orchify.svg)](https://pypi.org/project/orchify) [![Python versions](https://img.shields.io/pypi/pyversions/orchify.svg)](https://pypi.org/project/orchify)

AI-driven Dockerfile, DevOps automation, and CI/CD orchestrator for **any** Python project.

---

## 🚀 Overview

Orchify (formerly Orchestron) is a command-line tool that uses AI agents (via Agno and the Model Context Protocol) to:

1. **Scan** a Python project and analyze its structure, dependencies, entrypoints, and infrastructure needs.
2. **Generate** production-grade, multi-stage **Dockerfiles**, **.dockerignore**, **Docker Compose**, **CI/CD workflows**, and other DevOps configurations—tailored to your project automatically.

Whether you’re containerizing microservices, setting up cloud deployments, or building full CI/CD pipelines, Orchify crafts best-practice infrastructure in seconds.

---

## 🔧 Features

- **Framework Agnostic**: Works with plain Python scripts, Flask, FastAPI, Django, AWS Lambdas, and more.
- **AI-Powered**: Leverages Anthropic Claude or OpenAI GPT models to write idiomatic DevOps artifacts.
- **Extensible**: Generates Dockerfiles, `docker-compose.yml`, GitHub Actions workflows, and can be extended for Terraform, Kubernetes, etc.
- **Token-Aware**: Dynamically selects models based on codebase size to avoid context limits.
- **Typed Manifest**: Produces a Pydantic-validated `orchify.json` as a single source of truth for your DevOps pipeline.
- **Logging & Debugging**: Built-in logging to trace scans and generations.

---

## 📦 Installation

```bash
pip install orchify
```

Or from source:

```bash
git clone https://github.com/sattyamjjain/Orchify.git
cd orchify
pip install -e .
```

---

## 🔨 Usage

Orchify CLI has three main commands:

### `hello`

A quick check:

```bash
orchify hello
# 👋 Welcome to Orchify!
```

### `scan`

Analyze and build `orchify.json` manifest:

```bash
orchify scan  --dir /path/to/your/project
```

**Options:**

- `-d, --dir` _path_: Project directory (default: current).
- `-p, --prompt` _text_: Custom AI prompt.

### `gen`

Generate DevOps artifacts from the manifest:

```bash
orchify gen   --model-id claude-3-7-sonnet-latest   --output ./Dockerfile
```

**Options:**

- `-m, --model-id` _model_: AI model.
- `-o, --output` _path_: Dockerfile path (default: `Dockerfile`).

---

## ⚙️ Configuration

Authenticate AI providers via environment variables:

| Variable            | Description                 |
|---------------------|-----------------------------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API token. |
| `OPENAI_API_KEY`    | OpenAI API key.             |

---

## 📄 Manifest Schema (`orchify.json`)

Orchify emits a Pydantic-validated manifest that includes:

- Project metadata (name, version, repo)
- Dependencies & install commands
- Source & entrypoint files
- Docker Compose service definitions
- CI/CD workflow settings
- Security scanning configs
- Notification hooks

Use this manifest to drive CI/CD or further automation.

---

## 🛠️ Development

```bash
pip install -e .
pytest tests/
flake8 orchify tests
black orchify tests
```

---

## 🤝 Contributing

Contributions welcome! Please fork, branch, and open a PR.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.