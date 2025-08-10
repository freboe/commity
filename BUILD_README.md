## 打包

使用 hatch 打包

可以在 pyproject.toml 中添加 [tool.hatch.build]，配置打包后包含/忽略的文件

```bash
 # 如果没有安装需要先安装
uv add --dev hatch

 # 打包
uv run hatch build
```

## 本地开发

使用 hatch 打包后，再执行如下命令

```Bash
# 本地安装：
uv pip install ./dist/commity-0.1.0-py3-none-any.whl

# 本地卸载：
uv pip uninstall commity

# 本地运行包命令
./.venv/bin/commity
```

## 发布到 PyPI

```bash
uv add --dev twine # 如果没有安装需要先安装

# 先上传到测试 PyPI（推荐），https://test.pypi.org/account/register/
uv run twine upload --repository testpypi dist/*
# 安装测试：
uv pip install --index-url https://test.pypi.org/simple/ commity

# 发布到正式 PyPI ，https://pypi.org/account/register/
uv run twine upload dist/*
```

## 命令使用

```Bash
commity
```

## Reference

### Git-related commands

- `git rev-parse --is-inside-work-tree` 检测是否在 Git 仓库内
- `git diff --cached` 获取已暂存的改动
- `git diff --cached --name-only` 只获取已暂存的改动的文件名


