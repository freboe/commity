# 开发指南

## 环境设置

### 1. 安装依赖

```bash
# 安装开发依赖
make setup
# 或者手动执行：
uv sync --group dev
# 安装 pre-commit 钩子
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
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

项目配置了 pre-commit 和 pre-push 钩子：

- **Pre-commit (提交时)**:
  - 自动运行代码格式化和 Lint 检查 (Ruff)
  - 运行单元测试 (忽略 `tests/integration`)，确保基础逻辑正确
  - 文件格式检查
- **Pre-push (推送时)**:
  - 运行**所有**测试 (包含集成测试)，确保代码完整性以及不破坏现有功能

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

## 运行与调试 CLI

- 使用 `uv run python -m commity --help` 快速验证入口脚本（`python -m commity` 与 `commity` 命令等价）
- `make run-commity` 提供了一个包含代理与 emoji 的示例调用，可按需修改参数。
- 构建产物会输出到 `dist/` 目录，该目录已被 `.gitignore` 忽略；发布前可运行 `make clean` 或 `uv run hatch clean` 清理旧包，避免误提交。

### 本地调试

在其他 Git 仓库中调试当前工作区的 Commity 源码时，先进入目标仓库并暂存待分析的
变更。`uv --project` 只负责选择 Commity 的 Python 项目，CLI 仍会读取当前目录的 Git
暂存区。

```bash
# Commity 源码目录
export COMMITY_PROJECT=~/dev_space/my_github_freboe/commity

# 进入需要生成 commit message 的目标仓库
cd /path/to/target-repository
git add <files>
git diff --cached

# 使用当前 Commity 源码生成中文 commit message
uv run --project "$COMMITY_PROJECT" commity --language zh

#相当于：
uv run --project ~/dev_space/my_github_freboe/commity commity --language zh
```

生成完成后，CLI 会提示选择 `commit`、`edit`、`regenerate` 或 `cancel`。仅查看生成效果时
选择 `n`（默认选项）取消提交。不要传入 `--confirm n`：该参数表示跳过交互确认并直接
执行 commit。

如果只需确认跨目录入口是否正确，不调用模型也不读取 Git 暂存区，可以执行：

```bash
uv run --project "$COMMITY_PROJECT" commity --version
```

需要频繁调用时，建议在 `~/.zshrc` 或 `~/.bashrc` 中增加一个独立的开发命令，避免与
通过 `uv tool install commity` 安装的正式版冲突：

```bash
export COMMITY_PROJECT=~/dev_space/my_github_freboe/commity
alias commity-dev='uv run --project "$COMMITY_PROJECT" commity'

cd /path/to/target-repository
commity-dev --language zh
```

也可以用 editable tool 替换正式版，但二者的工具名和可执行命令都是 `commity`，不能
并存。先用 `uv tool list` 确认当前安装来源，再执行：

```bash
uv tool install --editable --force "$COMMITY_PROJECT"
```

editable 安装会引用当前源码目录，源码修改无需重复安装。调试结束后，卸载本地版本并
恢复正式版：

```bash
uv tool uninstall commity
uv tool install commity
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
5. 单元测试必须通过

如果提交失败，请运行 `make fix` 修复问题后重新提交。
