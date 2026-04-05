# 语义映射表

将用户自然语言表述映射为结构化 GoalSpec 字段。

## 用户表述 → 结构化字段

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
