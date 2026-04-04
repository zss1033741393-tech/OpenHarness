---
name: tpl-cei-perception
description: "CEI体验感知方案预制模板：包含完整JSON骨架和参数查找表，按GoalSpec填值即可"
---
# CEI 体验感知方案模板

## JSON 骨架（默认值版本）

以下是完整的方案 JSON，所有字段都已填入保守默认值。
你的任务是根据 GoalSpec 中的 user_type、scenario、guarantee_target 等字段，
查阅下方参数表，替换对应字段的值。

```json
{
  "cei_warning_threshold": {
    "level": "标准",
    "value": 70,
    "description": "默认标准阈值"
  },
  "cei_scenario_model": {
    "model_type": "balanced",
    "parameters": {
      "primary_metric": "cei_score",
      "secondary_metrics": ["rtt", "packet_loss", "jitter"],
      "weights": {"cei_score": 0.4, "rtt": 0.2, "packet_loss": 0.2, "jitter": 0.2}
    }
  },
  "cei_granularity": {
    "sampling_interval_seconds": 900,
    "aggregation_window_seconds": 300,
    "metrics": ["bandwidth", "packet_loss", "rtt", "jitter", "cei_score"]
  },
  "cei_trigger_window": {
    "detection_window_minutes": 15,
    "confirmation_count": 3,
    "cooldown_minutes": 30
  }
}
```

## 参数查找表

### CEI 预警阈值 → 按 (user_type, priority) 查表

| user_type | priority=高 | priority=中 | priority=低 |
|-----------|-----------|-----------|-----------|
| 直播用户   | 85        | 75        | 65        |
| 游戏用户   | 80        | 70        | 60        |
| 办公用户   | 75        | 65        | 55        |
| 教育用户   | 75        | 65        | 55        |
| 普通家庭用户 | 70       | 60        | 50        |
| SOHO用户   | 75        | 65        | 55        |

### 场景模型 → 按 scenario 查表

| scenario | model_type | primary_metric | weights 覆盖 |
|----------|-----------|----------------|-------------|
| 直播推流 | uplink_priority | uplink_loss | {"uplink_loss": 0.35, "uplink_jitter": 0.3, "rtt": 0.2, "cei_score": 0.15} |
| 在线游戏 | low_latency_priority | rtt | {"rtt": 0.4, "packet_loss": 0.3, "jitter": 0.2, "cei_score": 0.1} |
| 视频会议 | bidirectional_balanced | mos_score | {"mos_score": 0.35, "jitter": 0.25, "packet_loss": 0.2, "rtt": 0.2} |
| 在线教育 | availability_first | availability | {"availability": 0.4, "rtt": 0.2, "packet_loss": 0.2, "jitter": 0.2} |
| 高清视频 | downlink_priority | downlink_bandwidth | {"downlink_bandwidth": 0.4, "rtt": 0.2, "packet_loss": 0.2, "jitter": 0.2} |
| 智能家居 | iot_balanced | availability | {"availability": 0.4, "packet_loss": 0.3, "rtt": 0.2, "jitter": 0.1} |
| 综合场景 | balanced | cei_score | {"cei_score": 0.4, "rtt": 0.2, "packet_loss": 0.2, "jitter": 0.2} |

### 感知粒度 → 按 sensitivity.latency 查表

| sensitivity | sampling_interval | aggregation_window | detection_window | confirmation_count | cooldown_minutes |
|-------------|------------------|--------------------|------------------|--------------------|-----------------|
| 高敏感 | 300 | 60 | 5 | 2 | 15 |
| 中敏感 | 900 | 300 | 15 | 3 | 30 |
| 低敏感 | 1800 | 900 | 30 | 5 | 60 |

### 采集指标 → 按 scenario 查表

| scenario | metrics |
|----------|---------|
| 直播推流 | ["uplink_bandwidth", "uplink_packet_loss", "uplink_jitter", "rtt", "cei_score"] |
| 在线游戏 | ["rtt", "packet_loss", "jitter", "download_speed", "cei_score"] |
| 视频会议 | ["mos_score", "rtt", "jitter", "packet_loss", "bandwidth", "cei_score"] |
| 在线教育 | ["download_speed", "rtt", "packet_loss", "availability", "cei_score"] |
| 高清视频 | ["downlink_bandwidth", "rtt", "packet_loss", "buffer_ratio", "cei_score"] |
| 智能家居 | ["availability", "packet_loss", "rtt", "device_count", "cei_score"] |
| 综合场景 | ["bandwidth", "packet_loss", "rtt", "jitter", "cei_score"] |

## 填值规则

1. 读取 GoalSpec.user_type + GoalSpec.guarantee_target.priority → 查阈值表 → 填入 cei_warning_threshold.value
2. 读取 GoalSpec.scenario → 查场景模型表 → 覆盖 cei_scenario_model 全部字段
3. 读取 GoalSpec.guarantee_target.sensitivity.latency → 查粒度表 → 覆盖 cei_granularity 和 cei_trigger_window
4. 读取 GoalSpec.scenario → 查采集指标表 → 覆盖 cei_granularity.metrics
5. 若 GoalSpec.core_metrics.cei_threshold 有值，用该值覆盖 cei_warning_threshold.value
6. 若 GoalSpec.user_history 中有 perception_trigger_time，用该值推算 detection_window
7. 输出修改后的完整 JSON（保留未命中字段的默认值）
