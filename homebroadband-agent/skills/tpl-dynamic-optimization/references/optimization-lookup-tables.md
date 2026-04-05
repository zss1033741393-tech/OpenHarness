# 动态优化方案参数查找表

## 实时优化 → 按 scenario 查表

| scenario | WIFI频段切换 | 信道优化 | 带宽分配 | 漫游优化 | check_interval |
|----------|------------|---------|---------|---------|---------------|
| 直播推流 | true | true | true | false | 120 |
| 在线游戏 | true | true | true | false | 60 |
| 视频会议 | true | true | true | true | 120 |
| 在线教育 | true | true | false | true | 300 |
| 高清视频 | true | true | false | false | 300 |
| 智能家居 | true | true | false | false | 600 |
| 综合场景 | true | true | false | false | 300 |

## 预测优化 → 按 (user_type, priority) 查表

| user_type + priority=高 | predictive_enabled | prediction_window | model_type |
|------------------------|-------------------|-------------------|------------|
| 直播用户 | true | 60 | pattern_based |
| 游戏用户 | true | 30 | time_series |
| 办公用户 | true | 30 | calendar_based |
| 其他 | false | 30 | time_series |

## 节能策略 → 按 user_history 查表

| 条件 | power_saving_enabled | trigger_time | resume_time |
|------|---------------------|-------------|-------------|
| 有power_saving_trigger_time | true | 使用历史值 | 使用历史值+5h |
| 普通家庭用户+低优先级 | true | 01:00 | 06:00 |
| 其他 | false | - | - |

## APPflow 策略 → 按 (scenario, applications) 查表

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
