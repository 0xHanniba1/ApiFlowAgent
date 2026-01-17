# 变更日志

本文档记录 ApiFlowAgent 的所有版本变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [Unreleased]

暂无

---

## [0.1.1] - 2026-01-17

### Added
- **CLI 命令分离**
  - `apiflow generate` - 仅解析文档并生成测试计划（调用 AI）
  - `apiflow execute` - 仅执行已有测试计划（不调用 AI）
  - 重构 `apiflow run` 为 generate + execute 组合

- **Jenkins 集成支持**
  - JUnit XML 报告输出 (`--junit` 参数)
  - Jenkins Pipeline 示例文档

### Changed
- CLI 帮助文档更新，添加使用示例
- 代码重构，提取 `_parse_and_generate` 和 `_execute_plan` 内部函数

---

## [0.1.0] - 2026-01-16

### Added
- **AI 层**
  - Claude SDK 封装 (`src/ai/client.py`)
  - API 文档解析模块 (`src/ai/parser.py`)
  - 测试用例生成模块 (`src/ai/generator.py`)

- **执行层**
  - HTTP 客户端封装 (`src/executor/http_client.py`)
  - 断言引擎 (`src/executor/assertion.py`)
  - 变量管理器 (`src/executor/variable.py`)
  - 测试运行器 (`src/executor/runner.py`)

- **报告层**
  - Allure 报告适配器 (`src/reporter/allure_adapter.py`)

- **CLI**
  - `apiflow run` 命令 (`src/cli.py`)
  - `pyproject.toml` 项目配置

- **文档**
  - 项目规格文档 (`docs/spec.md`)
  - 架构设计文档 (`docs/architecture.md`)
  - 项目状态追踪 (`docs/project-status.md`)

- **项目配置**
  - 目录结构初始化
  - `requirements.txt` 依赖配置
  - `.env.example` 环境变量模板
  - `config/config.yaml` 应用配置
  - `.gitignore` Git 忽略规则
  - `pytest.ini` 测试配置

---

## 版本规划

- **v0.1** - MVP：核心流程跑通 ✅
- **v0.2** - 完善断言类型
- **v0.3** - 多格式支持（Postman、OpenAPI 2.0）
- **v0.4** - CLI 增强
- **v0.5** - 监控巡检
- **v1.0** - 生产就绪

---

*创建时间：2026-01-16*
*最后更新：2026-01-17*
