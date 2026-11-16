"""
Global Trade Assistant — 三选一模式：地区 / 节点 / 运输方式
知识库体量有限，三选一加载，不同时选
"""
import os, sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rag import RAGChatbot, REGIONS, NODES, TRANSPORT

st.set_page_config(page_title="Global Trade Assistant", page_icon="📦", layout="wide")

def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Force rebuild every load to filter stale state
st.session_state.chatbot = RAGChatbot(base_dir=get_base_dir(), mode="region", region="europe")
st.session_state._prev_mode = "region"
st.session_state._prev_key = "europe"

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("📦 Global Trade Assistant")
    st.caption("跨境物流问答助手")
    
    st.subheader("选择范围")
    mode_map = {"地区": "region", "节点": "node", "运输方式": "transport"}
    mode_label = st.radio("范围", list(mode_map.keys()), index=0, key="mode_radio",
                         label_visibility="collapsed")
    mode = mode_map[mode_label]
    
    if mode == "region":
        region_keys = list(REGIONS.keys())
        region_labels = [REGIONS[r]["label"] for r in region_keys]
        selected_label = st.radio("地区", region_labels, index=0, key="region_radio")
        selected_key = region_keys[region_labels.index(selected_label)]
    elif mode == "node":
        node_keys = list(NODES.keys())
        node_labels = [NODES[n]["label"] for n in node_keys]
        selected_label = st.radio("节点", node_labels, index=0, key="node_radio")
        selected_key = node_keys[node_labels.index(selected_label)]
    else:
        trans_keys = list(TRANSPORT.keys())
        trans_labels = [TRANSPORT[t]["label"] for t in trans_keys]
        selected_label = st.radio("运输方式", trans_labels, index=0, key="trans_radio")
        selected_key = trans_keys[trans_labels.index(selected_label)]
    
    # Rebuild chatbot if changed
    prev = st.session_state._prev_mode + ":" + st.session_state._prev_key
    curr = mode + ":" + selected_key
    if prev != curr:
        st.session_state.messages = []
        st.session_state.chatbot = RAGChatbot(
            base_dir=get_base_dir(),
            mode=mode,
            region=selected_key if mode == "region" else "europe",
            node=selected_key if mode == "node" else None,
            transport=selected_key if mode == "transport" else None,
        )
        st.session_state._prev_mode = mode
        st.session_state._prev_key = selected_key
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
    st.info("👋 你好！左侧选一个范围（地区 / 节点 / 运输方式）后提问。")

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
