# OpenHarness - 家宽体验感知优化 Agent 智能体

## Git 提交规范

- **必须使用 `git push` 命令进行代码提交和推送**，禁止使用 MCP 工具进行代码提交
- 提交前先 `git add` 相关文件，再 `git commit`，最后 `git push -u origin <branch-name>`
- commit message 使用中文或英文均可，需简明扼要描述变更内容
- 推送失败时最多重试 4 次，使用指数退避（2s, 4s, 8s, 16s）

## 项目结构

本项目基于 OpenHarness 框架构建家宽体验感知优化 Agent 智能体原型，核心代码位于 `homebroadband-agent/` 目录下：

```
homebroadband-agent/
├── agents/          # Agent 定义（.md，YAML frontmatter）
├── skills/          # 领域知识 Skill（.md）
├── tools/           # 自定义 Tool（Python）
├── hooks/           # 生命周期 Hook
├── schemas/         # JSON Schema 定义
├── scripts/         # 辅助脚本
├── configs/         # 配置输出目录（运行时生成）
├── memory/          # 持久化记忆
├── plugins/         # 可选 Plugin 扩展
└── tests/           # 测试
```

## 开发分支

- 主开发分支：`dev`
- 推送命令：`git push -u origin dev`

## 技术栈

- Python 3.10+
- OpenHarness v0.1.0
- Pydantic v2 (数据模型)
- pytest + pytest-asyncio (测试)
