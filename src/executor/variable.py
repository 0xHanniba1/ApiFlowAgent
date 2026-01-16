"""
变量管理模块

负责从响应中提取变量，以及将变量注入到请求中。
"""

import re
from typing import Any, Dict, List, Optional

from jsonpath_ng import parse as jsonpath_parse

from .http_client import HttpResponse


class VariableManager:
    """变量管理器"""

    def __init__(self):
        """初始化变量管理器"""
        self._variables: Dict[str, Any] = {}

    @property
    def variables(self) -> Dict[str, Any]:
        """获取所有变量"""
        return self._variables.copy()

    def set(self, name: str, value: Any) -> None:
        """
        设置变量

        Args:
            name: 变量名
            value: 变量值
        """
        self._variables[name] = value

    def get(self, name: str, default: Any = None) -> Any:
        """
        获取变量

        Args:
            name: 变量名
            default: 默认值

        Returns:
            变量值
        """
        return self._variables.get(name, default)

    def clear(self) -> None:
        """清空所有变量"""
        self._variables.clear()

    def extract(self, response: HttpResponse, extracts: List[dict]) -> Dict[str, Any]:
        """
        从响应中提取变量

        Args:
            response: HTTP 响应
            extracts: 提取规则列表，格式：[{"name": "var_name", "from": "$.json.path"}]

        Returns:
            提取的变量字典
        """
        extracted = {}

        for extract in extracts:
            name = extract.get("name")
            json_path = extract.get("from")

            if not name or not json_path:
                continue

            try:
                jsonpath_expr = jsonpath_parse(json_path)
                matches = jsonpath_expr.find(response.body)

                if matches:
                    value = matches[0].value
                    self._variables[name] = value
                    extracted[name] = value
            except Exception:
                # 提取失败时跳过
                pass

        return extracted

    def substitute(self, data: Any) -> Any:
        """
        替换数据中的变量占位符

        支持 {{variable_name}} 格式的占位符

        Args:
            data: 待替换的数据（可以是 str、dict、list）

        Returns:
            替换后的数据
        """
        if isinstance(data, str):
            return self._substitute_string(data)
        elif isinstance(data, dict):
            return {k: self.substitute(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.substitute(item) for item in data]
        else:
            return data

    def _substitute_string(self, text: str) -> str:
        """替换字符串中的变量占位符"""
        pattern = r"\{\{(\w+)\}\}"

        def replacer(match):
            var_name = match.group(1)
            value = self._variables.get(var_name)
            if value is not None:
                return str(value)
            return match.group(0)  # 未找到变量时保留原样

        return re.sub(pattern, replacer, text)

    def inject_dependencies(self, test_case: dict, dependencies: dict) -> dict:
        """
        根据依赖配置注入变量到测试用例

        Args:
            test_case: 测试用例字典
            dependencies: 依赖配置

        Returns:
            注入后的测试用例
        """
        tc_id = test_case.get("id")
        dep_config = dependencies.get(tc_id)

        if not dep_config:
            return test_case

        inject_rules = dep_config.get("inject", {})

        # 深拷贝测试用例以避免修改原数据
        import copy
        test_case = copy.deepcopy(test_case)

        # 处理注入规则
        for key, value_template in inject_rules.items():
            # 替换模板中的变量
            value = self.substitute(value_template)

            # 解析 key 路径，例如 "headers.Authorization"
            parts = key.split(".")

            if len(parts) == 2:
                section, field = parts

                if section == "headers":
                    if "inputs" not in test_case:
                        test_case["inputs"] = {}
                    if "headers" not in test_case["inputs"]:
                        test_case["inputs"]["headers"] = {}
                    test_case["inputs"]["headers"][field] = value

                elif section == "body":
                    if "inputs" not in test_case:
                        test_case["inputs"] = {}
                    if "body" not in test_case["inputs"]:
                        test_case["inputs"]["body"] = {}
                    test_case["inputs"]["body"][field] = value

                elif section == "params":
                    if "inputs" not in test_case:
                        test_case["inputs"] = {}
                    if "query_params" not in test_case["inputs"]:
                        test_case["inputs"]["query_params"] = {}
                    test_case["inputs"]["query_params"][field] = value

        return test_case
