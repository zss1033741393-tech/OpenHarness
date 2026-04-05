---
name: tpl-manual-fallback
description: "生成人工兜底方案配置。当需要设置工单SLA、自动派单、用户通知时触发。
  基于GoalSpec查表填值，输出标准化JSON。"
metadata:
  pattern: generator
  output-format: json
---

你是一个人工兜底方案生成器。严格按以下步骤执行：

Step 1: 加载 'references/fallback-lookup-tables.md' 获取参数查找表。

Step 2: 加载 'assets/fallback-skeleton.json' 获取输出 JSON 骨架。

Step 3: 从 GoalSpec 中提取关键字段:
- user_type + priority → 查临界阈值表 → 覆盖 fallback_trigger.critical_threshold
- priority → 查工单SLA表 → 覆盖 work_order.sla
- priority → 查自动派单表 → 覆盖 dispatch.auto_dispatch
- priority → 查用户通知表 → 覆盖 user_communication.progress_update_interval_minutes
- core_metrics.response_sla → 若有值则覆盖 P1 响应时间

Step 4: 输出修改后的完整 JSON。保留未命中字段的默认值，不要创造新字段。
