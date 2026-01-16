"""
ApiFlowAgent 命令行接口

提供 apiflow 命令行工具。
"""

import json
from pathlib import Path
from typing import Optional

import typer

from .ai import APIParser, TestGenerator
from .executor import HttpClient, TestRunner
from .reporter import AllureReporter


app = typer.Typer(
    name="apiflow",
    help="AI-powered API test automation tool",
    add_completion=False,
)


@app.command()
def run(
    doc: str = typer.Option(..., "--doc", "-d", help="Path to API document (Swagger/OpenAPI)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output path for test plan"),
    base_url: Optional[str] = typer.Option(None, "--base-url", "-b", help="Override API base URL"),
    save_plan: bool = typer.Option(True, "--save-plan/--no-save-plan", help="Save generated test plan"),
):
    """
    Run the complete API test flow: parse → generate → execute → report
    """
    typer.echo("=" * 60)
    typer.echo("ApiFlowAgent - AI-powered API Test Automation")
    typer.echo("=" * 60)

    # 检查文件是否存在
    doc_path = Path(doc)
    if not doc_path.exists():
        typer.echo(f"Error: API document not found: {doc}", err=True)
        raise typer.Exit(1)

    # Step 1: 解析 API 文档
    typer.echo(f"\n[1/4] Parsing API document: {doc}")
    parser = APIParser()
    try:
        parsed_api = parser.parse_file(doc_path)
        endpoint_count = len(parsed_api.get("endpoints", []))
        typer.echo(f"      Found {endpoint_count} endpoints")
    except Exception as e:
        typer.echo(f"Error parsing document: {e}", err=True)
        raise typer.Exit(1)

    # Step 2: 生成测试计划
    typer.echo("\n[2/4] Generating test plan...")
    generator = TestGenerator()
    try:
        test_plan = generator.generate(parsed_api)
        test_case_count = len(test_plan.get("test_cases", []))
        typer.echo(f"      Generated {test_case_count} test cases")
    except Exception as e:
        typer.echo(f"Error generating test plan: {e}", err=True)
        raise typer.Exit(1)

    # 保存测试计划
    if save_plan:
        plan_output = output or f"data/test_plans/{doc_path.stem}_plan.json"
        plan_path = Path(plan_output)
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(test_plan, f, indent=2, ensure_ascii=False)
        typer.echo(f"      Saved test plan to: {plan_path}")

    # Step 3: 执行测试
    typer.echo("\n[3/4] Executing tests...")
    http_client = HttpClient(base_url=base_url) if base_url else HttpClient()
    runner = TestRunner(http_client=http_client)
    try:
        result = runner.run(test_plan)
    except Exception as e:
        typer.echo(f"Error executing tests: {e}", err=True)
        raise typer.Exit(1)

    # Step 4: 生成报告
    typer.echo("\n[4/4] Generating report...")
    reporter = AllureReporter()
    reporter.print_summary(result)

    # 保存结果
    results_path = reporter.save_results(result)
    typer.echo(f"      Results saved to: {results_path}")

    # 返回状态码
    if result.failed > 0:
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information"""
    typer.echo("ApiFlowAgent v0.1.0 (MVP)")


def main():
    """CLI 入口点"""
    app()


if __name__ == "__main__":
    main()
