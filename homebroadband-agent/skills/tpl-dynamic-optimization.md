---
name: tpl-dynamic-optimization
description: "动态优化方案预制模板：包含完整JSON骨架和参数查找表，按GoalSpec填值即可"
---
# 动态优化方案模板

## JSON 骨架（默认值版本）

```json
{
  "realtime_optimization": {
    "enabled": true,
    "check_interval_seconds": 300,
    "actions": [
      {
        "name": "WIFI频段自动切换",
        "enabled": true,
        "condition": "signal_quality_degraded",
        "target": "切换至最优频段(2.4G/5G)"
      },
      {
        "name": "信道自动优化",
        "enabled": true,
        "condition": "channel_interference_high",
        "target": "切换至干扰最小信道"
      },
      {
        "name": "带宽动态分配",
        "enabled": false,
        "condition": "bandwidth_contention",
        "target": "按优先级重新分配带宽"
      },
      {
        "name": "漫游优化",
        "enabled": false,
        "condition": "roaming_quality_poor",
        "target": "优化AP切换阈值"
      }
    ]
  },
  "predictive_optimization": {
    "enabled": false,
    "prediction_window_minutes": 30,
    "model_type": "time_series",
    "actions": [
      {
        "name": "预调度带宽",
        "trigger": "predicted_peak_traffic",
        "advance_minutes": 15
      },
      {
        "name": "预切换信道",
        "trigger": "predicted_interference",
        "advance_minutes": 10
      }
    ]
  },
  "power_saving": {
    "enabled": false,
    "trigger_time": "01:00",
    "resume_time": "06:00",
    "actions": ["降低WIFI发射功率", "关闭非必要端口", "降低采集频率"]
  },
  "appflow_policy": {
    "enabled": false,
    "rules": []
  }
}
```

## 参数查找表

### 实时优化 → 按 scenario 查表

| scenario | WIFI频段切换 | 信道优化 | 带宽分配 | 漫游优化 | check_interval |
|----------|------------|---------|---------|---------|---------------|
| 直播推流 | true | true | true | false | 120 |
| 在线游戏 | true | true | true | false | 60 |
| 视频会议 | true | true | true | true | 120 |
| 在线教育 | true | true | false | true | 300 |
| 高清视频 | true | true | false | false | 300 |
| 智能家居 | true | true | false | false | 600 |
| 综合场景 | true | true | false | false | 300 |

### 预测优化 → 按 (user_type, priority) 查表

| user_type + priority=高 | predictive_enabled | prediction_window | model_type |
|------------------------|-------------------|-------------------|------------|
| 直播用户 | true | 60 | pattern_based |
| 游戏用户 | true | 30 | time_series |
| 办公用户 | true | 30 | calendar_based |
| 其他 | false | 30 | time_series |

### 节能策略 → 按 user_history 查表

| 条件 | power_saving_enabled | trigger_time | resume_time |
|------|---------------------|-------------|-------------|
| 有power_saving_trigger_time | true | 使用历史值 | 使用历史值+5h |
| 普通家庭用户+低优先级 | true | 01:00 | 06:00 |
| 其他 | false | - | - |

### APPflow 策略 → 按 (scenario, applications) 查表

| scenario | appflow_enabled | 规则模板 |
|----------|----------------|---------|
| 直播推流 | true | 推流应用上行优先 |
| 在线游戏 | true | 游戏应用低延迟优先 |
| 视频会议 | true | 会议应用双向优先 |
| 其他 | false | - |

## 填值规则

1. 读取 GoalSpec.scenario → 查实时优化表 → 覆盖 realtime_optimization 各动作的 enabled 和 check_interval
2. 读取 GoalSpec.user_type + priority → 查预测优化表 → 覆盖 predictive_optimization
3. 读取 GoalSpec.user_history.app_history.power_saving_trigger_time → 查节能策略表 → 覆盖 power_saving
4. 读取 GoalSpec.scenario + applications → 查 APPflow 表 → 覆盖 appflow_policy
5. 冲突检测：若节能时间与保障时段重叠 → 禁用节能或调整时间
6. 输出修改后的完整 JSON
