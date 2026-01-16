"""
测试运行器模块

编排测试用例的执行流程。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .http_client import HttpClient, HttpResponse
from .assertion import AssertionEngine, AssertionResult
from .variable import VariableManager


@dataclass
class TestCaseResult:
    """测试用例执行结果"""
    test_case_id: str
    test_case_name: str
    endpoint_id: str
    category: str  # positive / negative
    passed: bool
    request: dict
    response: Optional[dict]
    assertions: List[AssertionResult]
    extracted_variables: Dict[str, Any]
    elapsed_ms: float
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TestPlanResult:
    """测试计划执行结果"""
    plan_name: str
    total: int
    passed: int
    failed: int
    results: List[TestCaseResult]
    elapsed_ms: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def pass_rate(self) -> float:
        """通过率"""
        return self.passed / self.total * 100 if self.total > 0 else 0


class TestRunner:
    """测试运行器"""

    def __init__(
        self,
        http_client: Optional[HttpClient] = None,
        continue_on_failure: bool = True,
    ):
        """
        初始化测试运行器

        Args:
            http_client: HTTP 客户端，如不传则自动创建
            continue_on_failure: 失败后是否继续执行
        """
        self.http_client = http_client or HttpClient()
        self.assertion_engine = AssertionEngine()
        self.variable_manager = VariableManager()
        self.continue_on_failure = continue_on_failure

    def run(self, test_plan: dict) -> TestPlanResult:
        """
        执行测试计划

        Args:
            test_plan: 测试计划字典

        Returns:
            TestPlanResult 对象
        """
        start_time = datetime.now()

        # 提取测试计划信息
        meta = test_plan.get("meta", {})
        plan_name = meta.get("name", "Unnamed Test Plan")
        endpoints = {ep["id"]: ep for ep in test_plan.get("endpoints", [])}
        test_cases = test_plan.get("test_cases", [])
        execution_order = test_plan.get("execution_order", [tc["id"] for tc in test_cases])
        dependencies = test_plan.get("dependencies", {})

        # 按执行顺序构建用例映射
        tc_map = {tc["id"]: tc for tc in test_cases}

        results = []
        passed_count = 0
        failed_count = 0

        for tc_id in execution_order:
            test_case = tc_map.get(tc_id)
            if not test_case:
                continue

            # 注入依赖变量
            test_case = self.variable_manager.inject_dependencies(test_case, dependencies)

            # 执行测试用例
            result = self._run_test_case(test_case, endpoints)
            results.append(result)

            if result.passed:
                passed_count += 1
            else:
                failed_count += 1
                if not self.continue_on_failure:
                    break

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        return TestPlanResult(
            plan_name=plan_name,
            total=len(results),
            passed=passed_count,
            failed=failed_count,
            results=results,
            elapsed_ms=elapsed_ms,
        )

    def _run_test_case(self, test_case: dict, endpoints: dict) -> TestCaseResult:
        """
        执行单个测试用例

        Args:
            test_case: 测试用例字典
            endpoints: 端点定义映射

        Returns:
            TestCaseResult 对象
        """
        tc_id = test_case.get("id")
        tc_name = test_case.get("name", tc_id)
        endpoint_id = test_case.get("endpoint_id")
        category = test_case.get("category", "positive")
        inputs = test_case.get("inputs", {})
        assertions = test_case.get("assertions", [])
        extracts = test_case.get("extract", [])

        # 获取端点定义
        endpoint = endpoints.get(endpoint_id, {})
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "")

        # 替换路径中的变量
        path = self.variable_manager.substitute(path)

        # 处理路径参数
        path_params = inputs.get("path_params", {})
        path_params = self.variable_manager.substitute(path_params)
        for param_name, param_value in path_params.items():
            path = path.replace(f"{{{param_name}}}", str(param_value))

        # 处理请求参数
        query_params = inputs.get("query_params", {})
        query_params = self.variable_manager.substitute(query_params)

        headers = inputs.get("headers", {})
        headers = self.variable_manager.substitute(headers)

        body = inputs.get("body")
        if body:
            body = self.variable_manager.substitute(body)

        # 构造请求信息（用于报告）
        request_info = {
            "method": method,
            "path": path,
            "headers": headers,
            "params": query_params,
            "body": body,
        }

        try:
            # 发送请求
            response = self.http_client.request(
                method=method,
                path=path,
                headers=headers if headers else None,
                params=query_params if query_params else None,
                body=body,
            )

            # 执行断言
            assertion_results = self.assertion_engine.check_all(response, assertions)
            all_passed = all(r.passed for r in assertion_results)

            # 提取变量
            extracted = self.variable_manager.extract(response, extracts)

            # 构造响应信息（用于报告）
            response_info = {
                "status_code": response.status_code,
                "headers": response.headers,
                "body": response.body,
                "elapsed_ms": response.elapsed_ms,
            }

            return TestCaseResult(
                test_case_id=tc_id,
                test_case_name=tc_name,
                endpoint_id=endpoint_id,
                category=category,
                passed=all_passed,
                request=request_info,
                response=response_info,
                assertions=assertion_results,
                extracted_variables=extracted,
                elapsed_ms=response.elapsed_ms,
            )

        except Exception as e:
            return TestCaseResult(
                test_case_id=tc_id,
                test_case_name=tc_name,
                endpoint_id=endpoint_id,
                category=category,
                passed=False,
                request=request_info,
                response=None,
                assertions=[],
                extracted_variables={},
                elapsed_ms=0,
                error=str(e),
            )
