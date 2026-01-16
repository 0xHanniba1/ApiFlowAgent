# ApiFlowAgent

AI 驱动的 API 自动化测试工具，基于 Claude SDK。

## 功能特性

- 自动解析 Swagger/OpenAPI 文档
- AI 智能生成测试用例
- 自动推断接口依赖关系
- 执行测试并生成 Allure 报告

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 运行测试

```bash
apiflow run --doc data/api_docs/swagger.json
```

## 项目结构

```
ApiFlowAgent/
├── src/
│   ├── ai/          # AI 智能层（Claude SDK）
│   ├── executor/    # 执行引擎层
│   └── reporter/    # 报告层
├── config/          # 配置文件
├── data/            # API 文档和测试计划
├── reports/         # 测试报告输出
├── tests/           # pytest 入口
└── docs/            # 项目文档
```

## 文档

- [项目规格](docs/spec.md) - 功能列表和 MVP 范围
- [架构设计](docs/architecture.md) - 技术架构和模块设计
- [变更日志](docs/changelog.md) - 版本变更记录
- [项目状态](docs/project-status.md) - 当前开发进度

## 开发状态

当前版本：v0.1 (MVP 开发中)

详见 [project-status.md](docs/project-status.md)
