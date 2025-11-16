# 测试文档

本项目使用 pytest 作为测试框架，包含**单元测试**和**集成测试**。

## 测试类型

### 单元测试 (Unit Tests)

- 快速执行（~0.5秒）
- 使用 Mock 隔离外部依赖
- 不需要外部服务
- 位于 `tests/test_*.py`

### 集成测试 (Integration Tests)

- 较慢（需要真实 API 调用）
- 测试与真实服务的交互
- 需要外部服务（Ollama、Git）
- 位于 `tests/integration/test_*.py`

## 运行测试

### 运行所有测试（单元 + 集成）

```bash
uv run pytest


# 运行 pytest，显示覆盖率，并只显示前 60 行输出
#  --cov 开启 coverage 测试覆盖率统计
#  --cov-report=term-missing 在终端输出每个文件缺失覆盖率的行
#  -v verbose 模式，显示更详细测试信息
uv run pytest --cov --cov-report=term-missing -v | head -60


# 运行 pytest，只显示覆盖率不足的文件（跳过已完全覆盖的文件）
#  --cov-report=term-missing:skip-covered 只显示覆盖率小于 100% 的文件
uv run pytest --cov-report=term-missing:skip-covered
```

### 只运行单元测试（快速）

```bash
uv run pytest -m "not integration"
```

### 只运行集成测试

```bash
uv run pytest -m integration
```

### 运行测试并显示覆盖率

```bash
uv run pytest --cov
```

### 生成 HTML 覆盖率报告

```bash
uv run pytest --cov --cov-report=html
# 然后打开 htmlcov/index.html 查看报告
```

### 运行详细模式

```bash
uv run pytest -v
```

### 运行特定测试文件

```bash
uv run pytest tests/test_config.py
```

### 运行特定测试类或方法

```bash
uv run pytest tests/test_config.py::TestLLMConfig
uv run pytest tests/test_config.py::TestLLMConfig::test_valid_config
```

### 使用 markers 过滤测试

```bash
# 只运行单元测试（快速，无外部依赖）
uv run pytest -m "not integration"

# 只运行集成测试
uv run pytest -m integration

# 跳过慢速测试（包括 LLM API 调用）
uv run pytest -m "not slow"

# 只运行快速测试（排除集成和慢速测试）
uv run pytest -m "not integration and not slow"
```

## 集成测试要求

### Git 集成测试

- 需要系统安装 Git
- 自动创建临时 Git 仓库
- 测试真实的 Git 操作

### Ollama 集成测试

- 需要本地运行 Ollama (`http://localhost:11434`)
- 建议使用小模型如 `llama3.2:1b` 以加快测试速度
- 如果 Ollama 不可用，测试会自动跳过

**启动 Ollama:**

```bash
# 拉取测试需要的模型（需要预先安装，测试不会自动安装）
ollama pull gpt-oss:20b

# 启动 Ollama 服务
ollama serve
```

## 测试结构

```
tests/
├── __init__.py                          # 测试包初始化
├── conftest.py                          # pytest 配置和共享 fixtures
├── README.md                            # 测试文档（本文件）
├── test_config.py                       # config 模块单元测试
├── test_core.py                         # core 模块单元测试
├── test_llm.py                          # llm 模块单元测试
└── integration/                         # 集成测试目录
    ├── __init__.py                      # 集成测试包初始化
    ├── conftest.py                      # 集成测试 fixtures
    ├── test_git_integration.py          # Git 真实操作测试
    ├── test_llm_integration.py          # Ollama 真实 API 调用测试
    └── test_e2e.py                      # 端到端完整流程测试
```

## 测试统计

### 单元测试

- **测试数量**: 50 个
- **执行时间**: ~0.5 秒
- **覆盖范围**: config, core, llm 模块的核心逻辑

### 集成测试

- **Git 测试**: 7 个（真实 Git 操作）
- **Ollama 测试**: 11 个（真实 API 调用）
- **E2E 测试**: 5 个（完整工作流）
- **执行时间**: 依赖外部服务响应时间

### 测试覆盖率

| 模块                    | 覆盖率  | 测试类型        |
|-----------------------|------|-------------|
| **config.py**         | 96%  | 单元测试        |
| **core.py**           | 97%  | 单元测试 + 集成测试 |
| **llm/base.py**       | 96%  | 单元测试        |
| **llm/factory.py**    | 100% | 单元测试        |
| **llm/ollama.py**     | 81%  | 单元测试 + 集成测试 |
| **llm/gemini.py**     | 82%  | 单元测试        |
| **llm/openai.py**     | 81%  | 单元测试        |
| **llm/openrouter.py** | 81%  | 单元测试        |

## 编写新测试

### 1. 添加 fixture

在 `conftest.py` 中添加共享的 fixtures：

```python
@pytest.fixture
def my_fixture():
    return "test data"
```

### 2. 使用 mock

使用 `pytest-mock` 进行模拟：

```python
def test_something(mocker):
    mock_func = mocker.patch('commity.module.function')
    mock_func.return_value = "mocked"
    # 测试代码
```

### 3. 测试异常

```python
def test_validation_error():
    with pytest.raises(ValidationError, match="error message"):
        pass  # 触发异常的代码
```

## CI/CD 集成

测试可以集成到 CI/CD 流程中：

```yaml
# .github/workflows/test.yml 示例
- name: Run tests
  run: uv run pytest --cov --cov-report=xml
```

## 提交前检查

在提交代码前，建议运行：

```bash
# 格式化代码
uv run ruff format .

# 检查代码风格
uv run ruff check .

# 类型检查
uv run mypy .

```
