# CEI 感知方案参数查找表

## CEI 预警阈值 → 按 (user_type, priority) 查表

| user_type | priority=高 | priority=中 | priority=低 |
|-----------|-----------|-----------|-----------|
| 直播用户   | 85        | 75        | 65        |
| 游戏用户   | 80        | 70        | 60        |
| 办公用户   | 75        | 65        | 55        |
| 教育用户   | 75        | 65        | 55        |
| 普通家庭用户 | 70       | 60        | 50        |
| SOHO用户   | 75        | 65        | 55        |

## 场景模型 → 按 scenario 查表

| scenario | model_type | primary_metric | weights 覆盖 |
|----------|-----------|----------------|-------------|
| 直播推流 | uplink_priority | uplink_loss | {"uplink_loss": 0.35, "uplink_jitter": 0.3, "rtt": 0.2, "cei_score": 0.15} |
| 在线游戏 | low_latency_priority | rtt | {"rtt": 0.4, "packet_loss": 0.3, "jitter": 0.2, "cei_score": 0.1} |
| 视频会议 | bidirectional_balanced | mos_score | {"mos_score": 0.35, "jitter": 0.25, "packet_loss": 0.2, "rtt": 0.2} |
| 在线教育 | availability_first | availability | {"availability": 0.4, "rtt": 0.2, "packet_loss": 0.2, "jitter": 0.2} |
| 高清视频 | downlink_priority | downlink_bandwidth | {"downlink_bandwidth": 0.4, "rtt": 0.2, "packet_loss": 0.2, "jitter": 0.2} |
| 智能家居 | iot_balanced | availability | {"availability": 0.4, "packet_loss": 0.3, "rtt": 0.2, "jitter": 0.1} |
| 综合场景 | balanced | cei_score | {"cei_score": 0.4, "rtt": 0.2, "packet_loss": 0.2, "jitter": 0.2} |

## 感知粒度 → 按 sensitivity.latency 查表

| sensitivity | sampling_interval | aggregation_window | detection_window | confirmation_count | cooldown_minutes |
|-------------|------------------|--------------------|------------------|--------------------|-----------------|
| 高敏感 | 300 | 60 | 5 | 2 | 15 |
| 中敏感 | 900 | 300 | 15 | 3 | 30 |
| 低敏感 | 1800 | 900 | 30 | 5 | 60 |

## 采集指标 → 按 scenario 查表

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
