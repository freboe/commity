# 开发指南

## 环境设置

### 1. 安装依赖

```bash
# 安装开发依赖
make setup
# 或者手动执行：
uv sync --group dev
uv run pre-commit install
```

### 2. 配置编辑器

项目已经配置了 VS Code 设置，包括：
- 自动格式化（保存时）
- Ruff 代码检查
- MyPy 类型检查 (uv add --group dev mypy types-requests)
- 自动导入排序

## 开发工作流

### 代码格式化

```bash
# 格式化所有代码
make format

# 检查代码质量
make lint

# 自动修复问题
make fix

# 检查格式和质量
make check
```

### 类型检查

```bash
# 运行类型检查
make typecheck
```

### 提交前检查

项目配置了 pre-commit 钩子，会在每次提交时自动运行：
- 代码格式化
- 代码质量检查
- 类型检查
- 文件格式检查

```bash
# 手动运行 pre-commit 检查
make pre-commit-run
```

## 工具配置

### Ruff

- 行长度限制：100 字符
- 自动修复：启用
- 格式化：启用
- 导入排序：启用

### MyPy

- 严格类型检查：启用
- 忽略缺失导入：启用
- Python 版本：3.12

### Pre-commit

- 文件格式检查
- 代码质量检查
- 自动修复
- 类型检查

## 常用命令

```bash
# 查看所有可用命令
make help

# 安装依赖
make install

# 安装开发依赖
make install-dev

# 格式化代码
make format

# 检查代码质量
make lint

# 自动修复问题
make fix

# 检查格式和质量
make check

# 类型检查
make typecheck

# 运行测试
make test

# 构建项目
make build

# 清理构建文件
make clean

# 安装 pre-commit 钩子
make pre-commit-install

# 运行 pre-commit 检查
make pre-commit-run
```

## 编辑器集成

### VS Code

项目包含 VS Code 配置：
- 自动格式化（保存时）
- Ruff 集成
- MyPy 集成
- 推荐的扩展

### 其他编辑器

对于其他编辑器，请确保：
1. 使用 Ruff 作为格式化工具
2. 启用保存时自动格式化
3. 配置行长度为 100 字符

## 提交规范

项目使用 pre-commit 钩子确保代码质量：
1. 代码会自动格式化
2. 导入会自动排序
3. 类型错误会被检查
4. 文件格式会被验证

如果提交失败，请运行 `make fix` 修复问题后重新提交。
