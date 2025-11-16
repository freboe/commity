# 集成测试使用说明

集成测试用于测试与真实外部系统的交互。

## 前置要求

### 1. Git 集成测试

- 需要系统安装 Git
- 测试会自动创建临时 Git 仓库
- 无需额外配置

### 2. Ollama 集成测试

**注意：** 测试不会自动安装模型，需要手动预先安装。

**验证 Ollama 可用性:**

```bash
curl http://localhost:11434/api/tags
```

## 运行测试

### 运行所有集成测试

```bash
uv run pytest -m integration -v
```

### 只运行 Git 集成测试

```bash
uv run pytest tests/integration/test_git_integration.py -v
```

### 只运行 Ollama 集成测试

```bash
uv run pytest tests/integration/test_llm_integration.py -v
```

### 运行端到端测试

```bash
uv run pytest tests/integration/test_e2e.py -v
```

### 跳过慢速测试

```bash
uv run pytest -m "integration and not slow" -v
```

## 测试跳过机制

集成测试使用智能跳过机制：

1. **Ollama 未运行** - 自动跳过需要 Ollama 的测试
2. **Git 未安装** - 自动跳过需要 Git 的测试
3. **模型未安装** - 会报错但不影响其他测试

示例输出：

```
tests/integration/test_llm_integration.py::TestOllamaIntegration::test_ollama_connection SKIPPED [Ollama is not running]
```

## 测试内容

### Git 集成测试 (6个)

- ✅ 真实 Git 仓库创建
- ✅ 获取 staged diff
- ✅ 文件修改、删除
- ✅ 多文件变更
- ✅ 二进制文件处理

### Ollama 集成测试 (10个)

- ✅ 连接测试
- ✅ 简单 prompt 生成
- ✅ Commit message 生成
- ✅ Emoji 支持
- ✅ 多语言支持
- ✅ 错误处理（无效模型、连接失败）

### 端到端测试 (5个)

- ✅ 完整工作流（修改 → diff → prompt → LLM → commit message）
- ✅ 配置加载
- ✅ 多文件变更
- ✅ 文件修改场景

## 注意事项

1. **执行时间**: 集成测试较慢，尤其是 LLM API 调用
  - Git 测试: ~1秒
  - Ollama 测试: 取决于模型大小和硬件，可能需要 10-60 秒

2. **并发运行**: 不建议并发运行 Ollama 测试（可能导致资源竞争）

3. **CI/CD**: 在 CI 环境中，建议跳过集成测试或使用 mock 服务
   ```bash
   # 只运行单元测试（CI 推荐）
   uv run pytest -m "not integration"
   ```

4. **调试**: 使用 `-s` 选项查看详细输出
   ```bash
   uv run pytest tests/integration/ -v -s
   ```

## 故障排查

### Ollama 连接失败

```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 重启 Ollama
pkill ollama
ollama serve
```

### 模型未找到

```bash
# 查看已安装模型
ollama list

# 拉取测试需要的模型
ollama pull gpt-oss:20b

# 或修改 tests/integration/conftest.py 使用其他已安装模型
```

### Git 测试失败

```bash
# 检查 Git 版本
git --version

# 确保 Git 配置正确
git config --global user.name "Test User"
git config --global user.email "test@example.com"
```
