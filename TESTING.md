# 测试文档总览

本项目拥有完整的测试套件，包含**单元测试**和**集成测试**两种类型。

## 📊 测试统计

| 指标 | 数量 |
|------|------|
| **总测试数** | 71 个 |
| **单元测试** | 50 个 |
| **集成测试** | 21 个 |
| **测试代码行数** | 1,484 行 |
| **测试文件** | 7 个 |

## 🎯 测试类型对比

### 单元测试 (Unit Tests)
```bash
# 运行单元测试（快速）
uv run pytest -m "not integration"
```

| 特点 | 描述 |
|------|------|
| **执行速度** | ~0.5 秒 ⚡️ |
| **外部依赖** | 无（使用 Mock） |
| **覆盖范围** | 核心逻辑、边界条件、错误处理 |
| **适用场景** | CI/CD、本地开发、快速反馈 |

**测试内容:**
- ✅ Config 模块 (16个): Pydantic 验证、配置加载、优先级
- ✅ Core 模块 (13个): Git diff、Prompt 生成
- ✅ LLM 模块 (21个): 基类、工厂、各客户端

### 集成测试 (Integration Tests)
```bash
# 运行集成测试（需要外部服务）
uv run pytest -m integration
```

| 特点 | 描述 |
|------|------|
| **执行速度** | 10-60 秒（依赖 LLM 响应） |
| **外部依赖** | Git、Ollama |
| **覆盖范围** | 真实场景、端到端流程 |
| **适用场景** | 本地测试、发布前验证 |

**测试内容:**
- ✅ Git 集成 (6个): 真实 Git 仓库操作
- ✅ Ollama 集成 (10个): 真实 LLM API 调用
- ✅ 端到端 (5个): 完整工作流

## 📈 代码覆盖率

| 模块 | 覆盖率 | 说明 |
|------|--------|------|
| **config.py** | 96% | ⭐️ 优秀 |
| **core.py** | 97% | ⭐️ 优秀 |
| **llm/base.py** | 96% | ⭐️ 优秀 |
| **llm/factory.py** | 100% | ⭐️ 完美 |
| **llm/ollama.py** | 81% | ✅ 良好 |
| **llm/gemini.py** | 82% | ✅ 良好 |
| **llm/openai.py** | 81% | ✅ 良好 |
| **llm/openrouter.py** | 81% | ✅ 良好 |

**未覆盖部分:**
- CLI 交互逻辑（需要集成测试）
- Spinner 和 UI 组件（需要手动测试）
- Prompt organizer（工具函数）

## 🚀 快速开始

### 1. 安装依赖
```bash
uv sync --dev
```

### 2. 运行单元测试（推荐日常开发）
```bash
# 快速测试所有核心功能
uv run pytest -m "not integration"

# 带覆盖率报告
uv run pytest -m "not integration" --cov
```

### 3. 运行集成测试（发布前）
```bash
# 前置条件：启动 Ollama
ollama serve

# 拉取测试需要的模型（测试不会自动安装）
ollama pull gpt-oss:20b

# 运行集成测试
uv run pytest -m integration -v
```

## 📁 测试结构

```
tests/
├── __init__.py                          # 测试包初始化
├── conftest.py                          # 单元测试 fixtures
├── README.md                            # 测试使用文档
├── test_config.py                       # Config 单元测试 (16个)
├── test_core.py                         # Core 单元测试 (13个)
├── test_llm.py                          # LLM 单元测试 (21个)
└── integration/                         # 集成测试目录
    ├── __init__.py
    ├── conftest.py                      # 集成测试 fixtures
    ├── README.md                        # 集成测试说明
    ├── test_git_integration.py          # Git 集成测试 (6个)
    ├── test_llm_integration.py          # Ollama 集成测试 (10个)
    └── test_e2e.py                      # 端到端测试 (5个)
```

## 🔧 常用命令

### 基础测试
```bash
# 运行所有测试
uv run pytest

# 详细模式
uv run pytest -v

# 只运行单元测试
uv run pytest -m "not integration"

# 只运行集成测试
uv run pytest -m integration
```

### 覆盖率报告
```bash
# 终端显示覆盖率
uv run pytest --cov

# 生成 HTML 报告
uv run pytest --cov --cov-report=html
# 打开 htmlcov/index.html

# 只显示未完全覆盖的文件
uv run pytest --cov-report=term-missing:skip-covered
```

### 特定测试
```bash
# 运行特定文件
uv run pytest tests/test_config.py

# 运行特定类
uv run pytest tests/test_config.py::TestLLMConfig

# 运行特定方法
uv run pytest tests/test_config.py::TestLLMConfig::test_valid_config
```

### 调试测试
```bash
# 显示 print 输出
uv run pytest -s

# 遇到失败立即停止
uv run pytest -x

# 显示最后 N 个失败测试
uv run pytest --lf

# 并行运行（需要 pytest-xdist）
uv run pytest -n auto
```

## ✅ CI/CD 集成

**推荐配置（GitHub Actions）:**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync --dev

      - name: Run unit tests
        run: uv run pytest -m "not integration" --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 📝 编写新测试

### 单元测试
```python
# tests/test_module.py
from commity.module import function

def test_function():
    result = function(input)
    assert result == expected
```

### 集成测试
```python
# tests/integration/test_feature.py
import pytest

@pytest.mark.integration
@pytest.mark.slow
def test_real_feature(temp_git_repo, ollama_config):
    # 使用真实服务测试
    pass
```

## 🎓 测试最佳实践

1. **单元测试优先** - 快速反馈，高覆盖率
2. **Mock 外部依赖** - 隔离测试，提高稳定性
3. **使用 fixtures** - 复用测试数据和设置
4. **清晰的测试名称** - `test_<what>_<when>_<then>`
5. **测试边界条件** - 空值、极值、异常情况
6. **独立性** - 每个测试应该独立运行
7. **集成测试分离** - 使用 markers 区分

## 🔍 故障排查

### 测试失败
```bash
# 查看详细错误
uv run pytest -v --tb=short

# 只运行失败的测试
uv run pytest --lf
```

### 集成测试跳过
- 检查 Ollama 是否运行: `curl http://localhost:11434/api/tags`
- 检查 Git 是否安装: `git --version`
- 查看跳过原因: `uv run pytest -v -rs`

### 覆盖率不准确
```bash
# 清除缓存
rm -rf .pytest_cache htmlcov .coverage

# 重新运行
uv run pytest --cov
```

## 📚 更多信息

- 测试使用指南: `tests/README.md`
- 集成测试说明: `tests/integration/README.md`
- pytest 文档: https://docs.pytest.org/
- 覆盖率文档: https://coverage.readthedocs.io/
