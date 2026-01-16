# ApiFlowAgent 架构设计

## 一、整体架构

### 1.1 混合架构

```
┌─────────────────────────────────────────────────────────────┐
│                      ApiFlowAgent                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   AI 智能层     │    │         执行引擎层              │ │
│  │  (Claude SDK)   │    │       (Python 代码)             │ │
│  ├─────────────────┤    ├─────────────────────────────────┤ │
│  │ • 文档解析理解   │───▶│ • HTTP 请求执行 (httpx)        │ │
│  │ • 测试用例生成   │    │ • 断言校验引擎                  │ │
│  │ • 依赖关系推断   │    │ • 数据提取与传递                │ │
│  │ • 智能断言生成   │    │ • Allure 报告生成              │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│           │                           │                      │
│           ▼                           ▼                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              中间数据格式 (JSON Schema)                  ││
│  │   AI 输出结构化数据 → 执行引擎消费                       ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| AI 做智能决策 | 理解文档、生成用例、推断依赖 |
| 代码做确定性执行 | HTTP 请求、断言校验、报告生成 |
| Token 节省 | AI 只在规划阶段调用，测试计划可复用 |
| MVP 优先 | 每个模块先实现最简版本 |

---

## 二、工作流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  输入    │───▶│  解析    │───▶│  生成    │───▶│  执行    │───▶│  报告    │
│ API 文档 │    │ (AI)     │    │ (AI)     │    │ (代码)   │    │ (代码)   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                    │               │               │               │
                    ▼               ▼               ▼               ▼
               解析结果.json   测试计划.json   执行结果.json   Allure报告
```

| 阶段 | 执行者 | 输入 | 输出 |
|------|--------|------|------|
| 解析 | Claude | Swagger/Postman 文件 | 标准化接口定义 JSON |
| 生成 | Claude | 接口定义 + 业务上下文 | 测试计划 JSON |
| 执行 | Python | 测试计划 JSON | 执行结果 JSON |
| 报告 | Python | 执行结果 JSON | Allure HTML 报告 |

**Token 节省策略**：解析和生成合并为一次 AI 调用，测试计划可持久化复用。

---

## 三、项目目录结构

```
ApiFlowAgent/
├── README.md
├── requirements.txt
├── pytest.ini
├── .env.example                 # 环境变量模板
│
├── config/
│   ├── base.yaml               # 通用配置（超时、重试策略）
│   ├── dev.yaml                # 开发环境
│   └── test.yaml               # 测试环境
│
├── src/
│   ├── __init__.py
│   ├── ai/                     # AI 智能层
│   │   ├── __init__.py
│   │   ├── client.py           # Claude SDK 封装
│   │   ├── parser.py           # 文档解析 Prompt
│   │   └── generator.py        # 用例生成 Prompt
│   │
│   ├── executor/               # 执行引擎层
│   │   ├── __init__.py
│   │   ├── http_client.py      # HTTP 请求封装
│   │   ├── assertion.py        # 断言引擎
│   │   ├── variable.py         # 变量提取与注入
│   │   └── runner.py           # 测试运行器
│   │
│   └── reporter/               # 报告层
│       ├── __init__.py
│       └── allure_adapter.py   # Allure 适配器
│
├── tests/                      # pytest 用例入口
│   └── test_api.py
│
├── data/
│   ├── api_docs/               # 存放 Swagger/Postman 文件
│   └── test_plans/             # AI 生成的测试计划 JSON
│
├── reports/                    # Allure 报告输出目录
│
└── docs/                       # 项目文档
    ├── spec.md
    ├── architecture.md
    ├── changelog.md
    ├── project-status.md
    └── plans/
```

---

## 四、核心数据结构

### 4.1 测试计划 JSON Schema

```json
{
  "meta": {
    "name": "用户模块接口测试",
    "version": "1.0",
    "generated_at": "2026-01-16T10:00:00Z"
  },
  "endpoints": [
    {
      "id": "login",
      "name": "用户登录",
      "method": "POST",
      "path": "/api/auth/login",
      "headers": {"Content-Type": "application/json"},
      "body_template": {"username": "{{username}}", "password": "{{password}}"}
    }
  ],
  "test_cases": [
    {
      "id": "tc_login_success",
      "name": "登录成功-正常用户",
      "endpoint_id": "login",
      "category": "positive",
      "inputs": {"username": "testuser", "password": "Test@123"},
      "assertions": [
        {"type": "status_code", "expected": 200},
        {"type": "json_path", "path": "$.token", "operator": "exists"},
        {"type": "json_path", "path": "$.user.id", "operator": "is_number"}
      ],
      "extract": [
        {"name": "auth_token", "from": "$.token"}
      ]
    }
  ],
  "execution_order": ["tc_login_success", "tc_get_profile"],
  "dependencies": {
    "tc_get_profile": {
      "depends_on": "tc_login_success",
      "inject": {"Authorization": "Bearer {{auth_token}}"}
    }
  }
}
```

### 4.2 关键字段说明

| 字段 | 说明 |
|------|------|
| `endpoints` | 接口定义列表 |
| `test_cases` | 测试用例列表 |
| `assertions` | 断言规则 |
| `extract` | 从响应中提取变量 |
| `execution_order` | 执行顺序 |
| `dependencies` | 依赖关系和变量注入 |

---

## 五、模块设计

### 5.1 AI 层 (`src/ai/`)

**职责**：调用 Claude SDK，完成文档解析和用例生成

**核心类**：
- `AIClient`：Claude SDK 封装，统一处理请求/响应
- `parser.py`：文档解析 Prompt 模板
- `generator.py`：用例生成 Prompt 模板

**Prompt 设计策略**：
- System Prompt 定义输出 JSON Schema
- 要求输出纯 JSON，便于解析
- 只传必要的 API 定义，控制 Token 消耗

### 5.2 执行层 (`src/executor/`)

**职责**：执行测试计划，完成 HTTP 请求和断言校验

**核心类**：
- `HttpClient`：httpx 封装，支持各种 HTTP 请求
- `AssertionEngine`：断言校验引擎
- `VariableManager`：变量提取和注入
- `TestRunner`：测试运行器，编排执行流程

**运行时变量池**：
- 存储 `extract` 提取的值
- 支持 `{{variable}}` 模板语法注入

### 5.3 报告层 (`src/reporter/`)

**职责**：生成 Allure 测试报告

**核心类**：
- `AllureAdapter`：适配 allure-pytest

**记录内容**：
- 每个用例的请求详情
- 响应内容
- 断言结果
- 执行时间

---

## 六、断言引擎设计

### 6.1 断言类型

| 类型 | 语法 | 说明 |
|------|------|------|
| `status_code` | `{"type": "status_code", "expected": 200}` | HTTP 状态码 |
| `json_path` + `exists` | `{"type": "json_path", "path": "$.token", "operator": "exists"}` | 字段存在 |
| `json_path` + `equals` | `{"type": "json_path", "path": "$.code", "operator": "equals", "expected": 0}` | 值相等 |

### 6.2 AI 生成断言策略

1. **必生成**：每个用例必有 status_code 断言
2. **自动推断**：根据响应 Schema 生成 exists、类型校验
3. **智能建议**：根据字段语义生成业务断言

---

## 七、技术选型

| 用途 | 库 | 说明 |
|------|-----|------|
| AI 调用 | `anthropic` | Claude SDK |
| HTTP 请求 | `httpx` | 现代异步 HTTP 库 |
| 配置管理 | `pydantic` + `pyyaml` | 类型安全配置 |
| JSONPath | `jsonpath-ng` | 响应数据提取 |
| 测试框架 | `pytest` | 用例组织执行 |
| 报告 | `allure-pytest` | Allure 报告 |
| CLI | `typer` | 命令行工具 |
| 环境变量 | `python-dotenv` | .env 加载 |

**Python 版本**：3.10+

---

## 八、CI/CD 集成

### 8.1 GitHub Actions 示例

```yaml
name: API Test

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run API tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          API_BASE_URL: ${{ secrets.API_BASE_URL }}
        run: apiflow run --doc data/api_docs/swagger.json

      - name: Generate Allure report
        uses: simple-elf/allure-report-action@master
        if: always()
        with:
          allure_results: reports/allure-results

      - name: Publish report
        uses: peaceiris/actions-gh-pages@v3
        if: always()
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: reports/allure-report
```

---

## 九、扩展性预留

### 9.1 后续扩展点

| 扩展点 | 当前设计 | 后续扩展 |
|--------|----------|----------|
| 调度 | CLI 手动触发 | 定时任务 / Cron |
| 通知 | 无 | 插件化通知渠道 |
| 存储 | 文件 JSON | 可选数据库 |
| 流程 | 单链依赖 | 多分支编排 |
| 模式 | test | test / monitor / e2e |

### 9.2 监控巡检（规划）

- 定时任务调度器（APScheduler）
- 健康检查模式（轻量断言）
- 告警通知（钉钉/Slack/邮件）
- 历史趋势存储

### 9.3 端到端测试（规划）

- 业务流程编排 DSL
- 多场景分支支持
- 测试数据工厂
- 环境隔离与清理

---

## 十、设计决策记录

| 决策 | 选项 | 选择 | 原因 |
|------|------|------|------|
| 架构 | 单Agent/多Agent/混合 | 混合 | AI做决策，代码做执行，省Token |
| API来源 | 文档/自然语言/代码 | 文档解析 | 标准化，准确 |
| 用例生成 | AI/模板/用户定义 | AI智能生成 | 自动化程度高 |
| 依赖处理 | 自动/手动/交互 | AI推断+确认 | 平衡自动化与准确性 |
| 断言策略 | AI/Schema/混合 | 混合 | AI基础+用户补充 |
| 报告格式 | Console/Allure | Allure | 业界标准，CI友好 |
| 配置管理 | 文件/环境变量 | 混合 | 安全且灵活 |

---

*创建时间：2026-01-16*
