# ApiFlowAgent

AI 驱动的 API 自动化测试工具，基于 Claude SDK。

## 功能特性

- 自动解析 Swagger/OpenAPI 文档
- AI 智能生成测试用例
- 自动推断接口依赖关系
- 执行测试并生成 Allure / JUnit 报告
- 支持 Jenkins CI/CD 集成

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
pip install -e .
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 使用方式

#### 方式一：分离式（推荐用于 CI/CD）

```bash
# 1. 生成测试计划（调用 AI，本地执行一次）
apiflow generate --doc data/api_docs/swagger.json

# 2. 执行测试计划（不调用 AI，可重复执行）
apiflow execute --plan data/test_plans/xxx_plan.json --base-url https://api.example.com
```

#### 方式二：一键式（调试/演示）

```bash
apiflow run --doc data/api_docs/swagger.json
```

## 命令参考

```bash
# 生成测试计划
apiflow generate --doc <swagger.json> [--output <plan.json>]

# 执行测试计划
apiflow execute --plan <plan.json> [--base-url URL] [--junit <report.xml>]

# 完整流程
apiflow run --doc <swagger.json> [--base-url URL] [--junit <report.xml>]

# 查看版本
apiflow version
```

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
                sh '''
                    pip install -e .
                    apiflow execute \
                        --plan data/test_plans/plan.json \
                        --junit reports/junit.xml
                '''
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

当前版本：v0.1.1

详见 [project-status.md](docs/project-status.md)
