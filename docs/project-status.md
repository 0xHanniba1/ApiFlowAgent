# 项目状态

## 已完成

### v0.1.0 MVP
- [x] 项目需求梳理
- [x] 架构设计
- [x] 功能模块规划
- [x] 文档结构建立
- [x] 项目初始化（目录结构、依赖配置）
- [x] AI 层：Claude SDK 封装 (`src/ai/client.py`)
- [x] AI 层：文档解析模块 (`src/ai/parser.py`)
- [x] AI 层：用例生成模块 (`src/ai/generator.py`)
- [x] 执行层：HTTP 客户端 (`src/executor/http_client.py`)
- [x] 执行层：断言引擎 (`src/executor/assertion.py`)
- [x] 执行层：变量管理 (`src/executor/variable.py`)
- [x] 执行层：测试运行器 (`src/executor/runner.py`)
- [x] 报告层：Allure 适配器 (`src/reporter/allure_adapter.py`)
- [x] CLI：apiflow run 命令 (`src/cli.py`)
- [x] 准备示例 Swagger 文件 (`data/api_docs/sample_user_api.json`)
- [x] 端到端测试验证

### v0.1.1 命令分离 & Jenkins 集成
- [x] CLI：apiflow generate 命令（仅生成测试计划）
- [x] CLI：apiflow execute 命令（仅执行测试计划）
- [x] 报告层：JUnit XML 输出（Jenkins 原生支持）
- [x] 重构 apiflow run 命令（组合 generate + execute）

## 当前版本

**v0.1.1** - 命令分离版本

## 使用方式

### 方式一：分离式（推荐用于 CI/CD）

```bash
# 开发阶段：生成测试计划（调用 AI）
apiflow generate --doc data/api_docs/swagger.json

# CI 阶段：执行测试计划（不调用 AI，快速）
apiflow execute --plan data/test_plans/xxx_plan.json --junit reports/junit.xml
```

### 方式二：一键式（调试/演示）

```bash
apiflow run --doc data/api_docs/swagger.json
```

## 待开始

- [ ] v0.2：完善断言类型（contains, regex, length 等）
- [ ] v0.3：多格式支持（Postman Collection, OpenAPI 2.0）
- [ ] v0.4：CLI 增强（--filter, --env 参数）
- [ ] v0.5：监控巡检（定时任务 + 告警）

## Jenkins 集成

```groovy
pipeline {
    agent any
    environment {
        API_BASE_URL = 'https://your-api.com'
    }
    stages {
        stage('API Tests') {
            steps {
                sh 'apiflow execute --plan data/test_plans/plan.json --junit reports/junit.xml'
            }
            post {
                always {
                    junit 'reports/junit.xml'
                }
            }
        }
    }
}
```
