"""Tests for ADK-pattern skill directory structure validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


SKILLS_DIR = Path(__file__).parent.parent / "skills"

# All expected skill directories and their ADK patterns
EXPECTED_SKILLS = {
    "goal-parsing": {"pattern": "inversion", "has_references": True, "has_assets": True},
    "user-profile": {"pattern": "tool-wrapper", "has_references": True, "has_assets": False},
    "tpl-cei-perception": {"pattern": "generator", "has_references": True, "has_assets": True},
    "tpl-fault-diagnosis": {"pattern": "generator", "has_references": True, "has_assets": True},
    "tpl-remote-closure": {"pattern": "generator", "has_references": True, "has_assets": True},
    "tpl-dynamic-optimization": {"pattern": "generator", "has_references": True, "has_assets": True},
    "tpl-manual-fallback": {"pattern": "generator", "has_references": True, "has_assets": True},
    "constraint-review": {"pattern": "reviewer", "has_references": True, "has_assets": False},
    "e2e-pipeline": {"pattern": "pipeline", "has_references": False, "has_assets": False},
}


class TestSkillDirectoryStructure:
    """Validate that all skills follow the ADK directory convention."""

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS.keys())
    def test_skill_dir_exists(self, skill_name: str):
        skill_dir = SKILLS_DIR / skill_name
        assert skill_dir.is_dir(), f"Skill directory missing: {skill_name}/"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS.keys())
    def test_skill_has_skill_md(self, skill_name: str):
        skill_md = SKILLS_DIR / skill_name / "SKILL.md"
        assert skill_md.exists(), f"SKILL.md missing in {skill_name}/"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS.keys())
    def test_skill_has_frontmatter(self, skill_name: str):
        skill_md = SKILLS_DIR / skill_name / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")
        assert content.startswith("---"), f"{skill_name}/SKILL.md missing YAML frontmatter"
        assert f"name: {skill_name}" in content

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS.keys())
    def test_skill_has_pattern_metadata(self, skill_name: str):
        expected = EXPECTED_SKILLS[skill_name]
        skill_md = SKILLS_DIR / skill_name / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")
        assert f"pattern: {expected['pattern']}" in content

    @pytest.mark.parametrize("skill_name", [
        k for k, v in EXPECTED_SKILLS.items() if v["has_references"]
    ])
    def test_skill_has_references(self, skill_name: str):
        refs_dir = SKILLS_DIR / skill_name / "references"
        assert refs_dir.is_dir(), f"references/ missing in {skill_name}/"
        refs = list(refs_dir.glob("*.md"))
        assert len(refs) > 0, f"No .md files in {skill_name}/references/"

    @pytest.mark.parametrize("skill_name", [
        k for k, v in EXPECTED_SKILLS.items() if v["has_assets"]
    ])
    def test_skill_has_assets(self, skill_name: str):
        assets_dir = SKILLS_DIR / skill_name / "assets"
        assert assets_dir.is_dir(), f"assets/ missing in {skill_name}/"
        assets = list(assets_dir.glob("*.json"))
        assert len(assets) > 0, f"No .json files in {skill_name}/assets/"

    def test_no_flat_skill_files_remain(self):
        """Ensure old flat .md skill files have been removed."""
        flat_files = list(SKILLS_DIR.glob("*.md"))
        assert len(flat_files) == 0, (
            f"Flat skill files still exist (should be directories): "
            f"{[f.name for f in flat_files]}"
        )


class TestGeneratorSkeletons:
    """Validate that Generator skill JSON skeletons are valid JSON."""

    GENERATOR_SKILLS = [
        "tpl-cei-perception",
        "tpl-fault-diagnosis",
        "tpl-remote-closure",
        "tpl-dynamic-optimization",
        "tpl-manual-fallback",
    ]

    @pytest.mark.parametrize("skill_name", GENERATOR_SKILLS)
    def test_skeleton_is_valid_json(self, skill_name: str):
        assets_dir = SKILLS_DIR / skill_name / "assets"
        for json_file in assets_dir.glob("*.json"):
            data = json.loads(json_file.read_text(encoding="utf-8"))
            assert isinstance(data, dict), f"{json_file.name} should be a JSON object"

    def test_cei_skeleton_has_required_fields(self):
        skeleton = json.loads(
            (SKILLS_DIR / "tpl-cei-perception" / "assets" / "cei-skeleton.json")
            .read_text(encoding="utf-8")
        )
        assert "cei_warning_threshold" in skeleton
        assert "cei_scenario_model" in skeleton
        assert "cei_granularity" in skeleton
        assert "cei_trigger_window" in skeleton

    def test_diagnosis_skeleton_has_required_fields(self):
        skeleton = json.loads(
            (SKILLS_DIR / "tpl-fault-diagnosis" / "assets" / "diagnosis-skeleton.json")
            .read_text(encoding="utf-8")
        )
        assert "diagnosis_methods" in skeleton
        assert "escalation" in skeleton
        assert "diagnosis_schedule" in skeleton

    def test_closure_skeleton_has_required_fields(self):
        skeleton = json.loads(
            (SKILLS_DIR / "tpl-remote-closure" / "assets" / "closure-skeleton.json")
            .read_text(encoding="utf-8")
        )
        assert "closure_strategy" in skeleton
        assert "auto_recovery" in skeleton
        assert "audit" in skeleton

    def test_optimization_skeleton_has_required_fields(self):
        skeleton = json.loads(
            (SKILLS_DIR / "tpl-dynamic-optimization" / "assets" / "optimization-skeleton.json")
            .read_text(encoding="utf-8")
        )
        assert "realtime_optimization" in skeleton
        assert "predictive_optimization" in skeleton
        assert "power_saving" in skeleton
        assert "appflow_policy" in skeleton

    def test_fallback_skeleton_has_required_fields(self):
        skeleton = json.loads(
            (SKILLS_DIR / "tpl-manual-fallback" / "assets" / "fallback-skeleton.json")
            .read_text(encoding="utf-8")
        )
        assert "fallback_trigger" in skeleton
        assert "work_order" in skeleton
        assert "dispatch" in skeleton
        assert "user_communication" in skeleton


class TestGoalSpecTemplate:
    """Validate the GoalSpec template asset."""

    def test_template_is_valid_json(self):
        template_path = SKILLS_DIR / "goal-parsing" / "assets" / "goal-spec-template.json"
        data = json.loads(template_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_template_has_all_required_fields(self):
        template_path = SKILLS_DIR / "goal-parsing" / "assets" / "goal-spec-template.json"
        data = json.loads(template_path.read_text(encoding="utf-8"))
        required = ["user_type", "scenario", "guarantee_period", "guarantee_target", "core_metrics"]
        for field in required:
            assert field in data, f"Template missing required field: {field}"


class TestConstraintReviewSkill:
    """Validate the constraint-review Reviewer skill."""

    def test_checklist_has_three_categories(self):
        checklist = (
            SKILLS_DIR / "constraint-review" / "references" / "constraint-checklist.md"
        ).read_text(encoding="utf-8")
        assert "性能约束" in checklist
        assert "组网约束" in checklist
        assert "方案冲突" in checklist

    def test_checklist_has_severity_levels(self):
        checklist = (
            SKILLS_DIR / "constraint-review" / "references" / "constraint-checklist.md"
        ).read_text(encoding="utf-8")
        assert "blocker" in checklist
        assert "warning" in checklist
        assert "info" in checklist


class TestE2EPipelineSkill:
    """Validate the e2e-pipeline Pipeline skill."""

    def test_pipeline_has_four_steps(self):
        content = (SKILLS_DIR / "e2e-pipeline" / "SKILL.md").read_text(encoding="utf-8")
        assert "Step 1" in content
        assert "Step 2" in content
        assert "Step 3" in content
        assert "Step 4" in content

    def test_pipeline_has_gates(self):
        content = (SKILLS_DIR / "e2e-pipeline" / "SKILL.md").read_text(encoding="utf-8")
        assert "门禁" in content

    def test_pipeline_references_all_skills(self):
        content = (SKILLS_DIR / "e2e-pipeline" / "SKILL.md").read_text(encoding="utf-8")
        assert "goal-parsing" in content
        assert "tpl-cei-perception" in content
        assert "tpl-fault-diagnosis" in content
        assert "tpl-remote-closure" in content
        assert "tpl-dynamic-optimization" in content
        assert "tpl-manual-fallback" in content
        assert "constraint-review" in content
