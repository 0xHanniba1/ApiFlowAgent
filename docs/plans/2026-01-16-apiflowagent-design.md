# ApiFlowAgent 设计文档

> 接口自动化全流程 Agent，基于 Claude SDK

## 一、项目概述

### 1.1 目标
构建一个 AI 驱动的 API 自动化测试工具，能够：
- 解析 API 文档，自动理解接口定义
- 智能生成测试用例（正向/异常/边界）
- 自动推断接口依赖关系并编排执行顺序
- 执行测试并生成 Allure 报告
- 支持 CI/CD 集成

### 1.2 技术栈
- **语言**：Python 3.10+
- **AI**：Claude SDK (anthropic)
- **HTTP**：httpx
- **测试框架**：pytest
- **报告**：allure-pytest
- **CLI**：typer 或 click
- **配置**：pydantic + pyyaml + python-dotenv

### 1.3 适用场景
| 阶段 | 场景 | 状态 |
|------|------|------|
| 当前 | API 测试自动化 | MVP |
| 后续 | API 监控巡检 | 规划中 |
| 后续 | 端到端流程测试 | 规划中 |

---

## 二、整体架构

### 2.1 混合架构设计

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

### 2.2 设计原则
- **AI 做智能决策**：理解文档、生成用例、推断依赖
- **代码做确定性执行**：HTTP 请求、断言校验、报告生成
- **Token 节省**：AI 只在规划阶段调用，测试计划可复用

---

## 三、工作流程

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

---

## 五、项目目录结构

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
└── reports/                    # Allure 报告输出目录
```

---

## 六、功能模块详细设计

### 6.1 文档解析模块 (`src/ai/parser.py`)

| 功能 | MVP | 后续迭代 |
|------|:---:|:--------:|
| Swagger/OpenAPI 3.0 解析 | ✅ | |
| OpenAPI 2.0 (Swagger 2.0) 解析 | | ✅ |
| Postman Collection v2.1 解析 | | ✅ |
| API Blueprint 解析 | | ✅ |
| GraphQL Schema 解析 | | ✅ |
| 从代码注释提取 API 定义 | | ✅ |

**MVP 实现要点**：
- 读取 OpenAPI 3.0 JSON/YAML 文件
- 提取 paths、methods、parameters、requestBody、responses
- 输出标准化的接口定义 JSON

---

### 6.2 用例生成模块 (`src/ai/generator.py`)

| 功能 | MVP | 后续迭代 |
|------|:---:|:--------:|
| 正向用例生成（每接口 1 个） | ✅ | |
| 异常用例生成（每接口 1 个） | ✅ | |
| 边界值用例生成 | | ✅ |
| 参数组合用例（正交实验） | | ✅ |
| 业务场景用例（多接口串联） | | ✅ |
| 安全测试用例（SQL注入、XSS等） | | ✅ |
| 性能测试用例模板 | | ✅ |

**MVP 实现要点**：
- 每个接口生成 1 个正向用例 + 1 个异常用例
- 正向用例：合法参数，期望成功响应
- 异常用例：缺少必填参数或非法值，期望错误响应

---

### 6.3 依赖推断模块

| 功能 | MVP | 后续迭代 |
|------|:---:|:--------:|
| AI 推断 + 人工确认（交互式） | ✅ | |
| 全自动静默推断 | | ✅ |
| 循环依赖检测 | | ✅ |
| 并行执行优化（无依赖接口并发） | | ✅ |
| 依赖可视化图谱 | | ✅ |

**MVP 实现要点**：
- AI 分析接口参数和响应，推断可能的依赖关系
- 输出推断结果供用户确认
- 用户可修正后保存

---

### 6.4 断言引擎 (`src/executor/assertion.py`)

| 断言类型 | MVP | 后续迭代 | 说明 |
|----------|:---:|:--------:|------|
| `status_code` | ✅ | | HTTP 状态码校验 |
| `json_path` + `exists` | ✅ | | 字段存在性校验 |
| `json_path` + `equals` | ✅ | | 字段值相等校验 |
| `json_path` + `contains` | | ✅ | 字符串包含校验 |
| `json_path` + `is_number` | | ✅ | 类型校验 |
| `json_path` + `is_string` | | ✅ | 类型校验 |
| `json_path` + `is_array` | | ✅ | 类型校验 |
| `json_path` + `length` | | ✅ | 数组/字符串长度校验 |
| `json_path` + `regex` | | ✅ | 正则匹配校验 |
| `json_path` + `greater_than` | | ✅ | 数值比较 |
| `json_path` + `less_than` | | ✅ | 数值比较 |
| `header` | | ✅ | 响应头校验 |
| `response_time` | | ✅ | 响应时间校验 |
| `schema` | | ✅ | JSON Schema 校验 |
| `custom` | | ✅ | 用户自定义 Python 表达式 |

**MVP 实现要点**：
- 支持 status_code、json_path exists/equals 三种核心断言
- 使用 jsonpath-ng 库提取响应数据

---

### 6.5 变量管理模块 (`src/executor/variable.py`)

| 功能 | MVP | 后续迭代 |
|------|:---:|:--------:|
| 单层 JSONPath 提取 `$.token` | ✅ | |
| 嵌套提取 `$.data.user.id` | ✅ | |
| 数组元素提取 `$.items[0].id` | | ✅ |
| 数组遍历提取 `$.items[*].id` | | ✅ |
| 响应头提取 | | ✅ |
| 正则提取 | | ✅ |
| 内置变量（时间戳、UUID等） | | ✅ |
| 环境变量引用 | ✅ | |

**MVP 实现要点**：
- 变量池 dict 存储提取的值
- 模板语法 `{{variable_name}}` 注入到请求中

---

### 6.6 HTTP 客户端 (`src/executor/http_client.py`)

| 功能 | MVP | 后续迭代 |
|------|:---:|:--------:|
| GET/POST/PUT/DELETE 请求 | ✅ | |
| JSON 请求体 | ✅ | |
| Form 表单请求 | | ✅ |
| 文件上传 | | ✅ |
| 自定义 Headers | ✅ | |
| Query 参数 | ✅ | |
| Path 参数 | ✅ | |
| 超时配置 | ✅ | |
| 重试机制 | | ✅ |
| 代理支持 | | ✅ |
| SSL 证书配置 | | ✅ |
| Cookie 管理 | | ✅ |

**MVP 实现要点**：
- 使用 httpx 库
- 支持基础的 REST 请求

---

### 6.7 测试运行器 (`src/executor/runner.py`)

| 功能 | MVP | 后续迭代 |
|------|:---:|:--------:|
| 顺序执行测试用例 | ✅ | |
| 依赖注入 | ✅ | |
| 失败继续执行 | ✅ | |
| 失败快速终止 | | ✅ |
| 并发执行（无依赖用例） | | ✅ |
| 重试失败用例 | | ✅ |
| 用例过滤（标签/名称） | | ✅ |
| 数据驱动（参数化） | | ✅ |
| 前置/后置钩子 | | ✅ |

**MVP 实现要点**：
- 按 execution_order 顺序执行
- 执行前检查依赖，注入变量
- 记录每个用例的执行结果

---

### 6.8 报告模块 (`src/reporter/`)

| 功能 | MVP | 后续迭代 |
|------|:---:|:--------:|
| Allure 基础报告（通过/失败） | ✅ | |
| 请求/响应详情记录 | ✅ | |
| 断言详情记录 | ✅ | |
| 执行时间统计 | ✅ | |
| 失败截图/日志附件 | | ✅ |
| 历史趋势图 | | ✅ |
| 环境信息展示 | | ✅ |
| 分类统计（按模块/标签） | | ✅ |
| 邮件报告 | | ✅ |
| Slack/钉钉通知 | | ✅ |

**MVP 实现要点**：
- 使用 allure-pytest 集成
- 记录每个用例的请求、响应、断言结果

---

### 6.9 CLI 模块

| 命令 | MVP | 后续迭代 | 说明 |
|------|:---:|:--------:|------|
| `apiflow run` | ✅ | | 完整流程：解析→生成→执行→报告 |
| `apiflow generate` | | ✅ | 仅生成测试计划 |
| `apiflow execute` | | ✅ | 仅执行已有计划 |
| `apiflow report` | | ✅ | 仅生成报告 |
| `apiflow validate` | | ✅ | 校验 API 文档格式 |
| `apiflow diff` | | ✅ | 对比两个版本的 API 变更 |
| `--env` 参数 | | ✅ | 指定运行环境 |
| `--filter` 参数 | | ✅ | 过滤执行的用例 |
| `--parallel` 参数 | | ✅ | 并发执行 |

**MVP 实现要点**：
- 单命令 `apiflow run --doc <file>` 跑通全流程
- 使用 typer 或 click 构建 CLI

---

### 6.10 配置管理

| 功能 | MVP | 后续迭代 |
|------|:---:|:--------:|
| `.env` 环境变量 | ✅ | |
| 单配置文件 `config.yaml` | ✅ | |
| 多环境配置切换 | | ✅ |
| 配置继承与覆盖 | | ✅ |
| 配置校验（pydantic） | | ✅ |
| 命令行参数覆盖配置 | | ✅ |

**MVP 实现要点**：
- `.env` 存放敏感信息（API_KEY 等）
- `config.yaml` 存放基础配置（base_url、timeout）

---

## 七、CI/CD 集成

### 7.1 GitHub Actions 示例

```yaml
# .github/workflows/api-test.yml
name: API Test

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 8 * * *'  # 每天 8 点执行（后续巡检用）

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

### 7.2 Token 成本控制策略

| 策略 | MVP | 后续迭代 |
|------|:---:|:--------:|
| 测试计划 JSON 持久化复用 | ✅ | |
| 检测 API 文档变更才重新生成 | | ✅ |
| 增量生成（仅变更接口） | | ✅ |
| 本地缓存 Prompt 结果 | | ✅ |
| 使用更便宜的模型做简单任务 | | ✅ |

---

## 八、扩展性预留

### 8.1 后续扩展：监控巡检

```
┌─────────────────────────────────────────┐
│           监控巡检模式                   │
├─────────────────────────────────────────┤
│ • 定时任务调度器（APScheduler）          │
│ • 健康检查模式（轻量断言）               │
│ • 告警通知（钉钉/Slack/邮件/Webhook）    │
│ • 历史趋势存储（InfluxDB/Prometheus）    │
│ • 可视化面板（Grafana 集成）             │
└─────────────────────────────────────────┘
```

### 8.2 后续扩展：端到端流程测试

```
┌─────────────────────────────────────────┐
│         端到端流程测试                   │
├─────────────────────────────────────────┤
│ • 业务流程编排 DSL（YAML 定义流程）      │
│ • 多场景分支支持（条件判断）             │
│ • 测试数据工厂（Faker 集成）             │
│ • 环境隔离与清理（Setup/Teardown）       │
│ • 事务回滚机制                           │
└─────────────────────────────────────────┘
```

### 8.3 预留扩展接口

| 扩展点 | 当前设计 | 后续扩展 |
|--------|----------|----------|
| 调度 | CLI 手动触发 | 定时任务 / Cron |
| 通知 | 无 | 插件化通知渠道 |
| 存储 | 文件 JSON | 可选数据库持久化 |
| 流程 | 单链依赖 | 多分支流程编排 |
| 模式 | test | test / monitor / e2e |

---

## 九、技术依赖

### 9.1 requirements.txt

```
# AI
anthropic>=0.18.0

# HTTP
httpx>=0.27.0

# Testing
pytest>=8.0.0
allure-pytest>=2.13.0

# Data
pydantic>=2.5.0
pyyaml>=6.0.0
jsonpath-ng>=1.6.0

# CLI
typer>=0.9.0

# Config
python-dotenv>=1.0.0
```

---

## 十、MVP 交付清单

### 10.1 核心交付物

- [ ] 项目骨架代码
- [ ] AI 层：Claude SDK 封装 + 文档解析 + 用例生成
- [ ] 执行层：HTTP 客户端 + 断言引擎 + 变量管理 + 运行器
- [ ] 报告层：Allure 适配器
- [ ] CLI：`apiflow run` 命令
- [ ] 配置：`.env.example` + `config.yaml`
- [ ] 文档：README.md 使用说明
- [ ] 示例：示例 Swagger 文件 + 生成的测试计划

### 10.2 验收标准

1. 能解析一个 Swagger 3.0 文件
2. AI 能为每个接口生成 1 正向 + 1 异常用例
3. 能按依赖顺序执行测试用例
4. 能输出 Allure 测试报告
5. 单命令 `apiflow run` 跑通全流程

---

## 十一、版本规划

| 版本 | 目标 | 核心功能 |
|------|------|----------|
| v0.1 | MVP | 核心流程跑通 |
| v0.2 | 完善断言 | 更多断言类型 + 自定义断言 |
| v0.3 | 多格式支持 | Postman + OpenAPI 2.0 |
| v0.4 | CLI 增强 | 命令分离 + 环境切换 |
| v0.5 | 监控巡检 | 定时任务 + 告警通知 |
| v1.0 | 生产就绪 | 稳定性 + 文档完善 |

---

## 附录：设计决策记录

| 决策 | 选项 | 选择 | 原因 |
|------|------|------|------|
| 架构 | 单Agent/多Agent/混合 | 混合 | AI 做智能决策，代码做执行，节省 token |
| API 信息来源 | 文档/自然语言/代码分析 | 文档解析 | 标准化，准确 |
| 用例生成 | AI/模板/用户指定 | AI 智能生成 | 自动化程度高 |
| 依赖处理 | 自动/手动/交互确认 | AI推断+人工确认 | 平衡自动化与准确性 |
| 断言策略 | AI/Schema/用户定义/混合 | 混合 | AI 生成基础，用户可补充 |
| 报告格式 | Console/HTML/JSON/Allure | Allure | 业界标准，CI/CD 友好 |
| 配置管理 | 文件/数据库/环境变量 | 环境变量+配置文件 | 安全且灵活 |

---

*文档创建时间：2026-01-16*
*最后更新：2026-01-16*
