"""配置转义 Tool：将优化方案转义为设备可执行的 JSON 配置文件."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from openharness.tools.base import BaseTool, ToolExecutionContext, ToolResult


class ConfigTranslateInput(BaseModel):
    """Input for config_translate tool."""

    validated_plan: str = Field(description="校验通过的方案 JSON")
    config_type: str = Field(
        default="all",
        description="配置类型: perception / diagnosis / remote_closure / dynamic_optimization / all",
    )
    output_dir: str = Field(default="configs", description="输出目录")
    user_id: str = Field(default="USER_001", description="用户标识")


def _translate_perception(plan: dict, user_id: str) -> dict:
    """Translate experience_perception plan to device config."""
    perception = plan.get("plans", {}).get("experience_perception", {})
    threshold = perception.get("cei_warning_threshold", {})
    model = perception.get("cei_scenario_model", {})
    granularity = perception.get("cei_granularity", {})
    trigger = perception.get("cei_trigger_window", {})

    return {
        "version": "1.0",
        "user_id": user_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cei_config": {
            "warning_threshold": threshold.get("value", 70),
            "scenario_model": model.get("model_type", "balanced"),
            "model_parameters": model.get("parameters", {}),
            "sampling": {
                "interval_seconds": granularity.get("sampling_interval_seconds", 900),
                "aggregation_window_seconds": granularity.get("aggregation_window_seconds", 300),
                "metrics": granularity.get("metrics", []),
            },
            "trigger": {
                "detection_window_minutes": trigger.get("detection_window_minutes", 15),
                "confirmation_count": trigger.get("confirmation_count", 3),
                "cooldown_minutes": trigger.get("cooldown_minutes", 30),
            },
        },
    }


def _translate_diagnosis(plan: dict, user_id: str) -> dict:
    """Translate fault_diagnosis plan to device config."""
    diagnosis = plan.get("plans", {}).get("fault_diagnosis", {})

    return {
        "version": "1.0",
        "user_id": user_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "diagnosis_config": {
            "methods": [
                {
                    "name": m["name"],
                    "enabled": m.get("enabled", False),
                    "trigger_condition": m.get("trigger_condition", ""),
                    "timeout_seconds": m.get("timeout_seconds", 60),
                    "priority": m.get("priority", 99),
                }
                for m in diagnosis.get("diagnosis_methods", [])
            ],
            "escalation": diagnosis.get("escalation", {}),
            "schedule": diagnosis.get("diagnosis_schedule", {}),
        },
    }


def _translate_remote_closure(plan: dict, user_id: str) -> dict:
    """Translate remote_closure plan to device config."""
    closure = plan.get("plans", {}).get("remote_closure", {})

    return {
        "version": "1.0",
        "user_id": user_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "closure_config": {
            "strategy": closure.get("closure_strategy", {}).get("mode", "balanced"),
            "strategy_description": closure.get("closure_strategy", {}).get("description", ""),
            "auto_recovery": {
                "enabled": closure.get("auto_recovery", {}).get("enabled", True),
                "max_retries": closure.get("auto_recovery", {}).get("max_retries", 3),
                "retry_interval_seconds": closure.get("auto_recovery", {}).get("retry_interval_seconds", 300),
                "actions": [
                    {
                        "name": a["name"],
                        "enabled": a.get("enabled", False),
                        "condition": a.get("condition", ""),
                        "rollback_supported": a.get("rollback_supported", False),
                    }
                    for a in closure.get("auto_recovery", {}).get("actions", [])
                ],
            },
            "audit": closure.get("audit", {}),
            "notification": closure.get("notification", {}),
        },
    }


def _translate_dynamic_optimization(plan: dict, user_id: str) -> dict:
    """Translate dynamic_optimization plan to device config."""
    optimization = plan.get("plans", {}).get("dynamic_optimization", {})

    return {
        "version": "1.0",
        "user_id": user_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "optimization_config": {
            "realtime_optimization": {
                "enabled": optimization.get("realtime_optimization", {}).get("enabled", True),
                "check_interval_seconds": optimization.get("realtime_optimization", {}).get("check_interval_seconds", 300),
                "actions": [
                    {
                        "name": a["name"],
                        "enabled": a.get("enabled", False),
                        "condition": a.get("condition", ""),
                        "target": a.get("target", ""),
                    }
                    for a in optimization.get("realtime_optimization", {}).get("actions", [])
                ],
            },
            "predictive_optimization": optimization.get("predictive_optimization", {}),
            "power_saving": optimization.get("power_saving", {}),
            "appflow_policy": optimization.get("appflow_policy", {}),
        },
    }


CONFIG_TRANSLATORS: dict[str, Any] = {
    "perception": ("perception_config.json", _translate_perception),
    "diagnosis": ("diagnosis_config.json", _translate_diagnosis),
    "remote_closure": ("remote_closure_config.json", _translate_remote_closure),
    "dynamic_optimization": ("dynamic_optimization_config.json", _translate_dynamic_optimization),
}


class ConfigTranslateTool(BaseTool):
    """将优化方案转义为设备可执行的 JSON 配置文件."""

    name = "config_translate"
    description = "将校验通过的优化方案转义为设备可执行的JSON配置文件（感知/诊断/闭环/优化）"
    input_model = ConfigTranslateInput

    async def execute(
        self, arguments: ConfigTranslateInput, context: ToolExecutionContext
    ) -> ToolResult:
        try:
            plan = json.loads(arguments.validated_plan)
        except json.JSONDecodeError as exc:
            return ToolResult(output=f"方案 JSON 解析失败: {exc}", is_error=True)

        output_dir = Path(context.cwd) / arguments.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        if arguments.config_type == "all":
            types_to_translate = list(CONFIG_TRANSLATORS.keys())
        elif arguments.config_type in CONFIG_TRANSLATORS:
            types_to_translate = [arguments.config_type]
        else:
            return ToolResult(
                output=f"未知配置类型: {arguments.config_type}，可用类型: {list(CONFIG_TRANSLATORS.keys()) + ['all']}",
                is_error=True,
            )

        generated_files: list[str] = []
        for config_type in types_to_translate:
            filename, translator = CONFIG_TRANSLATORS[config_type]
            config = translator(plan, arguments.user_id)
            filepath = output_dir / filename
            filepath.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
            generated_files.append(str(filepath))

        return ToolResult(
            output=json.dumps(
                {"generated_files": generated_files, "count": len(generated_files)},
                ensure_ascii=False,
            )
        )

    def is_read_only(self, arguments: BaseModel) -> bool:
        return False
