# OpenHarness - 家宽体验感知优化 Agent 智能体

## Git 提交规范

- **必须使用 `git push` 命令进行代码提交和推送**，禁止使用 MCP 工具进行代码提交
- 提交前先 `git add` 相关文件，再 `git commit`，最后 `git push -u origin <branch-name>`
- commit message 使用中文或英文均可，需简明扼要描述变更内容
- 推送失败时最多重试 4 次，使用指数退避（2s, 4s, 8s, 16s）

## 项目结构

本项目在 OpenHarness 框架上进行二次开发，家宽领域扩展深度集成到框架各子系统中：

### 自定义 Tool（注册到框架 Tool Registry）
```
src/openharness/tools/
├── plan_from_template_tool.py     # 模板填值 Tool（支持并行调用）
├── constraint_check_tool.py       # 约束校验 Tool（三层校验）
├── config_translate_tool.py       # 配置转义 Tool（4 种设备配置）
├── device_query_tool.py           # 设备信息查询 Tool（Mock）
└── kpi_query_tool.py              # 网络 KPI 查询 Tool（Mock）
```

### Plugin（领域 Skill + Agent + Hook）
```
.openharness/plugins/homebroadband/
├── plugin.json                    # 插件清单
├── skills/                        # 领域 Skill（ADK 目录结构）
│   ├── goal-parsing/              # [Inversion] 目标解析采访
│   │   ├── SKILL.md
│   │   ├── references/semantic-mapping.md
│   │   └── assets/goal-spec-template.json
│   ├── user-profile/              # [Tool Wrapper] 用户画像知识
│   ├── tpl-cei-perception/        # [Generator] CEI 感知方案
│   ├── tpl-fault-diagnosis/       # [Generator] 故障诊断方案
│   ├── tpl-remote-closure/        # [Generator] 远程闭环方案
│   ├── tpl-dynamic-optimization/  # [Generator] 动态优化方案
│   ├── tpl-manual-fallback/       # [Generator] 人工兜底方案
│   ├── constraint-review/         # [Reviewer] 约束校验评审
│   └── e2e-pipeline/              # [Pipeline] 端到端流程编排
├── agents/                        # Agent 定义
│   ├── coordinator.md             # 总协调 Agent
│   ├── goal-parser.md             # 目标解析 Agent
│   ├── plan-generator.md          # 方案生成协调 Agent
│   ├── plan-worker.md             # 方案填值 Worker
│   └── config-translator.md       # 配置转义 Agent
├── hooks.json                     # PreToolUse/PostToolUse Hook
├── schemas/                       # JSON Schema 定义
└── scripts/                       # Hook 辅助脚本
```

### 框架扩展（Skill Loader 增强）
- `src/openharness/skills/loader.py` — 支持 ADK 目录结构 (`<name>/SKILL.md`)
- `src/openharness/plugins/loader.py` — 插件目录同样支持 ADK 结构

### 测试
```
tests/test_homebroadband/          # 家宽领域测试（117 tests）
├── conftest.py                    # 共享 fixtures
├── test_plan_generation.py        # 模板填值测试（19 tests）
├── test_constraint_check.py       # 约束校验测试（9 tests）
├── test_config_translate.py       # 配置转义测试（8 tests）
├── test_goal_parsing.py           # 目标解析测试（12 tests）
└── test_skill_adk_structure.py    # ADK 结构验证（69 tests）
```

## 开发分支

- 主开发分支：`dev`
- 推送命令：`git push -u origin dev`

## 技术栈

- Python 3.10+
- OpenHarness v0.1.0
- Pydantic v2 (数据模型)
- pytest + pytest-asyncio (测试)

## 运行测试

```bash
# 家宽领域测试
uv run python -m pytest tests/test_homebroadband/ -v

# 全量测试
uv run python -m pytest tests/ -v
```
