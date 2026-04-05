---
name: e2e-pipeline
description: "家宽体验优化端到端工作流。从用户需求采集到配置下发的完整流程。
  当用户要求'完整优化'、'端到端保障'、'全流程配置'时触发。"
metadata:
  pattern: pipeline
  steps: "4"
---

你正在执行家宽体验优化全流程。按顺序执行每个步骤。不要跳过步骤，失败时不要继续。

## Step 1 — 目标解析（Inversion）
加载 'goal-parsing' skill，执行结构化采访。
输出: GoalSpec JSON。
🚫 门禁: 用户必须确认 GoalSpec 后才能继续。若用户说"不对"或提出修改，返回修正。

## Step 2 — 方案生成（Generator × 5 并行）
将确认的 GoalSpec 分发到 5 个 Generator Skill 并行填值:
- tpl-cei-perception
- tpl-fault-diagnosis
- tpl-remote-closure
- tpl-dynamic-optimization
- tpl-manual-fallback

输出: 5 个方案 JSON，组合为 SolutionPlan。
🚫 门禁: 全部 5 个方案生成成功后才能继续。任何一个失败需重试。

## Step 3 — 约束校验（Reviewer）
加载 'constraint-review' skill，对 SolutionPlan 执行评审。
同时调用 constraint_check tool 执行机器可算的数值校验。
- 若存在 blocker → 回退到 Step 2，附带违反信息让 Generator 调整参数后重新生成
- 若只有 warning/info → 展示评审报告给用户确认
🚫 门禁: 无 blocker 且用户确认后才能继续。最多重试 3 次。

## Step 4 — 配置转义与输出
调用 config_translate tool，将通过校验的方案转义为 4 个设备配置 JSON:
- perception_config.json
- diagnosis_config.json
- remote_closure_config.json
- dynamic_optimization_config.json

输出: 全部配置文件 + 可读方案文档 (solution_plan.md)。
向用户展示最终结果，询问是否需要调整。

## 模式组合关系

```
e2e-pipeline [Pipeline]
  │
  ├── Step 1: goal-parsing [Inversion]
  │     └── 引用: user-profile [Tool Wrapper]
  │
  ├── Step 2: tpl-*  ×5 并行 [Generator]
  │
  ├── Step 3: constraint-review [Reviewer]
  │     └── 不通过 → 回退 Step 2
  │
  └── Step 4: config_translate [Tool]
```
