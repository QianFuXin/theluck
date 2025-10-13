import os
import platform
import subprocess
from pathlib import Path


def run_cmd(cmd):
    """执行命令并返回输出（忽略错误）"""
    try:
        return subprocess.check_output(cmd, shell=True, text=True).strip()
    except Exception:
        return "N/A"


def get_system_context(history_lines=20):
    """收集系统上下文信息，返回一个 dict"""
    context = {}

    # 基础系统信息
    context["操作系统"] = platform.system()
    context["发行版本"] = run_cmd("grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '\"'") \
        if context["操作系统"] == "Linux" else "N/A"
    context["内核版本"] = run_cmd("uname -r")
    context["CPU 架构"] = run_cmd("uname -m")
    context["Shell"] = os.environ.get("SHELL", "unknown")

    # # 用户 & 路径
    # context["当前用户"] = run_cmd("whoami")
    # context["是否有 sudo 权限"] = "是" if run_cmd("groups").find("sudo") >= 0 else "否"
    # context["主目录"] = str(Path.home())
    # context["当前工作目录"] = os.getcwd()
    #
    # # 包管理器（简单探测）
    # for pm in ["apt", "yum", "dnf", "pacman", "brew"]:
    #     if run_cmd(f"which {pm}") != "N/A":
    #         context["包管理器"] = pm
    #         break
    # else:
    #     context["包管理器"] = "未知"

    # # 常用工具版本
    # tools = {
    #     "python": "python3 --version",
    #     "node": "node -v",
    #     "java": "java -version 2>&1 | head -n 1",
    #     "docker": "docker --version",
    #     "git": "git --version"
    # }
    # installed = {}
    # for tool, cmd in tools.items():
    #     out = run_cmd(cmd)
    #     if out != "N/A":
    #         installed[tool] = out
    # context["已安装工具"] = installed

    # # 最近命令历史
    # history_file = Path.home() / ".bash_history"
    # history = []
    # if history_file.exists():
    #     try:
    #         lines = history_file.read_text(encoding="utf-8").splitlines()
    #         history = lines[-history_lines:]
    #     except Exception:
    #         history = []
    # context["最近命令历史"] = history

    return context


def format_context(context: dict) -> str:
    """格式化上下文为字符串"""
    lines = []
    for key, value in context.items():
        if isinstance(value, dict):
            lines.append(f"- {key}: " + ", ".join(f"{k} {v}" for k, v in value.items()))
        elif isinstance(value, list):
            lines.append(f"- {key}:\n  " + "\n  ".join(value))
        else:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)


if __name__ == "__main__":
    ctx = get_system_context()
    print("=== 系统上下文信息 ===")
    print(format_context(ctx))
