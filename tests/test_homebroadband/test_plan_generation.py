"""Tests for plan_from_template_tool.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openharness.tools.plan_from_template_tool import (
    PlanFromTemplateTool,
    PlanFromTemplateInput,
    _render_cei_perception,
    _render_fault_diagnosis,
    _render_remote_closure,
    _render_dynamic_optimization,
    _render_manual_fallback,
    TEMPLATE_RENDERERS,
)
from openharness.tools.base import ToolExecutionContext


# ---------------------------------------------------------------------------
# Unit tests for individual renderers
# ---------------------------------------------------------------------------

class TestCeiPerceptionRenderer:
    def test_live_streaming_high_priority(self, sample_goal_spec: dict):
        result = _render_cei_perception(sample_goal_spec)
        assert result["cei_warning_threshold"]["value"] == 85
        assert result["cei_scenario_model"]["model_type"] == "uplink_priority"
        assert result["cei_granularity"]["sampling_interval_seconds"] == 300
        assert result["cei_trigger_window"]["detection_window_minutes"] == 5
        assert result["cei_trigger_window"]["confirmation_count"] == 2
        assert "uplink_bandwidth" in result["cei_granularity"]["metrics"]

    def test_gaming_user(self, sample_game_goal_spec: dict):
        result = _render_cei_perception(sample_game_goal_spec)
        assert result["cei_warning_threshold"]["value"] == 80
        assert result["cei_scenario_model"]["model_type"] == "low_latency_priority"
        assert result["cei_scenario_model"]["parameters"]["primary_metric"] == "rtt"

    def test_explicit_threshold_overrides(self, sample_goal_spec: dict):
        sample_goal_spec["core_metrics"]["cei_threshold"] = 90
        result = _render_cei_perception(sample_goal_spec)
        assert result["cei_warning_threshold"]["value"] == 90

    def test_default_values_for_unknown_user(self):
        goal = {
            "user_type": "未知用户",
            "scenario": "综合场景",
            "guarantee_target": {"priority": "中", "sensitivity": {"latency": "中敏感"}},
            "core_metrics": {},
        }
        result = _render_cei_perception(goal)
        assert result["cei_warning_threshold"]["value"] == 70
        assert result["cei_scenario_model"]["model_type"] == "balanced"


class TestFaultDiagnosisRenderer:
    def test_live_streaming_all_methods_enabled(self, sample_goal_spec: dict):
        result = _render_fault_diagnosis(sample_goal_spec)
        methods = {m["name"]: m["enabled"] for m in result["diagnosis_methods"]}
        assert methods["光衰检测"] is True
        assert methods["路由追踪诊断"] is True

    def test_high_priority_escalation(self, sample_goal_spec: dict):
        result = _render_fault_diagnosis(sample_goal_spec)
        assert result["escalation"]["auto_escalate_after_minutes"] == 15
        assert result["escalation"]["max_auto_retries"] == 2

    def test_proactive_check_for_live_streaming(self, sample_goal_spec: dict):
        result = _render_fault_diagnosis(sample_goal_spec)
        assert result["diagnosis_schedule"]["proactive_check_enabled"] is True
        assert result["diagnosis_schedule"]["proactive_check_interval_hours"] == 6


class TestRemoteClosureRenderer:
    def test_aggressive_mode_for_high_priority(self, sample_goal_spec: dict):
        result = _render_remote_closure(sample_goal_spec)
        assert result["closure_strategy"]["mode"] == "aggressive"
        assert result["auto_recovery"]["max_retries"] == 2
        assert result["auto_recovery"]["retry_interval_seconds"] == 120

    def test_qos_enabled_for_live_streaming(self, sample_goal_spec: dict):
        result = _render_remote_closure(sample_goal_spec)
        qos_action = next(
            (a for a in result["auto_recovery"]["actions"] if a["name"] == "QoS策略自动调整"),
            None,
        )
        assert qos_action is not None
        assert qos_action["enabled"] is True

    def test_audit_high_sensitivity(self, sample_goal_spec: dict):
        result = _render_remote_closure(sample_goal_spec)
        assert result["audit"]["audit_interval_minutes"] == 15


class TestDynamicOptimizationRenderer:
    def test_live_streaming_bandwidth_allocation(self, sample_goal_spec: dict):
        result = _render_dynamic_optimization(sample_goal_spec)
        actions = {a["name"]: a["enabled"] for a in result["realtime_optimization"]["actions"]}
        assert actions["带宽动态分配"] is True
        assert result["realtime_optimization"]["check_interval_seconds"] == 120

    def test_predictive_optimization_for_live_streaming(self, sample_goal_spec: dict):
        result = _render_dynamic_optimization(sample_goal_spec)
        assert result["predictive_optimization"]["enabled"] is True
        assert result["predictive_optimization"]["model_type"] == "pattern_based"
        assert result["predictive_optimization"]["prediction_window_minutes"] == 60

    def test_appflow_for_live_streaming(self, sample_goal_spec: dict):
        result = _render_dynamic_optimization(sample_goal_spec)
        assert result["appflow_policy"]["enabled"] is True
        assert len(result["appflow_policy"]["rules"]) == 2

    def test_power_saving_disabled_for_high_priority(self, sample_goal_spec: dict):
        result = _render_dynamic_optimization(sample_goal_spec)
        assert result["power_saving"]["enabled"] is False


class TestManualFallbackRenderer:
    def test_critical_threshold_for_live_streaming(self, sample_goal_spec: dict):
        result = _render_manual_fallback(sample_goal_spec)
        assert result["fallback_trigger"]["critical_threshold"] == 50

    def test_auto_dispatch_for_high_priority(self, sample_goal_spec: dict):
        result = _render_manual_fallback(sample_goal_spec)
        assert result["dispatch"]["auto_dispatch"] is True

    def test_low_priority_no_auto_dispatch(self):
        goal = {
            "user_type": "普通家庭用户",
            "scenario": "综合场景",
            "guarantee_target": {"priority": "低"},
            "core_metrics": {},
        }
        result = _render_manual_fallback(goal)
        assert result["dispatch"]["auto_dispatch"] is False
        assert result["user_communication"]["progress_update_interval_minutes"] == 120


# ---------------------------------------------------------------------------
# Integration test for PlanFromTemplateTool
# ---------------------------------------------------------------------------

class TestPlanFromTemplateTool:
    @pytest.mark.asyncio
    async def test_generate_cei_perception(self, sample_goal_spec_json: str, tmp_work_dir: Path):
        tool = PlanFromTemplateTool()
        ctx = ToolExecutionContext(cwd=tmp_work_dir)
        inp = PlanFromTemplateInput(
            template_name="tpl-cei-perception",
            goal_spec=sample_goal_spec_json,
            output_path="output/perception.json",
        )
        result = await tool.execute(inp, ctx)
        assert not result.is_error
        output_file = tmp_work_dir / "output" / "perception.json"
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["cei_warning_threshold"]["value"] == 85

    @pytest.mark.asyncio
    async def test_generate_all_templates(self, sample_goal_spec_json: str, tmp_work_dir: Path):
        tool = PlanFromTemplateTool()
        ctx = ToolExecutionContext(cwd=tmp_work_dir)
        for tpl_name in TEMPLATE_RENDERERS:
            inp = PlanFromTemplateInput(
                template_name=tpl_name,
                goal_spec=sample_goal_spec_json,
                output_path=f"output/{tpl_name}.json",
            )
            result = await tool.execute(inp, ctx)
            assert not result.is_error, f"Template {tpl_name} failed: {result.output}"
            output_file = tmp_work_dir / "output" / f"{tpl_name}.json"
            assert output_file.exists()
            data = json.loads(output_file.read_text())
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_unknown_template(self, sample_goal_spec_json: str, tmp_work_dir: Path):
        tool = PlanFromTemplateTool()
        ctx = ToolExecutionContext(cwd=tmp_work_dir)
        inp = PlanFromTemplateInput(
            template_name="tpl-nonexistent",
            goal_spec=sample_goal_spec_json,
            output_path="output/test.json",
        )
        result = await tool.execute(inp, ctx)
        assert result.is_error

    @pytest.mark.asyncio
    async def test_invalid_json(self, tmp_work_dir: Path):
        tool = PlanFromTemplateTool()
        ctx = ToolExecutionContext(cwd=tmp_work_dir)
        inp = PlanFromTemplateInput(
            template_name="tpl-cei-perception",
            goal_spec="not json",
            output_path="output/test.json",
        )
        result = await tool.execute(inp, ctx)
        assert result.is_error
