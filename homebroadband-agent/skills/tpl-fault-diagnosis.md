---
name: tpl-fault-diagnosis
description: "故障诊断方案预制模板：包含完整JSON骨架和参数查找表，按GoalSpec填值即可"
---
# 故障诊断方案模板

## JSON 骨架（默认值版本）

```json
{
  "diagnosis_methods": [
    {
      "name": "光衰检测",
      "enabled": true,
      "trigger_condition": "cei_score < threshold",
      "timeout_seconds": 60,
      "priority": 1
    },
    {
      "name": "WIFI信道诊断",
      "enabled": true,
      "trigger_condition": "wifi_interference_detected",
      "timeout_seconds": 120,
      "priority": 2
    },
    {
      "name": "PPPoE连接诊断",
      "enabled": true,
      "trigger_condition": "connection_drop_detected",
      "timeout_seconds": 90,
      "priority": 3
    },
    {
      "name": "DNS解析诊断",
      "enabled": true,
      "trigger_condition": "dns_resolution_slow",
      "timeout_seconds": 30,
      "priority": 4
    },
    {
      "name": "路由追踪诊断",
      "enabled": false,
      "trigger_condition": "high_rtt_detected",
      "timeout_seconds": 180,
      "priority": 5
    }
  ],
  "escalation": {
    "auto_escalate_after_minutes": 30,
    "escalation_levels": ["L1-自动诊断", "L2-远程运维", "L3-现场处理"],
    "max_auto_retries": 3
  },
  "diagnosis_schedule": {
    "proactive_check_enabled": false,
    "proactive_check_interval_hours": 24,
    "check_time_window": {"start": "02:00", "end": "06:00"}
  }
}
```

## 参数查找表

### 诊断方法启用 → 按 scenario 查表

| scenario | 光衰检测 | WIFI信道 | PPPoE | DNS | 路由追踪 |
|----------|---------|---------|-------|-----|---------|
| 直播推流 | true | true | true | true | true |
| 在线游戏 | true | true | true | true | true |
| 视频会议 | true | true | true | true | false |
| 在线教育 | true | true | true | true | false |
| 高清视频 | true | true | true | false | false |
| 智能家居 | true | true | false | true | false |
| 综合场景 | true | true | true | true | false |

### 升级时间 → 按 priority 查表

| priority | auto_escalate_after_minutes | max_auto_retries |
|----------|---------------------------|-----------------|
| 高 | 15 | 2 |
| 中 | 30 | 3 |
| 低 | 60 | 5 |

### 主动巡检 → 按 (user_type, priority) 查表

| user_type + priority=高 | proactive_check_enabled | interval_hours |
|------------------------|------------------------|----------------|
| 直播用户 | true | 6 |
| 游戏用户 | true | 12 |
| 办公用户 | true | 12 |
| 教育用户 | true | 12 |
| 其他 | false | 24 |

## 填值规则

1. 读取 GoalSpec.scenario → 查诊断方法启用表 → 设置各方法的 enabled
2. 读取 GoalSpec.guarantee_target.priority → 查升级时间表 → 覆盖 escalation 字段
3. 读取 GoalSpec.user_type + priority → 查主动巡检表 → 覆盖 diagnosis_schedule
4. 若 GoalSpec.user_history.network_kpi.periodic_behaviors 有周期性断电记录 → 调整巡检时间窗口避开断电时段
5. 输出修改后的完整 JSON
