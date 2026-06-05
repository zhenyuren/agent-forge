# AgentForge — 一键 AI 智能体安装器 🚀

一条命令装遍 6 大主流 AI 编程智能体。

[在线介绍页](https://zhenyuonline.cn/agent-forge/) | [直接安装](https://zhenyuonline.cn/agent-installer.py)

## 安装

```bash
curl -fsSL https://zhenyuonline.cn/agent-installer.py | python3
```

## 一键静默（无需交互）

```bash
AGENTS_TO_INSTALL=hermes,aider curl -fsSL https://zhenyuonline.cn/agent-installer.py | python3
```

## v2 新特性（2026-06-05）

- 🔄 PyPI 国内镜像自动检测 + 失败重试切换
- 📊 实时安装进度显示
- 🔑 API Key 免费获取引导（一键打开注册页）
- 🔗 自动添加到 shell profile
- 🧹 菜单内置卸载
- 🪟 Windows 兼容提示

## 支持的智能体

| 智能体 | 类型 | 短名称 |
|--------|------|--------|
| Hermes Agent | Python | hermes |
| Open CLAW | Python | openclaw |
| Aider | Python | aider |
| Codex CLI | Node.js | codex |
| Claude Code | Node.js | claude-code |
| Cline | Node.js | cline |

## License

MIT
