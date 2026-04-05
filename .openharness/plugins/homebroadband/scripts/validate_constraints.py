#!/usr/bin/env python3
"""Hook 脚本：在 config_translate Tool 执行前校验方案约束.

被 PreToolUse Hook 调用。从环境变量 OPENHARNESS_HOOK_PAYLOAD 读取 payload，
提取 tool_input.validated_plan 进行基本校验。
退出码 0 表示通过，非 0 表示阻止执行。
"""

from __future__ import annotations

import json
import os
import sys


def main() -> int:
    payload_str = os.environ.get("OPENHARNESS_HOOK_PAYLOAD", "{}")
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        print("警告: 无法解析 hook payload，跳过校验")
        return 0

    tool_input = payload.get("tool_input", {})
    plan_str = tool_input.get("validated_plan", "")
    if not plan_str:
        print("警告: 未找到 validated_plan，跳过校验")
        return 0

    try:
        plan = json.loads(plan_str)
    except json.JSONDecodeError:
        print("错误: validated_plan 不是有效的 JSON")
        return 1

    # Basic structural checks
    plans = plan.get("plans", {})
    required_keys = ["experience_perception", "fault_diagnosis", "remote_closure",
                     "dynamic_optimization", "manual_fallback"]

    missing = [k for k in required_keys if k not in plans]
    if missing:
        print(f"错误: 方案缺少必要组件: {missing}")
        return 1

    # Check CEI threshold is within reasonable range
    perception = plans.get("experience_perception", {})
    threshold = perception.get("cei_warning_threshold", {}).get("value", 0)
    if not (0 <= threshold <= 100):
        print(f"错误: CEI 阈值 {threshold} 不在合理范围 [0, 100]")
        return 1

    print("约束校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
