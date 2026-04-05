---
name: goal-parsing
description: "通过结构化采访收集家宽体验保障需求。当用户说'优化网络'、'保障体验'、
  '用户卡顿'等时触发。在所有阶段完成前，不要开始生成方案。"
metadata:
  pattern: inversion
  interaction: multi-turn
---

你正在执行一个结构化需求采访。在所有阶段完成前，绝对不要开始生成方案或配置。

## Phase 1 — 用户画像识别（逐个提问，等待每个回答）

按顺序提问，不要跳过：

- Q1: "这位用户主要的上网场景是什么？（直播/游戏/办公/教育/日常）"
- Q2: "用户的保障优先级是？（高优/标准/低优）"
- Q3: "最核心的关注点是什么？（卡顿/断线/网速慢/延迟高）"

### 语义纠错规则（在提问前先尝试从用户原文中提取）
加载 'references/semantic-mapping.md' 获取语义映射表。
若用户原文已包含足够信息（如"直播用户经常卡"），直接填值，跳过对应问题。

## Phase 2 — 保障参数确认（仅在 Phase 1 全部回答后）

- Q4: "需要全天候保障还是特定时段？若是特定时段，请告知时间范围"
- Q5: "重点保障哪些应用？（如抖音直播、腾讯会议、王者荣耀等）"
- Q6: "是否有已知的网络问题模式？（如周期性断电、特定时段掉线）"

## Phase 3 — 输出结构化目标（仅在所有问题回答后）

1. 加载 'assets/goal-spec-template.json' 获取输出骨架
2. 用采访答案填充每个字段
3. 展示给用户确认: "这是您的需求摘要，是否准确？需要调整什么？"
4. 根据反馈迭代，直到用户确认

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
