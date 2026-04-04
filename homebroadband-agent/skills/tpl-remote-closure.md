---
name: tpl-remote-closure
description: "远程闭环方案预制模板：包含完整JSON骨架和参数查找表，按GoalSpec填值即可"
---
# 远程闭环方案模板

## JSON 骨架（默认值版本）

```json
{
  "closure_strategy": {
    "mode": "balanced",
    "description": "均衡模式：自动修复常见问题，异常情况人工介入"
  },
  "auto_recovery": {
    "enabled": true,
    "max_retries": 3,
    "retry_interval_seconds": 300,
    "actions": [
      {
        "name": "WIFI信道自动切换",
        "enabled": true,
        "condition": "wifi_interference > threshold",
        "rollback_supported": true
      },
      {
        "name": "PPPoE自动重拨",
        "enabled": true,
        "condition": "pppoe_session_lost",
        "rollback_supported": false
      },
      {
        "name": "QoS策略自动调整",
        "enabled": false,
        "condition": "bandwidth_contention_detected",
        "rollback_supported": true
      },
      {
        "name": "DNS自动切换",
        "enabled": true,
        "condition": "dns_resolution_timeout",
        "rollback_supported": true
      },
      {
        "name": "网关自动重启",
        "enabled": false,
        "condition": "gateway_unresponsive",
        "rollback_supported": false
      }
    ]
  },
  "audit": {
    "enabled": true,
    "audit_interval_minutes": 30,
    "rollback_on_failure": true,
    "success_criteria": {
      "cei_improvement_threshold": 10,
      "check_duration_minutes": 15
    }
  },
  "notification": {
    "notify_user": true,
    "notify_channel": "sms",
    "notify_on_auto_recovery": true,
    "notify_on_escalation": true
  }
}
```

## 参数查找表

### 闭环策略 → 按 priority 查表

| priority | mode | 启用动作 | max_retries | retry_interval |
|----------|------|---------|-------------|----------------|
| 高 | aggressive | WIFI切换+PPPoE重拨+QoS调整+DNS切换+网关重启 | 2 | 120 |
| 中 | balanced | WIFI切换+PPPoE重拨+DNS切换 | 3 | 300 |
| 低 | conservative | WIFI切换+DNS切换 | 5 | 600 |

### QoS 策略 → 按 scenario 查表

| scenario | QoS_enabled | 优先级策略 |
|----------|------------|----------|
| 直播推流 | true | 上行优先，预留50%上行带宽 |
| 在线游戏 | true | 低延迟优先，游戏流量最高优先级 |
| 视频会议 | true | 双向均衡，视频会议流量优先 |
| 在线教育 | true | 下行优先，教育应用流量优先 |
| 高清视频 | false | 无特殊QoS |
| 智能家居 | false | 无特殊QoS |
| 综合场景 | false | 无特殊QoS |

### 稽核参数 → 按 sensitivity.latency 查表

| sensitivity | audit_interval | check_duration | cei_improvement_threshold |
|-------------|---------------|----------------|--------------------------|
| 高敏感 | 15 | 10 | 5 |
| 中敏感 | 30 | 15 | 10 |
| 低敏感 | 60 | 30 | 15 |

## 填值规则

1. 读取 GoalSpec.guarantee_target.priority → 查闭环策略表 → 覆盖 closure_strategy 和 auto_recovery
2. 读取 GoalSpec.scenario → 查 QoS 策略表 → 设置 QoS 自动调整的 enabled 和条件
3. 读取 GoalSpec.guarantee_target.sensitivity.latency → 查稽核参数表 → 覆盖 audit 字段
4. 若 GoalSpec.user_history.network_kpi.alarm_suppression 有抑制规则 → 对应动作不触发通知
5. 输出修改后的完整 JSON
