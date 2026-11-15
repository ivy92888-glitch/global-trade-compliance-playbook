"""Streamlit 聊天界面

启动方式：
    streamlit run chatbot/app.py

首次启动会自动加载知识库并构建检索索引（约 2-3 秒）。
然后就可以在浏览器里聊天了。
"""
import sys, os

# 让 Streamlit 能 import 同级的 config / rag
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from chatbot import config
from chatbot.rag import CustomsChatbot


# ==================== 页面配置 ====================
st.set_page_config(
    page_title="清关合规智能客服 · Playbook",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Global Trade Compliance Chatbot")
st.caption("基于清关合规知识库的 RAG 问答机器人 · 支持自定义 LLM 端点")

# ==================== 侧边栏（配置） ====================
with st.sidebar:
    st.header("⚙️ LLM 配置")
    
    base_url = st.text_input(
        "API Base URL",
        value=config.LLM_BASE_URL,
        help="OpenAI-compatible 端点。Ollama: http://localhost:11434/v1",
    )
    api_key = st.text_input(
        "API Key",
        value=config.LLM_API_KEY,
        type="password",
        help="Ollama 可填任意值或留空",
    )
    model = st.text_input(
        "Model",
        value=config.LLM_MODEL,
        help="Ollama 本地模型名（qwen2.5 / llama3.2），API 端点模型名（deepseek-chat / qwen-plus / gpt-4o-mini）",
    )
    
    st.divider()
    
    top_k = st.slider("检索 top-K", min_value=3, max_value=10, value=config.TOP_K)
    st.caption("每次回答会参考多少个知识段落")
    
    st.divider()
    
    st.header("🔌 快速配置模板")
    st.markdown("""
    **本地 Ollama（免费离线）：**
    ```
    # 终端运行
    ollama serve &
    ollama pull qwen2.5
    # 然后在上面填：
    URL: http://localhost:11434/v1
    Key: ollama
    Model: qwen2.5
    ```
    
    **硅基流动 / OpenRouter：**
    ```
    URL: https://api.siliconflow.cn/v1
    Key: sk-xxxxxx
    Model: deepseek-ai/DeepSeek-V3
    ```
    """)
    
    st.divider()
    
    if st.button("🗑️ 清空对话"):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()


# ==================== 初始化（缓存） ====================

@st.cache_resource
def get_bot():
    """单例 bot 对象，Streamlit 会缓存它"""
    return CustomsChatbot()

bot = get_bot()


# ==================== 对话界面 ====================

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []  # 显示用的消息列表
if "history" not in st.session_state:
    st.session_state.history = []  # LLM 上下文用的历史（最多 6 轮）

# 欢迎语
if not st.session_state.messages:
    st.chat_message("assistant").write("""你好！我是清关合规智能客服 📚

我可以回答跨境清关相关的问题，比如：
- 灯具 / 玩具 / 陶瓷走哪个渠道？
- 比利时 vs 荷兰查验率差多少？
- HS 编码能改吗？怎么发起异议？
- VAT 递延怎么操作？CBAM 碳关税什么时候要交？
- 2026 年有哪些新规要注意？

直接问我就行 —— 比如：*"陶瓷发欧盟走比利时行不行？"*""")

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sources"):
            with st.expander(f"📚 参考来源（{len(msg['sources'])} 条）"):
                for src in msg["sources"]:
                    st.markdown(
                        f"**{src['chunk']['source']} → {src['chunk']['title']}** "
                        f"（相关性 {src['score']:.2%}）"
                    )

# 接收新问题
if query := st.chat_input("问我清关合规问题..."):
    # 显示用户问题
    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)
    
    # 调 RAG（带 loading spinner）
    with st.chat_message("assistant"):
        with st.spinner("📖 检索知识并生成回答..."):
            try:
                # 临时覆盖 config 值（不影响全局默认）
                import chatbot.config as _cfg
                _cfg.LLM_BASE_URL = base_url
                _cfg.LLM_API_KEY = api_key
                _cfg.LLM_MODEL = model
                _cfg.TOP_K = top_k
                
                answer, refs = bot.answer(
                    query,
                    history=st.session_state.history,
                    top_k=top_k,
                )
            except Exception as e:
                answer = f"❌ 出错了：{e}\n\n请检查侧边栏的 LLM 配置是否正确。"
                refs = []
    
    st.write(answer)
    
    # 显示参考来源
    if refs:
        with st.expander(f"📚 参考来源（{len(refs)} 条）"):
            for src in refs:
                st.markdown(
                    f"**{src['chunk']['source']} → {src['chunk']['title']}** "
                    f"（相关性 {src['score']:.2%}）"
                )
    
    # 存会话状态
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": refs,
    })
    st.session_state.history.append({"role": "assistant", "content": answer})
    
    # 历史最多保留 6 轮上下文（避免 token 爆炸）
    if len(st.session_state.history) > 12:
        st.session_state.history = st.session_state.history[-12:]
