# === 可配置项 ===
# 优先读环境变量，没配就用默认值

# LLM API 端点（支持 OpenAI-compatible 的任何端点，包括 Ollama）
# Ollama 本地默认：http://localhost:11434/v1
# 通义千问：https://dashscope.aliyuncs.com/compatible-mode/v1
# DeepSeek：https://api.deepseek.com/v1
# OpenAI：https://api.openai.com/v1
import os

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "ollama")  # Ollama 不需要 key，但 API 端点要
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5")  # Ollama 用 qwen2.5，API 用 gpt-4o / deepseek-chat / qwen-plus 等

# 检索参数
CHUNK_SIZE = 500        # 每个 chunk 目标字数
CHUNK_OVERLAP = 50      # chunk 间重叠字数
TOP_K = 5               # 检索 top-K 个 chunk

# 知识库路径（相对于项目根目录）
KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")

# 系统提示词
SYSTEM_PROMPT = """你是一个跨境清关合规智能客服助手。你的所有知识都来自提供的参考材料。

**规则**：
1. 优先使用参考材料中的具体数字和结论（如查验费用 1200-1900 欧、申报 30% 底线等）
2. 如果参考材料里没提到，就明说"我不确定，建议向清关行确认"，不要瞎编
3. 回答要结构化——分点、用表格、给决策建议
4. 如果你觉得用户的问题还可以追问更多信息来给出更好的建议，主动问（比如"你这批货的品类是什么？"、"走哪个国家入境？"）
5. 不要用"可能"、"大概"这类模糊词，有具体数据就用具体数据
6. 如果涉及风险提醒，要显眼地标出来

**输出格式建议**：
- 📋 核心建议（1-3 句话直接给答案）
- 📊 数据参考（数字、比例、对比）
- ⚠️ 风险提示
- 📚 相关知识出处（来自哪个文件）
"""
