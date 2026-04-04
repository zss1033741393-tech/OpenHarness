"""Shared test fixtures for homebroadband-agent tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_goal_spec() -> dict:
    """A sample GoalSpec for a live-streaming user."""
    return {
        "user_type": "直播用户",
        "scenario": "直播推流",
        "guarantee_period": {
            "type": "固定时段",
            "time_ranges": [
                {"start": "20:00", "end": "00:00", "days": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]}
            ],
        },
        "guarantee_target": {
            "priority": "高",
            "focus": "上行",
            "applications": ["抖音直播", "OBS推流"],
            "sensitivity": {
                "latency": "高敏感",
                "jitter": "高敏感",
                "packet_loss": "高敏感",
            },
        },
        "core_metrics": {
            "cei_threshold": 85,
            "response_sla": "<15min",
            "availability_target": 99.5,
        },
    }


@pytest.fixture
def sample_goal_spec_json(sample_goal_spec: dict) -> str:
    """Sample GoalSpec as a JSON string."""
    return json.dumps(sample_goal_spec, ensure_ascii=False)


@pytest.fixture
def sample_game_goal_spec() -> dict:
    """A sample GoalSpec for a gaming user."""
    return {
        "user_type": "游戏用户",
        "scenario": "在线游戏",
        "guarantee_period": {"type": "全天候"},
        "guarantee_target": {
            "priority": "高",
            "focus": "双向",
            "applications": ["王者荣耀", "和平精英"],
            "sensitivity": {
                "latency": "高敏感",
                "jitter": "中敏感",
                "packet_loss": "高敏感",
            },
        },
        "core_metrics": {
            "cei_threshold": 80,
            "response_sla": "<15min",
            "availability_target": 99.5,
        },
    }


@pytest.fixture
def sample_solution_plan(sample_goal_spec: dict) -> dict:
    """A minimal sample SolutionPlan for testing."""
    return {
        "version": "1.0",
        "generated_at": "2026-04-05T10:30:00Z",
        "goal_spec": sample_goal_spec,
        "plans": {
            "experience_perception": {
                "cei_warning_threshold": {"level": "严格", "value": 85, "description": "直播用户 高优先级 阈值"},
                "cei_scenario_model": {
                    "model_type": "uplink_priority",
                    "parameters": {
                        "primary_metric": "uplink_loss",
                        "secondary_metrics": ["uplink_jitter", "rtt", "cei_score"],
                        "weights": {"uplink_loss": 0.35, "uplink_jitter": 0.3, "rtt": 0.2, "cei_score": 0.15},
                    },
                },
                "cei_granularity": {
                    "sampling_interval_seconds": 300,
                    "aggregation_window_seconds": 60,
                    "metrics": ["uplink_bandwidth", "uplink_packet_loss", "uplink_jitter", "rtt", "cei_score"],
                },
                "cei_trigger_window": {
                    "detection_window_minutes": 5,
                    "confirmation_count": 2,
                    "cooldown_minutes": 15,
                },
            },
            "fault_diagnosis": {
                "diagnosis_methods": [
                    {"name": "光衰检测", "enabled": True, "trigger_condition": "cei_score < threshold", "timeout_seconds": 60, "priority": 1},
                    {"name": "WIFI信道诊断", "enabled": True, "trigger_condition": "wifi_interference_detected", "timeout_seconds": 120, "priority": 2},
                ],
                "escalation": {"auto_escalate_after_minutes": 15, "escalation_levels": ["L1-自动诊断", "L2-远程运维"], "max_auto_retries": 2},
                "diagnosis_schedule": {"proactive_check_enabled": True, "proactive_check_interval_hours": 6, "check_time_window": {"start": "02:00", "end": "06:00"}},
            },
            "remote_closure": {
                "closure_strategy": {"mode": "aggressive", "description": "激进模式"},
                "auto_recovery": {
                    "enabled": True, "max_retries": 2, "retry_interval_seconds": 120,
                    "actions": [{"name": "WIFI信道自动切换", "enabled": True, "condition": "wifi_interference > threshold", "rollback_supported": True}],
                },
                "audit": {"enabled": True, "audit_interval_minutes": 15, "rollback_on_failure": True, "success_criteria": {"cei_improvement_threshold": 5, "check_duration_minutes": 10}},
                "notification": {"notify_user": True, "notify_channel": "sms", "notify_on_auto_recovery": True, "notify_on_escalation": True},
            },
            "dynamic_optimization": {
                "realtime_optimization": {"enabled": True, "check_interval_seconds": 120, "actions": []},
                "predictive_optimization": {"enabled": True, "prediction_window_minutes": 60, "model_type": "pattern_based", "actions": []},
                "power_saving": {"enabled": False, "trigger_time": "01:00", "resume_time": "06:00", "actions": []},
                "appflow_policy": {"enabled": True, "rules": [{"application": "抖音直播", "priority": "high"}]},
            },
            "manual_fallback": {
                "fallback_trigger": {"auto_diagnosis_failed": True, "auto_recovery_failed": True, "cei_below_critical": True, "critical_threshold": 50, "user_complaint": True, "max_auto_attempts_exceeded": True},
                "work_order": {"auto_create": True, "priority_mapping": {"高": "P1-紧急"}, "required_info": [], "sla": {}},
                "dispatch": {"auto_dispatch": True, "dispatch_rules": []},
                "user_communication": {"auto_notify": True, "notify_template": "standard", "channels": ["sms"], "progress_update_interval_minutes": 30},
            },
        },
        "metadata": {"generation_mode": "parallel_template", "worker_count": 5},
    }


@pytest.fixture
def tmp_work_dir(tmp_path: Path) -> Path:
    """Create a temporary working directory."""
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    return work_dir
