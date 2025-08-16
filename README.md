# 🤖 commity

[![PyPI version](https://img.shields.io/pypi/v/commity.svg)](https://pypi.org/project/commity)
[![Python versions](https://img.shields.io/pypi/pyversions/commity.svg)](https://pypi.org/project/commity)
[![License](https://img.shields.io/pypi/l/commity.svg?cacheSeconds=0)](https://github.com/freboe/commity/blob/main/LICENSE)

[![English](https://img.shields.io/badge/Language-English-blue.svg)](https://github.com/freboe/commity/blob/main/README.md) | [![简体中文](https://img.shields.io/badge/Language-简体中文-blue.svg)](https://github.com/freboe/commity/blob/main/README.zh.md)

Generate intelligent Git commit messages with AI. Supports Conventional Commits, emoji, and multiple LLM providers like OpenAI, Ollama, and Gemini.

## 🤔 What is Commity?

**Commity** is an open-source, AI-powered Git commit message generation tool. It analyzes your staged code changes and automatically generates commit messages that follow the [**Conventional Commits**](https://www.conventionalcommits.org/) specification, and can even add emojis for you!

With a simple `commity --emoji` command, you can get a professional and clear commit message like this:

```
feat(api): ✨ add user authentication endpoint
```

## 🔧 Installation

Install with `pip`:

```bash
pip install commity
```

Or install with `uv`:

```bash
uv tool install commity
```

## ⚙️ Configuration

`commity` supports three configuration methods, with the following priority: **Command-line Arguments > Environment
Variables > Configuration File**.

Supported model providers are: `Gemini` (default), `Ollama`, `OpenAI`.

### ✨ Method 1: Specify Model Parameters via Command-line

#### OpenAI

```Bash
commity --provider openai --model gpt-3.5-turbo --api_key <your-api-key>
```

#### Ollama

```Bash
commity --provider ollama --model llama2 --base_url http://localhost:11434
```

#### Gemini

```Bash
commity --provider gemini --model gemini-2.5-flash --base_url https://generativelanguage.googleapis.com --api_key <your-api-key> --timeout 30
```

or

```Bash
commity \
--provider gemini \
--model gemini-2.5-flash \
--base_url https://generativelanguage.googleapis.com \
--api_key <your-api-key> \
--timeout 30 \
```

### 🌱 Method 2: Set Environment Variables as Defaults

You can add the following to your `.bashrc`, `.zshrc`, or `.env` file:

#### OpenAI

```Bash
export COMMITY_PROVIDER=openai
export COMMITY_MODEL=gpt-3.5-turbo
export COMMITY_API_KEY=your-api-key
```

#### Ollama

```Bash
export COMMITY_PROVIDER=ollama
export COMMITY_MODEL=llama2
export COMMITY_BASE_URL=http://localhost:11434
```

#### Gemini

```Bash
export COMMITY_PROVIDER=gemini
export COMMITY_MODEL=gemini-2.5-flash
export COMMITY_BASE_URL=https://generativelanguage.googleapis.com
export COMMITY_API_KEY=your-api-key
export COMMITY_TEMPERATURE=0.5
```

### 📝 Method 3: Use a Configuration File (Recommended)

For easier configuration management, you can create a `~/.commity/config.json` file in your user's home directory.

1. Create the directory:

   ```bash
   mkdir -p ~/.commity
   ```

2. Create and edit the `config.json` file:

   ```bash
   touch ~/.commity/config.json
   ```

3. Add your configuration to `config.json`, for example:

   ```json
   {
     "PROVIDER": "ollama",
     "MODEL": "llama3",
     "BASE_URL": "http://localhost:11434"
   }
   ```

   Or using Gemini:

   ```json
   {
     "PROVIDER": "gemini",
     "MODEL": "gemini-1.5-flash",
     "BASE_URL": "https://generativelanguage.googleapis.com",
     "API_KEY": "your-gemini-api-key"
   }
   ```

   Or using OpenAI:

   ```json
   {
     "PROVIDER": "openai",
     "MODEL": "gpt-3.5-turbo",
     "API_KEY": "your-openai-api-key"
   }
   ```

## 🚀 Usage

```Bash
# Run
commity

# View help
commity --help

# Use Chinese
commity --lang zh

# Include emojis
commity --emoji
