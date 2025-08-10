# 🤖 commity

使用大语言模型（LLM）生成智能 Git 提交信息的工具，支持 Conventional Commits 格式和 emoji 插入。

## 🔧 安装

```bash
pip install commity
```

## ⚙️ 配置

`commity` 支持通过三种方式进行配置，优先级从高到低依次为：**命令行参数 > 环境变量 > 配置文件**。

支持的模型提供商有：`Gemini` (默认)、`Ollama`。

### ✨ 方法一：运行命令时指定模型参数

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
     "MODEL": "gemini-2.5-flash",
     "BASE_URL": "https://generativelanguage.googleapis.com",
     "API_KEY": "your-gemini-api-key"
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
