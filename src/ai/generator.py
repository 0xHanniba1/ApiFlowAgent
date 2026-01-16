"""
测试用例生成模块

使用 Claude 根据 API 定义生成测试用例、推断依赖关系、生成断言。
"""

import json
from datetime import datetime
from typing import Optional

from .client import AIClient


# 测试用例生成的系统提示词
GENERATOR_SYSTEM_PROMPT = """You are a professional API test case generator. Your task is to generate comprehensive test cases based on API endpoint definitions.

For each endpoint, generate:
1. One positive test case (valid inputs, expected success)
2. One negative test case (invalid/missing inputs, expected error)

You must also:
1. Infer dependencies between endpoints (e.g., login must happen before accessing protected resources)
2. Generate appropriate assertions for each test case
3. Identify variables to extract from responses for use in subsequent requests

Output the complete test plan in JSON format:
{
  "meta": {
    "name": "Test plan name",
    "version": "1.0",
    "generated_at": "ISO timestamp"
  },
  "endpoints": [...],  // Copy from input
  "test_cases": [
    {
      "id": "tc_endpoint_positive",
      "name": "测试用例中文名称",
      "endpoint_id": "endpoint_id",
      "category": "positive" | "negative",
      "priority": "high" | "medium" | "low",
      "inputs": {
        "path_params": {},
        "query_params": {},
        "headers": {},
        "body": {}
      },
      "assertions": [
        {"type": "status_code", "expected": 200},
        {"type": "json_path", "path": "$.field", "operator": "exists"},
        {"type": "json_path", "path": "$.code", "operator": "equals", "expected": 0}
      ],
      "extract": [
        {"name": "variable_name", "from": "$.json.path"}
      ]
    }
  ],
  "execution_order": ["tc_id_1", "tc_id_2", ...],
  "dependencies": {
    "tc_id_2": {
      "depends_on": "tc_id_1",
      "inject": {
        "headers.Authorization": "Bearer {{token}}"
      }
    }
  }
}

Assertion operators:
- exists: Field exists
- equals: Exact value match
- not_equals: Value doesn't match
- contains: String contains
- greater_than: Numeric comparison
- less_than: Numeric comparison"""


GENERATOR_USER_PROMPT_TEMPLATE = """Based on the following API endpoints, generate a complete test plan.

API Endpoints:
```json
{endpoints_json}
```

Requirements:
1. Generate 1 positive + 1 negative test case for each endpoint
2. For positive cases: use realistic valid test data
3. For negative cases: test missing required fields or invalid data types
4. Infer dependencies (e.g., auth endpoints should run first)
5. Generate meaningful assertions based on expected responses
6. Extract important response values (tokens, IDs) for subsequent requests
7. Use Chinese for test case names

Current timestamp for generated_at: {timestamp}

Output only valid JSON."""


class TestGenerator:
    """测试用例生成器"""

    def __init__(self, ai_client: AIClient = None):
        """
        初始化生成器

        Args:
            ai_client: AI 客户端实例，如不传则自动创建
        """
        self.ai_client = ai_client or AIClient()

    def generate(self, parsed_api: dict, name: Optional[str] = None) -> dict:
        """
        生成测试计划

        Args:
            parsed_api: 解析后的 API 定义（来自 APIParser）
            name: 测试计划名称（可选）

        Returns:
            完整的测试计划字典
        """
        # 准备端点信息
        endpoints = parsed_api.get("endpoints", [])
        if not endpoints:
            raise ValueError("No endpoints found in parsed API")

        # 生成时间戳
        timestamp = datetime.now().isoformat()

        # 构造提示词
        prompt = GENERATOR_USER_PROMPT_TEMPLATE.format(
            endpoints_json=json.dumps(endpoints, indent=2, ensure_ascii=False),
            timestamp=timestamp,
        )

        # 调用 AI 生成测试计划
        test_plan = self.ai_client.generate_json(
            prompt=prompt,
            system_prompt=GENERATOR_SYSTEM_PROMPT,
            max_tokens=8192,
        )

        # 补充元信息
        if name:
            test_plan["meta"]["name"] = name

        # 确保 endpoints 包含在输出中
        if "endpoints" not in test_plan:
            test_plan["endpoints"] = endpoints

        return test_plan

    def generate_from_file(self, parsed_api: dict, output_path: str) -> dict:
        """
        生成测试计划并保存到文件

        Args:
            parsed_api: 解析后的 API 定义
            output_path: 输出文件路径

        Returns:
            生成的测试计划字典
        """
        test_plan = self.generate(parsed_api)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(test_plan, f, indent=2, ensure_ascii=False)

        return test_plan
