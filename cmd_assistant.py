import os
import sys
import subprocess
import logging
from config import api_key
from system_context import get_system_context, format_context
from langchain_openai import ChatOpenAI

# =============== 日志配置 ===============
logging.basicConfig(
    level=logging.WARNING,  # 默认级别，可改为 INFO
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# =============== 构造提示词 ===============
def build_prompt(user_query: str, history_lines: int = 20) -> str:
    context = get_system_context(history_lines)
    context_text = format_context(context)

    prompt = f"""
你是一名专业的命令行助手。  
你的职责是根据用户的问题和提供的上下文，返回唯一可执行的命令行指令。  

上下文信息：
{context_text}

规则：
1. 只返回最终的命令行指令，不要附加解释或额外说明。  
2. 如果有多个可行解，选择最常见、最安全的一个。  
3. 如果无法确定，返回最可能的命令。  
4. 不要输出多余的格式，例如 Markdown、代码块、说明性文字。  

用户: {user_query}
助手:"""

    return prompt.strip()


# =============== 命令检测 ===============
def sanitize_command(cmd: str) -> bool:
    """
    检查命令是否合法（简单安全检查）
    - 不允许 rm -rf, shutdown, reboot 等危险操作
    - 仅允许单行命令
    """
    dangerous = ["rm -rf", "shutdown", "reboot", ":(){:|:&};:"]
    if any(d in cmd for d in dangerous):
        return False
    if "\n" in cmd or ";" in cmd:
        return False
    return True


# =============== 执行命令 ===============
def execute_command(cmd: str):
    try:
        output = subprocess.check_output(
            cmd, shell=True, stderr=subprocess.STDOUT, text=True
        )
        return output.strip()
    except subprocess.CalledProcessError as e:
        return f"[错误] 命令执行失败：\n{e.output.strip()}"


# =============== 主入口 ===============
if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("用法: python cmd_assistant.py \"你的问题\"")
        sys.exit(1)

    query = sys.argv[1]

    # 1. 构造提示词
    prompt = build_prompt(query).strip()
    logger.debug("=== 构造的提示词 ===\n%s", prompt)

    # 2. 调用大模型
    model = ChatOpenAI(
        # 从环境变量获取
        api_key=os.getenv("SILICONFLOW_API_KEY", api_key),
        model="Qwen/Qwen3-14B",
        base_url="https://api.siliconflow.cn/v1",
        temperature=0.01
    )
    model_output = model.invoke(prompt).content.strip()
    logger.info("模型输出命令: %s", model_output)

    # 3. 安全检测
    if not sanitize_command(model_output):
        logger.warning("检测到危险命令，已阻止执行: %s", model_output)
        sys.exit(1)
    # 4. 确认是否执行
    confirm = input(f"\n是否执行命令 {model_output}? (y/n): ").lower()
    if confirm == "y":
        logger.warning("开始执行命令: %s", model_output)
        result = execute_command(model_output)
        logger.warning("=== 执行结果 ===\n%s", result)
    else:
        logger.info("用户取消执行")
