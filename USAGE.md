# 家宽体验感知优化 Agent 智能体 — 使用与开发指南

> 基于 [OpenHarness](https://github.com/HKUDS/OpenHarness) v0.1.0 框架二次开发

---

## 1. 快速开始

### 1.1 环境准备

```bash
# 克隆项目
git clone https://github.com/zss1033741393-tech/OpenHarness.git
cd OpenHarness

# 安装依赖
uv sync --extra dev

# 配置 LLM 后端（以 Kimi 为例）
export ANTHROPIC_BASE_URL=https://api.moonshot.cn/anthropic
export ANTHROPIC_API_KEY=your_key
export ANTHROPIC_MODEL=kimi-k2.5
```

### 1.2 验证安装

```bash
# 运行家宽领域测试（117 tests）
uv run python -m pytest tests/test_homebroadband/ -v

# 运行全量测试（含框架测试）
uv run python -m pytest tests/ -v
```

### 1.3 启动使用

```bash
# 交互模式
uv run oh

# 非交互模式（单次 prompt）
uv run oh -p "我是一个直播用户，晚上8点到12点直播，最近经常卡顿，需要保障"
```

---

## 2. 架构概览

本项目通过 OpenHarness 的 **Tool + Skill + Hook + Plugin** 四层扩展体系，实现家宽领域的端到端闭环优化。

### 2.1 集成方式

```
OpenHarness 框架
├── src/openharness/
│   ├── tools/                         # ← 家宽 Tool 注册在此
│   │   ├── plan_from_template_tool.py   # 模板填值（支持并行）
│   │   ├── constraint_check_tool.py     # 三层约束校验
│   │   ├── config_translate_tool.py     # 配置转义（4种设备配置）
│   │   ├── device_query_tool.py         # 设备信息查询（Mock）
│   │   └── kpi_query_tool.py            # 网络KPI查询（Mock）
│   ├── skills/loader.py               # ← 增强：支持 ADK 目录结构
│   └── plugins/loader.py              # ← 增强：支持 ADK 目录结构
│
├── .openharness/plugins/homebroadband/  # ← 家宽领域 Plugin
│   ├── plugin.json                      # 插件清单
│   ├── skills/                          # 9 个 ADK 模式 Skill
│   ├── agents/                          # 5 个 Agent 定义
│   ├── hooks.json                       # 生命周期 Hook
│   └── schemas/                         # JSON Schema
│
└── tests/test_homebroadband/            # ← 家宽领域测试
```

### 2.2 端到端流水线

```
用户输入（自然语言）
    │
    ▼
┌─────────────────────────────────────┐
│ 阶段一：目标解析（GoalParser Agent）   │
│ Skill: goal-parsing [Inversion]      │
│ 多轮追问 → 结构化 GoalSpec JSON       │
└────────────────┬────────────────────┘
                 ▼
┌─────────────────────────────────────┐
│ 阶段二：方案生成（PlanGenerator）      │
│ Tool: plan_from_template × 5 并行    │
│ 查表填值 → SolutionPlan JSON         │
└────────────────┬────────────────────┘
                 ▼
┌─────────────────────────────────────┐
│ 阶段三：约束校验                      │
│ Tool: constraint_check               │
│ Skill: constraint-review [Reviewer]  │
│ 不通过 → 回退重新生成（最多3次）        │
└────────────────┬────────────────────┘
                 ▼
┌─────────────────────────────────────┐
│ 阶段四：配置转义（ConfigTranslator）   │
│ Tool: config_translate               │
│ 输出 4 个设备配置 JSON                │
└─────────────────────────────────────┘
```

---

## 3. 核心组件说明

### 3.1 自定义 Tool（5 个）

Tool 是框架中可被 LLM 调用的原子操作，注册在 `src/openharness/tools/__init__.py`。

| Tool 名称 | 文件 | 功能 | 是否可并行 |
|-----------|------|------|-----------|
| `plan_from_template` | `plan_from_template_tool.py` | 基于 GoalSpec 查表填值生成单维度方案 | 是 |
| `constraint_check` | `constraint_check_tool.py` | 性能约束 + 组网约束 + 冲突检测 | 否 |
| `config_translate` | `config_translate_tool.py` | 方案转义为设备可执行 JSON 配置 | 否 |
| `device_query` | `device_query_tool.py` | 查询设备信息（当前为 Mock） | 是 |
| `kpi_query` | `kpi_query_tool.py` | 查询网络 KPI 数据（当前为 Mock） | 是 |

**使用示例**（LLM 在对话中调用）：
```
# LLM 在一轮中同时发出 5 个 tool call，框架自动 asyncio.gather 并行执行
plan_from_template(template_name="tpl-cei-perception", goal_spec="{...}", output_path="out/cei.json")
plan_from_template(template_name="tpl-fault-diagnosis", goal_spec="{...}", output_path="out/diag.json")
plan_from_template(template_name="tpl-remote-closure", goal_spec="{...}", output_path="out/closure.json")
plan_from_template(template_name="tpl-dynamic-optimization", goal_spec="{...}", output_path="out/opt.json")
plan_from_template(template_name="tpl-manual-fallback", goal_spec="{...}", output_path="out/fallback.json")
```

### 3.2 领域 Skill（9 个，ADK 五大模式）

Skill 是注入给 LLM 的领域知识，位于 `.openharness/plugins/homebroadband/skills/`。

每个 Skill 采用 Google ADK 目录结构：
```
skill-name/
├── SKILL.md                # 主指令文件（含 YAML frontmatter）
├── references/             # 按需加载的参考资料（查找表、映射表）
│   └── *.md
└── assets/                 # 结构化资源（JSON 骨架、模板）
    └── *.json
```

| Skill 名称 | ADK 模式 | 功能 |
|------------|---------|------|
| `goal-parsing` | **Inversion** | 分 3 阶段采访用户，收集需求，输出 GoalSpec |
| `user-profile` | **Tool Wrapper** | 6 类用户画像知识（直播/游戏/办公/教育/家庭/SOHO） |
| `tpl-cei-perception` | **Generator** | CEI 感知方案模板（阈值 + 场景模型 + 粒度） |
| `tpl-fault-diagnosis` | **Generator** | 故障诊断方案模板（5种诊断方法 + 升级策略） |
| `tpl-remote-closure` | **Generator** | 远程闭环方案模板（闭环策略 + QoS + 稽核） |
| `tpl-dynamic-optimization` | **Generator** | 动态优化方案模板（实时 + 预测 + 节能 + APPflow） |
| `tpl-manual-fallback` | **Generator** | 人工兜底方案模板（工单SLA + 派单 + 通知） |
| `constraint-review` | **Reviewer** | 按 blocker/warning/info 分级评审方案合规性 |
| `e2e-pipeline` | **Pipeline** | 端到端 4 步工作流编排，含门禁条件 |

### 3.3 Agent 定义（5 个）

Agent 是带有特定职责的 LLM 角色，位于 `.openharness/plugins/homebroadband/agents/`。

| Agent | 角色 | 调度方式 |
|-------|------|---------|
| `Coordinator` | 总协调，调度各阶段 | 主 Agent，用户直接交互 |
| `GoalParser` | 目标解析，多轮追问 | 被 Coordinator 通过 `agent` Tool 调度 |
| `PlanGenerator` | 方案生成协调 | 并行 spawn 5 个 Worker 或 5 次 Tool Call |
| `PlanWorker` | 单维度方案填值 | background Worker，被 PlanGenerator spawn |
| `ConfigTranslator` | 配置转义输出 | 被 Coordinator 调度 |

### 3.4 Hook

Hook 在 Tool 执行前后自动触发，定义在 `.openharness/plugins/homebroadband/hooks.json`：

- **PreToolUse**：`config_translate` 执行前运行 `validate_constraints.py`，校验方案完整性
- **PostToolUse**：`config_translate` 执行后输出完成提示

---

## 4. 开发指南

### 4.1 新增 Tool

1. 在 `src/openharness/tools/` 创建 `your_tool.py`：

```python
from pydantic import BaseModel, Field
from openharness.tools.base import BaseTool, ToolExecutionContext, ToolResult

class YourToolInput(BaseModel):
    param: str = Field(description="参数说明")

class YourTool(BaseTool):
    name = "your_tool"
    description = "Tool 功能描述（LLM 看到的）"
    input_model = YourToolInput

    async def execute(self, arguments: YourToolInput,
                      context: ToolExecutionContext) -> ToolResult:
        # 实现逻辑
        return ToolResult(output="结果")
```

2. 在 `src/openharness/tools/__init__.py` 中注册：

```python
from openharness.tools.your_tool import YourTool

# 在 create_default_tool_registry() 的 tool 列表中添加：
YourTool(),
```

3. 编写测试 `tests/test_homebroadband/test_your_tool.py`。

### 4.2 新增 Skill

在 `.openharness/plugins/homebroadband/skills/` 下创建目录：

```bash
mkdir -p .openharness/plugins/homebroadband/skills/your-skill/references
mkdir -p .openharness/plugins/homebroadband/skills/your-skill/assets
```

创建 `SKILL.md`（必须含 YAML frontmatter）：

```markdown
---
name: your-skill
description: "Skill 功能描述（用于触发匹配）"
metadata:
  pattern: generator    # inversion / tool-wrapper / generator / reviewer / pipeline
  output-format: json   # 可选
---

你是一个 XXX 专家。按以下步骤执行：

Step 1: 加载 'references/your-lookup-tables.md' 获取参数表。
Step 2: 加载 'assets/your-skeleton.json' 获取输出骨架。
Step 3: 根据输入查表填值。
Step 4: 输出完整 JSON。
```

> **框架会自动发现**：`_load_plugin_skills()` 同时支持 `*.md`（扁平）和 `*/SKILL.md`（ADK 目录）两种格式。

### 4.3 新增 Agent

在 `.openharness/plugins/homebroadband/agents/` 下创建 `.md` 文件：

```markdown
---
name: YourAgent
description: "何时使用该 Agent"
tools:
  - plan_from_template
  - constraint_check
  - write_file
skills:
  - your-skill
maxTurns: 10
color: green
---

你是 XXX 专家。你的任务是...
```

### 4.4 修改查找表

模板 Skill 的核心数据在 `references/` 目录的 Markdown 表格中，同时也在 `plan_from_template_tool.py` 的 Python dict 中硬编码。

**修改方法**（两处需同步）：

1. **Skill 查找表**（供 LLM 理解）：编辑 `.openharness/plugins/homebroadband/skills/tpl-*/references/*.md`
2. **Tool 硬编码表**（供代码执行）：编辑 `src/openharness/tools/plan_from_template_tool.py` 中对应的 `*_TABLE` dict

示例 — 添加新用户类型"电竞用户"的 CEI 阈值：

```python
# src/openharness/tools/plan_from_template_tool.py
CEI_THRESHOLD_TABLE = {
    ("直播用户", "高"): 85,
    ("游戏用户", "高"): 80,
    ("电竞用户", "高"): 90,   # ← 新增
    ...
}
```

### 4.5 添加新的方案维度

若要新增第 6 个方案维度（如"安全防护方案"）：

1. **新增 Generator Skill**：创建 `.openharness/plugins/homebroadband/skills/tpl-security-protection/`
2. **新增渲染函数**：在 `plan_from_template_tool.py` 中添加 `_render_security_protection()` 和对应查找表
3. **注册到 TEMPLATE_RENDERERS**：`"tpl-security-protection": _render_security_protection`
4. **更新 PlanGenerator**：修改 `agents/plan-generator.md`，从 5 个并行变为 6 个
5. **更新 e2e-pipeline Skill**：在 Step 2 中添加新维度
6. **新增配置转义**：在 `config_translate_tool.py` 中添加 `_translate_security_protection()`

### 4.6 对接真实设备 API

当前 `device_query_tool.py` 和 `kpi_query_tool.py` 使用 Mock 数据。对接真实 API 的推荐方式：

**方式一：直接修改 Tool**

替换 `MOCK_DEVICES` / `MOCK_KPI` 为真实 API 调用。

**方式二：MCP Server（推荐）**

创建 MCP Server 并在插件中配置：

```json
// .openharness/plugins/homebroadband/mcp.json
{
  "mcpServers": {
    "device-api": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/device_server.py"]
    }
  }
}
```

---

## 5. GoalSpec 数据结构

GoalSpec 是整个流水线的核心输入，Schema 定义在 `.openharness/plugins/homebroadband/schemas/goal_spec.json`。

```json
{
  "user_type": "直播用户",              // 必填：6 种用户类型
  "scenario": "直播推流",               // 必填：7 种场景
  "guarantee_period": {                 // 必填：保障时段
    "type": "固定时段",
    "time_ranges": [{"start": "20:00", "end": "00:00"}]
  },
  "guarantee_target": {                 // 必填：保障对象
    "priority": "高",                   //   优先级：高/中/低
    "focus": "上行",                    //   方向：上行/下行/双向
    "applications": ["抖音直播"],        //   重点应用
    "sensitivity": {                    //   灵敏度
      "latency": "高敏感",
      "jitter": "高敏感",
      "packet_loss": "高敏感"
    }
  },
  "core_metrics": {                     // 必填：核心指标
    "cei_threshold": 85,
    "response_sla": "<15min",
    "availability_target": 99.5
  },
  "user_history": { ... }              // 可选：用户历史数据
}
```

**支持的用户类型**：直播用户、游戏用户、办公用户、教育用户、普通家庭用户、SOHO用户

**支持的场景**：直播推流、在线游戏、视频会议、在线教育、高清视频、智能家居、综合场景

---

## 6. 测试

### 6.1 测试结构

```
tests/test_homebroadband/
├── conftest.py                  # 共享 fixtures（sample_goal_spec 等）
├── test_plan_generation.py      # 模板填值 + 渲染器测试（19 tests）
├── test_constraint_check.py     # 约束校验测试（9 tests）
├── test_config_translate.py     # 配置转义测试（8 tests）
├── test_goal_parsing.py         # Schema + Skill 结构测试（12 tests）
└── test_skill_adk_structure.py  # ADK 目录结构 + Plugin 验证（69 tests）
```

### 6.2 运行测试

```bash
# 家宽领域测试
uv run python -m pytest tests/test_homebroadband/ -v

# 单个模块
uv run python -m pytest tests/test_homebroadband/test_plan_generation.py -v

# 含框架测试的全量回归
uv run python -m pytest tests/ -v
```

### 6.3 编写新测试

测试中可直接导入框架模块：

```python
from openharness.tools.plan_from_template_tool import PlanFromTemplateTool
from openharness.tools.base import ToolExecutionContext, ToolResult
```

Plugin 资源路径通过 `conftest.py` 中的 `PLUGIN_ROOT` 常量获取：

```python
from tests.test_homebroadband.conftest import PLUGIN_ROOT
schema_path = PLUGIN_ROOT / "schemas" / "goal_spec.json"
```

---

## 7. LLM 后端配置

OpenHarness 支持多种 LLM 后端：

| 后端 | 环境变量 | 适用场景 |
|------|---------|---------|
| **Kimi** | `ANTHROPIC_BASE_URL=https://api.moonshot.cn/anthropic` | 国内开发调试 |
| **DashScope** | `--api-format openai --base-url https://dashscope.aliyuncs.com/compatible-mode/v1` | 国内替代 |
| **Claude** | `ANTHROPIC_API_KEY=sk-ant-...` | 效果最佳 |
| **Ollama 本地** | `ANTHROPIC_BASE_URL=http://localhost:11434/v1` | 离线/数据安全 |

```bash
# Kimi 示例
export ANTHROPIC_BASE_URL=https://api.moonshot.cn/anthropic
export ANTHROPIC_API_KEY=your_key
export ANTHROPIC_MODEL=kimi-k2.5
uv run oh

# DashScope (OpenAI 格式) 示例
uv run oh --api-format openai \
  --base-url "https://dashscope.aliyuncs.com/compatible-mode/v1" \
  --api-key "sk-xxx" --model "qwen3.5-flash"
```

---

## 8. 常见场景示例

### 场景一：直播用户保障

```
输入: "我是一个直播用户，晚上8点到12点直播，最近经常卡顿，需要保障"

Agent 执行流程:
1. GoalParser 识别: user_type=直播用户, scenario=直播推流
2. GoalParser 追问: "保障优先级？" → "高"
3. GoalParser 输出 GoalSpec JSON
4. PlanGenerator 并行生成 5 个方案（~100ms/个）
5. ConstraintCheck 校验通过
6. ConfigTranslator 输出:
   - perception_config.json   (CEI 阈值 85, 上行优先模型)
   - diagnosis_config.json    (5 种诊断全开, 6h 巡检)
   - remote_closure_config.json (激进模式, QoS 上行优先)
   - dynamic_optimization_config.json (带宽分配+预测优化)
```

### 场景二：游戏用户保障

```
输入: "帮我为一个游戏用户做全天候保障，他玩王者荣耀经常延迟高"

自动推断:
- user_type=游戏用户, scenario=在线游戏
- sensitivity.latency=高敏感, focus=双向
- applications=["王者荣耀"]
- CEI 阈值=80, 场景模型=low_latency_priority
```

### 场景三：仅生成单维度方案

```
输入: "为办公用户生成 CEI 感知配置，中优先级"

仅调用: plan_from_template(template_name="tpl-cei-perception", ...)
输出: CEI 阈值=65, 场景模型=bidirectional_balanced
```

---

## 9. 项目路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| **Phase 1** | 最小可行穿刺（直播用户场景跑通） | ✅ 已完成 |
| **Phase 2** | 丰富查找表 + Swarm Worker 模式 + 用户历史注入 | 待开发 |
| **Phase 3** | 多 Agent 协同 + 真实设备 API (MCP) + Memory 持久化 | 待开发 |
