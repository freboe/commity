# Repository Guidelines

## 项目结构

Commity 使用 Python 3.12+，根据 Git 暂存区的改动生成提交信息。

- `commity/cli.py` 是命令行入口，`commity/core.py` 读取 Git 差异并生成提示词，`commity/config.py` 解析配置。
- `commity/llm/` 存放模型服务的客户端及工厂，`commity/utils/` 存放通用工具。
- `tests/` 存放单元测试，`tests/integration/` 存放集成和端到端测试，`.github/workflows/` 存放 CI 配置。

## 常用开发命令

- `uv sync --group dev` 安装项目和开发依赖。
- `uv run commity --help` 查看本地 CLI 参数。试跑生成流程时，先在测试仓库中用 `git add` 暂存改动。
- `make test` 运行 pytest。`make build` 用 Hatch 清理旧产物并构建到 `dist/`。
- `make format` 格式化代码，`make check` 用 Ruff 检查代码和格式，`make typecheck` 用 mypy 检查类型。

## 代码风格与命名

用 4 个空格缩进，字符串用双引号，Ruff 格式化行宽为 100 字符。模块、函数和变量用 `snake_case`，类用 `PascalCase`。模型服务特有的逻辑放在 `commity/llm/`，优先复用客户端的共用逻辑。

## 测试

测试文件用 `test_*.py`，测试函数用 `test_*`。复用 `tests/conftest.py` 的 fixture，单元测试中模拟模型服务请求。行为变更应有针对性的回归测试。

- `uv run pytest --ignore=tests/integration` 只跑单元测试。
- `uv run pytest -m integration` 跑集成测试。按用例准备 Git 或本地 Ollama。
- 分支覆盖率报告可在终端和 `htmlcov/` 查看。

## 提交与拉取请求

沿用近期提交的 Conventional Commits 格式，例如 `feat(config): add provider setting` 或 `fix(cli): handle empty diffs`。标题简短，以动词开头。提交 PR 时，说明行为改动，列出已运行的检查，并关联相关 Issue。CLI 输出有变化时，附上终端输出示例。

## 查找代码

优先用 codebase-memory MCP 的 `search_graph` 定位符号、用 `trace_path` 追踪调用。如果仓库根目录有 `.codegraph/`，在回退到文本搜索前先查 CodeGraph。
