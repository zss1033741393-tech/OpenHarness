---
name: tpl-manual-fallback
description: "人工兜底方案预制模板：包含完整JSON骨架和参数查找表，按GoalSpec填值即可"
---
# 人工兜底方案模板

## JSON 骨架（默认值版本）

```json
{
  "fallback_trigger": {
    "auto_diagnosis_failed": true,
    "auto_recovery_failed": true,
    "cei_below_critical": true,
    "critical_threshold": 40,
    "user_complaint": true,
    "max_auto_attempts_exceeded": true
  },
  "work_order": {
    "auto_create": true,
    "priority_mapping": {
      "高": "P1-紧急",
      "中": "P2-重要",
      "低": "P3-一般"
    },
    "required_info": [
      "用户ID",
      "故障现象描述",
      "自动诊断结果",
      "自动修复尝试记录",
      "当前CEI评分",
      "网络拓扑信息"
    ],
    "sla": {
      "P1": {"response_minutes": 15, "resolve_hours": 4},
      "P2": {"response_minutes": 30, "resolve_hours": 8},
      "P3": {"response_minutes": 60, "resolve_hours": 24}
    }
  },
  "dispatch": {
    "auto_dispatch": false,
    "dispatch_rules": [
      {
        "condition": "光衰问题",
        "team": "线路维护组",
        "skill_required": "光纤熔接"
      },
      {
        "condition": "设备故障",
        "team": "设备维护组",
        "skill_required": "网关更换"
      },
      {
        "condition": "WIFI覆盖问题",
        "team": "装维组",
        "skill_required": "组网优化"
      }
    ]
  },
  "user_communication": {
    "auto_notify": true,
    "notify_template": "standard",
    "channels": ["sms", "app_push"],
    "progress_update_interval_minutes": 60
  }
}
```

## 参数查找表

### 临界阈值 → 按 (user_type, priority) 查表

| user_type | priority=高 | priority=中 | priority=低 |
|-----------|-----------|-----------|-----------|
| 直播用户 | 50 | 40 | 30 |
| 游戏用户 | 45 | 35 | 25 |
| 办公用户 | 40 | 30 | 20 |
| 教育用户 | 40 | 30 | 20 |
| 普通家庭用户 | 35 | 25 | 15 |
| SOHO用户 | 40 | 30 | 20 |

### 工单SLA → 按 priority 查表

| priority | P1响应 | P1解决 | P2响应 | P2解决 | P3响应 | P3解决 |
|----------|-------|-------|-------|-------|-------|-------|
| 高 | 10min | 2h | 20min | 4h | 30min | 8h |
| 中 | 15min | 4h | 30min | 8h | 60min | 24h |
| 低 | 30min | 8h | 60min | 24h | 120min | 48h |

### 自动派单 → 按 priority 查表

| priority | auto_dispatch |
|----------|--------------|
| 高 | true |
| 中 | false |
| 低 | false |

### 用户通知 → 按 priority 查表

| priority | progress_update_interval |
|----------|------------------------|
| 高 | 30 |
| 中 | 60 |
| 低 | 120 |

## 填值规则

1. 读取 GoalSpec.user_type + priority → 查临界阈值表 → 覆盖 fallback_trigger.critical_threshold
2. 读取 GoalSpec.guarantee_target.priority → 查工单SLA表 → 覆盖 work_order.sla
3. 读取 GoalSpec.guarantee_target.priority → 查自动派单表 → 覆盖 dispatch.auto_dispatch
4. 读取 GoalSpec.guarantee_target.priority → 查用户通知表 → 覆盖 user_communication.progress_update_interval_minutes
5. 若 GoalSpec.core_metrics.response_sla 有值 → 用该值覆盖 P1 响应时间
6. 输出修改后的完整 JSON
