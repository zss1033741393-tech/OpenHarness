#!/usr/bin/env python3
"""环境初始化脚本：将 agents/skills 拷贝到 OpenHarness 用户配置目录."""

from __future__ import annotations

import shutil
from pathlib import Path


def get_openharness_config_dir() -> Path:
    """Get the OpenHarness config directory."""
    config_dir = Path.home() / ".openharness"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def setup():
    """Copy agents and skills to OpenHarness config directory."""
    project_root = Path(__file__).parent.parent
    config_dir = get_openharness_config_dir()

    # Copy agents
    agents_src = project_root / "agents"
    agents_dst = config_dir / "agents"
    agents_dst.mkdir(parents=True, exist_ok=True)
    for f in agents_src.glob("*.md"):
        shutil.copy2(f, agents_dst / f.name)
        print(f"  Copied agent: {f.name}")

    # Copy skills
    skills_src = project_root / "skills"
    skills_dst = config_dir / "skills"
    skills_dst.mkdir(parents=True, exist_ok=True)
    for f in skills_src.glob("*.md"):
        shutil.copy2(f, skills_dst / f.name)
        print(f"  Copied skill: {f.name}")

    # Copy hooks
    hooks_src = project_root / "hooks"
    hooks_dst = config_dir / "hooks"
    hooks_dst.mkdir(parents=True, exist_ok=True)
    for f in hooks_src.glob("*.json"):
        shutil.copy2(f, hooks_dst / f.name)
        print(f"  Copied hook config: {f.name}")

    print("\nSetup complete! You can now run:")
    print("  uv run oh -p '我是一个直播用户，晚上8点到12点直播，最近经常卡顿'")


if __name__ == "__main__":
    setup()
