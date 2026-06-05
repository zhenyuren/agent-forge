#!/usr/bin/env python3
"""
AgentForge — 一键智能体安装器
一键安装 Hermes、Open CLAW、Aider、Codex CLI、Claude Code、Cline 等 AI 编程智能体
跨平台（macOS / Windows / Linux），零依赖（仅 Python 标准库）
"""

import os
import sys
import json
import shutil
import subprocess
import platform
import textwrap
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Callable

# ── 颜色 & 样式 ──────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"

# 前景色
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# 背景色
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

# 亮色
LIGHT_RED = "\033[91m"
LIGHT_GREEN = "\033[92m"
LIGHT_YELLOW = "\033[93m"
LIGHT_BLUE = "\033[94m"
LIGHT_MAGENTA = "\033[95m"
LIGHT_CYAN = "\033[96m"

CHECK = f"{GREEN}✓{RESET}"
CROSS = f"{RED}✗{RESET}"
ARROW = f"{CYAN}→{RESET}"
INFO = f"{BLUE}ℹ{RESET}"
WARN = f"{YELLOW}⚠{RESET}"
STAR = f"{LIGHT_YELLOW}★{RESET}"

def supports_color():
    return os.environ.get("TERM") and "color" in os.environ.get("TERM", "") or platform.system() != "Windows"

def color_text(text, color_code):
    if supports_color():
        return f"{color_code}{text}{RESET}"
    return text

def cprint(text, color=None, bold=False, end="\n"):
    """Colored print."""
    if color and supports_color():
        prefix = BOLD if bold else ""
        print(f"{prefix}{color}{text}{RESET}", end=end)
    elif bold and supports_color():
        print(f"{BOLD}{text}{RESET}", end=end)
    else:
        print(text, end=end)

# ── Banner ───────────────────────────────────────────────────
BANNER = f"""
{BLUE}{BOLD}╔══════════════════════════════════════════════════════╗
║           🤖  AgentForge  一键智能体安装器        ║
║     Hermes · Open CLAW · Aider · Codex · Claude Code · Cline  ║
╚══════════════════════════════════════════════════════╝{RESET}
"""

# ── 平台检测 ─────────────────────────────────────────────────
class Platform:
    """检测当前系统环境。"""
    
    @staticmethod
    def os_name() -> str:
        """macOS / Windows / Linux"""
        sys_name = platform.system()
        if sys_name == "Darwin":
            return "macOS"
        return sys_name
    
    @staticmethod
    def is_windows() -> bool:
        return platform.system() == "Windows"
    
    @staticmethod
    def is_macos() -> bool:
        return platform.system() == "Darwin"
    
    @staticmethod
    def is_linux() -> bool:
        return platform.system() == "Linux"
    
    @staticmethod
    def has_command(cmd: str) -> bool:
        return shutil.which(cmd) is not None
    
    @staticmethod
    def python_version() -> tuple:
        return sys.version_info[:3]
    
    @staticmethod
    def python_version_str() -> str:
        v = Platform.python_version()
        return f"{v[0]}.{v[1]}.{v[2]}"
    
    @staticmethod
    def python_path() -> str:
        return sys.executable
    
    @staticmethod
    def python_pip() -> bool:
        """Check if pip is available."""
        return Platform.has_command("pip3") or Platform.has_command("pip") or (not Platform.is_windows() and Platform.has_command("pip3"))
    
    @staticmethod
    def get_pip_cmd() -> str:
        if Platform.is_windows():
            return "pip" if Platform.has_command("pip") else "python -m pip"
        return "pip3" if Platform.has_command("pip3") else "pip" if Platform.has_command("pip") else f"{sys.executable} -m pip"
    
    @staticmethod
    def node_version() -> Optional[str]:
        try:
            result = subprocess.run(
                ["node", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    @staticmethod
    def npm_global_prefix() -> str:
        """Get npm global install prefix."""
        try:
            result = subprocess.run(
                ["npm", "root", "-g"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return ""
    
    @staticmethod
    def is_venv() -> bool:
        return hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    
    @staticmethod
    def shell_config_file() -> str:
        """Recommend shell config file for PATH/alias."""
        if Platform.is_windows():
            return "$PROFILE"  # PowerShell profile
        shell = os.environ.get("SHELL", "")
        home = str(Path.home())
        if "zsh" in shell:
            return os.path.join(home, ".zshrc")
        elif "bash" in shell:
            return os.path.join(home, ".bashrc")
        return os.path.join(home, ".profile")

    @staticmethod
    def check_python_version(min_major=3, min_minor=10):
        v = Platform.python_version()
        if v[0] < min_major or (v[0] == min_major and v[1] < min_minor):
            return False, f"需要 Python {min_major}.{min_minor}+，当前是 {v[0]}.{v[1]}.{v[2]}"
        return True, f"Python {v[0]}.{v[1]}.{v[2]} ✓"


# ── 工具函数 ─────────────────────────────────────────────────
def run_cmd(cmd: list, desc: str = "", timeout: int = 120) -> tuple[bool, str]:
    """运行命令，返回 (成功?, 输出文本)"""
    if desc:
        print(f"  {ARROW} {desc}...", end=" ", flush=True)
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout + result.stderr
        if result.returncode == 0:
            if desc:
                print(f"{CHECK}")
            return True, output
        else:
            if desc:
                print(f"{CROSS}")
            return False, output
    except subprocess.TimeoutExpired:
        if desc:
            print(f"{CROSS} (超时)")
        return False, "Timeout"
    except FileNotFoundError as e:
        if desc:
            print(f"{CROSS} (命令未找到: {e})")
        return False, str(e)
    except Exception as e:
        if desc:
            print(f"{CROSS} (错误: {e})")
        return False, str(e)


# ── PyPI 镜像自动检测 ────────────────────────────────────────
# PyPI 镜像自动检测
PYPI_MIRRORS = [
    ("官方 (pypi.org)", ""),
    ("清华 (tuna)", "https://pypi.tuna.tsinghua.edu.cn/simple"),
    ("阿里云", "https://mirrors.aliyun.com/pypi/simple/"),
    ("中科大 (ustc)", "https://pypi.mirrors.ustc.edu.cn/simple/"),
]

def get_best_pypi_mirror() -> str:
    """自动检测国内网络环境，返回最快的 PyPI 镜像 URL。"""
    try:
        req = urllib.request.Request("http://www.baidu.com", method="HEAD")
        urllib.request.urlopen(req, timeout=3)
        for name, url in PYPI_MIRRORS:
            if url and "tuna" in url:
                return url
    except Exception:
        pass
    return ""


def pip_install_live(pip_python: str, package: str, desc: str = "安装") -> bool:
    """实时显示 pip install 输出，带超时和自动重试。
    解决学生看到屏幕"卡住"就 Ctrl+C 的问题。
    """
    mirror = get_best_pypi_mirror()

    def _do_install(retry_count: int = 0) -> bool:
        label = f"{desc}（{package}）"
        if retry_count > 0:
            label += f" [重试 {retry_count}]"

        print(f"  {ARROW} {label}...", flush=True)

        cmd = [pip_python, "-m", "pip", "install"]
        if mirror:
            cmd.extend(["-i", mirror,
                        "--trusted-host", "mirrors.aliyun.com",
                        "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
                        "--trusted-host", "pypi.mirrors.ustc.edu.cn"])
        cmd.append(package)

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            last_line = ""
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    last_line = line
                    if any(kw in line.lower() for kw in
                           ["installing", "download", "success", "error",
                            "requirement already", "collecting", "preparing"]):
                        print(f"    {DIM}{line[:80]}{RESET}", flush=True)
                    elif "progress" in line.lower():
                        print(f"    {DIM}{line[:60]}{RESET}", end="\r", flush=True)

            process.wait(timeout=300)
            if process.returncode == 0:
                print(f"  {CHECK} {GREEN}{package} 安装成功{RESET}", flush=True)
                return True
            else:
                print(f"  {CROSS} {RED}安装失败（exit code {process.returncode}）{RESET}", flush=True)
                if last_line:
                    print(f"    {DIM}最后输出: {last_line[:120]}{RESET}", flush=True)
                return False

        except subprocess.TimeoutExpired:
            print(f"  {CROSS} {RED}安装超时（300秒）{RESET}", flush=True)
            process.kill()
            return False
        except Exception as e:
            print(f"  {CROSS} {RED}安装异常: {e}{RESET}", flush=True)
            return False

    for attempt in range(3):
        if attempt > 0 and mirror:
            mirrors = [m[1] for m in PYPI_MIRRORS if m[1] and m[1] != mirror]
            mirror = mirrors[0] if mirrors else ""
            print(f"  {INFO} {YELLOW}切换镜像源重试...{RESET}", flush=True)
        if _do_install(retry_count=attempt):
            return True
    return False


def add_to_shell_profile(cmds: list[str], marker: str) -> bool:
    """将命令追加到 shell profile（.bashrc / .zshrc）。
    带 marker 标记，重复运行不会重复添加。
    """
    profile = Platform.shell_config_file()
    if not profile or profile == "$PROFILE":
        return False

    try:
        with open(profile, "r", encoding="utf-8") as f:
            existing = f.read()
        if marker in existing:
            return True

        with open(profile, "a", encoding="utf-8") as f:
            f.write(f"\n# {marker}\n")
            for line in cmds:
                f.write(f"{line}\n")

        print_success(f"已添加到 {profile}")
        print_info(f"运行 source {profile} 或重启终端生效")
        return True
    except Exception as e:
        print_warn(f"无法写入 {profile}: {e}")
        return False


def uninstall_venv(agent_dir: str, agent_name: str) -> bool:
    """卸载指定智能体（删除整个目录）。"""
    if not os.path.isdir(agent_dir):
        print_warn(f"未找到 {agent_name} 安装目录: {agent_dir}")
        return False

    try:
        shutil.rmtree(agent_dir)
        print_success(f"{agent_name} 已完全卸载")
        return True
    except Exception as e:
        print_error(f"卸载 {agent_name} 失败: {e}")
        return False


def open_url(url: str):
    """尝试在浏览器中打开 URL。"""
    import webbrowser
    try:
        webbrowser.open(url)
        print_info(f"已在浏览器中打开:\n  {LIGHT_CYAN}{url}{RESET}")
    except Exception:
        print_info(f"请手动访问:\n  {LIGHT_CYAN}{url}{RESET}")

def confirm(prompt: str, default: bool = True) -> bool:
    """获取用户 Yes/No 确认。"""
    suffix = " [Y/n] " if default else " [y/N] "
    while True:
        try:
            resp = input(f"  {ARROW} {prompt}{suffix}").strip().lower()
            if not resp:
                return default
            if resp in ("y", "yes"):
                return True
            if resp in ("n", "no"):
                return False
        except (EOFError, KeyboardInterrupt):
            print()
            return False


def select_option(prompt: str, options: list[str], default: int = 0) -> int:
    """让用户从选项列表中选择，返回索引。"""
    print(f"\n  {ARROW} {prompt}")
    for i, opt in enumerate(options):
        marker = f"{LIGHT_CYAN}▶{RESET}" if i == default else " "
        print(f"    {marker} {i+1}. {opt}")
    print(f"    (输入 1-{len(options)}，回车默认 {default+1})", end=" ", flush=True)
    try:
        resp = input().strip()
        if resp:
            idx = int(resp) - 1
            if 0 <= idx < len(options):
                return idx
    except (ValueError, EOFError, KeyboardInterrupt):
        pass
    return default


def input_text(prompt: str, default: str = "", secret: bool = False) -> str:
    """获取用户文本输入。"""
    display_default = f" [{default}]" if default else ""
    try:
        if secret:
            import getpass
            val = getpass.getpass(f"  {ARROW} {prompt}{display_default}: ")
            return val.strip() or default
        else:
            resp = input(f"  {ARROW} {prompt}{display_default}: ").strip()
            return resp or default
    except (EOFError, KeyboardInterrupt):
        print()
        return default or ""


def print_step(step_num: int, total: int, title: str):
    """打印步骤标题。"""
    print(f"\n{BOLD}{BLUE}  ── 步骤 {step_num}/{total}: {title} ──{RESET}\n")


def print_success(text: str):
    """打印成功消息。"""
    print(f"  {CHECK} {GREEN}{text}{RESET}")


def print_info(text: str):
    """打印信息消息。"""
    print(f"  {INFO} {text}")


def print_warn(text: str):
    """打印警告消息。"""
    print(f"  {WARN} {YELLOW}{text}{RESET}")


def print_error(text: str):
    """打印错误消息。"""
    print(f"  {CROSS} {RED}{text}{RESET}")


def print_header(text: str):
    """打印区域标题。"""
    width = 60
    line = "─" * (width - len(text) - 2)
    print(f"\n{BOLD}{BLUE}  {text} {line}{RESET}\n")


def print_box(text: str, color=LIGHT_CYAN, width=56):
    """打印带边框的文本。"""
    lines = text.strip().split("\n")
    print(f"  {color}╔{'═' * width}╗{RESET}")
    for line in lines:
        # Wrap if too long
        while len(line) > width:
            print(f"  {color}║ {RESET}{line[:width]}{color} ║{RESET}")
            line = line[width:]
        print(f"  {color}║ {RESET}{line:<{width}}{color} ║{RESET}")
    print(f"  {color}╚{'═' * width}╝{RESET}")


# ── 依赖安装引导 ────────────────────────────────────────────
class DependencyManager:
    """检查并引导安装缺失的系统依赖。"""
    
    @staticmethod
    def check_python() -> bool:
        ok, msg = Platform.check_python_version()
        if ok:
            print_info(msg)
            return True
        print_warn(msg)
        print_info("请安装 Python 3.10+：https://python.org/downloads/")
        return False
    
    @staticmethod
    def check_pip() -> bool:
        pip_cmd = Platform.get_pip_cmd()
        # Try running pip --version
        success, _ = run_cmd(pip_cmd.split() + ["--version"], desc="检查 pip")
        if success:
            print_info(f"pip 已就绪")
            return True
        print_warn("pip 未安装或不可用")
        suggest = "python -m ensurepip --upgrade" if Platform.is_windows() else "python3 -m ensurepip --upgrade"
        print_info(f"尝试运行: {suggest}")
        return False
    
    @staticmethod
    def check_node() -> bool:
        ver = Platform.node_version()
        if ver:
            print_info(f"Node.js {ver}")
            return True
        print_warn("Node.js 未安装")
        print_info("请安装 Node.js 18+：https://nodejs.org/")
        return False
    
    @staticmethod
    def check_git() -> bool:
        if Platform.has_command("git"):
            try:
                result = subprocess.run(
                    ["git", "--version"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    print_info(f"Git {result.stdout.strip()}")
                    return True
            except:
                pass
        print_warn("Git 未安装")
        return False
    
    @staticmethod
    def auto_install_python() -> bool:
        """Attempt to install Python via available package manager."""
        os_name = Platform.os_name()
        if os_name == "macOS":
            if Platform.has_command("brew"):
                print_info("通过 Homebrew 安装 Python...")
                ok, out = run_cmd(
                    ["brew", "install", "python@3.12"],
                    desc="安装 Python 3.12"
                )
                return ok
            print_info("建议先安装 Homebrew: https://brew.sh/")
            return False
        elif os_name == "Linux":
            if Platform.has_command("apt-get"):
                print_info("通过 apt 安装 Python...")
                ok, _ = run_cmd(
                    ["sudo", "apt-get", "install", "-y", "python3", "python3-pip", "python3-venv"],
                    desc="安装 Python3 + pip + venv"
                )
                return ok
            return False
        return False
    
    @staticmethod
    def auto_install_node() -> bool:
        """Attempt to install Node.js via nvm or package manager."""
        os_name = Platform.os_name()
        if os_name == "macOS":
            if Platform.has_command("brew"):
                print_info("通过 Homebrew 安装 Node.js...")
                ok, out = run_cmd(
                    ["brew", "install", "node@20"],
                    desc="安装 Node.js 20"
                )
                return ok
            return False
        elif os_name == "Linux":
            if Platform.has_command("apt-get"):
                print_info("通过 apt 安装 Node.js...")
                ok, _ = run_cmd(
                    ["sudo", "apt-get", "install", "-y", "nodejs", "npm"],
                    desc="安装 Node.js + npm"
                )
                return ok
        return False


# ── Agent 基类 ──────────────────────────────────────────────
class AgentInstaller:
    """智能体安装器基类。"""
    
    name = ""
    description = ""
    category = ""  # "python" or "node"
    install_guide_url = ""
    requires = []  # List of required commands
    
    def __init__(self, work_dir: str = str(Path.home() / "agent-env" / "agents")):
        self.work_dir = work_dir
    
    def check_installed(self) -> bool:
        """检查是否已安装。"""
        raise NotImplementedError
    
    def get_installed_version(self) -> str:
        """获取已安装版本。"""
        return ""
    
    def install(self) -> bool:
        """执行安装。"""
        raise NotImplementedError
    
    def configure(self) -> bool:
        """配置引导（API key 等）。"""
        return True
    
    def verify(self) -> bool:
        """验证安装成功。"""
        raise NotImplementedError

    def uninstall(self) -> bool:
        """卸载智能体（删除安装目录）。"""
        agent_dir = os.path.join(self.work_dir, self.name.lower().replace(" ", "-"))
        if self.category == "node":
            # Node agents are global, prompt separately
            if self.check_installed():
                print_warn(f"{self.name} 是全局 npm 安装，请手动运行:")
                if hasattr(self, 'npm_package'):
                    print_info(f"  npm uninstall -g {self.npm_package}")
            return True
        return uninstall_venv(agent_dir, self.name)


# ── Hermes Agent 安装器 ─────────────────────────────────────
class HermesInstaller(AgentInstaller):
    name = "Hermes Agent"
    description = "Nous Research 出品的通用 AI 智能体，支持 20+ 工具、飞书集成、多模型"
    category = "python"
    install_guide_url = "https://hermes-agent.nousresearch.com/docs"
    
    def check_installed(self) -> bool:
        return Platform.has_command("hermes")
    
    def get_installed_version(self) -> str:
        try:
            result = subprocess.run(
                ["hermes", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                # Extract just the first line (version info)
                first_line = result.stdout.strip().split("\n")[0]
                return first_line
        except:
            pass
        # Fallback: pip show
        success, out = run_cmd(
            [sys.executable, "-m", "pip", "show", "hermes-agent"],
            desc=""
        )
        if success:
            for line in out.split("\n"):
                if line.startswith("Version:"):
                    return f"v{line.split(':', 1)[1].strip()}"
        return ""
    
    def install(self) -> bool:
        sub_dir = "hermes-agent"
        agent_dir = os.path.join(self.work_dir, sub_dir)
        os.makedirs(agent_dir, exist_ok=True)
        
        print_info(f"安装目录: {agent_dir}")
        
        # Step 1: Create venv
        venv_path = os.path.join(agent_dir, "venv")
        if not os.path.exists(venv_path):
            ok, out = run_cmd(
                [sys.executable, "-m", "venv", venv_path],
                desc="创建虚拟环境"
            )
            if not ok:
                print_error("创建虚拟环境失败")
                return False
        else:
            print_info("虚拟环境已存在，跳过创建")
        
        # Determine pip in venv
        if Platform.is_windows():
            pip_cmd = os.path.join(venv_path, "Scripts", "python")
        else:
            pip_cmd = os.path.join(venv_path, "bin", "python")
        
        # Step 2: Upgrade pip
        ok, _ = run_cmd(
            [pip_cmd, "-m", "pip", "install", "--upgrade", "pip"],
            desc="升级 pip"
        )
        
        # Step 3: Install hermes-agent with live output + retry
        ok = pip_install_live(pip_cmd, "hermes-agent", desc="安装 hermes-agent")
        if not ok:
            print_error("安装 hermes-agent 失败")
            return False
        
        # Step 4: Create .hermes config directory
        hermes_config_dir = os.path.join(agent_dir, ".hermes")
        os.makedirs(hermes_config_dir, exist_ok=True)
        
        # Step 5: Auto-add to shell profile for convenience
        if not Platform.is_windows():
            hermes_wrapper = (
                f'hermes() {{ cd {agent_dir} && source {venv_path}/bin/activate && '
                f'hermes "$@"; }}'
            )
            add_to_shell_profile(
                [hermes_wrapper],
                marker=f"AgentForge: {self.name}"
            )

        print_success("Hermes Agent 安装完成！")

        # Print activation instructions
        if Platform.is_windows():
            activate_cmd = f"{venv_path}\\Scripts\\activate"
        else:
            activate_cmd = f"source {venv_path}/bin/activate"

        print_box(
            f"使用 Hermes:\n"
            f"  方式一（推荐）: 直接运行 hermes（已添加到 shell profile）\n"
            f"  方式二:  cd {agent_dir}\n"
            f"           {activate_cmd}\n"
            f"           hermes\n"
            f"\n"
            f"然后运行 hermes setup 配置 API key 和模型"
        )

        return True
    
    def configure(self) -> bool:
        """引导用户配置 API Key 和模型。"""
        print_header("Hermes Agent 配置引导")
        print_info("你需要至少一个 LLM API Key 才能使用 Hermes。")
        print_info("以下提供商有免费额度，学生可零成本使用\n")

        free_providers = [
            "DeepSeek（免费注册送500万tokens，平台 platform.deepseek.com）",
            "硅基流动 SiliconFlow（送20元额度，GPU加速，国内可直接访问）",
        ]
        for i, fp in enumerate(free_providers):
            print(f"  {LIGHT_YELLOW}{STAR} 一键打开 {i+1}: {fp}{RESET}")
        print()

        providers = [
            "DeepSeek（推荐，便宜又好用）",
            "OpenAI (GPT-4o)",
            "Anthropic (Claude)",
            "OpenRouter（聚合多个模型）",
            "火山引擎 Ark（Doubao 豆包模型）",
            "硅基流动 SiliconFlow（国内友好，送额度）",
            "先跳过，之后手动配置"
        ]
        choice = select_option("选择 API 提供商:", providers, default=0)

        if choice == 6:  # 跳过
            print_info("之后可以运行 hermes setup 或手动编辑 ~/.hermes/config.yaml 配置")
            return True

        # ── 免费获取引导 ──
        free_guide = {
            0: ("DeepSeek 注册", "https://platform.deepseek.com/sign_up"),
            1: ("OpenAI 注册", "https://platform.openai.com/signup"),
            5: ("硅基流动注册", "https://cloud.siliconflow.cn/?currency=CNY"),
        }
        if choice in free_guide:
            name, url = free_guide[choice]
            print()
            print_info(f"正在为你打开 {name} 注册页面...")
            open_url(url)
            print_warn("注册后获得 API Key，再回来粘贴到下面 ↓")
            print()

        provider_configs = {
            0: {
                "name": "deepseek",
                "model": "deepseek-v4-flash",
                "base_url": "https://api.deepseek.com/v1",
                "key_prompt": "输入 DeepSeek API Key（以 sk- 开头）",
                "key_env": "DEEPSEEK_API_KEY",
                "key_start": "sk-"
            },
            1: {
                "name": "openai",
                "model": "gpt-4o",
                "base_url": "https://api.openai.com/v1",
                "key_prompt": "输入 OpenAI API Key（以 sk- 开头）",
                "key_env": "OPENAI_API_KEY",
                "key_start": "sk-"
            },
            2: {
                "name": "anthropic",
                "model": "claude-sonnet-4",
                "base_url": "https://api.anthropic.com/v1",
                "key_prompt": "输入 Anthropic API Key（以 sk-ant- 开头）",
                "key_env": "ANTHROPIC_API_KEY",
                "key_start": "sk-ant-"
            },
            3: {
                "name": "openrouter",
                "model": "anthropic/claude-sonnet-4",
                "base_url": "https://openrouter.ai/api/v1",
                "key_prompt": "输入 OpenRouter API Key（以 sk-or- 开头）",
                "key_env": "OPENROUTER_API_KEY",
                "key_start": "sk-or-"
            },
            4: {
                "name": "volcengine",
                "model": "doubao-1.6-flash",
                "base_url": "https://ark.cn-beijing.volcesapi.com/api/v3",
                "key_prompt": "输入火山引擎 Ark API Key",
                "key_env": "ARK_API_KEY",
                "key_start": ""
            },
            5: {
                "name": "siliconflow",
                "model": "deepseek-v4-flash",
                "base_url": "https://api.siliconflow.cn/v1",
                "key_prompt": "输入硅基流动 API Key（从 cloud.siliconflow.cn 获取）",
                "key_env": "SILICONFLOW_API_KEY",
                "key_start": "sk-"
            },
        }

        cfg = provider_configs.get(choice)
        if not cfg:
            return True
        
        # Ask for API key
        api_key = input_text(cfg["key_prompt"], secret=(choice != 4))
        if not api_key:
            print_warn("API Key 为空，跳过配置")
            return True
        
        # Write config
        agent_dir = os.path.join(self.work_dir, "hermes-agent")
        hermes_config_dir = os.path.join(agent_dir, ".hermes")
        os.makedirs(hermes_config_dir, exist_ok=True)
        
        config_yaml = textwrap.dedent(f"""\
            model:
              default: {cfg["model"]}
              provider: custom
              base_url: {cfg["base_url"]}
              api_key: {api_key}
        """)
        
        config_path = os.path.join(hermes_config_dir, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_yaml)
        
        print_success(f"配置文件已写入: {config_path}")
        
        # Also write .env
        env_path = os.path.join(agent_dir, ".env")
        with open(env_path, "a", encoding="utf-8") as f:
            f.write(f'{cfg["key_env"]}={api_key}\n')
        
        print_success(f"环境变量已追加到: {env_path}")
        return True
    
    def verify(self) -> bool:
        """Verify Hermes is accessible."""
        agent_dir = os.path.join(self.work_dir, "hermes-agent")
        venv_path = os.path.join(agent_dir, "venv")
        
        if Platform.is_windows():
            hermes_bin = os.path.join(venv_path, "Scripts", "hermes")
        else:
            hermes_bin = os.path.join(venv_path, "bin", "hermes")
        
        if os.path.exists(hermes_bin):
            ok, out = run_cmd([hermes_bin, "--help"], desc="验证 hermes --help")
            if ok:
                # Extract version
                for line in out.split("\n"):
                    if "hermes" in line.lower():
                        print_success(f"Hermes Agent 已就绪: {line.strip()}")
                        break
                else:
                    print_success("Hermes Agent 已就绪")
                return True
        
        print_warn("未找到 hermes 命令。可以手动检查：激活虚拟环境后运行 hermes --help")
        return False


# ── Open CLAW 安装器 ────────────────────────────────────────
class OpenClawInstaller(AgentInstaller):
    name = "Open CLAW"
    description = "开箱即用的开源 AI 编程助手，支持代码生成、文件编辑、终端执行"
    category = "python"
    
    def check_installed(self) -> bool:
        return Platform.has_command("claw") or Platform.has_command("openclaw")
    
    def get_installed_version(self) -> str:
        for cmd in ["claw", "openclaw"]:
            if Platform.has_command(cmd):
                try:
                    result = subprocess.run(
                        [cmd, "--version"], capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        return result.stdout.strip()
                except:
                    pass
        # Fallback: pip show
        success, out = run_cmd(
            [sys.executable, "-m", "pip", "show", "openclaw"],
            desc=""
        )
        if success:
            for line in out.split("\n"):
                if line.startswith("Version:"):
                    return f"v{line.split(':', 1)[1].strip()}"
        return ""
    
    def install(self) -> bool:
        sub_dir = "openclaw"
        agent_dir = os.path.join(self.work_dir, sub_dir)
        os.makedirs(agent_dir, exist_ok=True)
        
        venv_path = os.path.join(agent_dir, "venv")
        if not os.path.exists(venv_path):
            ok, _ = run_cmd(
                [sys.executable, "-m", "venv", venv_path],
                desc="创建虚拟环境"
            )
            if not ok:
                return False
        else:
            print_info("虚拟环境已存在")
        
        pip_cmd = os.path.join(venv_path, "bin", "python")
        if Platform.is_windows():
            pip_cmd = os.path.join(venv_path, "Scripts", "python")
        
        ok, _ = run_cmd([pip_cmd, "-m", "pip", "install", "--upgrade", "pip"], desc="升级 pip")
        ok = pip_install_live(pip_cmd, "openclaw", desc="安装 openclaw")
        if not ok:
            print_error("安装 Open CLAW 失败")
            return False
        
        print_success("Open CLAW 安装完成！")
        
        if Platform.is_windows():
            activate_cmd = f"{venv_path}\\Scripts\\activate"
        else:
            activate_cmd = f"source {venv_path}/bin/activate"
        
        print_box(
            f"使用 Open CLAW:\n"
            f"  cd {agent_dir}\n"
            f"  {activate_cmd}\n"
            f"  claw (或 openclaw)\n"
            f"\n"
            f"首次使用需配置 API Key（会在启动时引导）"
        )
        return True
    
    def verify(self) -> bool:
        # Check via pip
        ok, out = run_cmd([Platform.get_pip_cmd(), "show", "openclaw"], desc="验证 openclaw 已安装")
        if ok:
            for line in out.split("\n"):
                if line.startswith("Version:"):
                    print_success(f"Open CLAW v{line.split()[1]}")
                    return True
        return False


# ── Aider 安装器 ────────────────────────────────────────────
class AiderInstaller(AgentInstaller):
    name = "Aider"
    description = "终端里的 AI 结对编程助手，支持多模型、git 集成、多文件编辑"
    category = "python"
    install_guide_url = "https://aider.chat/docs/install.html"
    
    def check_installed(self) -> bool:
        return Platform.has_command("aider")
    
    def get_installed_version(self) -> str:
        success, out = run_cmd(
            [sys.executable, "-m", "pip", "show", "aider-chat"],
            desc=""
        )
        if success:
            for line in out.split("\n"):
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()
        return ""
    
    def install(self) -> bool:
        sub_dir = "aider"
        agent_dir = os.path.join(self.work_dir, sub_dir)
        os.makedirs(agent_dir, exist_ok=True)
        
        venv_path = os.path.join(agent_dir, "venv")
        if not os.path.exists(venv_path):
            ok, _ = run_cmd(
                [sys.executable, "-m", "venv", venv_path],
                desc="创建虚拟环境"
            )
            if not ok:
                return False
        else:
            print_info("虚拟环境已存在")
        
        if Platform.is_windows():
            pip_cmd = os.path.join(venv_path, "Scripts", "python")
        else:
            pip_cmd = os.path.join(venv_path, "bin", "python")
        
        ok, _ = run_cmd([pip_cmd, "-m", "pip", "install", "--upgrade", "pip"], desc="升级 pip")
        ok = pip_install_live(pip_cmd, "aider-chat", desc="安装 aider-chat")
        if not ok:
            print_error("安装 Aider 失败")
            return False
        
        print_success("Aider 安装完成！")
        
        if Platform.is_windows():
            activate_cmd = f"{venv_path}\\Scripts\\activate"
        else:
            activate_cmd = f"source {venv_path}/bin/activate"
        
        print_box(
            f"使用 Aider:\n"
            f"  cd {agent_dir}\n"
            f"  {activate_cmd}\n"
            f"  aider --model deepseek/deepseek-v4-flash\n"
            f"\n"
            f"常用:\n"
            f"  aider --model openai/gpt-4o\n"
            f"  aider --model anthropic/claude-sonnet-4"
        )
        return True
    
    def verify(self) -> bool:
        ok, out = run_cmd([Platform.get_pip_cmd(), "show", "aider-chat"], desc="验证 aider 已安装")
        if ok:
            for line in out.split("\n"):
                if line.startswith("Version:"):
                    print_success(f"Aider v{line.split()[1]}")
                    return True
        return False


# ── Codex CLI 安装器 ────────────────────────────────────────
class CodexCliInstaller(AgentInstaller):
    name = "Codex CLI"
    description = "OpenAI 出品的本地运行编程智能体，支持自动编码、调试、重构"
    category = "node"
    npm_package = "@openai/codex"
    install_guide_url = "https://github.com/openai/codex"
    
    def check_installed(self) -> bool:
        return Platform.has_command("codex")
    
    def get_installed_version(self) -> str:
        try:
            result = subprocess.run(
                ["codex", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return ""
    
    def install(self) -> bool:
        print_info("Codex CLI 通过 npm 全局安装")
        
        # Check if already installed
        ver = self.get_installed_version()
        if ver:
            print_info(f"Codex CLI {ver} 已安装")
            if not confirm("重新安装?"):
                return True
        
        ok, out = run_cmd(
            ["npm", "install", "-g", "@openai/codex"],
            desc="npm install -g @openai/codex"
        )
        if not ok:
            print_error("安装 Codex CLI 失败")
            print_info(out[:500])
            return False
        
        print_success("Codex CLI 安装完成！")
        
        print_box(
            "使用 Codex CLI:\n"
            "  codex\n"
            "\n"
            "首次运行会自动提示配置 OpenAI API Key。\n"
            "也可以在项目目录中创建 .env 文件:\n"
            "  OPENAI_API_KEY=sk-...\n"
            "\n"
            "必备: OpenAI API Key (https://platform.openai.com/api-keys)"
        )
        return True
    
    def verify(self) -> bool:
        ok, out = run_cmd(["codex", "--version"], desc="验证 codex --version")
        if ok:
            print_success(f"Codex CLI {out.strip()}")
            return True
        return False


# ── Claude Code 安装器 ──────────────────────────────────────
class ClaudeCodeInstaller(AgentInstaller):
    name = "Claude Code"
    description = "Anthropic 出品，终端里的 Claude——理解代码库、编辑文件、执行命令"
    category = "node"
    npm_package = "@anthropic-ai/claude-code"
    install_guide_url = "https://docs.anthropic.com/en/docs/claude-code/overview"
    
    def check_installed(self) -> bool:
        return Platform.has_command("claude")
    
    def get_installed_version(self) -> str:
        try:
            result = subprocess.run(
                ["claude", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return ""
    
    def install(self) -> bool:
        print_info("Claude Code 通过 npm 全局安装")
        
        ver = self.get_installed_version()
        if ver:
            print_info(f"Claude Code {ver} 已安装")
            if not confirm("重新安装?"):
                return True
        
        ok, out = run_cmd(
            ["npm", "install", "-g", "@anthropic-ai/claude-code"],
            desc="npm install -g @anthropic-ai/claude-code"
        )
        if not ok:
            print_error("安装 Claude Code 失败")
            print_info(out[:500])
            return False
        
        print_success("Claude Code 安装完成！")
        
        print_box(
            "使用 Claude Code:\n"
            "  claude\n"
            "\n"
            "首次运行会自动提示配置 Anthropic API Key。\n"
            "也可以在终端设置环境变量:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "\n"
            "必备: Anthropic API Key (https://console.anthropic.com/)"
        )
        return True
    
    def verify(self) -> bool:
        ok, out = run_cmd(["claude", "--version"], desc="验证 claude --version")
        if ok:
            print_success(f"Claude Code {out.strip()}")
            return True
        return False


# ── Cline 安装器 ────────────────────────────────────────────
class ClineInstaller(AgentInstaller):
    name = "Cline"
    description = "自主编码智能体 CLI——创建/编辑文件、运行命令、使用浏览器"
    category = "node"
    npm_package = "cline"
    install_guide_url = "https://cline.bot"
    
    def check_installed(self) -> bool:
        return Platform.has_command("cline")
    
    def get_installed_version(self) -> str:
        try:
            result = subprocess.run(
                ["cline", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return ""
    
    def install(self) -> bool:
        print_info("Cline 通过 npm 全局安装")
        
        ver = self.get_installed_version()
        if ver:
            print_info(f"Cline {ver} 已安装")
            if not confirm("重新安装?"):
                return True
        
        ok, out = run_cmd(
            ["npm", "install", "-g", "cline"],
            desc="npm install -g cline"
        )
        if not ok:
            print_error("安装 Cline 失败")
            print_info(out[:500])
            return False
        
        print_success("Cline 安装完成！")
        
        print_box(
            "使用 Cline:\n"
            "  cline\n"
            "\n"
            "首次运行会自动引导配置。\n"
            "支持 OpenAI、Anthropic、Google、DeepSeek 等多种模型。\n"
            "也支持 Ollama 本地模型。"
        )
        return True
    
    def verify(self) -> bool:
        ok, out = run_cmd(["cline", "--version"], desc="验证 cline --version")
        if ok:
            print_success(f"Cline {out.strip()}")
            return True
        return False


# ── 智能体注册表 ─────────────────────────────────────────────
AGENTS: list[AgentInstaller] = [
    HermesInstaller(),
    OpenClawInstaller(),
    AiderInstaller(),
    CodexCliInstaller(),
    ClaudeCodeInstaller(),
    ClineInstaller(),
]

# 短名称 → 索引映射（用于 AGENTS_TO_INSTALL 环境变量）
AGENT_NAME_MAP = {
    "hermes": 0, "hermes-agent": 0,
    "openclaw": 1, "open-claw": 1, "open_claw": 1, "claw": 1,
    "aider": 2,
    "codex": 3, "codex-cli": 3,
    "claude": 4, "claude-code": 4,
    "cline": 5,
}


def parse_agent_names(env_val: str) -> list[int]:
    """解析 AGENTS_TO_INSTALL 环境变量值，返回索引列表。"""
    indices = []
    for part in env_val.split(","):
        part = part.strip().lower()
        if not part:
            continue
        if part in ("all", "a", "*"):
            return list(range(len(AGENTS)))
        if part in AGENT_NAME_MAP:
            idx = AGENT_NAME_MAP[part]
            if idx not in indices:
                indices.append(idx)
        else:
            print_warn(f"未知的智能体名称: {part}，跳过")
    return indices


# ── 主程序 ───────────────────────────────────────────────────
def show_welcome():
    """显示欢迎界面。"""
    print(BANNER)
    
    os_name = Platform.os_name()
    py_ok, py_msg = Platform.check_python_version()
    node_ver = Platform.node_version()
    
    print(f"  系统: {LIGHT_CYAN}{os_name}{RESET}  |  {py_msg}")
    if node_ver:
        print(f"  Node: {LIGHT_CYAN}{node_ver}{RESET}")
    else:
        print(f"  Node: {YELLOW}未安装{RESET}（安装 Node Agent 时需要）")
    print()


def check_environment(auto: bool = False):
    """检查环境信息，显示摘要。"""
    print_header("环境检测")
    
    # Python
    py_ok, _ = Platform.check_python_version()
    if not py_ok:
        print_warn(f"Python 版本过低: {Platform.python_version_str()}")
        if auto:
            if Platform.is_macos() and Platform.has_command("brew"):
                DependencyManager.auto_install_python()
            elif Platform.is_linux() and Platform.has_command("apt-get"):
                DependencyManager.auto_install_python()
        else:
            if Platform.is_macos() and Platform.has_command("brew"):
                if confirm("自动安装 Python 3.12?"):
                    DependencyManager.auto_install_python()
            elif Platform.is_linux() and Platform.has_command("apt-get"):
                if confirm("自动安装 Python 3?"):
                    DependencyManager.auto_install_python()
    
    # Node
    if not Platform.has_command("node"):
        print_warn("Node.js 未安装（安装 Codex/Claude Code/Cline 时需要）")
        has_brew = Platform.is_macos() and Platform.has_command("brew")
        has_apt = Platform.is_linux() and Platform.has_command("apt-get")
        if auto and (has_brew or has_apt):
            DependencyManager.auto_install_node()
        elif has_brew or has_apt:
            if confirm("自动安装 Node.js?"):
                DependencyManager.auto_install_node()
    else:
        print_info(f"Node.js {Platform.node_version()}")
    
    # Git
    if Platform.has_command("git"):
        try:
            v = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
            print_info(f"Git {v.stdout.strip()}")
        except:
            print_warn("Git 未安装")
    else:
        print_warn("Git 未安装（部分 Agent 需要）")
    
    print()


def show_agent_menu() -> list[int]:
    """显示智能体选择菜单，返回选择的索引列表。"""
    print_header("选择要安装的智能体")
    print(f"  {DIM}可以多选，用逗号分隔（如 1,3,5），或输入 a 全选{RESET}\n")
    
    for i, agent in enumerate(AGENTS):
        installed = agent.check_installed()
        ver = agent.get_installed_version()
        install_status = ""
        if installed:
            install_status = f" {GREEN}[已安装 {ver}]{RESET}"
        else:
            install_status = f" {DIM}[未安装]{RESET}"
        
        print(f"  {i+1}. {BOLD}{agent.name}{RESET}{install_status}")
        print(f"     {DIM}{agent.description}{RESET}")
        print(f"     {DIM}类型: {agent.category.upper()}{RESET}")
        print()
    
    print(f"  a. {BOLD}全部安装{RESET}")
    print(f"  u. {BOLD}卸载智能体{RESET}")
    print(f"  0. {BOLD}退出{RESET}")
    print()

    while True:
        try:
            resp = input(f"  {ARROW} 请选择（如 1,3,5, a 全选, u 卸载）: ").strip().lower()
            if resp == "0":
                return []
            if resp == "u":
                return ["uninstall"]
            if resp == "a":
                return list(range(len(AGENTS)))
            
            indices = []
            for part in resp.split(","):
                part = part.strip()
                if part:
                    idx = int(part) - 1
                    if 0 <= idx < len(AGENTS):
                        indices.append(idx)
            if indices:
                return indices
            
            print_info("无效选择，请重试")
        except (ValueError, EOFError, KeyboardInterrupt):
            print()
            return []


def show_uninstall_menu():
    """显示卸载菜单，返回选择的索引列表。"""
    print_header("卸载智能体")
    print(f"  {DIM}选择要卸载的智能体{RESET}\n")

    installable = []
    for i, agent in enumerate(AGENTS):
        if agent.check_installed():
            ver = agent.get_installed_version()
            ver_str = f" [{ver}]" if ver else ""
            print(f"  {i+1}. {BOLD}{agent.name}{RESET}{ver_str}")
            installable.append(i)
        else:
            print(f"  {i+1}. {DIM}{agent.name} [未安装]{RESET}")

    if not installable:
        print(f"  {INFO} 没有已安装的智能体可卸载\n")
        return []

    print(f"  0. {BOLD}返回{RESET}\n")
    while True:
        try:
            resp = input(f"  {ARROW} 选择要卸载的序号（如 1,3,5）: ").strip().lower()
            if resp == "0":
                return []
            indices = []
            for part in resp.split(","):
                part = part.strip()
                if part:
                    idx = int(part) - 1
                    if 0 <= idx < len(AGENTS):
                        indices.append(idx)
            if indices:
                return indices
            print_info("无效选择，请重试")
        except (ValueError, EOFError, KeyboardInterrupt):
            print()
            return []


def uninstall_agents(indices: list[int]):
    """卸载选中的智能体。"""
    if not indices:
        return

    selected = [AGENTS[i] for i in indices]
    print_header("确认卸载")
    print(f"  即将卸载: {', '.join(a.name for a in selected)}\n")

    if not confirm("确认卸载?", default=False):
        print_info("已取消")
        return

    for agent in selected:
        print(f"\n  {ARROW} 卸载 {BOLD}{agent.name}{RESET}...", flush=True)
        success = agent.uninstall()
        if success:
            print_success(f"{agent.name} 卸载完成")
        else:
            print_error(f"{agent.name} 卸载失败")

    print(f"\n{GREEN}{BOLD}  🧹 卸载完成！{RESET}\n")


def install_agents(indices: list[int], auto: bool = False):
    """安装选中的智能体。"""
    if not indices:
        return
    
    selected = [AGENTS[i] for i in indices]
    
    print_header("开始安装")
    print(f"  即将安装: {', '.join(a.name for a in selected)}\n")
    
    if not auto and not confirm("确认开始?"):
        print_info("已取消")
        return
    
    for i, agent in enumerate(selected):
        step_num = i + 1
        total = len(selected)
        
        print(f"\n{'='*56}")
        print(f"  {BOLD}{CYAN}[{step_num}/{total}] {agent.name}{RESET}")
        print(f"{'='*56}")
        print()
        
        # Check dependencies
        if agent.category == "node" and not Platform.has_command("node"):
            print_error("Node.js 未安装，跳过")
            continue
        
        if agent.category == "python" and not Platform.has_command("python3") and not Platform.has_command("python"):
            print_error("Python 未安装，跳过")
            continue
        
        # Check if already installed
        if agent.check_installed():
            ver = agent.get_installed_version()
            print_info(f"{agent.name} {ver} 已安装")
            if auto:
                print_info("自动模式：跳过已安装的组件")
                continue
            if not confirm("重新安装?", default=False):
                print_info("跳过")
                continue
        
        # Install
        success = agent.install()
        if not success:
            print_error(f"{agent.name} 安装失败")
            if auto:
                continue
            if confirm("继续安装下一个?"):
                continue
            else:
                break
        
        # Verify
        print()
        agent.verify()
        
        # Configure (only for Hermes)
        if agent.name == "Hermes Agent" and not auto:
            print()
            if confirm("配置 Hermes API Key?"):
                agent.configure()
    
    print(f"\n{GREEN}{BOLD}  🎉 安装完成！{RESET}\n")


def show_summary(indices: list[int]):
    """显示安装总结。"""
    if not indices:
        return
    
    selected = [AGENTS[i] for i in indices]
    
    print_header("安装总结")
    
    for agent in selected:
        installed = agent.check_installed()
        ver = agent.get_installed_version()
        status = f"{CHECK} {GREEN}{ver}{RESET}" if installed else f"{CROSS} {RED}失败{RESET}"
        print(f"  {agent.name:20s}  {status}")
    
    print()
    
    # Show quick-start guide
    print_header("快速启动指南")
    
    agent_dir = str(Path.home() / "agent-env" / "agents")
    
    if Platform.is_windows():
        activate_hermes = f"{agent_dir}\\hermes-agent\\venv\\Scripts\\activate"
        activate_openclaw = f"{agent_dir}\\openclaw\\venv\\Scripts\\activate"
        activate_aider = f"{agent_dir}\\aider\\venv\\Scripts\\activate"
    else:
        activate_hermes = f"source {agent_dir}/hermes-agent/venv/bin/activate"
        activate_openclaw = f"source {agent_dir}/openclaw/venv/bin/activate"
        activate_aider = f"source {agent_dir}/aider/venv/bin/activate"
    
    lines = []
    if HermesInstaller().check_installed():
        lines.append(f"  {STAR} Hermes:  cd ~/agent-env/agents/hermes-agent && {activate_hermes} && hermes")
    if OpenClawInstaller().check_installed():
        lines.append(f"  {STAR} Open CLAW:  cd ~/agent-env/agents/openclaw && {activate_openclaw} && claw")
    if AiderInstaller().check_installed():
        lines.append(f"  {STAR} Aider:  cd ~/agent-env/agents/aider && {activate_aider} && aider")
    if CodexCliInstaller().check_installed():
        lines.append(f"  {STAR} Codex CLI:  codex （全局安装，任何目录可用）")
    if ClaudeCodeInstaller().check_installed():
        lines.append(f"  {STAR} Claude Code:  claude （全局安装，任何目录可用）")
    if ClineInstaller().check_installed():
        lines.append(f"  {STAR} Cline:  cline （全局安装，任何目录可用）")
    
    for line in lines:
        print(line)
    
    print()
    print_info(f"所有 Agent 安装位置: {agent_dir}")
    print()


def main():
    """主入口。"""
    try:
        show_welcome()

        # Windows 兼容提示：cmd 不支持 curl | python3
        if Platform.is_windows():
            print(f"  {INFO} {YELLOW}提示: Windows 用户如用 cmd，请改用 PowerShell 或使用以下命令:{RESET}")
            print(f"      {LIGHT_GREEN}python -c \"import urllib.request; exec(urllib.request.urlopen('https://zhenyuonline.cn/agent-installer.py').read())\"{RESET}")
            print()
        
        # 检查环境变量：AGENTS_TO_INSTALL=hermes,aider 可跳过交互菜单
        auto_val = os.environ.get("AGENTS_TO_INSTALL", "").strip()
        auto_mode = bool(auto_val)
        
        if auto_mode:
            indices = parse_agent_names(auto_val)
            if not indices:
                print_error(f"无效的 AGENTS_TO_INSTALL: {auto_val}")
                print_info("可用: hermes, openclaw, aider, codex, claude-code, cline, all")
                return
            check_environment(auto=True)
        else:
            check_environment()
            indices = show_agent_menu()
            if not indices:
                print_info("已退出")
                return
            if indices == ["uninstall"]:
                uninstall_indices = show_uninstall_menu()
                if uninstall_indices:
                    uninstall_agents(uninstall_indices)
                return

        install_agents(indices, auto=auto_mode)
        show_summary(indices)
        
        # Final tips
        print_header("还没装好？")
        print(f"  交互模式（选择菜单）:\n")
        print(f"    {LIGHT_GREEN}curl -fsSL https://zhenyuonline.cn/agent-installer.py | python3{RESET}\n")
        print(f"  一键模式（无需交互 — 自动安装指定组件）:\n")
        print(f"    {LIGHT_GREEN}AGENTS_TO_INSTALL=aider,hermes-agent curl -fsSL https://zhenyuonline.cn/agent-installer.py | python3{RESET}\n")
        print(f"  可选值: hermes, openclaw, aider, codex, claude-code, cline, all\n")
        print()
        
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}用户中断，已退出{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
