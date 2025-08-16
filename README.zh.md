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

支持的模型提供商有：`Gemini` (默认)、`Ollama`、`OpenAI`。

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

### 🌱 方法二：设置环境变量作为默认值

你可以在 `.bashrc`、`.zshrc` 或 `.env` 文件中添加：

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

### 📝 方法三：使用配置文件（推荐）

为了更方便地管理配置，你可以在用户主目录下创建 `~/.commity/config.json` 文件。

1. 创建目录：

   ```bash
   mkdir -p ~/.commity
   ```

2. 创建并编辑 `config.json` 文件：

   ```bash
   touch ~/.commity/config.json
   ```

3. 在 `config.json` 中添加你的配置，例如：

   ```json
   {
     "PROVIDER": "ollama",
     "MODEL": "llama3",
     "BASE_URL": "http://localhost:11434"
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
     "API_KEY": "your-openai-api-key"
   }
   ```

## 🚀 使用

```Bash
commity

# 查看帮助
commity --help

# 使用中文
commity --lang zh

# 包含 emoji
commity --emoji
