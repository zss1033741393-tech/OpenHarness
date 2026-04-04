"""基于预制模板 + GoalSpec 生成单维度方案的 Tool（纯查表填值，无需 LLM）."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from openharness.tools.base import BaseTool, ToolExecutionContext, ToolResult


class PlanFromTemplateInput(BaseModel):
    """Input for plan_from_template tool."""

    template_name: str = Field(description="模板 Skill 名称，如 tpl-cei-perception")
    goal_spec: str = Field(description="GoalSpec JSON 字符串")
    output_path: str = Field(description="输出文件路径")


# ---------------------------------------------------------------------------
# 参数查找表（硬编码，与 Skill 模板中的表格对应）
# ---------------------------------------------------------------------------

CEI_THRESHOLD_TABLE: dict[tuple[str, str], int] = {
    ("直播用户", "高"): 85, ("直播用户", "中"): 75, ("直播用户", "低"): 65,
    ("游戏用户", "高"): 80, ("游戏用户", "中"): 70, ("游戏用户", "低"): 60,
    ("办公用户", "高"): 75, ("办公用户", "中"): 65, ("办公用户", "低"): 55,
    ("教育用户", "高"): 75, ("教育用户", "中"): 65, ("教育用户", "低"): 55,
    ("普通家庭用户", "高"): 70, ("普通家庭用户", "中"): 60, ("普通家庭用户", "低"): 50,
    ("SOHO用户", "高"): 75, ("SOHO用户", "中"): 65, ("SOHO用户", "低"): 55,
}

SCENARIO_MODEL_TABLE: dict[str, dict[str, Any]] = {
    "直播推流": {
        "model_type": "uplink_priority",
        "parameters": {
            "primary_metric": "uplink_loss",
            "secondary_metrics": ["uplink_jitter", "rtt", "cei_score"],
            "weights": {"uplink_loss": 0.35, "uplink_jitter": 0.3, "rtt": 0.2, "cei_score": 0.15},
        },
    },
    "在线游戏": {
        "model_type": "low_latency_priority",
        "parameters": {
            "primary_metric": "rtt",
            "secondary_metrics": ["packet_loss", "jitter", "cei_score"],
            "weights": {"rtt": 0.4, "packet_loss": 0.3, "jitter": 0.2, "cei_score": 0.1},
        },
    },
    "视频会议": {
        "model_type": "bidirectional_balanced",
        "parameters": {
            "primary_metric": "mos_score",
            "secondary_metrics": ["jitter", "packet_loss", "rtt"],
            "weights": {"mos_score": 0.35, "jitter": 0.25, "packet_loss": 0.2, "rtt": 0.2},
        },
    },
    "在线教育": {
        "model_type": "availability_first",
        "parameters": {
            "primary_metric": "availability",
            "secondary_metrics": ["rtt", "packet_loss", "jitter"],
            "weights": {"availability": 0.4, "rtt": 0.2, "packet_loss": 0.2, "jitter": 0.2},
        },
    },
    "高清视频": {
        "model_type": "downlink_priority",
        "parameters": {
            "primary_metric": "downlink_bandwidth",
            "secondary_metrics": ["rtt", "packet_loss", "jitter"],
            "weights": {"downlink_bandwidth": 0.4, "rtt": 0.2, "packet_loss": 0.2, "jitter": 0.2},
        },
    },
    "智能家居": {
        "model_type": "iot_balanced",
        "parameters": {
            "primary_metric": "availability",
            "secondary_metrics": ["packet_loss", "rtt", "jitter"],
            "weights": {"availability": 0.4, "packet_loss": 0.3, "rtt": 0.2, "jitter": 0.1},
        },
    },
    "综合场景": {
        "model_type": "balanced",
        "parameters": {
            "primary_metric": "cei_score",
            "secondary_metrics": ["rtt", "packet_loss", "jitter"],
            "weights": {"cei_score": 0.4, "rtt": 0.2, "packet_loss": 0.2, "jitter": 0.2},
        },
    },
}

SENSITIVITY_TABLE: dict[str, dict[str, int]] = {
    "高敏感": {
        "sampling_interval_seconds": 300,
        "aggregation_window_seconds": 60,
        "detection_window_minutes": 5,
        "confirmation_count": 2,
        "cooldown_minutes": 15,
    },
    "中敏感": {
        "sampling_interval_seconds": 900,
        "aggregation_window_seconds": 300,
        "detection_window_minutes": 15,
        "confirmation_count": 3,
        "cooldown_minutes": 30,
    },
    "低敏感": {
        "sampling_interval_seconds": 1800,
        "aggregation_window_seconds": 900,
        "detection_window_minutes": 30,
        "confirmation_count": 5,
        "cooldown_minutes": 60,
    },
}

SCENARIO_METRICS_TABLE: dict[str, list[str]] = {
    "直播推流": ["uplink_bandwidth", "uplink_packet_loss", "uplink_jitter", "rtt", "cei_score"],
    "在线游戏": ["rtt", "packet_loss", "jitter", "download_speed", "cei_score"],
    "视频会议": ["mos_score", "rtt", "jitter", "packet_loss", "bandwidth", "cei_score"],
    "在线教育": ["download_speed", "rtt", "packet_loss", "availability", "cei_score"],
    "高清视频": ["downlink_bandwidth", "rtt", "packet_loss", "buffer_ratio", "cei_score"],
    "智能家居": ["availability", "packet_loss", "rtt", "device_count", "cei_score"],
    "综合场景": ["bandwidth", "packet_loss", "rtt", "jitter", "cei_score"],
}

# --- 故障诊断查找表 ---
DIAGNOSIS_ENABLE_TABLE: dict[str, dict[str, bool]] = {
    "直播推流": {"光衰检测": True, "WIFI信道诊断": True, "PPPoE连接诊断": True, "DNS解析诊断": True, "路由追踪诊断": True},
    "在线游戏": {"光衰检测": True, "WIFI信道诊断": True, "PPPoE连接诊断": True, "DNS解析诊断": True, "路由追踪诊断": True},
    "视频会议": {"光衰检测": True, "WIFI信道诊断": True, "PPPoE连接诊断": True, "DNS解析诊断": True, "路由追踪诊断": False},
    "在线教育": {"光衰检测": True, "WIFI信道诊断": True, "PPPoE连接诊断": True, "DNS解析诊断": True, "路由追踪诊断": False},
    "高清视频": {"光衰检测": True, "WIFI信道诊断": True, "PPPoE连接诊断": True, "DNS解析诊断": False, "路由追踪诊断": False},
    "智能家居": {"光衰检测": True, "WIFI信道诊断": True, "PPPoE连接诊断": False, "DNS解析诊断": True, "路由追踪诊断": False},
    "综合场景": {"光衰检测": True, "WIFI信道诊断": True, "PPPoE连接诊断": True, "DNS解析诊断": True, "路由追踪诊断": False},
}

ESCALATION_TABLE: dict[str, dict[str, int]] = {
    "高": {"auto_escalate_after_minutes": 15, "max_auto_retries": 2},
    "中": {"auto_escalate_after_minutes": 30, "max_auto_retries": 3},
    "低": {"auto_escalate_after_minutes": 60, "max_auto_retries": 5},
}

# --- 远程闭环查找表 ---
CLOSURE_STRATEGY_TABLE: dict[str, dict[str, Any]] = {
    "高": {
        "mode": "aggressive",
        "description": "激进模式：全面自动修复，快速响应",
        "enabled_actions": ["WIFI信道自动切换", "PPPoE自动重拨", "QoS策略自动调整", "DNS自动切换", "网关自动重启"],
        "max_retries": 2,
        "retry_interval_seconds": 120,
    },
    "中": {
        "mode": "balanced",
        "description": "均衡模式：自动修复常见问题，异常情况人工介入",
        "enabled_actions": ["WIFI信道自动切换", "PPPoE自动重拨", "DNS自动切换"],
        "max_retries": 3,
        "retry_interval_seconds": 300,
    },
    "低": {
        "mode": "conservative",
        "description": "保守模式：仅执行安全操作，多数情况人工介入",
        "enabled_actions": ["WIFI信道自动切换", "DNS自动切换"],
        "max_retries": 5,
        "retry_interval_seconds": 600,
    },
}

QOS_TABLE: dict[str, dict[str, Any]] = {
    "直播推流": {"enabled": True, "description": "上行优先，预留50%上行带宽"},
    "在线游戏": {"enabled": True, "description": "低延迟优先，游戏流量最高优先级"},
    "视频会议": {"enabled": True, "description": "双向均衡，视频会议流量优先"},
    "在线教育": {"enabled": True, "description": "下行优先，教育应用流量优先"},
    "高清视频": {"enabled": False, "description": "无特殊QoS"},
    "智能家居": {"enabled": False, "description": "无特殊QoS"},
    "综合场景": {"enabled": False, "description": "无特殊QoS"},
}

AUDIT_TABLE: dict[str, dict[str, int]] = {
    "高敏感": {"audit_interval_minutes": 15, "check_duration_minutes": 10, "cei_improvement_threshold": 5},
    "中敏感": {"audit_interval_minutes": 30, "check_duration_minutes": 15, "cei_improvement_threshold": 10},
    "低敏感": {"audit_interval_minutes": 60, "check_duration_minutes": 30, "cei_improvement_threshold": 15},
}

# --- 动态优化查找表 ---
REALTIME_OPT_TABLE: dict[str, dict[str, Any]] = {
    "直播推流": {"WIFI频段自动切换": True, "信道自动优化": True, "带宽动态分配": True, "漫游优化": False, "check_interval_seconds": 120},
    "在线游戏": {"WIFI频段自动切换": True, "信道自动优化": True, "带宽动态分配": True, "漫游优化": False, "check_interval_seconds": 60},
    "视频会议": {"WIFI频段自动切换": True, "信道自动优化": True, "带宽动态分配": True, "漫游优化": True, "check_interval_seconds": 120},
    "在线教育": {"WIFI频段自动切换": True, "信道自动优化": True, "带宽动态分配": False, "漫游优化": True, "check_interval_seconds": 300},
    "高清视频": {"WIFI频段自动切换": True, "信道自动优化": True, "带宽动态分配": False, "漫游优化": False, "check_interval_seconds": 300},
    "智能家居": {"WIFI频段自动切换": True, "信道自动优化": True, "带宽动态分配": False, "漫游优化": False, "check_interval_seconds": 600},
    "综合场景": {"WIFI频段自动切换": True, "信道自动优化": True, "带宽动态分配": False, "漫游优化": False, "check_interval_seconds": 300},
}

# --- 人工兜底查找表 ---
CRITICAL_THRESHOLD_TABLE: dict[tuple[str, str], int] = {
    ("直播用户", "高"): 50, ("直播用户", "中"): 40, ("直播用户", "低"): 30,
    ("游戏用户", "高"): 45, ("游戏用户", "中"): 35, ("游戏用户", "低"): 25,
    ("办公用户", "高"): 40, ("办公用户", "中"): 30, ("办公用户", "低"): 20,
    ("教育用户", "高"): 40, ("教育用户", "中"): 30, ("教育用户", "低"): 20,
    ("普通家庭用户", "高"): 35, ("普通家庭用户", "中"): 25, ("普通家庭用户", "低"): 15,
    ("SOHO用户", "高"): 40, ("SOHO用户", "中"): 30, ("SOHO用户", "低"): 20,
}

SLA_TABLE: dict[str, dict[str, dict[str, Any]]] = {
    "高": {
        "P1-紧急": {"response_minutes": 10, "resolve_hours": 2},
        "P2-重要": {"response_minutes": 20, "resolve_hours": 4},
        "P3-一般": {"response_minutes": 30, "resolve_hours": 8},
    },
    "中": {
        "P1-紧急": {"response_minutes": 15, "resolve_hours": 4},
        "P2-重要": {"response_minutes": 30, "resolve_hours": 8},
        "P3-一般": {"response_minutes": 60, "resolve_hours": 24},
    },
    "低": {
        "P1-紧急": {"response_minutes": 30, "resolve_hours": 8},
        "P2-重要": {"response_minutes": 60, "resolve_hours": 24},
        "P3-一般": {"response_minutes": 120, "resolve_hours": 48},
    },
}


# ---------------------------------------------------------------------------
# Helper: safe nested get
# ---------------------------------------------------------------------------

def _get(data: dict, *keys: str, default: Any = None) -> Any:
    """Safely get nested dict values."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
        if current is default:
            return default
    return current


# ---------------------------------------------------------------------------
# Template renderers
# ---------------------------------------------------------------------------

def _render_cei_perception(goal: dict) -> dict:
    user_type = goal.get("user_type", "普通家庭用户")
    priority = _get(goal, "guarantee_target", "priority", default="中")
    scenario = goal.get("scenario", "综合场景")
    sensitivity = _get(goal, "guarantee_target", "sensitivity", "latency", default="中敏感")

    threshold = CEI_THRESHOLD_TABLE.get((user_type, priority), 70)
    # Allow GoalSpec.core_metrics.cei_threshold to override
    explicit_threshold = _get(goal, "core_metrics", "cei_threshold")
    if explicit_threshold is not None:
        threshold = explicit_threshold

    model = SCENARIO_MODEL_TABLE.get(scenario, SCENARIO_MODEL_TABLE["综合场景"])
    sens = SENSITIVITY_TABLE.get(sensitivity, SENSITIVITY_TABLE["中敏感"])
    metrics = SCENARIO_METRICS_TABLE.get(scenario, SCENARIO_METRICS_TABLE["综合场景"])

    return {
        "cei_warning_threshold": {
            "level": {"高敏感": "严格", "中敏感": "标准", "低敏感": "宽松"}.get(sensitivity, "标准"),
            "value": threshold,
            "description": f"{user_type} {priority}优先级 阈值",
        },
        "cei_scenario_model": model,
        "cei_granularity": {
            "sampling_interval_seconds": sens["sampling_interval_seconds"],
            "aggregation_window_seconds": sens["aggregation_window_seconds"],
            "metrics": metrics,
        },
        "cei_trigger_window": {
            "detection_window_minutes": sens["detection_window_minutes"],
            "confirmation_count": sens["confirmation_count"],
            "cooldown_minutes": sens["cooldown_minutes"],
        },
    }


def _render_fault_diagnosis(goal: dict) -> dict:
    scenario = goal.get("scenario", "综合场景")
    priority = _get(goal, "guarantee_target", "priority", default="中")

    diag_enable = DIAGNOSIS_ENABLE_TABLE.get(scenario, DIAGNOSIS_ENABLE_TABLE["综合场景"])
    escalation = ESCALATION_TABLE.get(priority, ESCALATION_TABLE["中"])

    methods = [
        {"name": "光衰检测", "enabled": diag_enable.get("光衰检测", True), "trigger_condition": "cei_score < threshold", "timeout_seconds": 60, "priority": 1},
        {"name": "WIFI信道诊断", "enabled": diag_enable.get("WIFI信道诊断", True), "trigger_condition": "wifi_interference_detected", "timeout_seconds": 120, "priority": 2},
        {"name": "PPPoE连接诊断", "enabled": diag_enable.get("PPPoE连接诊断", True), "trigger_condition": "connection_drop_detected", "timeout_seconds": 90, "priority": 3},
        {"name": "DNS解析诊断", "enabled": diag_enable.get("DNS解析诊断", True), "trigger_condition": "dns_resolution_slow", "timeout_seconds": 30, "priority": 4},
        {"name": "路由追踪诊断", "enabled": diag_enable.get("路由追踪诊断", False), "trigger_condition": "high_rtt_detected", "timeout_seconds": 180, "priority": 5},
    ]

    # Proactive check
    user_type = goal.get("user_type", "普通家庭用户")
    proactive = False
    interval_hours = 24
    if priority == "高" and user_type in ("直播用户", "游戏用户", "办公用户", "教育用户"):
        proactive = True
        interval_hours = 6 if user_type == "直播用户" else 12

    return {
        "diagnosis_methods": methods,
        "escalation": {
            "auto_escalate_after_minutes": escalation["auto_escalate_after_minutes"],
            "escalation_levels": ["L1-自动诊断", "L2-远程运维", "L3-现场处理"],
            "max_auto_retries": escalation["max_auto_retries"],
        },
        "diagnosis_schedule": {
            "proactive_check_enabled": proactive,
            "proactive_check_interval_hours": interval_hours,
            "check_time_window": {"start": "02:00", "end": "06:00"},
        },
    }


def _render_remote_closure(goal: dict) -> dict:
    priority = _get(goal, "guarantee_target", "priority", default="中")
    scenario = goal.get("scenario", "综合场景")
    sensitivity = _get(goal, "guarantee_target", "sensitivity", "latency", default="中敏感")

    strategy = CLOSURE_STRATEGY_TABLE.get(priority, CLOSURE_STRATEGY_TABLE["中"])
    qos = QOS_TABLE.get(scenario, QOS_TABLE["综合场景"])
    audit = AUDIT_TABLE.get(sensitivity, AUDIT_TABLE["中敏感"])

    enabled_actions = strategy["enabled_actions"]
    actions = [
        {"name": "WIFI信道自动切换", "enabled": "WIFI信道自动切换" in enabled_actions, "condition": "wifi_interference > threshold", "rollback_supported": True},
        {"name": "PPPoE自动重拨", "enabled": "PPPoE自动重拨" in enabled_actions, "condition": "pppoe_session_lost", "rollback_supported": False},
        {"name": "QoS策略自动调整", "enabled": "QoS策略自动调整" in enabled_actions and qos["enabled"], "condition": "bandwidth_contention_detected", "rollback_supported": True, "qos_description": qos["description"]},
        {"name": "DNS自动切换", "enabled": "DNS自动切换" in enabled_actions, "condition": "dns_resolution_timeout", "rollback_supported": True},
        {"name": "网关自动重启", "enabled": "网关自动重启" in enabled_actions, "condition": "gateway_unresponsive", "rollback_supported": False},
    ]

    return {
        "closure_strategy": {"mode": strategy["mode"], "description": strategy["description"]},
        "auto_recovery": {
            "enabled": True,
            "max_retries": strategy["max_retries"],
            "retry_interval_seconds": strategy["retry_interval_seconds"],
            "actions": actions,
        },
        "audit": {
            "enabled": True,
            "audit_interval_minutes": audit["audit_interval_minutes"],
            "rollback_on_failure": True,
            "success_criteria": {
                "cei_improvement_threshold": audit["cei_improvement_threshold"],
                "check_duration_minutes": audit["check_duration_minutes"],
            },
        },
        "notification": {
            "notify_user": True,
            "notify_channel": "sms",
            "notify_on_auto_recovery": True,
            "notify_on_escalation": True,
        },
    }


def _render_dynamic_optimization(goal: dict) -> dict:
    scenario = goal.get("scenario", "综合场景")
    user_type = goal.get("user_type", "普通家庭用户")
    priority = _get(goal, "guarantee_target", "priority", default="中")

    rt_opt = REALTIME_OPT_TABLE.get(scenario, REALTIME_OPT_TABLE["综合场景"])

    realtime_actions = [
        {"name": "WIFI频段自动切换", "enabled": rt_opt.get("WIFI频段自动切换", True), "condition": "signal_quality_degraded", "target": "切换至最优频段(2.4G/5G)"},
        {"name": "信道自动优化", "enabled": rt_opt.get("信道自动优化", True), "condition": "channel_interference_high", "target": "切换至干扰最小信道"},
        {"name": "带宽动态分配", "enabled": rt_opt.get("带宽动态分配", False), "condition": "bandwidth_contention", "target": "按优先级重新分配带宽"},
        {"name": "漫游优化", "enabled": rt_opt.get("漫游优化", False), "condition": "roaming_quality_poor", "target": "优化AP切换阈值"},
    ]

    # Predictive optimization
    predictive_enabled = False
    prediction_window = 30
    model_type = "time_series"
    if priority == "高":
        if user_type == "直播用户":
            predictive_enabled, prediction_window, model_type = True, 60, "pattern_based"
        elif user_type == "游戏用户":
            predictive_enabled, prediction_window, model_type = True, 30, "time_series"
        elif user_type == "办公用户":
            predictive_enabled, prediction_window, model_type = True, 30, "calendar_based"

    # Power saving
    power_saving_enabled = False
    trigger_time = "01:00"
    resume_time = "06:00"
    ps_time = _get(goal, "user_history", "app_history", "power_saving_trigger_time")
    if ps_time:
        power_saving_enabled = True
        trigger_time = ps_time
        # Simple +5h logic
        hour = int(ps_time.split(":")[0])
        resume_time = f"{(hour + 5) % 24:02d}:00"
    elif user_type == "普通家庭用户" and priority == "低":
        power_saving_enabled = True

    # APPflow
    appflow_enabled = scenario in ("直播推流", "在线游戏", "视频会议")
    appflow_rules = []
    apps = _get(goal, "guarantee_target", "applications", default=[])
    if appflow_enabled and apps:
        appflow_rules = [{"application": app, "priority": "high"} for app in apps]

    return {
        "realtime_optimization": {
            "enabled": True,
            "check_interval_seconds": rt_opt.get("check_interval_seconds", 300),
            "actions": realtime_actions,
        },
        "predictive_optimization": {
            "enabled": predictive_enabled,
            "prediction_window_minutes": prediction_window,
            "model_type": model_type,
            "actions": [
                {"name": "预调度带宽", "trigger": "predicted_peak_traffic", "advance_minutes": 15},
                {"name": "预切换信道", "trigger": "predicted_interference", "advance_minutes": 10},
            ],
        },
        "power_saving": {
            "enabled": power_saving_enabled,
            "trigger_time": trigger_time,
            "resume_time": resume_time,
            "actions": ["降低WIFI发射功率", "关闭非必要端口", "降低采集频率"],
        },
        "appflow_policy": {
            "enabled": appflow_enabled,
            "rules": appflow_rules,
        },
    }


def _render_manual_fallback(goal: dict) -> dict:
    user_type = goal.get("user_type", "普通家庭用户")
    priority = _get(goal, "guarantee_target", "priority", default="中")

    critical = CRITICAL_THRESHOLD_TABLE.get((user_type, priority), 25)
    sla = SLA_TABLE.get(priority, SLA_TABLE["中"])
    auto_dispatch = priority == "高"
    progress_interval = {"高": 30, "中": 60, "低": 120}.get(priority, 60)

    return {
        "fallback_trigger": {
            "auto_diagnosis_failed": True,
            "auto_recovery_failed": True,
            "cei_below_critical": True,
            "critical_threshold": critical,
            "user_complaint": True,
            "max_auto_attempts_exceeded": True,
        },
        "work_order": {
            "auto_create": True,
            "priority_mapping": {"高": "P1-紧急", "中": "P2-重要", "低": "P3-一般"},
            "required_info": [
                "用户ID", "故障现象描述", "自动诊断结果",
                "自动修复尝试记录", "当前CEI评分", "网络拓扑信息",
            ],
            "sla": sla,
        },
        "dispatch": {
            "auto_dispatch": auto_dispatch,
            "dispatch_rules": [
                {"condition": "光衰问题", "team": "线路维护组", "skill_required": "光纤熔接"},
                {"condition": "设备故障", "team": "设备维护组", "skill_required": "网关更换"},
                {"condition": "WIFI覆盖问题", "team": "装维组", "skill_required": "组网优化"},
            ],
        },
        "user_communication": {
            "auto_notify": True,
            "notify_template": "standard",
            "channels": ["sms", "app_push"],
            "progress_update_interval_minutes": progress_interval,
        },
    }


# ---------------------------------------------------------------------------
# Template name → renderer mapping
# ---------------------------------------------------------------------------

TEMPLATE_RENDERERS: dict[str, Any] = {
    "tpl-cei-perception": _render_cei_perception,
    "tpl-fault-diagnosis": _render_fault_diagnosis,
    "tpl-remote-closure": _render_remote_closure,
    "tpl-dynamic-optimization": _render_dynamic_optimization,
    "tpl-manual-fallback": _render_manual_fallback,
}


class PlanFromTemplateTool(BaseTool):
    """基于预制模板 + GoalSpec 生成单维度方案（纯查表填值，无需 LLM）."""

    name = "plan_from_template"
    description = "加载预制方案模板，根据GoalSpec查表填值，输出方案JSON。可并行调用。"
    input_model = PlanFromTemplateInput

    async def execute(
        self, arguments: PlanFromTemplateInput, context: ToolExecutionContext
    ) -> ToolResult:
        renderer = TEMPLATE_RENDERERS.get(arguments.template_name)
        if renderer is None:
            return ToolResult(
                output=f"未知模板: {arguments.template_name}，可用模板: {list(TEMPLATE_RENDERERS.keys())}",
                is_error=True,
            )

        try:
            goal = json.loads(arguments.goal_spec)
        except json.JSONDecodeError as exc:
            return ToolResult(output=f"GoalSpec JSON 解析失败: {exc}", is_error=True)

        result = renderer(goal)

        output_path = Path(context.cwd) / arguments.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        return ToolResult(
            output=f"方案已生成: {output_path} ({len(json.dumps(result, ensure_ascii=False))} bytes)"
        )

    def is_read_only(self, arguments: BaseModel) -> bool:
        return False
