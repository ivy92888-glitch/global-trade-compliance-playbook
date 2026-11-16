"""
Global Trade Compliance Assistant — 5 地区 × 9 节点 跨境物流合规问答

支持地区：欧洲 / 英国 / 美国 / 加拿大 / 东南亚
支持节点：港前 / 装柜 / 订舱 / 报关 / 投保 / 清关 / 港后 / 理赔 / 财务
"""
import os, sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rag import RAGChatbot, REGIONS, NODES

# ========== 页面配置 ==========
st.set_page_config(page_title="Global Trade Assistant", page_icon="📦", layout="wide")

# ========== 状态初始化 ==========
def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if "chatbot" not in st.session_state:
    st.session_state.chatbot = RAGChatbot(base_dir=get_base_dir(), region="europe", node="all")
if "messages" not in st.session_state:
    st.session_state.messages = []

# ========== 侧边栏 ==========
with st.sidebar:
    st.title("📦 Global Trade Assistant")
    st.caption("跨境物流问答助手")
    
    # 地区选择
    st.subheader("选择地区")
    region_keys = list(REGIONS.keys())
    region_labels = [REGIONS[r]["label"] for r in region_keys]
    current_region_label = REGIONS.get(st.session_state.chatbot.region, REGIONS["europe"])["label"]
    region_idx = region_labels.index(current_region_label) if current_region_label in region_labels else 0
    selected_region_label = st.radio("地区", region_labels, index=region_idx, key="region_radio")
    selected_region = region_keys[region_labels.index(selected_region_label)]
    
    # 节点选择（新增）
    st.subheader("选择节点")
    node_keys = list(NODES.keys())
    node_labels = [NODES[n]["label"] for n in node_keys]
    current_node_label = NODES.get(st.session_state.chatbot.node, NODES["all"])["label"]
    node_idx = node_labels.index(current_node_label) if current_node_label in node_labels else 0
    selected_node_label = st.radio("节点", node_labels, index=node_idx, key="node_radio")
    selected_node = node_keys[node_labels.index(selected_node_label)]
    
    # 检测切换
    if selected_region != st.session_state.chatbot.region or selected_node != st.session_state.chatbot.node:
        st.session_state.chatbot.switch_context(region=selected_region, node=selected_node)
        st.session_state.messages = []
        status = st.session_state.chatbot.get_status()
        st.success(f"已切换 → {status['region']} · {status['node']}，知识库 {status['chunks']} 条")
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
    st.caption("TF-IDF char n-gram · RAG 架构")

# ========== 主区域 ==========
status = st.session_state.chatbot.get_status()
scope = f"{status['region']}"
if status['node'] != "全部节点":
    scope += f" · {status['node']}"

st.title(f"📦 {scope} 跨境物流助手")
st.caption(f"知识库 {status['chunks']} 条 · 进出口申报 · VAT 递延 · 查验应对 · 产品认证 · 风控合规")

if not st.session_state.messages:
    st.info("👋 你好！我是跨境物流助手。选择地区和节点后，提问更精准；默认覆盖全部 9 个运营节点。")

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
            st.session_state.messages.append({"role": "assistant", "content": f"抱歉，调用 LLM 时出错：{str(e)}"})
