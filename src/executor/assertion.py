"""
断言引擎模块

根据断言规则校验 HTTP 响应。
"""

from dataclasses import dataclass
from typing import Any, List

from jsonpath_ng import parse as jsonpath_parse

from .http_client import HttpResponse


@dataclass
class AssertionResult:
    """断言结果"""
    passed: bool
    assertion_type: str
    expected: Any
    actual: Any
    message: str


class AssertionEngine:
    """断言引擎"""

    def check(self, response: HttpResponse, assertion: dict) -> AssertionResult:
        """
        执行单个断言

        Args:
            response: HTTP 响应
            assertion: 断言规则字典

        Returns:
            AssertionResult 对象
        """
        assertion_type = assertion.get("type")

        if assertion_type == "status_code":
            return self._check_status_code(response, assertion)
        elif assertion_type == "json_path":
            return self._check_json_path(response, assertion)
        else:
            return AssertionResult(
                passed=False,
                assertion_type=assertion_type,
                expected=None,
                actual=None,
                message=f"Unknown assertion type: {assertion_type}",
            )

    def check_all(self, response: HttpResponse, assertions: List[dict]) -> List[AssertionResult]:
        """
        执行所有断言

        Args:
            response: HTTP 响应
            assertions: 断言规则列表

        Returns:
            AssertionResult 列表
        """
        return [self.check(response, assertion) for assertion in assertions]

    def _check_status_code(self, response: HttpResponse, assertion: dict) -> AssertionResult:
        """检查 HTTP 状态码"""
        expected = assertion.get("expected")
        actual = response.status_code

        passed = actual == expected

        return AssertionResult(
            passed=passed,
            assertion_type="status_code",
            expected=expected,
            actual=actual,
            message=f"Status code: expected {expected}, got {actual}" if not passed else "Status code matched",
        )

    def _check_json_path(self, response: HttpResponse, assertion: dict) -> AssertionResult:
        """检查 JSON 路径"""
        path = assertion.get("path")
        operator = assertion.get("operator", "exists")
        expected = assertion.get("expected")

        # 使用 jsonpath-ng 提取值
        try:
            jsonpath_expr = jsonpath_parse(path)
            matches = jsonpath_expr.find(response.body)

            if not matches:
                actual = None
                exists = False
            else:
                actual = matches[0].value
                exists = True
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion_type="json_path",
                expected=expected,
                actual=None,
                message=f"JSONPath error: {e}",
            )

        # 根据操作符判断
        if operator == "exists":
            passed = exists
            message = f"Path {path}: exists={exists}"

        elif operator == "not_exists":
            passed = not exists
            message = f"Path {path}: exists={exists}, expected not to exist"

        elif operator == "equals":
            passed = actual == expected
            message = f"Path {path}: expected {expected}, got {actual}"

        elif operator == "not_equals":
            passed = actual != expected
            message = f"Path {path}: expected not {expected}, got {actual}"

        elif operator == "contains":
            passed = exists and expected in str(actual)
            message = f"Path {path}: '{actual}' contains '{expected}' = {passed}"

        elif operator == "greater_than":
            try:
                passed = exists and float(actual) > float(expected)
                message = f"Path {path}: {actual} > {expected} = {passed}"
            except (TypeError, ValueError):
                passed = False
                message = f"Path {path}: cannot compare {actual} > {expected}"

        elif operator == "less_than":
            try:
                passed = exists and float(actual) < float(expected)
                message = f"Path {path}: {actual} < {expected} = {passed}"
            except (TypeError, ValueError):
                passed = False
                message = f"Path {path}: cannot compare {actual} < {expected}"

        else:
            passed = False
            message = f"Unknown operator: {operator}"

        return AssertionResult(
            passed=passed,
            assertion_type="json_path",
            expected=expected if operator != "exists" else "exists",
            actual=actual,
            message=message,
        )
