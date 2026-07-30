# 🤖 commity

[![PyPI version](https://img.shields.io/pypi/v/commity.svg)](https://pypi.org/project/commity)
[![Python versions](https://img.shields.io/pypi/pyversions/commity.svg)](https://pypi.org/project/commity)
[![License](https://img.shields.io/pypi/l/commity.svg?cacheSeconds=0)](https://github.com/freboe/commity/blob/main/LICENSE)

[![English](https://img.shields.io/badge/Language-English-blue.svg)](https://github.com/freboe/commity/blob/main/README.md) | [![简体中文](https://img.shields.io/badge/Language-简体中文-blue.svg)](https://github.com/freboe/commity/blob/main/README.zh.md)

使用 AI 生成智能 Git 提交信息。支持 Conventional Commits 格式、emoji 插入，并可选用 OpenAI、Ollama、Gemini 等多种大语言模型。

## 🤔 什么是 Commity？

**Commity** 是一款开源的、基于 AI 的 Git commit message 生成工具。它能够分析你暂存区的代码变更，并自动生成符合[**Conventional Commits**](https://www.conventionalcommits.org/) 规范的提交信息，甚至还能为你加上可爱的 emoji！

只需一个简单的 `commity --emoji` 命令，你就能得到像这样专业而清晰的 commit message：

```
feat(api): ✨ add user authentication endpoint
```

## 🔧 安装

使用 `pip` 安装:

```bash
pip install commity
```

或者使用 `uv` 安装:

```bash
uv tool install commity
```

## ⚙️ 配置

`commity` 支持通过三种方式进行配置，优先级从高到低依次为：**命令行参数 > 环境变量 > 配置文件**。

支持的模型提供商有：`Gemini` (默认)、`Ollama`、`OpenAI`、`OpenRouter`、`NVIDIA`。
> 使用 Gemini、OpenAI、OpenRouter、NVIDIA 时必须提供 API Key，Commity 会在请求前校验，缺失时立即终止以便快速发现问题。

模型仓库工具默认关闭。将 `ALLOW_TOOLS` 设为 `true` 后，支持工具调用的 provider
可以读取暂存变更、提交历史和 tracked 文件。未配置 `ALLOWED_TOOLS` 时允许使用全部
内置只读工具。有效名称为 `get_staged_summary`、`get_staged_diff`、
`list_recent_commits`、`get_commit` 和 `read_file`。

### ✨ 方法一：运行命令时指定模型参数

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
--timeout 30
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
--api_key <your-openrouter-api-key>
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
--api_key <your-nvidia-api-key>
```

### 🌱 方法二：设置环境变量作为默认值

你可以在 `.bashrc`、`.zshrc` 或 `.env` 文件中添加：

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

### 📝 方法三：使用配置文件（推荐）

为了更方便地管理配置，可以在用户主目录下创建 `~/.commity/config.jsonc` 或
`~/.commity/config.json`。JSONC 支持行注释、块注释和尾逗号；两者同时存在时，
优先读取 `config.jsonc`。

1. 创建目录：

   ```bash
   mkdir -p ~/.commity
   ```

2. 创建并编辑 `config.jsonc` 文件：

   ```bash
   touch ~/.commity/config.jsonc
   ```

3. 在 `config.jsonc` 中添加你的配置，例如：

   ```json
   {
     "PROVIDER": "ollama",
     "MODEL": "llama3",
     "BASE_URL": "http://localhost:11434",
     "MAX_ATTEMPTS": 3
   }
   ```

   或者使用 Gemini：

   ```json
   {
     "PROVIDER": "gemini",
     "MODEL": "gemini-1.5-flash",
     "BASE_URL": "https://generativelanguage.googleapis.com",
     "API_KEY": "your-gemini-api-key"
   }
   ```

   或者使用 OpenAI：

   ```json
   {
     "PROVIDER": "openai",
     "MODEL": "gpt-3.5-turbo",
     "API_KEY": "your-openai-api-key",
     "ALLOW_TOOLS": true,
     "ALLOWED_TOOLS": ["get_staged_diff", "read_file"]
   }
   ```

   或者使用 OpenRouter：

   ```json
   {
     "PROVIDER": "openrouter",
     "MODEL": "openai/gpt-3.5-turbo",
     "API_KEY": "your-openrouter-api-key"
   }
   ```

   或者使用 NVIDIA：

   ```json
   {
     "PROVIDER": "nvidia",
     "MODEL": "nvidia/llama-3.1-70b-instruct",
     "API_KEY": "your-nvidia-api-key"
   }
   ```

## 🚀 使用

```Bash
commity

# 查看帮助
commity --help

# 使用中文（`--lang` 仍可作为别名）
commity --language zh

# 包含 emoji
commity --emoji

# 为上下文较小的本地模型指定上下文窗口
commity --context_window_tokens 8192

# 显示 token 预算、压缩和变更分组诊断
commity --debug

# 允许全部只读仓库工具（OpenAI provider）
commity --provider openai --api_key <your-api-key> --allow_tools

# 只允许指定仓库工具
commity --provider openai --api_key <your-api-key> \
  --allow_tools --allowed_tools get_staged_diff read_file

# 使用 OpenRouter 指定模型
commity --provider openrouter --model anthropic/claude-3.5-sonnet --api_key <your-openrouter-api-key>

# 使用 OpenRouter 并包含 emoji
commity --provider openrouter --model openai/gpt-4o --api_key <your-openrouter-api-key> --emoji

# 使用 NVIDIA 指定模型
commity --provider nvidia --model nvidia/llama-3.1-70b-instruct --api_key <your-nvidia-api-key>

# 使用 NVIDIA 并包含 emoji
commity --provider nvidia --model nvidia/llama-3.1-nemotron-70b-instruct --api_key <your-nvidia-api-key> --emoji

# 跳过交互确认并直接提交
commity --confirm n

# 无需交互地生成、提交并推送
commity -y

# 通过模块入口运行
python -m commity --language zh --emoji

```

交互模式下可以选择：`c` 提交、`e` 使用 Git 编辑器修改消息、`r`
携带可选补充要求重新生成、`n` 取消。Commity 只使用暂存区 diff
和暂存文件元数据生成提交信息。
当代码、构建、CI 和文档变更可能相互独立时，Commity 会在生成一条
合并消息前提示用户考虑拆分 commit。
