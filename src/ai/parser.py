"""
API 文档解析模块

使用 Claude 解析 Swagger/OpenAPI 文档，提取标准化的接口定义。
"""

import json
import yaml
from pathlib import Path
from typing import Union

from .client import AIClient


# 文档解析的系统提示词
PARSER_SYSTEM_PROMPT = """You are an API documentation parser. Your task is to analyze OpenAPI/Swagger documents and extract endpoint information into a standardized JSON format.

For each endpoint, extract:
- id: A unique identifier (e.g., "get_users", "create_order")
- name: Human-readable name in Chinese
- method: HTTP method (GET, POST, PUT, DELETE, etc.)
- path: The endpoint path
- summary: Brief description
- parameters: Query and path parameters
- request_body: Request body schema (if applicable)
- responses: Expected response schemas

Output format:
{
  "info": {
    "title": "API title",
    "version": "API version",
    "base_url": "Base URL if specified"
  },
  "endpoints": [
    {
      "id": "unique_endpoint_id",
      "name": "接口中文名称",
      "method": "POST",
      "path": "/api/users",
      "summary": "Description",
      "parameters": [
        {"name": "id", "in": "path", "type": "integer", "required": true}
      ],
      "request_body": {
        "content_type": "application/json",
        "schema": {"type": "object", "properties": {...}}
      },
      "responses": {
        "200": {"description": "Success", "schema": {...}}
      }
    }
  ]
}"""


PARSER_USER_PROMPT_TEMPLATE = """Please parse the following OpenAPI/Swagger document and extract all endpoints into the standardized JSON format.

API Document:
```
{api_doc}
```

Remember:
1. Generate meaningful Chinese names for each endpoint
2. Extract all parameters (path, query, header)
3. Include request body schema if present
4. Include response schemas
5. Generate a unique id for each endpoint (snake_case, based on method and path)

Output only valid JSON, no markdown or explanation."""


class APIParser:
    """API 文档解析器"""

    def __init__(self, ai_client: AIClient = None):
        """
        初始化解析器

        Args:
            ai_client: AI 客户端实例，如不传则自动创建
        """
        self.ai_client = ai_client or AIClient()

    def load_file(self, file_path: Union[str, Path]) -> str:
        """
        加载 API 文档文件

        Args:
            file_path: 文件路径（支持 JSON 和 YAML）

        Returns:
            文档内容字符串
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"API document not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")

        # 如果是 YAML，转换为 JSON 字符串（便于 AI 处理）
        if file_path.suffix in [".yaml", ".yml"]:
            data = yaml.safe_load(content)
            content = json.dumps(data, indent=2, ensure_ascii=False)

        return content

    def parse(self, api_doc: str) -> dict:
        """
        解析 API 文档内容

        Args:
            api_doc: API 文档内容（JSON 或 YAML 字符串）

        Returns:
            标准化的接口定义字典
        """
        prompt = PARSER_USER_PROMPT_TEMPLATE.format(api_doc=api_doc)

        result = self.ai_client.generate_json(
            prompt=prompt,
            system_prompt=PARSER_SYSTEM_PROMPT,
            max_tokens=8192,  # 文档解析可能需要更多 token
        )

        return result

    def parse_file(self, file_path: Union[str, Path]) -> dict:
        """
        解析 API 文档文件

        Args:
            file_path: 文件路径

        Returns:
            标准化的接口定义字典
        """
        content = self.load_file(file_path)
        return self.parse(content)
