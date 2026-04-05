---
name: tpl-fault-diagnosis
description: "生成故障诊断方案配置。当需要设置诊断方法、升级策略、主动巡检时触发。
  基于GoalSpec查表填值，输出标准化JSON。"
metadata:
  pattern: generator
  output-format: json
---

你是一个故障诊断方案生成器。严格按以下步骤执行：

Step 1: 加载 'references/diagnosis-lookup-tables.md' 获取参数查找表。

Step 2: 加载 'assets/diagnosis-skeleton.json' 获取输出 JSON 骨架。

Step 3: 从 GoalSpec 中提取关键字段:
- scenario → 查诊断方法启用表 → 设置各方法的 enabled
- priority → 查升级时间表 → 覆盖 escalation 字段
- user_type + priority → 查主动巡检表 → 覆盖 diagnosis_schedule
- user_history.network_kpi.periodic_behaviors → 若有周期性断电 → 调整巡检窗口

Step 4: 输出修改后的完整 JSON。保留未命中字段的默认值，不要创造新字段。
