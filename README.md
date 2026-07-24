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

Supported model providers are: `Gemini` (default), `Ollama`, `OpenAI`, `OpenRouter`, `NVIDIA`.
> Gemini, OpenAI, OpenRouter, and NVIDIA always require an API key. Commity aborts early if those keys are missing so you get fast feedback before hitting the network.

Model repository tools are disabled by default. Set `ALLOW_TOOLS` to `true` to let a
tool-capable provider inspect staged changes, commit history, and tracked files. If
`ALLOWED_TOOLS` is omitted, every built-in read-only tool is available. Valid names are
`get_staged_summary`, `get_staged_diff`, `list_recent_commits`, `get_commit`, and `read_file`.

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

#### OpenRouter

```Bash
commity --provider openrouter --model openai/gpt-3.5-turbo --api_key <your-openrouter-api-key>
```

or

```Bash
commity \
--provider openrouter \
--model anthropic/claude-3.5-sonnet \
--api_key <your-openrouter-api-key> \
```

#### NVIDIA

```Bash
commity --provider nvidia --model nvidia/llama-3.1-70b-instruct --api_key <your-nvidia-api-key>
```

or

```Bash
commity \
--provider nvidia \
--model nvidia/llama-3.1-nemotron-70b-instruct \
--api_key <your-nvidia-api-key> \
```

### 🌱 Method 2: Set Environment Variables as Defaults

You can add the following to your `.bashrc`, `.zshrc`, or `.env` file:

```Bash
export COMMITY_ALLOW_TOOLS=true
export COMMITY_ALLOWED_TOOLS=get_staged_diff,read_file
```

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

#### OpenRouter

```Bash
export COMMITY_PROVIDER=openrouter
export COMMITY_MODEL=openai/gpt-3.5-turbo
export COMMITY_API_KEY=your-openrouter-api-key
export COMMITY_TEMPERATURE=0.5
```

#### NVIDIA

```Bash
export COMMITY_PROVIDER=nvidia
export COMMITY_MODEL=nvidia/llama-3.1-70b-instruct
export COMMITY_API_KEY=your-nvidia-api-key
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
     "API_KEY": "your-openai-api-key",
     "ALLOW_TOOLS": true,
     "ALLOWED_TOOLS": ["get_staged_diff", "read_file"]
   }
   ```

   Or using OpenRouter:

   ```json
   {
     "PROVIDER": "openrouter",
     "MODEL": "openai/gpt-3.5-turbo",
     "API_KEY": "your-openrouter-api-key"
   }
   ```

   Or using NVIDIA:

   ```json
   {
     "PROVIDER": "nvidia",
     "MODEL": "nvidia/llama-3.1-70b-instruct",
     "API_KEY": "your-nvidia-api-key"
   }
   ```

## 🚀 Usage

```Bash
# Run
commity

# View help
commity --help

# Use Chinese (--lang is kept as an alias)
commity --language zh

# Include emojis
commity --emoji

# Override the model context window for smaller local models
commity --context_window_tokens 8192

# Show token budgeting, compression, and change-group diagnostics
commity --debug

# Allow all read-only repository tools (OpenAI provider)
commity --provider openai --api_key <your-api-key> --allow_tools

# Allow only selected repository tools
commity --provider openai --api_key <your-api-key> \
  --allow_tools --allowed_tools get_staged_diff read_file

# Use OpenRouter with specific model
commity --provider openrouter --model anthropic/claude-3.5-sonnet --api_key <your-openrouter-api-key>

# Use OpenRouter with emoji support
commity --provider openrouter --model openai/gpt-4o --api_key <your-openrouter-api-key> --emoji

# Use NVIDIA with specific model
commity --provider nvidia --model nvidia/llama-3.1-70b-instruct --api_key <your-nvidia-api-key>

# Use NVIDIA with emoji support
commity --provider nvidia --model nvidia/llama-3.1-nemotron-70b-instruct --api_key <your-nvidia-api-key> --emoji

# Skip interactive confirmation and commit immediately
commity --confirm n

# Run via Python module entry point
python -m commity --language zh --emoji
```

In interactive mode, choose `c` to commit, `e` to edit the generated
message in your Git editor, `r` to regenerate it with optional guidance,
or `n` to cancel. Commity uses the repository description, recent commit
subjects, and staged-file metadata to improve the generated message.
When code, build, CI, and documentation changes appear independently,
Commity warns before generating one combined message.
