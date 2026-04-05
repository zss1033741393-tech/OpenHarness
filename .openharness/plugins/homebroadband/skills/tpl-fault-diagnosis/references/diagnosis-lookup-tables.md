# 故障诊断方案参数查找表

## 诊断方法启用 → 按 scenario 查表

| scenario | 光衰检测 | WIFI信道 | PPPoE | DNS | 路由追踪 |
|----------|---------|---------|-------|-----|---------|
| 直播推流 | true | true | true | true | true |
| 在线游戏 | true | true | true | true | true |
| 视频会议 | true | true | true | true | false |
| 在线教育 | true | true | true | true | false |
| 高清视频 | true | true | true | false | false |
| 智能家居 | true | true | false | true | false |
| 综合场景 | true | true | true | true | false |

## 升级时间 → 按 priority 查表

| priority | auto_escalate_after_minutes | max_auto_retries |
|----------|---------------------------|-----------------|
| 高 | 15 | 2 |
| 中 | 30 | 3 |
| 低 | 60 | 5 |

## 主动巡检 → 按 (user_type, priority) 查表

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
