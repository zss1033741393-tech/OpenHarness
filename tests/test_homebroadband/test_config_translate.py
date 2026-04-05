"""Tests for config_translate_tool.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openharness.tools.config_translate_tool import (
    ConfigTranslateTool,
    ConfigTranslateInput,
    _translate_perception,
    _translate_diagnosis,
    _translate_remote_closure,
    _translate_dynamic_optimization,
)
from openharness.tools.base import ToolExecutionContext


class TestPerceptionTranslation:
    def test_basic_translation(self, sample_solution_plan: dict):
        config = _translate_perception(sample_solution_plan, "USER_001")
        assert config["version"] == "1.0"
        assert config["user_id"] == "USER_001"
        assert config["cei_config"]["warning_threshold"] == 85
        assert config["cei_config"]["scenario_model"] == "uplink_priority"
        assert config["cei_config"]["sampling"]["interval_seconds"] == 300
        assert len(config["cei_config"]["sampling"]["metrics"]) > 0


class TestDiagnosisTranslation:
    def test_basic_translation(self, sample_solution_plan: dict):
        config = _translate_diagnosis(sample_solution_plan, "USER_001")
        assert config["version"] == "1.0"
        assert config["user_id"] == "USER_001"
        assert len(config["diagnosis_config"]["methods"]) > 0


class TestRemoteClosureTranslation:
    def test_basic_translation(self, sample_solution_plan: dict):
        config = _translate_remote_closure(sample_solution_plan, "USER_001")
        assert config["version"] == "1.0"
        assert config["closure_config"]["strategy"] == "aggressive"
        assert config["closure_config"]["auto_recovery"]["enabled"] is True


class TestDynamicOptimizationTranslation:
    def test_basic_translation(self, sample_solution_plan: dict):
        config = _translate_dynamic_optimization(sample_solution_plan, "USER_001")
        assert config["version"] == "1.0"
        assert config["optimization_config"]["realtime_optimization"]["enabled"] is True


class TestConfigTranslateTool:
    @pytest.mark.asyncio
    async def test_generate_all_configs(self, sample_solution_plan: dict, tmp_work_dir: Path):
        tool = ConfigTranslateTool()
        ctx = ToolExecutionContext(cwd=tmp_work_dir)
        inp = ConfigTranslateInput(
            validated_plan=json.dumps(sample_solution_plan, ensure_ascii=False),
            config_type="all",
            output_dir="configs",
            user_id="USER_TEST",
        )
        result = await tool.execute(inp, ctx)
        assert not result.is_error
        data = json.loads(result.output)
        assert data["count"] == 4
        for fpath in data["generated_files"]:
            assert Path(fpath).exists()

    @pytest.mark.asyncio
    async def test_generate_single_config(self, sample_solution_plan: dict, tmp_work_dir: Path):
        tool = ConfigTranslateTool()
        ctx = ToolExecutionContext(cwd=tmp_work_dir)
        inp = ConfigTranslateInput(
            validated_plan=json.dumps(sample_solution_plan, ensure_ascii=False),
            config_type="perception",
            output_dir="configs",
        )
        result = await tool.execute(inp, ctx)
        assert not result.is_error
        data = json.loads(result.output)
        assert data["count"] == 1

    @pytest.mark.asyncio
    async def test_invalid_config_type(self, sample_solution_plan: dict, tmp_work_dir: Path):
        tool = ConfigTranslateTool()
        ctx = ToolExecutionContext(cwd=tmp_work_dir)
        inp = ConfigTranslateInput(
            validated_plan=json.dumps(sample_solution_plan, ensure_ascii=False),
            config_type="invalid",
        )
        result = await tool.execute(inp, ctx)
        assert result.is_error

    @pytest.mark.asyncio
    async def test_invalid_json(self, tmp_work_dir: Path):
        tool = ConfigTranslateTool()
        ctx = ToolExecutionContext(cwd=tmp_work_dir)
        inp = ConfigTranslateInput(validated_plan="not json")
        result = await tool.execute(inp, ctx)
        assert result.is_error
