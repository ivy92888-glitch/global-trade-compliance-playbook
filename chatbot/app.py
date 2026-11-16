"""
Global Trade Compliance Assistant — 多地区跨境物流合规助手

支持地区：欧洲 / 英国 / 美国 / 加拿大 / 东南亚
覆盖：进出口申报、VAT 递延、查验应对、产品认证、风控合规、渠道选择、政策追踪
"""
import os, sys, time
import streamlit as st

# 确保能导入 rag
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rag import RAGChatbot, REGIONS

# ========== 页面配置 ==========
st.set_page_config(
    page_title="Global Trade Compliance Assistant",
    page_icon="📦",
    layout="wide",
)

# ========== 状态初始化 ==========
def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if "chatbot" not in st.session_state:
    st.session_state.chatbot = RAGChatbot(base_dir=get_base_dir(), region="europe")
if "messages" not in st.session_state:
    st.session_state.messages = []

# ========== 侧边栏 ==========
with st.sidebar:
    st.title("📦 Global Trade Compliance Assistant")
    st.caption("跨境物流合规问答助手")
    
    # 地区选择 —— 删 emoji 图标，只保留中文地区名
    st.subheader("选择地区")
    region_labels = [REGIONS[r]["label"].split()[-1] for r in REGIONS]  # 只取最后一个词（欧洲/英国/...）
    region_keys = list(REGIONS.keys())
    current_label = REGIONS.get(st.session_state.chatbot.region, REGIONS["europe"])["label"].split()[-1]
    
    selected_idx = region_labels.index(current_label) if current_label in region_labels else 0
    selected_label = st.radio("地区", region_labels, index=selected_idx)
    selected_region = region_keys[region_labels.index(selected_label)]
    
    if selected_region != st.session_state.chatbot.region:
        st.session_state.chatbot.switch_region(selected_region)
        st.session_state.messages = []
        st.success(f"已切换到 {selected_label}，知识库 {len(st.session_state.chatbot.chunks)} 条")
        st.rerun()
    
    st.divider()
    
    # API 配置
    st.subheader("LLM 配置")
    with st.expander("API 设置", expanded=False):
        base_url = st.text_input("API Base URL", 
            value=os.environ.get("LLM_BASE_URL", "https://api.siliconflow.cn/v1"))
        api_key = st.text_input("API Key", 
            value=os.environ.get("LLM_API_KEY", ""), type="password")
        model = st.text_input("Model", 
            value=os.environ.get("LLM_MODEL", "deepseek-ai/DeepSeek-V3"))
        
        os.environ["LLM_BASE_URL"] = base_url
        os.environ["LLM_API_KEY"] = api_key
        os.environ["LLM_MODEL"] = model
    
    # 检索参数
    st.subheader("检索参数")
    top_k = st.slider("Top-K 知识片段", min_value=2, max_value=10, 
                       value=st.session_state.chatbot.top_k)
    st.session_state.chatbot.top_k = top_k
    
    st.divider()
    st.caption("TF-IDF char n-gram 检索 + 自定义 prompt，RAG 架构")
    st.caption("仅基于公开合规常识，不提供规避建议")

# ========== 主区域 ==========
region_info = REGIONS.get(st.session_state.chatbot.region, REGIONS["europe"])
region_label = region_info["label"].split()[-1]  # 只取中文地区名

st.title(f"📦 {region_label} 跨境物流合规助手")
st.caption(f"知识库 {len(st.session_state.chatbot.chunks)} 条 · 进出口申报合规 · VAT 递延 · 产品认证 · 政策新规 · 查验应对")

# 欢迎语 —— 简化
if not st.session_state.messages:
    st.info("👋 你好！我是跨境物流合规助手。覆盖进出口申报、VAT 递延、查验应对、产品认证、风控合规、渠道选择、政策追踪等环节。")

# ========== 对话历史 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "sources" in msg:
            with st.expander("参考来源"):
                for src in msg["sources"]:
                    st.write(f"- {src}")

# ========== 输入框 ==========
if prompt := st.chat_input("提问..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # 检索
    with st.spinner("检索知识库..."):
        retrieved = st.session_state.chatbot.retrieve(prompt)
    
    # 生成回答
    with st.chat_message("assistant"):
        try:
            stream = st.session_state.chatbot.stream_llm(prompt, retrieved=retrieved)
            
            # 流式显示
            full_response = ""
            placeholder = st.empty()
            for chunk in stream:
                full_response += chunk
                placeholder.markdown(full_response)
            
            # 显示来源
            sources = list(set(f"来源: {src} (相关度 {score:.2f})" 
                             for _, src, score in retrieved if score > 0.08))
            if sources:
                with st.expander("参考来源"):
                    for s in sources:
                        st.write(s)
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_response,
                "sources": sources
            })
            
        except Exception as e:
            st.error(f"出错了：{str(e)}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"抱歉，调用 LLM 时出错：{str(e)}"
            })
