"""
Allure 报告适配器模块

将测试结果转换为 Allure 报告格式和 JUnit XML 格式。
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Optional

import allure
from allure_commons.types import AttachmentType

from ..executor.runner import TestCaseResult, TestPlanResult


class AllureReporter:
    """Allure 报告生成器"""

    def __init__(self, results_dir: str = "reports/allure-results"):
        """
        初始化报告生成器

        Args:
            results_dir: Allure 结果输出目录
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def report_test_case(self, result: TestCaseResult) -> None:
        """
        报告单个测试用例结果

        在 pytest 测试函数中调用此方法来记录 Allure 信息

        Args:
            result: 测试用例执行结果
        """
        # 添加描述
        allure.dynamic.title(result.test_case_name)
        allure.dynamic.description(
            f"Endpoint: {result.endpoint_id}\n"
            f"Category: {result.category}\n"
            f"Elapsed: {result.elapsed_ms:.2f}ms"
        )

        # 添加标签
        allure.dynamic.tag(result.category)
        allure.dynamic.tag(result.endpoint_id)

        # 添加请求详情
        allure.attach(
            json.dumps(result.request, indent=2, ensure_ascii=False),
            name="Request",
            attachment_type=AttachmentType.JSON,
        )

        # 添加响应详情
        if result.response:
            allure.attach(
                json.dumps(result.response, indent=2, ensure_ascii=False),
                name="Response",
                attachment_type=AttachmentType.JSON,
            )

        # 添加断言详情
        assertions_info = []
        for assertion in result.assertions:
            assertions_info.append({
                "type": assertion.assertion_type,
                "passed": assertion.passed,
                "expected": assertion.expected,
                "actual": assertion.actual,
                "message": assertion.message,
            })

        allure.attach(
            json.dumps(assertions_info, indent=2, ensure_ascii=False),
            name="Assertions",
            attachment_type=AttachmentType.JSON,
        )

        # 添加提取的变量
        if result.extracted_variables:
            allure.attach(
                json.dumps(result.extracted_variables, indent=2, ensure_ascii=False),
                name="Extracted Variables",
                attachment_type=AttachmentType.JSON,
            )

        # 如果有错误，添加错误信息
        if result.error:
            allure.attach(
                result.error,
                name="Error",
                attachment_type=AttachmentType.TEXT,
            )

    def generate_summary(self, plan_result: TestPlanResult) -> dict:
        """
        生成测试摘要

        Args:
            plan_result: 测试计划执行结果

        Returns:
            摘要字典
        """
        summary = {
            "plan_name": plan_result.plan_name,
            "total": plan_result.total,
            "passed": plan_result.passed,
            "failed": plan_result.failed,
            "pass_rate": f"{plan_result.pass_rate:.1f}%",
            "elapsed_ms": plan_result.elapsed_ms,
            "timestamp": plan_result.timestamp,
            "results": [],
        }

        for result in plan_result.results:
            summary["results"].append({
                "id": result.test_case_id,
                "name": result.test_case_name,
                "passed": result.passed,
                "elapsed_ms": result.elapsed_ms,
                "error": result.error,
            })

        return summary

    def save_results(self, plan_result: TestPlanResult, output_path: Optional[str] = None) -> str:
        """
        保存测试结果到 JSON 文件

        Args:
            plan_result: 测试计划执行结果
            output_path: 输出文件路径（可选）

        Returns:
            输出文件路径
        """
        if output_path is None:
            output_path = self.results_dir / "test_results.json"

        summary = self.generate_summary(plan_result)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return str(output_path)

    def save_junit_xml(self, plan_result: TestPlanResult, output_path: Optional[str] = None) -> str:
        """
        保存测试结果为 JUnit XML 格式（Jenkins 原生支持）

        Args:
            plan_result: 测试计划执行结果
            output_path: 输出文件路径（可选）

        Returns:
            输出文件路径
        """
        if output_path is None:
            output_path = self.results_dir / "junit_report.xml"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建 testsuite 元素
        testsuite = ET.Element("testsuite")
        testsuite.set("name", plan_result.plan_name)
        testsuite.set("tests", str(plan_result.total))
        testsuite.set("failures", str(plan_result.failed))
        testsuite.set("errors", "0")
        testsuite.set("time", f"{plan_result.elapsed_ms / 1000:.3f}")
        testsuite.set("timestamp", plan_result.timestamp)

        # 添加每个测试用例
        for result in plan_result.results:
            testcase = ET.SubElement(testsuite, "testcase")
            testcase.set("name", result.test_case_name)
            testcase.set("classname", result.endpoint_id)
            testcase.set("time", f"{result.elapsed_ms / 1000:.3f}")

            if not result.passed:
                failure = ET.SubElement(testcase, "failure")
                failure.set("type", "AssertionError")

                # 收集失败的断言信息
                failed_assertions = [
                    a for a in result.assertions if not a.passed
                ]
                if failed_assertions:
                    messages = []
                    for a in failed_assertions:
                        messages.append(
                            f"{a.assertion_type}: expected {a.expected}, got {a.actual}"
                        )
                    failure.set("message", "; ".join(messages))
                    failure.text = "\n".join(messages)
                elif result.error:
                    failure.set("message", result.error)
                    failure.text = result.error

        # 写入文件
        tree = ET.ElementTree(testsuite)
        ET.indent(tree, space="  ")
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

        return str(output_path)

    def print_summary(self, plan_result: TestPlanResult) -> None:
        """
        打印测试摘要到控制台

        Args:
            plan_result: 测试计划执行结果
        """
        print("\n" + "=" * 60)
        print(f"Test Plan: {plan_result.plan_name}")
        print("=" * 60)
        print(f"Total: {plan_result.total}")
        print(f"Passed: {plan_result.passed}")
        print(f"Failed: {plan_result.failed}")
        print(f"Pass Rate: {plan_result.pass_rate:.1f}%")
        print(f"Elapsed: {plan_result.elapsed_ms:.2f}ms")
        print("-" * 60)

        for result in plan_result.results:
            status = "✓" if result.passed else "✗"
            print(f"  {status} {result.test_case_name} ({result.elapsed_ms:.0f}ms)")
            if result.error:
                print(f"      Error: {result.error}")

        print("=" * 60 + "\n")
