.PHONY: help install install-dev format lint fix check typecheck test build clean pre-commit-install pre-commit-run

help: ## 显示帮助信息
	@echo "可用的命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装项目依赖
	uv sync

install-dev: ## 安装开发依赖
	uv sync --group dev

format: ## 格式化代码
	uv run ruff format .

lint: ## 检查代码质量
	uv run ruff check .

fix: ## 自动修复代码问题
	uv run ruff check --fix .

check: ## 检查代码格式和质量
	uv run ruff check . && uv run ruff format --check .

typecheck: ## 类型检查
	uv run mypy .

test: ## 运行测试
	uv run python -m pytest

run-commity:
	uv run python ./commity/cli.py --max_subject_chars 60 --proxy 127.0.0.1:10808 --emoji

build: ## 构建项目
	uv run hatch clean
	uv run hatch build

publish: ## 发布项目
	uv run twine upload dist/*

clean: ## 清理构建文件
	uv run hatch clean

pre-commit-install: ## 安装 pre-commit 钩子
	uv run pre-commit install

pre-commit-run: ## 运行 pre-commit 检查
	uv run pre-commit run --all-files

setup: install-dev pre-commit-install ## 完整设置开发环境
	@echo "开发环境设置完成！"
	@echo "现在你可以使用以下命令："
	@echo "  make format    - 格式化代码"
	@echo "  make lint      - 检查代码质量"
	@echo "  make fix       - 自动修复问题"
	@echo "  make check     - 检查格式和质量"
	@echo "  make typecheck - 类型检查"
