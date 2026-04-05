"""约束校验 Tool：校验优化方案的性能约束、组网约束和冲突检测."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from openharness.tools.base import BaseTool, ToolExecutionContext, ToolResult


class ConstraintCheckInput(BaseModel):
    """Input for constraint_check tool."""

    solution_plan: str = Field(description="方案 JSON 字符串")
    device_info: str = Field(
        default='{"model": "HG8145X6", "version": "V5R020C10", "managed": true}',
        description="设备信息 JSON（型号/版本/纳管状态）",
    )


# ---------------------------------------------------------------------------
# Performance limits per device model
# ---------------------------------------------------------------------------

DEVICE_CAPABILITIES: dict[str, dict[str, Any]] = {
    "HG8145X6": {
        "max_sampling_rate_per_second": 10,
        "max_metrics_count": 20,
        "max_concurrent_diagnosis": 3,
        "supported_features": [
            # 诊断方法
            "光衰检测", "WIFI信道诊断", "PPPoE连接诊断", "DNS解析诊断", "路由追踪诊断",
            # 闭环动作
            "WIFI信道自动切换", "PPPoE自动重拨", "QoS策略自动调整", "DNS自动切换", "网关自动重启",
            # 优化动作
            "WIFI频段自动切换", "信道自动优化", "带宽动态分配", "漫游优化",
        ],
        "min_firmware_version": "V5R020C00",
    },
    "HG8245Q2": {
        "max_sampling_rate_per_second": 5,
        "max_metrics_count": 10,
        "max_concurrent_diagnosis": 2,
        "supported_features": [
            # 诊断方法
            "光衰检测", "WIFI信道诊断", "PPPoE连接诊断", "DNS解析诊断",
            # 闭环动作
            "WIFI信道自动切换", "PPPoE自动重拨", "DNS自动切换",
            # 优化动作
            "WIFI频段自动切换", "信道自动优化",
        ],
        "min_firmware_version": "V3R017C10",
    },
    "default": {
        "max_sampling_rate_per_second": 5,
        "max_metrics_count": 10,
        "max_concurrent_diagnosis": 2,
        "supported_features": [
            "光衰检测", "WIFI信道诊断", "PPPoE连接诊断", "DNS解析诊断",
            "WIFI信道自动切换", "DNS自动切换",
        ],
        "min_firmware_version": "V1R000C00",
    },
}


def _check_performance(plan: dict, device: dict) -> dict[str, Any]:
    """Check performance constraints: sampling rate, metric count, etc."""
    violations: list[str] = []
    model = device.get("model", "default")
    caps = DEVICE_CAPABILITIES.get(model, DEVICE_CAPABILITIES["default"])

    # Check CEI perception metrics count
    perception = plan.get("plans", {}).get("experience_perception", {})
    granularity = perception.get("cei_granularity", {})
    metrics = granularity.get("metrics", [])
    if len(metrics) > caps["max_metrics_count"]:
        violations.append(
            f"性能约束违反：采集指标数({len(metrics)})超过设备{model}上限({caps['max_metrics_count']})"
        )

    # Check sampling rate
    interval = granularity.get("sampling_interval_seconds", 900)
    if interval > 0:
        rate = len(metrics) / interval
        if rate > caps["max_sampling_rate_per_second"]:
            violations.append(
                f"性能约束违反：采集频率({rate:.2f}/s)超过设备{model}上限({caps['max_sampling_rate_per_second']}/s)"
            )

    # Check concurrent diagnosis
    diagnosis = plan.get("plans", {}).get("fault_diagnosis", {})
    enabled_methods = [m for m in diagnosis.get("diagnosis_methods", []) if m.get("enabled")]
    if len(enabled_methods) > caps["max_concurrent_diagnosis"]:
        violations.append(
            f"性能约束违反：并发诊断方法数({len(enabled_methods)})超过设备{model}上限({caps['max_concurrent_diagnosis']})"
        )

    return {"passed": len(violations) == 0, "violations": violations}


def _check_network_topology(plan: dict, device: dict) -> dict[str, Any]:
    """Check network topology constraints: device capabilities, firmware, managed status."""
    violations: list[str] = []
    model = device.get("model", "default")
    caps = DEVICE_CAPABILITIES.get(model, DEVICE_CAPABILITIES["default"])
    supported = set(caps["supported_features"])

    # Check if device is managed
    if not device.get("managed", True):
        violations.append("组网约束违反：设备未纳管，无法下发配置")
        return {"passed": False, "violations": violations}

    # Check diagnosis methods availability
    diagnosis = plan.get("plans", {}).get("fault_diagnosis", {})
    for method in diagnosis.get("diagnosis_methods", []):
        if method.get("enabled") and method["name"] not in supported:
            violations.append(
                f"组网约束违反：设备{model}不支持'{method['name']}'"
            )

    # Check closure actions availability
    closure = plan.get("plans", {}).get("remote_closure", {})
    for action in closure.get("auto_recovery", {}).get("actions", []):
        if action.get("enabled") and action["name"] not in supported:
            violations.append(
                f"组网约束违反：设备{model}不支持'{action['name']}'"
            )

    # Check optimization actions availability
    optimization = plan.get("plans", {}).get("dynamic_optimization", {})
    for action in optimization.get("realtime_optimization", {}).get("actions", []):
        if action.get("enabled") and action["name"] not in supported:
            violations.append(
                f"组网约束违反：设备{model}不支持'{action['name']}'"
            )

    return {"passed": len(violations) == 0, "violations": violations}


def _check_conflicts(plan: dict) -> dict[str, Any]:
    """Detect conflicts between plan components."""
    violations: list[str] = []
    plans = plan.get("plans", {})

    # Conflict 1: Power saving vs guarantee period
    optimization = plans.get("dynamic_optimization", {})
    power_saving = optimization.get("power_saving", {})
    if power_saving.get("enabled"):
        # Check if power saving time overlaps with any guarantee period
        goal_spec = plan.get("goal_spec", {})
        guarantee_period = goal_spec.get("guarantee_period", {})
        time_ranges = guarantee_period.get("time_ranges", [])
        ps_trigger = power_saving.get("trigger_time", "01:00")
        ps_resume = power_saving.get("resume_time", "06:00")

        for tr in time_ranges:
            start = tr.get("start", "")
            end = tr.get("end", "")
            if _time_overlaps(ps_trigger, ps_resume, start, end):
                violations.append(
                    f"冲突检测：节能时段({ps_trigger}-{ps_resume})与保障时段({start}-{end})重叠"
                )

    # Conflict 2: APPflow vs high-sensitivity perception
    appflow = optimization.get("appflow_policy", {})
    perception = plans.get("experience_perception", {})
    trigger_window = perception.get("cei_trigger_window", {})
    if appflow.get("enabled") and trigger_window.get("detection_window_minutes", 15) <= 5:
        # High sensitivity perception + APPflow may cause measurement interference
        violations.append(
            "冲突检测：APPflow策略启用时，高敏感感知(<=5min检测窗口)可能受流量标记干扰"
        )

    # Conflict 3: Roaming optimization vs coverage optimization
    realtime = optimization.get("realtime_optimization", {})
    if realtime.get("enabled"):
        actions = {a["name"]: a.get("enabled", False) for a in realtime.get("actions", [])}
        if actions.get("漫游优化") and actions.get("WIFI频段自动切换"):
            # Both roaming and band switching can conflict
            violations.append(
                "冲突检测：漫游优化与WIFI频段自动切换同时启用可能导致频繁切换"
            )

    return {"passed": len(violations) == 0, "violations": violations}


def _time_overlaps(s1: str, e1: str, s2: str, e2: str) -> bool:
    """Check if two time ranges overlap (HH:MM format)."""
    try:
        s1_m = _to_minutes(s1)
        e1_m = _to_minutes(e1)
        s2_m = _to_minutes(s2)
        e2_m = _to_minutes(e2)
    except (ValueError, IndexError):
        return False

    # Handle overnight ranges
    if e1_m <= s1_m:
        e1_m += 1440
    if e2_m <= s2_m:
        e2_m += 1440

    return s1_m < e2_m and s2_m < e1_m


def _to_minutes(t: str) -> int:
    parts = t.split(":")
    return int(parts[0]) * 60 + int(parts[1])


class ConstraintCheckTool(BaseTool):
    """校验优化方案的性能约束、组网约束和冲突检测."""

    name = "constraint_check"
    description = "校验优化方案的性能约束、组网约束和冲突检测，返回校验结果和违反项"
    input_model = ConstraintCheckInput

    async def execute(
        self, arguments: ConstraintCheckInput, context: ToolExecutionContext
    ) -> ToolResult:
        try:
            plan = json.loads(arguments.solution_plan)
        except json.JSONDecodeError as exc:
            return ToolResult(output=f"方案 JSON 解析失败: {exc}", is_error=True)

        try:
            device = json.loads(arguments.device_info)
        except json.JSONDecodeError as exc:
            return ToolResult(output=f"设备信息 JSON 解析失败: {exc}", is_error=True)

        all_violations: list[str] = []

        perf = _check_performance(plan, device)
        all_violations.extend(perf["violations"])

        network = _check_network_topology(plan, device)
        all_violations.extend(network["violations"])

        conflicts = _check_conflicts(plan)
        all_violations.extend(conflicts["violations"])

        result = {
            "passed": len(all_violations) == 0,
            "performance_check": perf,
            "network_topology_check": network,
            "conflict_check": conflicts,
            "total_violations": len(all_violations),
            "violations": all_violations,
        }

        if all_violations:
            result["suggestion"] = "请根据违反项调整方案后重试"

        return ToolResult(
            output=json.dumps(result, ensure_ascii=False, indent=2),
            is_error=not result["passed"],
        )

    def is_read_only(self, arguments: BaseModel) -> bool:
        return True
