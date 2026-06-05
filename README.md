# AgentForge — 一键 AI 智能体安装器

一条命令装遍 6 大主流 AI 编程智能体。零依赖、跨平台、自动检测环境、国内镜像加速。

[在线介绍页](https://zhenyuonline.cn/agent-forge/) | [GitHub Pages](https://zhenyuren.github.io/agent-forge/)

## 安装

### macOS / Linux（推荐）

```bash
curl -fsSL https://zhenyuonline.cn/agent-installer.py | python3
```

### Windows / 通用（无需 curl，纯 Python）

任何有 Python 的系统都可用，cmd / PowerShell / macOS / Linux 全兼容：

```bash
python -c "import urllib.request as u; exec(u.urlopen('https://zhenyuonline.cn/agent-installer.py').read())"
```

### 一键静默（跳过菜单，直接安装指定组件）

```bash
AGENTS_TO_INSTALL=hermes,aider curl -fsSL https://zhenyuonline.cn/agent-installer.py | python3
```

Windows cmd:
```cmd
set AGENTS_TO_INSTALL=hermes,aider && python -c "import urllib.request as u; exec(u.urlopen('https://zhenyuonline.cn/agent-installer.py').read())"
```

可选值: `hermes`, `openclaw`, `aider`, `codex`, `claude-code`, `cline`, `all`

## v2 新特性（2026-06-05）

-  PyPI 国内镜像自动检测 + 失败重试切换
-  实时安装进度显示（不让学生以为卡死）
-  API Key 免费获取引导（一键打开注册页）
-  自动添加到 shell profile（hermes 命令随处可用）
-  菜单内置卸载功能
-  Windows 兼容提示 + Python 通用安装命令

## 支持的智能体

| 智能体 | 类型 | 短名称 | 说明 |
|--------|------|--------|------|
| Hermes Agent | Python | `hermes` | Nous Research 出品，20+ 工具 |
| Open CLAW | Python | `openclaw` | 开源 AI 编程助手 |
| Aider | Python | `aider` | 终端 AI 结对编程 |
| Codex CLI | Node.js | `codex` | OpenAI 官方出品 |
| Claude Code | Node.js | `claude-code` | Anthropic 出品 |
| Cline | Node.js | `cline` | 自主编码智能体 |

## 验证安装

安装完成后运行：

```bash
# Hermes Agent
cd ~/agent-env/agents/hermes-agent && source venv/bin/activate && hermes --version

# Aider
cd ~/agent-env/agents/aider && source venv/bin/activate && aider --version

# Codex CLI（全局安装）
codex --version
```

## License

MIT
