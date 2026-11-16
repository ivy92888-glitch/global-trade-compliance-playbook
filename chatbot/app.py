"""
Global Trade Assistant — 5 地区 × 9 节点 二选一模式
知识库体量有限，选地区或节点其中一个提问
"""
import os, sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rag import RAGChatbot, REGIONS, NODES

st.set_page_config(page_title="Global Trade Assistant", page_icon="📦", layout="wide")

def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if "chatbot" not in st.session_state:
    st.session_state.chatbot = RAGChatbot(base_dir=get_base_dir(), region="europe", node=None)
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("📦 Global Trade Assistant")
    st.caption("跨境物流问答助手")
    
    # ========== 二选一：地区 或 节点 ==========
    st.subheader("选择范围")
    mode = st.radio("模式", ["按地区", "按节点"], index=0, key="mode_radio",
                   label_visibility="collapsed")
    
    changed = False
    if mode == "按地区":
        region_keys = list(REGIONS.keys())
        region_labels = [REGIONS[r]["label"] for r in region_keys]
        current_label = REGIONS.get(st.session_state.chatbot.region, REGIONS["europe"])["label"]
        idx = region_labels.index(current_label) if current_label in region_labels else 0
        selected_label = st.radio("地区", region_labels, index=idx, key="region_radio")
        selected_region = region_keys[region_labels.index(selected_label)]
        if st.session_state.chatbot.node is not None or st.session_state.chatbot.region != selected_region:
            st.session_state.chatbot.switch_context(region=selected_region)
            changed = True
    else:
        node_keys = list(NODES.keys())
        node_labels = [NODES[n]["label"] for n in node_keys]
        current = st.session_state.chatbot.node if st.session_state.chatbot.node in NODES else node_keys[0]
        idx = node_keys.index(current)
        selected_node_label = st.radio("节点", node_labels, index=idx, key="node_radio")
        selected_node = node_keys[node_labels.index(selected_node_label)]
        if st.session_state.chatbot.node != selected_node:
            st.session_state.chatbot.switch_context(node=selected_node)
            changed = True
    
    if changed:
        st.session_state.messages = []
        status = st.session_state.chatbot.get_status()
        st.success(f"已切换 → {status['scope']}，知识库 {status['chunks']} 条")
        st.rerun()
    
    st.divider()
    
    with st.expander("API 设置", expanded=False):
        base_url = st.text_input("Base URL", value=os.environ.get("LLM_BASE_URL", "https://api.siliconflow.cn/v1"))
        api_key = st.text_input("API Key", value=os.environ.get("LLM_API_KEY", ""), type="password")
        model = st.text_input("Model", value=os.environ.get("LLM_MODEL", "deepseek-ai/DeepSeek-V3"))
        os.environ["LLM_BASE_URL"] = base_url
        os.environ["LLM_API_KEY"] = api_key
        os.environ["LLM_MODEL"] = model
    
    top_k = st.slider("Top-K", min_value=2, max_value=10, value=st.session_state.chatbot.top_k)
    st.session_state.chatbot.top_k = top_k

st.title("📦 跨境物流助手")

if not st.session_state.messages:
    st.info("👋 你好！选择一个范围后提问。地区维度（如欧洲清关）或节点维度（如港后操作），二选一。")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "sources" in msg:
            with st.expander("参考来源"):
                for src in msg["sources"]:
                    st.write(f"- {src}")

if prompt := st.chat_input("提问..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.spinner("检索知识库..."):
        retrieved = st.session_state.chatbot.retrieve(prompt)
    
    with st.chat_message("assistant"):
        try:
            stream = st.session_state.chatbot.stream_llm(prompt, retrieved=retrieved)
            full_response = ""
            placeholder = st.empty()
            for chunk in stream:
                full_response += chunk
                placeholder.markdown(full_response)
            
            sources = list(set(f"来源: {src} (相关度 {score:.2f})" 
                             for _, src, score in retrieved if score > 0.08))
            if sources:
                with st.expander("参考来源"):
                    for s in sources:
                        st.write(s)
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response, "sources": sources})
        except Exception as e:
            st.error(f"出错了：{str(e)}")
            st.session_state.messages.append({"role": "assistant", "content": f"抱歉：{str(e)}"})
