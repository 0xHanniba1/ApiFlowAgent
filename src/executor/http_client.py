"""
HTTP 客户端模块

封装 httpx，提供统一的 HTTP 请求接口。
"""

import os
from typing import Any, Optional
from dataclasses import dataclass, field

import httpx
from dotenv import load_dotenv


@dataclass
class HttpResponse:
    """HTTP 响应封装"""
    status_code: int
    headers: dict
    body: Any  # 可能是 dict、list 或 str
    elapsed_ms: float  # 响应时间（毫秒）
    raw_text: str  # 原始响应文本


@dataclass
class HttpRequest:
    """HTTP 请求封装"""
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)  # Query 参数
    body: Any = None  # 请求体


class HttpClient:
    """HTTP 客户端"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        default_headers: Optional[dict] = None,
    ):
        """
        初始化 HTTP 客户端

        Args:
            base_url: API 基础 URL，如不传则从环境变量读取
            timeout: 请求超时时间（秒）
            default_headers: 默认请求头
        """
        load_dotenv()

        self.base_url = (base_url or os.getenv("API_BASE_URL", "")).rstrip("/")
        self.timeout = timeout
        self.default_headers = default_headers or {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self.default_headers,
        )

    def request(
        self,
        method: str,
        path: str,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        body: Any = None,
    ) -> HttpResponse:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE 等)
            path: 请求路径
            headers: 请求头（会与默认请求头合并）
            params: Query 参数
            body: 请求体

        Returns:
            HttpResponse 对象
        """
        # 合并请求头
        merged_headers = {**self.default_headers}
        if headers:
            merged_headers.update(headers)

        # 构造请求参数
        request_kwargs = {
            "method": method.upper(),
            "url": path,
            "headers": merged_headers,
        }

        if params:
            request_kwargs["params"] = params

        if body is not None:
            request_kwargs["json"] = body

        # 发送请求
        response = self.client.request(**request_kwargs)

        # 解析响应体
        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        return HttpResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=response_body,
            elapsed_ms=response.elapsed.total_seconds() * 1000,
            raw_text=response.text,
        )

    def get(self, path: str, **kwargs) -> HttpResponse:
        """发送 GET 请求"""
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> HttpResponse:
        """发送 POST 请求"""
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> HttpResponse:
        """发送 PUT 请求"""
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> HttpResponse:
        """发送 DELETE 请求"""
        return self.request("DELETE", path, **kwargs)

    def close(self):
        """关闭客户端"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
