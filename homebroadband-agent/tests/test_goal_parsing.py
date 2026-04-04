"""Tests for GoalSpec schema validation and goal parsing skill content."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "goal_spec.json"
SKILL_PATH = Path(__file__).parent.parent / "skills" / "goal-parsing.md"


class TestGoalSpecSchema:
    @pytest.fixture
    def schema(self) -> dict:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_schema_loads(self, schema: dict):
        assert schema["title"] == "GoalSpec"
        assert "user_type" in schema["properties"]
        assert "scenario" in schema["properties"]
        assert "guarantee_period" in schema["properties"]
        assert "guarantee_target" in schema["properties"]
        assert "core_metrics" in schema["properties"]

    def test_required_fields(self, schema: dict):
        required = schema["required"]
        assert "user_type" in required
        assert "scenario" in required
        assert "guarantee_period" in required
        assert "guarantee_target" in required
        assert "core_metrics" in required

    def test_user_type_enum(self, schema: dict):
        enum_values = schema["properties"]["user_type"]["enum"]
        assert "直播用户" in enum_values
        assert "游戏用户" in enum_values
        assert "办公用户" in enum_values
        assert "教育用户" in enum_values
        assert "普通家庭用户" in enum_values
        assert "SOHO用户" in enum_values

    def test_scenario_enum(self, schema: dict):
        enum_values = schema["properties"]["scenario"]["enum"]
        assert "直播推流" in enum_values
        assert "在线游戏" in enum_values

    def test_sample_goal_spec_conforms(self, schema: dict, sample_goal_spec: dict):
        """Verify our sample fixture has all required fields."""
        for field in schema["required"]:
            assert field in sample_goal_spec, f"Missing required field: {field}"


class TestGoalParsingSkill:
    def test_skill_file_exists(self):
        assert SKILL_PATH.exists()

    def test_skill_has_frontmatter(self):
        content = SKILL_PATH.read_text(encoding="utf-8")
        assert content.startswith("---")
        assert "name: goal-parsing" in content

    def test_skill_has_semantic_mapping(self):
        content = SKILL_PATH.read_text(encoding="utf-8")
        assert "语义映射表" in content
        assert "直播" in content
        assert "游戏" in content

    def test_skill_has_default_values(self):
        content = SKILL_PATH.read_text(encoding="utf-8")
        assert "默认值补全规则" in content
        assert "直播用户默认值" in content
        assert "游戏用户默认值" in content
