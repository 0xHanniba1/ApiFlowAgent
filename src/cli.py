"""
ApiFlowAgent 命令行接口

提供 apiflow 命令行工具。

命令：
- generate: 解析 API 文档并生成测试计划（调用 AI）
- execute:  执行已有的测试计划（不调用 AI）
- run:      完整流程 = generate + execute
"""

import json
import os
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from .ai import APIParser, TestGenerator
from .executor import HttpClient, TestRunner
from .reporter import AllureReporter

load_dotenv()


app = typer.Typer(
    name="apiflow",
    help="AI-powered API test automation tool",
    add_completion=False,
)


def _parse_and_generate(doc_path: Path, output_path: Optional[Path] = None) -> tuple[dict, dict, Path]:
    """
    解析文档并生成测试计划（内部函数）

    Returns:
        (parsed_api, test_plan, plan_path)
    """
    # 解析 API 文档
    typer.echo(f"\n[1/2] Parsing API document: {doc_path}")
    parser = APIParser()
    parsed_api = parser.parse_file(doc_path)
    endpoint_count = len(parsed_api.get("endpoints", []))
    typer.echo(f"      Found {endpoint_count} endpoints")

    # 生成测试计划
    typer.echo("\n[2/2] Generating test plan (AI)...")
    generator = TestGenerator()
    test_plan = generator.generate(parsed_api)
    test_case_count = len(test_plan.get("test_cases", []))
    typer.echo(f"      Generated {test_case_count} test cases")

    # 确定输出路径
    if output_path is None:
        output_path = Path(f"data/test_plans/{doc_path.stem}_plan.json")

    # 保存测试计划
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(test_plan, f, indent=2, ensure_ascii=False)
    typer.echo(f"      Saved to: {output_path}")

    return parsed_api, test_plan, output_path


def _execute_plan(
    test_plan: dict,
    base_url: str,
    junit_output: Optional[Path] = None,
) -> int:
    """
    执行测试计划（内部函数）

    Returns:
        失败用例数
    """
    typer.echo(f"\n[1/2] Executing tests...")
    typer.echo(f"      Base URL: {base_url}")

    http_client = HttpClient(base_url=base_url)
    runner = TestRunner(http_client=http_client)
    result = runner.run(test_plan)

    # 生成报告
    typer.echo("\n[2/2] Generating report...")
    reporter = AllureReporter()
    reporter.print_summary(result)

    # 保存 JSON 结果
    results_path = reporter.save_results(result)
    typer.echo(f"      JSON report: {results_path}")

    # 保存 JUnit XML（如果指定）
    if junit_output:
        junit_path = reporter.save_junit_xml(result, junit_output)
        typer.echo(f"      JUnit XML:   {junit_path}")

    return result.failed


@app.command()
def generate(
    doc: str = typer.Option(..., "--doc", "-d", help="Path to API document (Swagger/OpenAPI)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output path for test plan"),
):
    """
    Parse API document and generate test plan (calls AI).

    Use this to generate test cases once, then commit to Git.

    Example:
        apiflow generate --doc swagger.json --output plan.json
    """
    typer.echo("=" * 60)
    typer.echo("ApiFlowAgent - Generate Test Plan")
    typer.echo("=" * 60)

    doc_path = Path(doc)
    if not doc_path.exists():
        typer.echo(f"Error: API document not found: {doc}", err=True)
        raise typer.Exit(1)

    output_path = Path(output) if output else None

    try:
        _, test_plan, plan_path = _parse_and_generate(doc_path, output_path)
        typer.echo("\n" + "=" * 60)
        typer.echo("Generation complete!")
        typer.echo(f"Test plan saved to: {plan_path}")
        typer.echo("Next step: Review the plan, then run:")
        typer.echo(f"  apiflow execute --plan {plan_path}")
        typer.echo("=" * 60)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def execute(
    plan: str = typer.Option(..., "--plan", "-p", help="Path to test plan JSON"),
    base_url: Optional[str] = typer.Option(None, "--base-url", "-b", help="API base URL"),
    junit: Optional[str] = typer.Option(None, "--junit", "-j", help="Output JUnit XML report path"),
):
    """
    Execute an existing test plan (no AI calls).

    Use this in CI/CD pipelines for fast, repeatable test execution.

    Example:
        apiflow execute --plan plan.json --base-url https://api.example.com
        apiflow execute --plan plan.json --junit reports/junit.xml
    """
    typer.echo("=" * 60)
    typer.echo("ApiFlowAgent - Execute Test Plan")
    typer.echo("=" * 60)

    plan_path = Path(plan)
    if not plan_path.exists():
        typer.echo(f"Error: Test plan not found: {plan}", err=True)
        raise typer.Exit(1)

    # 加载测试计划
    typer.echo(f"\nLoading test plan: {plan_path}")
    with open(plan_path, "r", encoding="utf-8") as f:
        test_plan = json.load(f)

    test_case_count = len(test_plan.get("test_cases", []))
    typer.echo(f"Found {test_case_count} test cases")

    # 确定 base_url
    effective_base_url = base_url or os.getenv("API_BASE_URL")
    if not effective_base_url:
        typer.echo("Error: No base URL. Provide --base-url or set API_BASE_URL env var.", err=True)
        raise typer.Exit(1)

    junit_path = Path(junit) if junit else None

    try:
        failed_count = _execute_plan(test_plan, effective_base_url, junit_path)
        if failed_count > 0:
            raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def run(
    doc: str = typer.Option(..., "--doc", "-d", help="Path to API document (Swagger/OpenAPI)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output path for test plan"),
    base_url: Optional[str] = typer.Option(None, "--base-url", "-b", help="Override API base URL"),
    junit: Optional[str] = typer.Option(None, "--junit", "-j", help="Output JUnit XML report path"),
    save_plan: bool = typer.Option(True, "--save-plan/--no-save-plan", help="Save generated test plan"),
):
    """
    Run complete flow: parse → generate → execute → report.

    This is a shortcut that combines 'generate' and 'execute'.
    For CI/CD, prefer using 'generate' once and 'execute' repeatedly.

    Example:
        apiflow run --doc swagger.json --base-url https://api.example.com
    """
    typer.echo("=" * 60)
    typer.echo("ApiFlowAgent - Full Test Flow")
    typer.echo("=" * 60)

    doc_path = Path(doc)
    if not doc_path.exists():
        typer.echo(f"Error: API document not found: {doc}", err=True)
        raise typer.Exit(1)

    output_path = Path(output) if output else None

    try:
        # Step 1: 解析并生成
        parsed_api, test_plan, plan_path = _parse_and_generate(doc_path, output_path)

        if not save_plan:
            plan_path.unlink(missing_ok=True)

        # Step 2: 确定 base_url
        effective_base_url = (
            base_url
            or os.getenv("API_BASE_URL")
            or parsed_api.get("info", {}).get("base_url")
        )
        if not effective_base_url:
            typer.echo(
                "Error: No base URL. Provide --base-url, set API_BASE_URL, "
                "or include servers in API doc.",
                err=True
            )
            raise typer.Exit(1)

        # Step 3: 执行
        junit_path = Path(junit) if junit else None
        failed_count = _execute_plan(test_plan, effective_base_url, junit_path)

        if failed_count > 0:
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    typer.echo("ApiFlowAgent v0.1.0")


def main():
    """CLI 入口点"""
    app()


if __name__ == "__main__":
    main()
