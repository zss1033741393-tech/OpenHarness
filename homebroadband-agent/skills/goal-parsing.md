---
name: goal-parsing
description: "家宽体验保障目标解析规则和模板，包含语义映射表和追问话术"
---
# 目标解析规则

## 解析模板字段
必填: user_type, scenario, guarantee_period, guarantee_target, core_metrics
可选: user_history

## 语义映射表
| 用户表述 | 映射字段 | 映射值 |
|---------|---------|--------|
| "直播/主播/推流" | user_type=直播用户, scenario=直播推流 | focus=上行 |
| "游戏/吃鸡/王者/LOL" | user_type=游戏用户, scenario=在线游戏 | latency=高敏感 |
| "会议/Teams/Zoom/腾讯会议" | user_type=办公用户, scenario=视频会议 | jitter=高敏感 |
| "网课/上课/钉钉课堂" | user_type=教育用户, scenario=在线教育 | availability>99.5% |
| "看剧/视频/B站/爱奇艺" | scenario=高清视频 | focus=下行 |
| "智能家居/摄像头/IoT" | scenario=智能家居 | availability>98% |
| "卡/卡顿/掉帧" | sensitivity.latency=高敏感 | response_sla=<30min |
| "断线/掉线/断网" | sensitivity.packet_loss=高敏感 | response_sla=<15min |
| "延迟高/ping高" | sensitivity.latency=高敏感 | focus=双向 |
| "上传慢" | focus=上行 | sensitivity.latency=中敏感 |
| "下载慢/缓冲" | focus=下行 | sensitivity.latency=中敏感 |

## 追问话术模板
- 缺少用户类型: "请问这位用户主要的上网场景是什么？（直播/游戏/办公/教育/日常浏览）"
- 缺少保障时段: "需要全天候保障还是特定时段保障？如果是特定时段，请告知时间范围"
- 缺少优先级: "该用户的保障优先级是？（高优先级适用于VIP用户/中/低）"
- 缺少核心指标: "对CEI预警阈值有特殊要求吗？（默认根据用户类型自动设置）"
- 缺少应用列表: "需要重点保障哪些应用？（如：抖音直播、王者荣耀、Zoom等）"

## 默认值补全规则
当用户未指定时，根据 user_type 自动补全以下字段：

### 直播用户默认值
- priority: 高
- focus: 上行
- sensitivity: {latency: 高敏感, jitter: 高敏感, packet_loss: 高敏感}
- cei_threshold: 85
- response_sla: "<15min"
- availability_target: 99.5
- applications: ["抖音直播", "快手直播", "B站直播", "OBS推流"]

### 游戏用户默认值
- priority: 高
- focus: 双向
- sensitivity: {latency: 高敏感, jitter: 中敏感, packet_loss: 高敏感}
- cei_threshold: 80
- response_sla: "<15min"
- availability_target: 99.5
- applications: ["王者荣耀", "和平精英", "LOL", "Steam"]

### 办公用户默认值
- priority: 中
- focus: 双向
- sensitivity: {latency: 中敏感, jitter: 高敏感, packet_loss: 中敏感}
- cei_threshold: 75
- response_sla: "<30min"
- availability_target: 99.0
- applications: ["Zoom", "Teams", "腾讯会议", "钉钉"]

### 教育用户默认值
- priority: 中
- focus: 下行
- sensitivity: {latency: 中敏感, jitter: 中敏感, packet_loss: 中敏感}
- cei_threshold: 75
- response_sla: "<30min"
- availability_target: 99.5
- applications: ["钉钉课堂", "腾讯课堂", "学而思", "作业帮"]

### 普通家庭用户默认值
- priority: 低
- focus: 下行
- sensitivity: {latency: 低敏感, jitter: 低敏感, packet_loss: 低敏感}
- cei_threshold: 70
- response_sla: "<60min"
- availability_target: 98.0
- applications: []

### SOHO用户默认值
- priority: 中
- focus: 双向
- sensitivity: {latency: 中敏感, jitter: 中敏感, packet_loss: 中敏感}
- cei_threshold: 75
- response_sla: "<30min"
- availability_target: 99.0
- applications: ["企业VPN", "云桌面", "企业邮箱"]
