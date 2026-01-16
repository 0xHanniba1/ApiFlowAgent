"""
Claude SDK 封装模块

提供与 Claude API 交互的统一接口，用于文档解析和测试用例生成。
"""

import os
import json
from typing import Optional

import anthropic
from dotenv import load_dotenv


class AIClient:
    """Claude SDK 客户端封装"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """
        初始化 AI 客户端

        Args:
            api_key: Anthropic API Key，如不传则从环境变量读取
            model: 使用的模型，默认 claude-sonnet-4-20250514
        """
        load_dotenv()

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Set it in .env or pass it directly.")

        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> str:
        """
        调用 Claude 生成内容

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            max_tokens: 最大生成 token 数
            temperature: 温度参数，0 表示确定性输出

        Returns:
            生成的文本内容
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> dict:
        """
        调用 Claude 生成 JSON 格式内容

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            max_tokens: 最大生成 token 数

        Returns:
            解析后的 JSON 字典
        """
        # 增强系统提示词，强调 JSON 输出
        json_system_prompt = (system_prompt or "") + "\n\nYou must respond with valid JSON only. No markdown, no explanation, just pure JSON."

        response_text = self.generate(
            prompt=prompt,
            system_prompt=json_system_prompt.strip(),
            max_tokens=max_tokens,
            temperature=0.0,  # JSON 输出需要确定性
        )

        # 清理可能的 markdown 代码块标记
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        return json.loads(response_text)
