"""Tests for constraint_check_tool.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.constraint_check_tool import (
    ConstraintCheckTool,
    ConstraintCheckInput,
    _check_performance,
    _check_network_topology,
    _check_conflicts,
    _time_overlaps,
)
from openharness.tools.base import ToolExecutionContext


class TestPerformanceCheck:
    def test_pass_normal_plan(self, sample_solution_plan: dict):
        device = {"model": "HG8145X6", "version": "V5R020C10", "managed": True}
        result = _check_performance(sample_solution_plan, device)
        assert result["passed"] is True

    def test_fail_too_many_metrics(self, sample_solution_plan: dict):
        # Override with too many metrics for a weaker device
        sample_solution_plan["plans"]["experience_perception"]["cei_granularity"]["metrics"] = [
            f"metric_{i}" for i in range(15)
        ]
        device = {"model": "HG8245Q2", "version": "V3R017C10", "managed": True}
        result = _check_performance(sample_solution_plan, device)
        assert result["passed"] is False
        assert any("采集指标数" in v for v in result["violations"])


class TestNetworkTopologyCheck:
    def test_pass_managed_device(self, sample_solution_plan: dict):
        device = {"model": "HG8145X6", "version": "V5R020C10", "managed": True}
        result = _check_network_topology(sample_solution_plan, device)
        assert result["passed"] is True

    def test_fail_unmanaged_device(self, sample_solution_plan: dict):
        device = {"model": "HG8145X6", "version": "V5R020C10", "managed": False}
        result = _check_network_topology(sample_solution_plan, device)
        assert result["passed"] is False
        assert any("未纳管" in v for v in result["violations"])


class TestConflictCheck:
    def test_no_conflicts_when_power_saving_disabled(self, sample_solution_plan: dict):
        result = _check_conflicts(sample_solution_plan)
        # Power saving is disabled, so no time overlap conflict
        assert all("节能时段" not in v for v in result.get("violations", []))

    def test_power_saving_guarantee_period_conflict(self, sample_solution_plan: dict):
        # Enable power saving during guarantee period
        sample_solution_plan["plans"]["dynamic_optimization"]["power_saving"] = {
            "enabled": True,
            "trigger_time": "21:00",
            "resume_time": "02:00",
        }
        result = _check_conflicts(sample_solution_plan)
        assert result["passed"] is False
        assert any("节能时段" in v for v in result["violations"])


class TestTimeOverlaps:
    def test_overlapping(self):
        assert _time_overlaps("20:00", "00:00", "22:00", "23:00") is True

    def test_non_overlapping(self):
        assert _time_overlaps("01:00", "06:00", "20:00", "00:00") is False

    def test_invalid_time(self):
        assert _time_overlaps("abc", "def", "20:00", "22:00") is False


class TestConstraintCheckTool:
    @pytest.mark.asyncio
    async def test_full_check_pass(self, sample_solution_plan: dict, tmp_work_dir: Path):
        # Disable appflow to avoid known conflict with 5min detection window
        sample_solution_plan["plans"]["dynamic_optimization"]["appflow_policy"]["enabled"] = False
        tool = ConstraintCheckTool()
        ctx = ToolExecutionContext(cwd=tmp_work_dir)
        inp = ConstraintCheckInput(
            solution_plan=json.dumps(sample_solution_plan, ensure_ascii=False),
            device_info='{"model": "HG8145X6", "version": "V5R020C10", "managed": true}',
        )
        result = await tool.execute(inp, ctx)
        data = json.loads(result.output)
        assert data["passed"] is True

    @pytest.mark.asyncio
    async def test_invalid_json_input(self, tmp_work_dir: Path):
        tool = ConstraintCheckTool()
        ctx = ToolExecutionContext(cwd=tmp_work_dir)
        inp = ConstraintCheckInput(solution_plan="not json")
        result = await tool.execute(inp, ctx)
        assert result.is_error
